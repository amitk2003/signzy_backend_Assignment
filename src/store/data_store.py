"""
In-Memory Data Store
---------------------
This is the central storage for all data in the application.
Instead of using a real database, we keep everything in memory using
Python dictionaries and lists. This makes the project easy to run
without any database setup.

Note: All data is lost when the server restarts. That's fine for this
assignment since we just need to demonstrate the routing logic.
"""

import threading
from datetime import datetime


class DataStore:
    """Holds all application data in memory with thread-safe access."""

    def __init__(self):
        # vendors stored as: { "vendor_id": { vendor_data } }
        self.vendors = {}

        # routing configs stored as: { "CAPABILITY_NAME": { config_data } }
        self.routing_configs = {}

        # metrics stored as: { "vendor_name": { metrics_data } }
        self.vendor_metrics = {}

        # list of all routing decision logs
        self.routing_logs = []

        # rate limit tracking: { "vendor_name": { "count": N, "window_start": timestamp } }
        self.rate_limits = {}

        # round-robin counters: { "CAPABILITY_NAME": counter }
        self.round_robin_counters = {}

        # lock for thread safety when multiple requests come in at once
        self._lock = threading.Lock()

    # ---- Vendor operations ----

    def add_vendor(self, vendor_data):
        """Add or update a vendor. If vendor with same name + capability exists, update it."""
        with self._lock:
            vendor_id = vendor_data.get("id")
            self.vendors[vendor_id] = vendor_data

            # set up empty metrics if this vendor doesn't have any yet
            vendor_name = vendor_data.get("name")
            if vendor_name not in self.vendor_metrics:
                self.vendor_metrics[vendor_name] = {
                    "vendor_name": vendor_name,
                    "total_requests": 0,
                    "successful_requests": 0,
                    "failed_requests": 0,
                    "total_latency_ms": 0,
                    "avg_latency_ms": 0,
                    "success_rate": 100.0,
                    "error_rate": 0.0,
                    "last_called": None,
                    "is_healthy": True,
                    "latency_history": [],  # keep last 20 latency values
                    "consecutive_failures": 0
                }
        return vendor_data

    def get_all_vendors(self):
        """Get all registered vendors as a list."""
        with self._lock:
            return list(self.vendors.values())

    def get_vendors_by_capability(self, capability):
        """Get all vendors that support a specific capability."""
        with self._lock:
            result = []
            for vendor in self.vendors.values():
                if vendor.get("capability") == capability:
                    result.append(vendor)
            return result

    def find_vendor_by_name_and_capability(self, name, capability):
        """Check if a vendor with this name and capability already exists."""
        with self._lock:
            for vendor in self.vendors.values():
                if vendor.get("name") == name and vendor.get("capability") == capability:
                    return vendor
            return None

    # ---- Routing config operations ----

    def set_routing_config(self, capability, config):
        """Set the routing configuration for a capability."""
        with self._lock:
            self.routing_configs[capability] = config

    def get_routing_config(self, capability):
        """Get routing config for a specific capability."""
        with self._lock:
            return self.routing_configs.get(capability)

    def get_all_routing_configs(self):
        """Get all routing configurations."""
        with self._lock:
            return dict(self.routing_configs)

    # ---- Metrics operations ----

    def record_request(self, vendor_name, success, latency_ms):
        """Record a vendor call result and update metrics."""
        with self._lock:
            if vendor_name not in self.vendor_metrics:
                # shouldn't happen, but handle it just in case
                self.vendor_metrics[vendor_name] = {
                    "vendor_name": vendor_name,
                    "total_requests": 0,
                    "successful_requests": 0,
                    "failed_requests": 0,
                    "total_latency_ms": 0,
                    "avg_latency_ms": 0,
                    "success_rate": 100.0,
                    "error_rate": 0.0,
                    "last_called": None,
                    "is_healthy": True,
                    "latency_history": [],
                    "consecutive_failures": 0
                }

            metrics = self.vendor_metrics[vendor_name]
            metrics["total_requests"] += 1
            metrics["total_latency_ms"] += latency_ms
            metrics["last_called"] = datetime.now().isoformat()

            # keep track of last 20 latency values for avg calculation
            metrics["latency_history"].append(latency_ms)
            if len(metrics["latency_history"]) > 20:
                metrics["latency_history"] = metrics["latency_history"][-20:]

            if success:
                metrics["successful_requests"] += 1
                metrics["consecutive_failures"] = 0
            else:
                metrics["failed_requests"] += 1
                metrics["consecutive_failures"] += 1

            # recalculate rates
            total = metrics["total_requests"]
            if total > 0:
                metrics["success_rate"] = round(
                    (metrics["successful_requests"] / total) * 100, 2
                )
                metrics["error_rate"] = round(
                    (metrics["failed_requests"] / total) * 100, 2
                )
                metrics["avg_latency_ms"] = round(
                    metrics["total_latency_ms"] / total, 2
                )

            # determine health: unhealthy if error rate > 50% or 5 consecutive failures
            if metrics["error_rate"] > 50 or metrics["consecutive_failures"] >= 5:
                metrics["is_healthy"] = False
            else:
                metrics["is_healthy"] = True

    def get_vendor_metrics(self, vendor_name):
        """Get metrics for a specific vendor."""
        with self._lock:
            return self.vendor_metrics.get(vendor_name)

    def get_all_metrics(self):
        """Get metrics for all vendors."""
        with self._lock:
            # return without internal fields like latency_history
            result = {}
            for name, metrics in self.vendor_metrics.items():
                clean = {k: v for k, v in metrics.items() if k != "latency_history"}
                result[name] = clean
            return result

    def is_vendor_healthy(self, vendor_name):
        """Check if a vendor is currently healthy."""
        with self._lock:
            metrics = self.vendor_metrics.get(vendor_name)
            if metrics is None:
                return True  # no data yet, assume healthy
            return metrics.get("is_healthy", True)

    def get_avg_latency(self, vendor_name):
        """Get average latency for a vendor from recent history."""
        with self._lock:
            metrics = self.vendor_metrics.get(vendor_name)
            if not metrics or not metrics.get("latency_history"):
                return float("inf")  # no data, return infinity so it gets lowest priority
            history = metrics["latency_history"]
            return sum(history) / len(history)

    # ---- Rate limit operations ----

    def check_rate_limit(self, vendor_name, limit_per_minute):
        """Check if vendor is under its rate limit. Returns True if OK to proceed."""
        with self._lock:
            now = datetime.now()

            if vendor_name not in self.rate_limits:
                self.rate_limits[vendor_name] = {
                    "count": 0,
                    "window_start": now
                }

            rl = self.rate_limits[vendor_name]

            # reset window if a minute has passed
            elapsed = (now - rl["window_start"]).total_seconds()
            if elapsed >= 60:
                rl["count"] = 0
                rl["window_start"] = now

            # check if under limit
            if rl["count"] >= limit_per_minute:
                return False

            return True

    def increment_rate_limit(self, vendor_name):
        """Increment the rate limit counter for a vendor."""
        with self._lock:
            if vendor_name in self.rate_limits:
                self.rate_limits[vendor_name]["count"] += 1

    # ---- Routing logs ----

    def add_routing_log(self, log_entry):
        """Add a routing decision log entry."""
        with self._lock:
            self.routing_logs.append(log_entry)
            # keep only last 500 logs to prevent memory issues
            if len(self.routing_logs) > 500:
                self.routing_logs = self.routing_logs[-500:]

    def get_routing_logs(self, limit=50, capability=None, vendor=None, status=None):
        """Get recent routing logs with optional filtering."""
        with self._lock:
            logs = self.routing_logs
            if capability:
                capability = capability.upper()
                logs = [log for log in logs if log.get("capability") == capability]
            if vendor:
                logs = [log for log in logs if log.get("vendor_used") == vendor]
            if status:
                logs = [log for log in logs if log.get("status") == status]
                
            return list(reversed(logs[-limit:] if limit else logs))

    # ---- Round robin ----

    def get_round_robin_index(self, capability, vendor_count):
        """Get next vendor index for round-robin and increment counter."""
        with self._lock:
            if capability not in self.round_robin_counters:
                self.round_robin_counters[capability] = 0

            index = self.round_robin_counters[capability] % vendor_count
            self.round_robin_counters[capability] += 1
            return index


# single global instance - all parts of the app use this same store
store = DataStore()
