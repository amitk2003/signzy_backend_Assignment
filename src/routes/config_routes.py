"""
Routing Config Routes
-----------------------
Handles setting and retrieving routing configurations.
A routing config tells the system HOW to route traffic for a specific capability.

Endpoints:
    POST /routing-config   - Set routing config for a capability
    GET  /routing-config   - Get all routing configs (or filter by capability)
"""

from flask import Blueprint, request, jsonify

from src.store.data_store import store
from src.strategies.strategy_router import get_available_strategies

config_bp = Blueprint("config", __name__)

# valid strategy names
VALID_STRATEGIES = get_available_strategies()


@config_bp.route("/routing-config", methods=["POST"])
def set_config():
    """
    Set routing configuration for a capability.
    
    Required fields: capability, strategy
    Optional fields: vendors (list), latencyThresholdMs, errorRateThreshold
    
    Example body:
    {
        "capability": "PAN_VERIFICATION",
        "strategy": "weighted",
        "latencyThresholdMs": 2000,
        "errorRateThreshold": 50
    }
    """
    data = request.get_json()

    if not data:
        return jsonify({"error": "Request body is required (JSON)"}), 400

    capability = data.get("capability")
    strategy = data.get("strategy")

    if not capability:
        return jsonify({"error": "'capability' is required"}), 400

    if not strategy:
        return jsonify({"error": "'strategy' is required. Available: " + ", ".join(VALID_STRATEGIES)}), 400

    # normalize
    capability = capability.upper().strip()
    strategy = strategy.lower().strip()

    # validate strategy name (we'll accept it but warn - strategy_router handles fallback)
    if strategy not in VALID_STRATEGIES and strategy.replace("-", "_") not in VALID_STRATEGIES:
        return jsonify({
            "error": f"Unknown strategy: '{strategy}'",
            "available_strategies": VALID_STRATEGIES
        }), 400

    config = {
        "capability": capability,
        "strategy": strategy,
        "latencyThresholdMs": data.get("latencyThresholdMs"),
        "errorRateThreshold": data.get("errorRateThreshold", 50),
        "vendors": data.get("vendors", [])
    }

    store.set_routing_config(capability, config)

    return jsonify({
        "message": f"Routing config set for {capability}",
        "config": config
    }), 200


@config_bp.route("/routing-config", methods=["GET"])
def get_config():
    """
    Get routing configuration.
    Use ?capability=PAN_VERIFICATION to get config for a specific capability.
    Without query param, returns all configs.
    """
    capability = request.args.get("capability")

    if capability:
        capability = capability.upper().strip()
        config = store.get_routing_config(capability)
        if config is None:
            return jsonify({
                "error": f"No routing config found for {capability}",
                "hint": "Set one with POST /routing-config"
            }), 404
        return jsonify({"config": config}), 200
    else:
        all_configs = store.get_all_routing_configs()
        return jsonify({
            "count": len(all_configs),
            "configs": all_configs
        }), 200
