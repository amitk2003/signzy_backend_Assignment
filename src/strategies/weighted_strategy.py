"""
Weighted Routing Strategy
--------------------------
Distributes traffic across vendors based on their weight values.
For example, if VendorA has weight 70 and VendorB has weight 30,
roughly 70% of traffic goes to A and 30% to B.

Uses a random number against cumulative weights to pick a vendor.
"""

import random


def select_vendor(available_vendors, _store):
    """
    Select vendor based on weight distribution.
    
    Args:
        available_vendors: list of vendor dicts that passed health/rate checks
        _store: data store instance (not used here)
    
    Returns:
        selected vendor dict, or None if no vendors available
    """
    if not available_vendors:
        return None

    # if only one vendor, just return it
    if len(available_vendors) == 1:
        return available_vendors[0]

    # calculate total weight
    total_weight = 0
    for vendor in available_vendors:
        total_weight += vendor.get("weight", 1)

    # handle edge case where all weights are 0
    if total_weight == 0:
        return random.choice(available_vendors)

    # pick random number between 0 and total weight
    pick = random.uniform(0, total_weight)

    # walk through vendors with cumulative weight
    cumulative = 0
    for vendor in available_vendors:
        cumulative += vendor.get("weight", 1)
        if pick <= cumulative:
            return vendor

    # fallback - shouldn't reach here but just in case
    return available_vendors[-1]
