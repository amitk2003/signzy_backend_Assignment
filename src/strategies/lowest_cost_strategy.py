"""
Lowest Cost Routing Strategy
------------------------------
Picks the vendor with the lowest cost per request.
Simple but effective when you want to minimize spending.

If two vendors have the same cost, picks the one that appears first.
"""


def select_vendor(available_vendors, _store):
    """
    Select vendor with lowest cost per request.
    
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

    # sort by cost - lowest cost first
    # if cost is not set, treat it as very high (9999)
    sorted_vendors = sorted(
        available_vendors,
        key=lambda v: v.get("costPerRequest", 9999)
    )

    return sorted_vendors[0]
