"""
Failover Handler
------------------
This is the core of the routing system. It coordinates everything:
1. Gets the routing config for the requested capability
2. Filters out unhealthy and rate-limited vendors
3. Applies the selected routing strategy to pick a vendor
4. Calls the vendor
5. If the call fails, tries the next vendor (failover)
6. Logs every routing decision

The failover chain continues until either:
- A vendor succeeds
- All vendors have been tried and failed
"""

from datetime import datetime
import uuid

from src.store.data_store import store
from src.services import vendor_caller
from src.services import metrics_tracker
from src.services import rate_limiter
from src.strategies import strategy_router


def route_request(capability, payload, required_features=None):
    """
    Route a request to the best available vendor.
    
    This is the main function that handles the entire routing flow including
    failover. It returns a standardized response regardless of which vendor
    handled the request.
    
    Args:
        capability: the capability needed (e.g., "PAN_VERIFICATION")
        payload: the request data to send to the vendor
        required_features: list of features the vendor must support (optional)
    
    Returns:
        dict with: success, data, metadata (including routing decision info)
    """
    request_id = str(uuid.uuid4())[:8]
    timestamp = datetime.now().isoformat()

    # step 1: get all vendors for this capability
    all_vendors = store.get_vendors_by_capability(capability)

    if not all_vendors:
        log_entry = _create_log(request_id, timestamp, capability, None, "FAILED",
                                "No vendors registered for this capability", None)
        store.add_routing_log(log_entry)
        return {
            "success": False,
            "data": None,
            "error": f"No vendors registered for capability: {capability}",
            "metadata": {
                "request_id": request_id,
                "capability": capability,
                "vendor_used": None,
                "strategy": None,
                "failover_chain": [],
                "timestamp": timestamp
            }
        }

    # step 2: get routing config
    config = store.get_routing_config(capability)
    strategy_name = "priority"  # default

    if config:
        strategy_name = config.get("strategy", "priority")

    strategy_module, actual_strategy = strategy_router.get_strategy(strategy_name)

    # step 3: filter vendors - remove unhealthy and rate-limited ones
    available_vendors = []
    skipped_vendors = []

    for vendor in all_vendors:
        vendor_name = vendor.get("name")
        skip_reason = None

        # check health
        if not metrics_tracker.is_healthy(vendor_name):
            skip_reason = "unhealthy (high error rate or consecutive failures)"

        # check rate limit
        elif not rate_limiter.can_proceed(vendor_name, vendor.get("rateLimitPerMinute")):
            skip_reason = "rate limit exceeded"

        # check required features
        elif required_features:
            vendor_features = vendor.get("supportedFeatures", [])
            missing = [f for f in required_features if f not in vendor_features]
            if missing:
                skip_reason = f"missing required features: {', '.join(missing)}"

        # check latency threshold
        elif config and config.get("latencyThresholdMs"):
            threshold = config["latencyThresholdMs"]
            if not metrics_tracker.check_latency_threshold(vendor_name, threshold):
                skip_reason = f"average latency exceeds threshold ({threshold}ms)"

        if skip_reason:
            skipped_vendors.append({"vendor": vendor_name, "reason": skip_reason})
        else:
            available_vendors.append(vendor)

    if not available_vendors:
        # all vendors are either unhealthy, rate-limited, or missing features
        log_entry = _create_log(request_id, timestamp, capability, None, "FAILED",
                                "All vendors unavailable", skipped_vendors)
        store.add_routing_log(log_entry)
        return {
            "success": False,
            "data": None,
            "error": "All vendors are currently unavailable",
            "metadata": {
                "request_id": request_id,
                "capability": capability,
                "vendor_used": None,
                "strategy": actual_strategy,
                "skipped_vendors": skipped_vendors,
                "failover_chain": [],
                "timestamp": timestamp
            }
        }

    # step 4: try vendors with failover
    failover_chain = []
    tried_vendors = set()

    while available_vendors:
        # pick a vendor using the selected strategy
        if actual_strategy == "round-robin" or actual_strategy == "round_robin":
            selected = strategy_module.select_vendor(available_vendors, store, capability)
        else:
            selected = strategy_module.select_vendor(available_vendors, store)

        if selected is None:
            break

        vendor_name = selected.get("name")

        # prevent trying the same vendor twice
        if vendor_name in tried_vendors:
            available_vendors.remove(selected)
            continue

        tried_vendors.add(vendor_name)

        # step 5: call the vendor
        result = vendor_caller.call_vendor(selected, payload)

        # record metrics
        metrics_tracker.record_call(vendor_name, result["success"], result["latency_ms"])

        # record rate limit usage
        rate_limiter.record_usage(vendor_name)

        if result["success"]:
            # vendor call succeeded
            failover_chain.append({
                "vendor": vendor_name,
                "status": "SUCCESS",
                "latency_ms": result["latency_ms"]
            })

            log_entry = _create_log(request_id, timestamp, capability, vendor_name,
                                    "SUCCESS", actual_strategy, skipped_vendors,
                                    failover_chain, result["latency_ms"])
            store.add_routing_log(log_entry)

            return {
                "success": True,
                "data": result["data"],
                "error": None,
                "metadata": {
                    "request_id": request_id,
                    "capability": capability,
                    "vendor_used": vendor_name,
                    "strategy": actual_strategy,
                    "latency_ms": result["latency_ms"],
                    "skipped_vendors": skipped_vendors,
                    "failover_chain": failover_chain,
                    "timestamp": timestamp
                }
            }
        else:
            # vendor call failed - add to failover chain and try next
            failover_chain.append({
                "vendor": vendor_name,
                "status": "FAILED",
                "error": result["error"],
                "latency_ms": result["latency_ms"]
            })

            # remove this vendor from available list so we don't pick it again
            available_vendors = [v for v in available_vendors if v.get("name") != vendor_name]

    # all vendors failed
    log_entry = _create_log(request_id, timestamp, capability, None, "FAILED",
                            "All vendors failed after failover", skipped_vendors,
                            failover_chain)
    store.add_routing_log(log_entry)

    return {
        "success": False,
        "data": None,
        "error": "All vendors failed to process the request",
        "metadata": {
            "request_id": request_id,
            "capability": capability,
            "vendor_used": None,
            "strategy": actual_strategy,
            "skipped_vendors": skipped_vendors,
            "failover_chain": failover_chain,
            "timestamp": timestamp
        }
    }


def _create_log(request_id, timestamp, capability, vendor_used, status,
                reason_or_strategy, skipped_vendors=None, failover_chain=None,
                latency_ms=None):
    """Create a routing log entry."""
    return {
        "request_id": request_id,
        "timestamp": timestamp,
        "capability": capability,
        "vendor_used": vendor_used,
        "status": status,
        "strategy": reason_or_strategy if status == "SUCCESS" else None,
        "reason": reason_or_strategy if status == "FAILED" else None,
        "latency_ms": latency_ms,
        "skipped_vendors": skipped_vendors or [],
        "failover_chain": failover_chain or []
    }
