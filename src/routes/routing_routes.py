"""
Routing Routes
----------------
Handles the core routing endpoint and supporting endpoints.

Endpoints:
    POST /route           - Route a request to the best vendor
    GET  /vendor-metrics  - Get performance metrics for all vendors
    GET  /routing-logs    - Get routing decision history
    GET  /health          - Health check
"""

from flask import Blueprint, request, jsonify
from datetime import datetime

from src.services import failover_handler
from src.services import metrics_tracker
from src.store.data_store import store

routing_bp = Blueprint("routing", __name__)


@routing_bp.route("/route", methods=["POST"])
def route_request():
    """
    Route a request to the best available vendor.
    
    This is the main endpoint clients use. The client sends what capability
    they need and the payload, and the system figures out which vendor to use.
    
    Required fields: capability
    Optional fields: payload (any data), requiredFeatures (list of strings)
    
    Example body:
    {
        "capability": "PAN_VERIFICATION",
        "payload": {
            "pan_number": "ABCDE1234F",
            "name": "John Doe"
        },
        "requiredFeatures": ["name_match"]
    }
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body is required (JSON)"}), 400

    capability = data.get("capability")

    if not capability:
        return jsonify({"error": "'capability' is required"}), 400

    # normalize
    capability = capability.upper().strip()

    if not capability:
        return jsonify({"error": "'capability' cannot be empty"}), 400

    payload = data.get("payload", {})
    required_features = data.get("requiredFeatures", None)

    # validate requiredFeatures if provided
    if required_features is not None and not isinstance(required_features, list):
        return jsonify({"error": "'requiredFeatures' must be a list of strings"}), 400

    # do the actual routing
    result = failover_handler.route_request(capability, payload, required_features)

    if result["success"]:
        return jsonify(result), 200
    else:
        return jsonify(result), 503


@routing_bp.route("/vendor-metrics", methods=["GET"])
def get_metrics():
    """
    Get performance metrics for all vendors.
    
    Returns metrics like total requests, success rate, error rate,
    average latency, and health status for each vendor.
    
    Use ?vendor=VendorA to get metrics for a specific vendor.
    """
    vendor_name = request.args.get("vendor")

    if vendor_name:
        vendor_name = vendor_name.strip()
        metrics = metrics_tracker.get_metrics(vendor_name)
        if metrics is None:
            return jsonify({"error": f"No metrics found for vendor: {vendor_name}"}), 404
        return jsonify({"metrics": metrics}), 200
    else:
        all_metrics = metrics_tracker.get_all_metrics()
        return jsonify({
            "count": len(all_metrics),
            "metrics": all_metrics
        }), 200


@routing_bp.route("/routing-logs", methods=["GET"])
def get_routing_logs():
    """
    Get routing decision logs.
    
    Shows the history of routing decisions: which vendor was selected,
    which were skipped and why, failover chains, etc.
    
    Use ?limit=N to control how many logs to return (default: 50).
    """
    limit = request.args.get("limit", 50)

    try:
        limit = int(limit)
        if limit < 1:
            limit = 1
        if limit > 200:
            limit = 200
    except (ValueError, TypeError):
        limit = 50

    logs = store.get_routing_logs(limit)

    return jsonify({
        "count": len(logs),
        "logs": logs
    }), 200


@routing_bp.route("/health", methods=["GET"])
def health_check():
    """
    Health check endpoint.
    Returns the overall status of the system including vendor counts
    and a quick summary.
    """
    all_vendors = store.get_all_vendors()
    all_metrics = metrics_tracker.get_all_metrics()

    # count healthy vs unhealthy vendors
    healthy_count = 0
    unhealthy_count = 0
    for name, metrics in all_metrics.items():
        if metrics.get("is_healthy", True):
            healthy_count += 1
        else:
            unhealthy_count += 1

    # vendors without metrics are assumed healthy
    vendors_without_metrics = len(all_vendors) - len(all_metrics)
    healthy_count += vendors_without_metrics

    return jsonify({
        "status": "healthy",
        "timestamp": datetime.now().isoformat(),
        "summary": {
            "total_vendors": len(all_vendors),
            "healthy_vendors": healthy_count,
            "unhealthy_vendors": unhealthy_count,
            "total_routing_configs": len(store.get_all_routing_configs())
        }
    }), 200
