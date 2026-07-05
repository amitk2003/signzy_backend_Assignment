"""
Feature Based Routing Strategy
------------------------------
Picks the vendor that supports the highest number of features.
"""

def select_vendor(available_vendors, _store):
    """
    Select vendor with the most supported features.
    
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

    # sort by number of supported features descending
    sorted_vendors = sorted(
        available_vendors,
        key=lambda v: len(v.get("supportedFeatures", [])),
        reverse=True
    )

    return sorted_vendors[0]
