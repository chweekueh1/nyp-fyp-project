#!/usr/bin/env python3
"""
Timezone utilities for the NYP FYP Chatbot.
Provides consistent timezone handling across the application.
"""

import os
from datetime import datetime, timezone, timedelta
from typing import Optional

# Singapore timezone (UTC+8)
SINGAPORE_TZ = timezone(timedelta(hours=8))


def get_app_timezone() -> timezone:
    """
    Get the application timezone.

    :return: Singapore timezone (UTC+8)
    :rtype: timezone
    """
    return SINGAPORE_TZ


def now_singapore() -> datetime:
    """
    Get current datetime in Singapore timezone.

    :return: Current datetime in Singapore timezone
    :rtype: datetime
    """
    return datetime.now(SINGAPORE_TZ)


def utc_to_singapore(utc_dt: datetime) -> datetime:
    """
    Convert UTC datetime to Singapore timezone.

    :param utc_dt: UTC datetime object
    :type utc_dt: datetime
    :return: Datetime in Singapore timezone
    :rtype: datetime
    """
    if utc_dt.tzinfo is None:
        utc_dt = utc_dt.replace(tzinfo=timezone.utc)
    return utc_dt.astimezone(SINGAPORE_TZ)


def singapore_to_utc(sg_dt: datetime) -> datetime:
    """
    Convert Singapore datetime to UTC.

    :param sg_dt: Singapore datetime object
    :type sg_dt: datetime
    :return: Datetime in UTC
    :rtype: datetime
    """
    if sg_dt.tzinfo is None:
        sg_dt = sg_dt.replace(tzinfo=SINGAPORE_TZ)
    return sg_dt.astimezone(timezone.utc)


def format_singapore_datetime(
    dt: Optional[datetime] = None, format_str: str = "%Y-%m-%d %H:%M:%S %Z"
) -> str:
    """
    Format datetime in Singapore timezone.

    :param dt: Datetime object (defaults to current time)
    :type dt: Optional[datetime]
    :param format_str: Format string for datetime
    :type format_str: str
    :return: Formatted datetime string
    :rtype: str
    """
    if dt is None:
        dt = now_singapore()
    elif dt.tzinfo is None:
        # Assume UTC if no timezone info
        dt = dt.replace(tzinfo=timezone.utc).astimezone(SINGAPORE_TZ)
    elif dt.tzinfo != SINGAPORE_TZ:
        dt = dt.astimezone(SINGAPORE_TZ)

    return dt.strftime(format_str)


def get_iso_timestamp_singapore(dt: Optional[datetime] = None) -> str:
    """
    Get ISO format timestamp in Singapore timezone.

    :param dt: Datetime object (defaults to current time)
    :type dt: Optional[datetime]
    :return: ISO format timestamp with Singapore timezone
    :rtype: str
    """
    if dt is None:
        dt = now_singapore()
    elif dt.tzinfo is None:
        dt = dt.replace(tzinfo=timezone.utc).astimezone(SINGAPORE_TZ)
    elif dt.tzinfo != SINGAPORE_TZ:
        dt = dt.astimezone(SINGAPORE_TZ)

    return dt.isoformat()


def get_utc_timestamp(dt: Optional[datetime] = None) -> str:
    """
    Get UTC timestamp for storage (maintains UTC for consistency).

    :param dt: Datetime object (defaults to current time)
    :type dt: Optional[datetime]
    :return: ISO format UTC timestamp
    :rtype: str
    """
    if dt is None:
        dt = datetime.now(timezone.utc)
    elif dt.tzinfo is None:
        dt = dt.replace(tzinfo=SINGAPORE_TZ)

    # Convert to UTC for storage
    utc_dt = dt.astimezone(timezone.utc)
    return utc_dt.isoformat()


def parse_stored_timestamp(timestamp_str: str) -> datetime:
    """
    Parse stored timestamp and return as Singapore timezone.

    :param timestamp_str: ISO format timestamp string
    :type timestamp_str: str
    :return: Datetime in Singapore timezone
    :rtype: datetime
    """
    try:
        # Parse the timestamp
        dt = datetime.fromisoformat(timestamp_str.replace("Z", "+00:00"))

        # If no timezone info, assume UTC
        if dt.tzinfo is None:
            dt = dt.replace(tzinfo=timezone.utc)

        # Convert to Singapore timezone for display
        return dt.astimezone(SINGAPORE_TZ)
    except Exception:
        # Fallback to current time if parsing fails
        return now_singapore()


def get_timezone_info() -> dict:
    """
    Get timezone information for debugging.

    :return: Timezone information
    :rtype: dict
    """
    now_utc = datetime.now(timezone.utc)
    now_sg = now_singapore()

    return {
        "app_timezone": "Asia/Singapore (UTC+8)",
        "current_utc": now_utc.isoformat(),
        "current_singapore": now_sg.isoformat(),
        "timezone_offset": "+08:00",
        "system_timezone": os.environ.get("TZ", "Not set"),
    }
