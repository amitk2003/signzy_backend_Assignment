"""
Vendor Routes
---------------
Handles vendor registration and listing.

Endpoints:
    POST /vendors   - Register a new vendor
    GET  /vendors   - List all vendors (optionally filter by capability)
"""

from flask import Blueprint, request, jsonify
import uuid

from src.store.data_store import store

vendor_bp = Blueprint("vendors", __name__)


@vendor_bp.route("/vendors", methods=["POST"])
def register_vendor():
    """
    Register a new vendor or update an existing one.
    
    Required fields: name, capability
    Optional fields: costPerRequest, timeoutMs, rateLimitPerMinute, 
                     priority, weight, supportedFeatures
    
    If a vendor with the same name and capability already exists,
    it updates the existing entry instead of creating a duplicate.
    """
    data = request.get_json()

    # validate required fields
    if not data:
        return jsonify({"error": "Request body is required (JSON)"}), 400

    name = data.get("name")
    capability = data.get("capability")

    if not name:
        return jsonify({"error": "'name' is required"}), 400

    if not capability:
        return jsonify({"error": "'capability' is required"}), 400

    # check for whitespace-only values
    if not name.strip():
        return jsonify({"error": "'name' cannot be empty"}), 400

    if not capability.strip():
        return jsonify({"error": "'capability' cannot be empty"}), 400

    # normalize capability to uppercase
    capability = capability.upper().strip()
    name = name.strip()

    # validate numeric fields if provided
    cost = data.get("costPerRequest", 1.0)
    timeout = data.get("timeoutMs", 3000)
    rate_limit = data.get("rateLimitPerMinute", 100)
    priority = data.get("priority", 1)
    weight = data.get("weight", 50)

    if not isinstance(cost, (int, float)) or cost < 0:
        return jsonify({"error": "'costPerRequest' must be a non-negative number"}), 400

    if not isinstance(timeout, (int, float)) or timeout <= 0:
        return jsonify({"error": "'timeoutMs' must be a positive number"}), 400

    if not isinstance(rate_limit, (int, float)) or rate_limit <= 0:
        return jsonify({"error": "'rateLimitPerMinute' must be a positive number"}), 400

    if not isinstance(priority, (int, float)) or priority < 1:
        return jsonify({"error": "'priority' must be a number >= 1"}), 400

    if not isinstance(weight, (int, float)) or weight < 0:
        return jsonify({"error": "'weight' must be a non-negative number"}), 400

    # check if vendor already exists (same name + capability)
    existing = store.find_vendor_by_name_and_capability(name, capability)
    is_update = existing is not None

    vendor_id = existing.get("id") if existing else str(uuid.uuid4())[:8]

    vendor_data = {
        "id": vendor_id,
        "name": name,
        "capability": capability,
        "costPerRequest": float(cost),
        "timeoutMs": int(timeout),
        "rateLimitPerMinute": int(rate_limit),
        "priority": int(priority),
        "weight": int(weight),
        "supportedFeatures": data.get("supportedFeatures", []),
    }

    store.add_vendor(vendor_data)

    status_code = 200 if is_update else 201
    message = "Vendor updated successfully" if is_update else "Vendor registered successfully"

    return jsonify({
        "message": message,
        "vendor": vendor_data
    }), status_code


@vendor_bp.route("/vendors", methods=["GET"])
def list_vendors():
    """
    List all registered vendors.
    Optionally filter by capability using query param: ?capability=PAN_VERIFICATION
    """
    capability_filter = request.args.get("capability")

    if capability_filter:
        capability_filter = capability_filter.upper().strip()
        vendors = store.get_vendors_by_capability(capability_filter)
    else:
        vendors = store.get_all_vendors()

    return jsonify({
        "count": len(vendors),
        "vendors": vendors
    }), 200
