"""
Failover Routing Strategy
------------------------------
Picks the vendor strictly based on priority. Failover to the next priority is handled universally by the failover handler.
"""

def select_vendor(available_vendors, _store):
    """
    Select vendor based on priority for failover chain.
    
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

    # sort by priority - lower number means higher priority
    sorted_vendors = sorted(
        available_vendors,
        key=lambda v: v.get("priority", 999)
    )

    return sorted_vendors[0]
