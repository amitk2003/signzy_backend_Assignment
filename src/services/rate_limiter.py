"""
Rate Limiter
--------------
Handles per-vendor rate limiting. Each vendor has a maximum number
of requests it can handle per minute (rateLimitPerMinute).

Before routing to a vendor, we check if it still has capacity.
After routing, we increment its counter.

The window resets automatically after 60 seconds.
"""

from src.store.data_store import store


def can_proceed(vendor_name, limit_per_minute):
    """
    Check if a vendor is under its rate limit.
    
    Args:
        vendor_name: name of the vendor to check
        limit_per_minute: maximum requests per minute for this vendor
    
    Returns:
        True if the vendor can accept more requests, False if rate limited
    """
    if limit_per_minute is None or limit_per_minute <= 0:
        return True  # no limit set, always allow

    return store.check_rate_limit(vendor_name, limit_per_minute)


def record_usage(vendor_name):
    """
    Increment the rate limit counter after routing to a vendor.
    Call this AFTER successfully routing a request.
    """
    store.increment_rate_limit(vendor_name)
