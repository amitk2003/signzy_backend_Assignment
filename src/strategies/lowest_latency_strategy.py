"""
Lowest Latency Routing Strategy
---------------------------------
Picks the vendor with the lowest average response time based on
recent performance data. If a vendor has no history yet, it gets
a chance to be tried (treated as having 0 latency initially).

Great for performance-sensitive applications where speed matters most.
"""


def select_vendor(available_vendors, store):
    """
    Select vendor with lowest average latency from recent metrics.
    
    Args:
        available_vendors: list of vendor dicts that passed health/rate checks
        store: data store instance (used to read latency metrics)
    
    Returns:
        selected vendor dict, or None if no vendors available
    """
    if not available_vendors:
        return None

    if len(available_vendors) == 1:
        return available_vendors[0]

    best_vendor = None
    best_latency = float("inf")

    for vendor in available_vendors:
        vendor_name = vendor.get("name")
        avg_latency = store.get_avg_latency(vendor_name)

        # vendors with no history get a latency of 0 (give them a chance)
        if avg_latency == float("inf"):
            avg_latency = 0

        if avg_latency < best_latency:
            best_latency = avg_latency
            best_vendor = vendor

    # if somehow none was selected, pick the first one
    if best_vendor is None:
        return available_vendors[0]

    return best_vendor
