"""
Health Based Routing Strategy
------------------------------
Picks the vendor with the best health metrics (highest success rate).
"""

from src.services import metrics_tracker

def select_vendor(available_vendors, _store):
    """
    Select vendor with highest success rate.
    
    Args:
        available_vendors: list of vendor dicts that passed health/rate checks
        _store: data store instance (not used here)
    
    Returns:
        selected vendor dict, or None if no vendors available
    """
    if not available_vendors:
        return None

    if len(available_vendors) == 1:
        return available_vendors[0]

    def health_score(vendor):
        metrics = metrics_tracker.get_metrics(vendor.get("name"))
        if not metrics:
            return 100.0  # Assume perfect health if no metrics
        return metrics.get("success_rate", 100.0)

    # sort by success rate descending
    sorted_vendors = sorted(
        available_vendors,
        key=health_score,
        reverse=True
    )

    return sorted_vendors[0]
