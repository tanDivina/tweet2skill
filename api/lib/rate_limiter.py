"""
Rate limiting logic using Upstash Redis.

Provides burst, daily, and monthly rate-limit checks.
All counters use atomic INCR with auto-expiring keys.
"""

import time
from api.lib import upstash


def _current_day_key_suffix():
    """UTC date string for daily bucket keys, e.g. '2026-06-23'."""
    return time.strftime("%Y-%m-%d", time.gmtime())


def _current_month_key_suffix():
    """UTC year-month string for monthly bucket keys, e.g. '2026-06'."""
    return time.strftime("%Y-%m", time.gmtime())


def check_burst(identifier: str) -> dict:
    """Check burst rate: max 3 calls per 60-second window.

    Args:
        identifier: unique string (IP, userId, or deviceId)

    Returns:
        {allowed: bool, remaining: int, limit: int, reset: int}
    """
    limit = 3
    window = 60  # seconds
    key = f"burst:{identifier}"

    count = upstash.incr_with_ttl(key, window)
    remaining = max(0, limit - count)
    current_ttl = upstash.ttl(key)
    reset_at = int(time.time()) + max(current_ttl, 0)

    return {
        "allowed": count <= limit,
        "remaining": remaining,
        "limit": limit,
        "reset": reset_at,
    }


def check_daily(identifier: str, limit: int = 10) -> dict:
    """Check daily rate: max `limit` calls per UTC day.

    Used for free-tier limiting per deviceId AND per IP.

    Args:
        identifier: unique string (deviceId or IP)
        limit: daily cap (default 10)

    Returns:
        {allowed: bool, remaining: int, limit: int, reset: int}
    """
    day = _current_day_key_suffix()
    key = f"daily:{identifier}:{day}"

    # 86400 seconds in a day; keys auto-expire at end of window
    count = upstash.incr_with_ttl(key, 86400)
    remaining = max(0, limit - count)
    current_ttl = upstash.ttl(key)
    reset_at = int(time.time()) + max(current_ttl, 0)

    return {
        "allowed": count <= limit,
        "remaining": remaining,
        "limit": limit,
        "reset": reset_at,
    }


def check_monthly(user_id: str, limit: int = 1250) -> dict:
    """Check monthly rate: max `limit` calls per calendar month.

    Used for Pro tier.

    Args:
        user_id: authenticated user ID
        limit: monthly cap (default 1250)

    Returns:
        {allowed: bool, remaining: int, limit: int, reset: int}
    """
    month = _current_month_key_suffix()
    key = f"monthly:{user_id}:{month}"

    # ~31 days max; use 32 days to be safe
    count = upstash.incr_with_ttl(key, 86400 * 32)
    remaining = max(0, limit - count)
    current_ttl = upstash.ttl(key)
    reset_at = int(time.time()) + max(current_ttl, 0)

    return {
        "allowed": count <= limit,
        "remaining": remaining,
        "limit": limit,
        "reset": reset_at,
    }


def get_daily_usage(identifier: str) -> int:
    """Get the current daily usage count for an identifier (no increment)."""
    day = _current_day_key_suffix()
    key = f"daily:{identifier}:{day}"
    val = upstash.get(key)
    return int(val) if val else 0


def get_monthly_usage(user_id: str) -> int:
    """Get the current monthly usage count for a user (no increment)."""
    month = _current_month_key_suffix()
    key = f"monthly:{user_id}:{month}"
    val = upstash.get(key)
    return int(val) if val else 0


def check_weekly(identifier: str, limit: int = 10) -> dict:
    """Check weekly rate: max `limit` calls per UTC week.

    Used for free-tier limiting per deviceId AND per IP.

    Args:
        identifier: unique string (deviceId or IP)
        limit: weekly cap (default 10)

    Returns:
        {allowed: bool, remaining: int, limit: int, reset: int}
    """
    week = time.strftime("%G-W%V", time.gmtime())
    key = f"weekly:{identifier}:{week}"

    # 7 days max; auto-expire at end of window
    count = upstash.incr_with_ttl(key, 86400 * 7)
    remaining = max(0, limit - count)
    current_ttl = upstash.ttl(key)
    reset_at = int(time.time()) + max(current_ttl, 0)

    return {
        "allowed": count <= limit,
        "remaining": remaining,
        "limit": limit,
        "reset": reset_at,
    }


def get_weekly_usage(identifier: str) -> int:
    """Get the current weekly usage count for an identifier (no increment)."""
    week = time.strftime("%G-W%V", time.gmtime())
    key = f"weekly:{identifier}:{week}"
    val = upstash.get(key)
    return int(val) if val else 0

