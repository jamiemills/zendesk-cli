"""Rich table formatters for CLI output."""

from typing import List, Optional, Dict, Any
from rich.table import Table
from rich.text import Text

from ..models.ticket import Ticket
from ..utils.date_utils import format_date_for_display


class TicketTableFormatter:
    """Formatter for displaying tickets in a Rich table."""
    
    def __init__(self) -> None:
        """Initialize the formatter."""
        pass
    
    def format_tickets_table(self, tickets: List[Ticket]) -> Table:
        """Format a list of tickets as a Rich table.
        
        Args:
            tickets: List of tickets to format
            
        Returns:
            Rich Table object ready for display
        """
        # Create table with styling
        table = Table(
            title="🎫 Zendesk Tickets",
            show_header=True,
            header_style="bold magenta",
            border_style="bright_blue",
            row_styles=["none", "dim"]
        )
        
        # Add columns - let Rich handle width automatically for better display
        table.add_column("Ticket #", style="cyan", no_wrap=True)
        table.add_column("Status", style="bright_magenta", no_wrap=True)
        table.add_column("Team", style="green", no_wrap=True)
        table.add_column("Description", style="white")
        table.add_column("Opened", style="yellow", no_wrap=True)
        table.add_column("Days Since Opened", style="red", justify="right", no_wrap=True)
        table.add_column("Updated", style="yellow", no_wrap=True)
        table.add_column("Days Since Updated", style="red", justify="right", no_wrap=True)
        table.add_column("Link", style="blue", no_wrap=True)
        
        # Add rows
        for ticket in tickets:
            row_data = self._format_ticket_row(ticket)
            table.add_row(*row_data)
        
        return table
    
    def _format_ticket_row(self, ticket: Ticket) -> List[str]:
        """Format a single ticket as a table row.
        
        Args:
            ticket: Ticket to format
            
        Returns:
            List of formatted strings for table row
        """
        return [
            f"#{ticket.id}",
            self._format_status(ticket.status),
            self._format_team_info(ticket.group_id),
            self._truncate_text(ticket.short_description, 25),
            format_date_for_display(ticket.created_at),
            str(ticket.days_since_created),
            format_date_for_display(ticket.updated_at),
            str(ticket.days_since_updated),
            ticket.url
        ]
    
    def _format_status(self, status: str) -> str:
        """Format ticket status for display.
        
        Args:
            status: Ticket status
            
        Returns:
            Capitalized status string
        """
        return status.capitalize()
    
    def _format_team_info(self, group_id: Optional[int]) -> str:
        """Format team/group information.
        
        Args:
            group_id: Group ID or None
            
        Returns:
            Formatted team string
        """
        if group_id is None:
            return "Unassigned"
        return str(group_id)
    
    def _truncate_text(self, text: str, max_length: int) -> str:
        """Truncate text to maximum length with ellipsis.
        
        Args:
            text: Text to truncate
            max_length: Maximum length
            
        Returns:
            Truncated text with ellipsis if needed
        """
        if len(text) <= max_length:
            return text
        return text[:max_length - 3] + "..."
    
    def format_tickets_with_teams_table(self, tickets_with_teams: List[Dict[str, Any]]) -> Table:
        """Format a list of tickets with team names as a Rich table.
        
        Args:
            tickets_with_teams: List of dicts with 'ticket' and 'team_name' keys
            
        Returns:
            Rich Table object ready for display
        """
        # Create table with styling
        table = Table(
            title="🎫 Zendesk Tickets",
            show_header=True,
            header_style="bold magenta",
            border_style="bright_blue",
            row_styles=["none", "dim"]
        )
        
        # Add columns - let Rich handle width automatically for better display
        table.add_column("Ticket #", style="cyan", no_wrap=True)
        table.add_column("Status", style="bright_magenta", no_wrap=True)
        table.add_column("Team Name", style="green", no_wrap=True)
        table.add_column("Description", style="white")
        table.add_column("Opened", style="yellow", no_wrap=True)
        table.add_column("Days Since Opened", style="red", justify="right", no_wrap=True)
        table.add_column("Updated", style="yellow", no_wrap=True)
        table.add_column("Days Since Updated", style="red", justify="right", no_wrap=True)
        table.add_column("Link", style="blue", no_wrap=True)
        
        # Add rows
        for item in tickets_with_teams:
            ticket = item["ticket"]
            team_name = item["team_name"]
            row_data = self._format_ticket_with_team_row(ticket, team_name)
            table.add_row(*row_data)
        
        return table
    
    def _format_ticket_with_team_row(self, ticket: Ticket, team_name: str) -> List[str]:
        """Format a single ticket with team name as a table row.
        
        Args:
            ticket: Ticket to format
            team_name: Resolved team name
            
        Returns:
            List of formatted strings for table row
        """
        return [
            f"#{ticket.id}",
            self._format_status(ticket.status),
            team_name,
            self._truncate_text(ticket.short_description, 25),
            format_date_for_display(ticket.created_at),
            str(ticket.days_since_created),
            format_date_for_display(ticket.updated_at),
            str(ticket.days_since_updated),
            ticket.url
        ]
    
