"""
Priority-Based Routing Strategy
---------------------------------
Picks the vendor with the lowest priority number (priority 1 = highest).
If two vendors have the same priority, picks the first one found.

This is the simplest and most predictable strategy. Good when you have
a clear preference for which vendor to use first.
"""


def select_vendor(available_vendors, _store):
    """
    Select vendor with highest priority (lowest priority number).
    
    Args:
        available_vendors: list of vendor dicts that passed health/rate checks
        _store: data store instance (not used in this strategy but kept for consistency)
    
    Returns:
        selected vendor dict, or None if no vendors available
    """
    if not available_vendors:
        return None

    # sort by priority number - lower number means higher priority
    # if priority is not set, treat it as very low priority (999)
    sorted_vendors = sorted(
        available_vendors,
        key=lambda v: v.get("priority", 999)
    )

    return sorted_vendors[0]
