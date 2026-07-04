"""
Intelligent Vendor Routing Platform
-------------------------------------
Main entry point for the application.

This sets up the Flask server, registers all route blueprints,
and loads sample data so the system is ready to use right after starting.

Run with: py app.py
Server starts on: http://localhost:3000
"""

import json
import os
from flask import Flask, jsonify

from src.routes.vendor_routes import vendor_bp
from src.routes.routing_routes import routing_bp
from src.routes.config_routes import config_bp
from src.store.data_store import store


def create_app():
    """Create and configure the Flask application."""
    app = Flask(__name__)

    # register route blueprints
    app.register_blueprint(vendor_bp)
    app.register_blueprint(routing_bp)
    app.register_blueprint(config_bp)

    # root endpoint - welcome message with API overview
    @app.route("/", methods=["GET"])
    def home():
        return jsonify({
            "message": "Intelligent Vendor Routing Platform",
            "version": "1.0.0",
            "endpoints": {
                "POST /vendors": "Register a new vendor",
                "GET /vendors": "List all vendors",
                "POST /route": "Route a request to best vendor",
                "GET /vendor-metrics": "Get vendor performance metrics",
                "GET /routing-logs": "Get routing decision history",
                "GET /health": "Health check",
                "POST /routing-config": "Set routing config for a capability",
                "GET /routing-config": "Get routing configurations"
            }
        }), 200

    # handle 404 errors
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "error": "Endpoint not found",
            "hint": "Try GET / to see all available endpoints"
        }), 404

    # handle 405 errors (wrong HTTP method)
    @app.errorhandler(405)
    def method_not_allowed(error):
        return jsonify({
            "error": "HTTP method not allowed for this endpoint"
        }), 405

    # handle 500 errors
    @app.errorhandler(500)
    def internal_error(error):
        return jsonify({
            "error": "Internal server error. Something went wrong on our end."
        }), 500

    return app


def load_sample_data():
    """
    Load sample vendors and routing configs from the configs/ directory.
    This gives the system some data to work with right away.
    """
    config_dir = os.path.join(os.path.dirname(__file__), "configs")

    # load sample vendors
    vendors_file = os.path.join(config_dir, "sample-vendors.json")
    if os.path.exists(vendors_file):
        try:
            with open(vendors_file, "r") as f:
                vendors = json.load(f)
            for vendor in vendors:
                vendor["capability"] = vendor.get("capability", "").upper()
                if "id" not in vendor:
                    import uuid
                    vendor["id"] = str(uuid.uuid4())[:8]
                store.add_vendor(vendor)
            print(f"[INFO] Loaded {len(vendors)} sample vendors")
        except Exception as e:
            print(f"[WARNING] Could not load sample vendors: {e}")

    # load sample routing config
    config_file = os.path.join(config_dir, "sample-routing-config.json")
    if os.path.exists(config_file):
        try:
            with open(config_file, "r") as f:
                configs = json.load(f)
            # handle both single config and list of configs
            if isinstance(configs, dict):
                configs = [configs]
            for config in configs:
                capability = config.get("capability", "").upper()
                if capability:
                    store.set_routing_config(capability, config)
            print(f"[INFO] Loaded {len(configs)} sample routing config(s)")
        except Exception as e:
            print(f"[WARNING] Could not load sample routing configs: {e}")


if __name__ == "__main__":
    app = create_app()

    # load sample data
    load_sample_data()

    print("\n" + "=" * 55)
    print("  Intelligent Vendor Routing Platform")
    print("  Running on: http://localhost:3000")
    print("  Press Ctrl+C to stop")
    print("=" * 55 + "\n")

    app.run(host="0.0.0.0", port=3000, debug=True)
