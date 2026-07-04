"""
Round-Robin Routing Strategy
------------------------------
Cycles through available vendors in order. Each request goes to the
next vendor in line. When it reaches the end, it wraps back to the start.

Good for distributing load evenly when all vendors are roughly equal.
"""


def select_vendor(available_vendors, store, capability="default"):
    """
    Select next vendor in round-robin order.
    
    Args:
        available_vendors: list of vendor dicts that passed health/rate checks
        store: data store instance (used to track round-robin counter)
        capability: the capability name (used as key for counter)
    
    Returns:
        selected vendor dict, or None if no vendors available
    """
    if not available_vendors:
        return None

    if len(available_vendors) == 1:
        return available_vendors[0]

    # get next index from the store's round-robin counter
    index = store.get_round_robin_index(capability, len(available_vendors))

    return available_vendors[index]
