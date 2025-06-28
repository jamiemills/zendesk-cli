"""Date and time utilities for zendesk-cli."""

from __future__ import annotations

from datetime import datetime


def days_between(date1: datetime, date2: datetime) -> int:
    """Calculate the number of days between two dates.
    
    Args:
        date1: First date
        date2: Second date
        
    Returns:
        Number of days between the dates (absolute value)
    """
    return abs((date2.date() - date1.date()).days)


def parse_zendesk_datetime(dt_str: str) -> datetime:
    """Parse a Zendesk datetime string to a Python datetime object.
    
    Args:
        dt_str: ISO format datetime string (e.g., "2024-01-01T10:00:00Z")
        
    Returns:
        Python datetime object
        
    Raises:
        ValueError: If the datetime string cannot be parsed
    """
    try:
        # Handle Zendesk's ISO format with 'Z' suffix
        if dt_str.endswith('Z'):
            dt_str = dt_str[:-1] + '+00:00'
        return datetime.fromisoformat(dt_str).replace(tzinfo=None)
    except ValueError as e:
        raise ValueError(f"Invalid datetime format: {dt_str}") from e


def format_date_for_display(dt: datetime) -> str:
    """Format a datetime for display in the CLI.
    
    Args:
        dt: Datetime to format
        
    Returns:
        Formatted date string (YYYY-MM-DD)
    """
    return dt.strftime("%Y-%m-%d")