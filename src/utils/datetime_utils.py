"""
Datetime utilities to prevent timezone-aware/naive comparison errors
"""
from datetime import datetime, timezone, timedelta


def now_utc() -> datetime:
    """Get current UTC time (timezone-aware)"""
    return datetime.now(timezone.utc)


def now_naive() -> datetime:
    """Get current time (timezone-naive) - use sparingly"""
    return datetime.now()


def ensure_utc(dt: datetime) -> datetime:
    """
    Ensure datetime is timezone-aware (UTC)
    
    Args:
        dt: datetime object (aware or naive)
    
    Returns:
        Timezone-aware datetime in UTC
    """
    if dt.tzinfo is None:
        # Naive datetime - assume UTC
        return dt.replace(tzinfo=timezone.utc)
    return dt.astimezone(timezone.utc)


def safe_timedelta(dt1: datetime, dt2: datetime) -> timedelta:
    """
    Safely calculate timedelta between two datetimes
    Handles timezone-aware and naive datetimes
    
    Args:
        dt1: First datetime
        dt2: Second datetime
    
    Returns:
        timedelta between the two datetimes
    """
    # Ensure both are timezone-aware
    dt1 = ensure_utc(dt1)
    dt2 = ensure_utc(dt2)
    return dt1 - dt2


def days_ago(dt: datetime) -> int:
    """
    Calculate days between datetime and now
    
    Args:
        dt: datetime to compare
    
    Returns:
        Number of days ago (positive) or in future (negative)
    """
    delta = safe_timedelta(now_utc(), dt)
    return delta.days


def hours_ago(dt: datetime) -> float:
    """
    Calculate hours between datetime and now
    
    Args:
        dt: datetime to compare
    
    Returns:
        Number of hours ago (positive) or in future (negative)
    """
    delta = safe_timedelta(now_utc(), dt)
    return delta.total_seconds() / 3600
