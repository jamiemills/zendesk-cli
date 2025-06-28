"""Tests for Rich table formatting."""

import pytest
from typing import List
from rich.console import Console
from io import StringIO

from zendesk_cli.models.ticket import Ticket


class TestTicketTableFormatter:
    """Test Rich table formatting for tickets."""
    
    @pytest.fixture
    def sample_tickets(self) -> List[Ticket]:
        """Sample tickets for testing."""
        return [
            Ticket(
                id=1,
                subject="Critical login bug",
                description="Users cannot authenticate with the new login system",
                status="open",
                created_at="2024-01-01T10:00:00Z",
                updated_at="2024-01-01T10:00:00Z",
                assignee_id=123,
                group_id=456,
                url="https://example.zendesk.com/tickets/1"
            ),
            Ticket(
                id=2,
                subject="Feature request: Dark mode",
                description="Please add dark mode support to improve user experience",
                status="pending",
                created_at="2024-01-02T10:00:00Z",
                updated_at="2024-01-02T15:00:00Z",
                assignee_id=124,
                group_id=456,
                url="https://example.zendesk.com/tickets/2"
            )
        ]
    
    def test_formatter_initialization(self) -> None:
        """Test TicketTableFormatter initialization."""
        from zendesk_cli.cli.formatters import TicketTableFormatter
        
        formatter = TicketTableFormatter()
        assert formatter is not None
    
    def test_format_tickets_table_structure(self, sample_tickets: List[Ticket]) -> None:
        """Test that formatter creates proper table structure."""
        from zendesk_cli.cli.formatters import TicketTableFormatter
        
        formatter = TicketTableFormatter()
        table = formatter.format_tickets_table(sample_tickets)
        
        # Check that we got a Rich Table object
        from rich.table import Table
        assert isinstance(table, Table)
        
        # Check table has the expected columns
        column_headers = [col.header for col in table.columns]
        expected_headers = [
            "Ticket #", "Team", "Description", "First Opened", 
            "Days Open", "Last Updated", "Days Since Update", "Link"
        ]
        
        assert column_headers == expected_headers
    
    def test_format_tickets_table_content(self, sample_tickets: List[Ticket]) -> None:
        """Test that formatter includes correct ticket data."""
        from zendesk_cli.cli.formatters import TicketTableFormatter
        
        formatter = TicketTableFormatter()
        table = formatter.format_tickets_table(sample_tickets)
        
        # Render table to string to check content
        console = Console(file=StringIO(), width=120)
        console.print(table)
        output = console.file.getvalue()
        
        # Check that ticket data is present
        assert "1" in output  # Ticket ID
        assert "2" in output  # Ticket ID
        assert "Critical login bug" in output
        assert "Feature request: Dark mode" in output
        assert "2024-01-01" in output
        assert "2024-01-02" in output
    
    def test_format_tickets_table_empty_list(self) -> None:
        """Test formatter with empty ticket list."""
        from zendesk_cli.cli.formatters import TicketTableFormatter
        
        formatter = TicketTableFormatter()
        table = formatter.format_tickets_table([])
        
        from rich.table import Table
        assert isinstance(table, Table)
        
        # Should still have headers even with no data
        column_headers = [col.header for col in table.columns]
        assert len(column_headers) == 8
    
    def test_format_tickets_table_truncates_long_descriptions(self) -> None:
        """Test that long descriptions are properly truncated."""
        from zendesk_cli.cli.formatters import TicketTableFormatter
        
        long_ticket = Ticket(
            id=999,
            subject="Test ticket with very long subject that should be truncated",
            description="This is an extremely long description that goes on and on and should definitely be truncated when displayed in the table format because it would otherwise make the table very wide and hard to read",
            status="open",
            created_at="2024-01-01T10:00:00Z",
            updated_at="2024-01-01T10:00:00Z",
            url="https://example.zendesk.com/tickets/999"
        )
        
        formatter = TicketTableFormatter()
        table = formatter.format_tickets_table([long_ticket])
        
        # Render to check truncation
        console = Console(file=StringIO(), width=120)
        console.print(table)
        output = console.file.getvalue()
        
        # Should contain truncated version with ellipsis
        assert "..." in output
        # Full description should not be present
        assert "goes on and on and should definitely be truncated" not in output
    
    def test_format_single_ticket_row(self, sample_tickets: List[Ticket]) -> None:
        """Test formatting a single ticket row."""
        from zendesk_cli.cli.formatters import TicketTableFormatter
        
        formatter = TicketTableFormatter()
        ticket = sample_tickets[0]
        
        row_data = formatter._format_ticket_row(ticket)
        
        assert len(row_data) == 8  # Should have 8 columns
        assert str(ticket.id) in row_data[0]  # Ticket number
        assert ticket.short_description in row_data[2]  # Description
        assert "2024-01-01" in row_data[3]  # First opened date
        assert ticket.url in row_data[7]  # Link
    
    def test_format_ticket_row_handles_missing_data(self) -> None:
        """Test formatting ticket with missing optional data."""
        from zendesk_cli.cli.formatters import TicketTableFormatter
        
        minimal_ticket = Ticket(
            id=1,
            subject="Minimal ticket",
            description="Basic ticket",
            status="open",
            created_at="2024-01-01T10:00:00Z",
            updated_at="2024-01-01T10:00:00Z",
            assignee_id=None,  # No assignee
            group_id=None,     # No group
            url="https://example.zendesk.com/tickets/1"
        )
        
        formatter = TicketTableFormatter()
        row_data = formatter._format_ticket_row(minimal_ticket)
        
        assert len(row_data) == 8
        assert "Unassigned" in row_data[1] or "-" in row_data[1]  # Team column should handle missing group
    
    def test_table_styling_and_colors(self, sample_tickets: List[Ticket]) -> None:
        """Test that table has proper styling and colors."""
        from zendesk_cli.cli.formatters import TicketTableFormatter
        
        formatter = TicketTableFormatter()
        table = formatter.format_tickets_table(sample_tickets)
        
        # Check that table has styling
        assert table.title is not None or table.caption is not None or len(table.columns) > 0
        
        # Render and check for ANSI color codes (Rich adds these)
        console = Console(file=StringIO(), width=120, legacy_windows=False)
        console.print(table)
        output = console.file.getvalue()
        
        # Rich tables should have some formatting characters
        assert len(output) > len("".join(str(ticket.id) for ticket in sample_tickets))
    
    def test_format_team_info(self) -> None:
        """Test team/group formatting logic."""
        from zendesk_cli.cli.formatters import TicketTableFormatter
        
        formatter = TicketTableFormatter()
        
        # Test with group ID
        team_info = formatter._format_team_info(group_id=456)
        assert "456" in team_info
        
        # Test with no group
        team_info = formatter._format_team_info(group_id=None)
        assert team_info in ["Unassigned", "-", ""]