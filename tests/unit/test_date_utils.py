"""Tests for date utilities."""

import pytest
from datetime import datetime
from freezegun import freeze_time


class TestDateUtils:
    """Test date utility functions."""
    
    def test_days_between_same_day(self) -> None:
        """Test days_between returns 0 for same day."""
        from zendesk_cli.utils.date_utils import days_between
        
        date1 = datetime(2024, 1, 1, 10, 0, 0)
        date2 = datetime(2024, 1, 1, 15, 0, 0)
        
        assert days_between(date1, date2) == 0
    
    def test_days_between_different_days(self) -> None:
        """Test days_between calculates correctly for different days."""
        from zendesk_cli.utils.date_utils import days_between
        
        date1 = datetime(2024, 1, 1, 10, 0, 0)
        date2 = datetime(2024, 1, 5, 15, 0, 0)
        
        assert days_between(date1, date2) == 4
    
    def test_days_between_reverse_order(self) -> None:
        """Test days_between with dates in reverse order."""
        from zendesk_cli.utils.date_utils import days_between
        
        date1 = datetime(2024, 1, 5, 10, 0, 0)
        date2 = datetime(2024, 1, 1, 15, 0, 0)
        
        assert days_between(date1, date2) == 4
    
    def test_parse_zendesk_datetime_valid(self) -> None:
        """Test parsing valid Zendesk datetime string."""
        from zendesk_cli.utils.date_utils import parse_zendesk_datetime
        
        dt_str = "2024-01-01T10:00:00Z"
        result = parse_zendesk_datetime(dt_str)
        
        assert result == datetime(2024, 1, 1, 10, 0, 0)
    
    def test_parse_zendesk_datetime_invalid(self) -> None:
        """Test parsing invalid datetime string raises ValueError."""
        from zendesk_cli.utils.date_utils import parse_zendesk_datetime
        
        with pytest.raises(ValueError):
            parse_zendesk_datetime("invalid-date")
    
    def test_format_date_for_display(self) -> None:
        """Test formatting date for display."""
        from zendesk_cli.utils.date_utils import format_date_for_display
        
        dt = datetime(2024, 1, 1, 15, 30, 45)
        result = format_date_for_display(dt)
        
        assert result == "2024-01-01"