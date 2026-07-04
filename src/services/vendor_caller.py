"""
Vendor Caller (Simulator)
---------------------------
Since we don't have actual third-party vendor APIs to call,
this module simulates what would happen when we call a vendor.

It generates realistic results:
- Random latency (between 50ms and vendor's timeout)
- Random success/failure (about 85% success rate by default)
- Timeout simulation (if latency exceeds vendor's timeoutMs)

In a real production system, this would be replaced with actual
HTTP calls to vendor APIs using something like the requests library.
"""

import random
import time


def call_vendor(vendor, payload):
    """
    Simulate calling a vendor API.
    
    Args:
        vendor: vendor dict with name, timeoutMs, etc.
        payload: the request payload (used in response)
    
    Returns:
        dict with: success (bool), latency_ms (int), data (dict), error (str or None)
    """
    vendor_name = vendor.get("name", "Unknown")
    timeout_ms = vendor.get("timeoutMs", 3000)

    # simulate some processing time
    # most calls are fast (100-500ms), some are slow
    if random.random() < 0.1:
        # 10% chance of slow response
        simulated_latency = random.randint(timeout_ms - 500, timeout_ms + 1000)
    else:
        # normal response time
        simulated_latency = random.randint(50, min(800, timeout_ms))

    # actually wait a tiny bit to make it feel real (but not too long)
    # we'll wait 1/100th of the simulated time so tests don't take forever
    actual_wait = min(simulated_latency / 1000, 0.05)
    time.sleep(actual_wait)

    # check if it timed out
    if simulated_latency > timeout_ms:
        return {
            "success": False,
            "latency_ms": simulated_latency,
            "data": None,
            "error": f"Vendor {vendor_name} timed out after {simulated_latency}ms (limit: {timeout_ms}ms)"
        }

    # simulate random failures (about 15% failure rate)
    if random.random() < 0.15:
        error_types = [
            f"Vendor {vendor_name} returned HTTP 500 Internal Server Error",
            f"Vendor {vendor_name} returned HTTP 503 Service Unavailable",
            f"Vendor {vendor_name} connection refused",
            f"Vendor {vendor_name} returned invalid response format"
        ]
        return {
            "success": False,
            "latency_ms": simulated_latency,
            "data": None,
            "error": random.choice(error_types)
        }

    # success case - return a standardized mock response
    return {
        "success": True,
        "latency_ms": simulated_latency,
        "data": {
            "verified": True,
            "confidence": round(random.uniform(0.85, 0.99), 2),
            "details": {
                "source": vendor_name,
                "processing_time_ms": simulated_latency,
                "payload_received": payload
            }
        },
        "error": None
    }
