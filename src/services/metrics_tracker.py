"""
Metrics Tracker
-----------------
Wraps the data store's metrics operations with higher-level functions.
Provides easy-to-use methods for recording results and checking vendor health.

This sits between the routing logic and the data store, adding some
business logic on top of raw metric storage.
"""

from src.store.data_store import store


def record_call(vendor_name, success, latency_ms):
    """
    Record the result of a vendor API call.
    
    Args:
        vendor_name: name of the vendor that was called
        success: whether the call was successful (True/False)
        latency_ms: how long the call took in milliseconds
    """
    store.record_request(vendor_name, success, latency_ms)


def is_healthy(vendor_name):
    """
    Check if a vendor is healthy enough to receive traffic.
    A vendor is unhealthy if:
    - Error rate is above 50%
    - Has 5 or more consecutive failures
    
    Returns True if healthy, False if not.
    """
    return store.is_vendor_healthy(vendor_name)


def get_metrics(vendor_name):
    """Get detailed metrics for a specific vendor."""
    return store.get_vendor_metrics(vendor_name)


def get_all_metrics():
    """Get metrics for all vendors."""
    return store.get_all_metrics()


def get_avg_latency(vendor_name):
    """Get average latency for a vendor based on recent calls."""
    return store.get_avg_latency(vendor_name)


def check_latency_threshold(vendor_name, threshold_ms):
    """
    Check if a vendor's average latency is below the threshold.
    
    Args:
        vendor_name: vendor to check
        threshold_ms: maximum acceptable average latency
    
    Returns:
        True if latency is acceptable, False if it's too high
    """
    avg = store.get_avg_latency(vendor_name)
    if avg == float("inf"):
        return True  # no data yet, give it a chance
    return avg <= threshold_ms
