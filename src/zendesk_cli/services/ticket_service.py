"""Business logic service for ticket operations."""

from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional

from ..models.ticket import Ticket
from .zendesk_client import ZendeskClient

logger = logging.getLogger(__name__)


class TicketService:
    """Service layer for ticket-related business logic."""
    
    def __init__(self, client: ZendeskClient) -> None:
        """Initialize the ticket service.
        
        Args:
            client: ZendeskClient instance for API operations
        """
        self.client = client
    
    def get_all_tickets(self, status: str = "open") -> List[Ticket]:
        """Get all tickets from Zendesk with specified status.
        
        Args:
            status: Status to filter by (default: "open")
        
        Returns:
            List of Ticket objects with the specified status
        """
        logger.info(f"Fetching all {status} tickets")
        return self.client.get_tickets(status=status)
    
    def get_all_open_tickets(self) -> List[Ticket]:
        """Get all open tickets from Zendesk.
        
        Returns:
            List of open Ticket objects
        """
        return self.get_all_tickets(status="open")
    
    def get_user_tickets(self, user_id: int, status: str = "open") -> List[Ticket]:
        """Get tickets assigned to a specific user with specified status.
        
        Args:
            user_id: ID of the user to get tickets for
            status: Status to filter by (default: "open")
            
        Returns:
            List of Ticket objects assigned to the user
        """
        logger.info(f"Fetching {status} tickets for user {user_id}")
        return self.client.get_tickets(assignee_id=user_id, status=status)
    
    def get_group_tickets(self, group_id: int, status: str = "open") -> List[Ticket]:
        """Get tickets assigned to a specific group with specified status.
        
        Args:
            group_id: ID of the group to get tickets for
            status: Status to filter by (default: "open")
            
        Returns:
            List of Ticket objects assigned to the group
        """
        logger.info(f"Fetching {status} tickets for group {group_id}")
        return self.client.get_tickets(group_id=group_id, status=status)
    
    def get_multiple_groups_tickets(self, group_ids: List[int], status: str = "open") -> List[Ticket]:
        """Get tickets assigned to multiple groups with specified status.
        
        Args:
            group_ids: List of group IDs to get tickets for
            status: Status to filter by (default: "open")
            
        Returns:
            List of Ticket objects assigned to any of the specified groups
        """
        logger.info(f"Fetching {status} tickets for groups {group_ids}")
        
        all_tickets = []
        ticket_ids_seen = set()  # To avoid duplicates if a ticket is in multiple groups
        
        for group_id in group_ids:
            group_tickets = self.client.get_tickets(group_id=group_id, status=status)
            for ticket in group_tickets:
                if ticket.id not in ticket_ids_seen:
                    all_tickets.append(ticket)
                    ticket_ids_seen.add(ticket.id)
        
        # Sort by creation date (newest first) for consistent output
        return self.sort_tickets_by_created_date(all_tickets, newest_first=True)
    
    def get_current_user_info(self) -> Dict[str, Any]:
        """Get information about the current authenticated user.
        
        Returns:
            User information dictionary
        """
        logger.info("Fetching current user information")
        return self.client.get_current_user()
    
    def filter_tickets_by_status(self, tickets: List[Ticket], status: str) -> List[Ticket]:
        """Filter tickets by status.
        
        Args:
            tickets: List of tickets to filter
            status: Status to filter by
            
        Returns:
            Filtered list of tickets
        """
        return [ticket for ticket in tickets if ticket.status == status]
    
    def sort_tickets_by_created_date(
        self, 
        tickets: List[Ticket], 
        newest_first: bool = True
    ) -> List[Ticket]:
        """Sort tickets by creation date.
        
        Args:
            tickets: List of tickets to sort
            newest_first: If True, sort newest first. If False, oldest first.
            
        Returns:
            Sorted list of tickets
        """
        return sorted(
            tickets, 
            key=lambda t: t.created_at, 
            reverse=newest_first
        )
    
    def get_tickets_summary(self, tickets: List[Ticket]) -> Dict[str, Any]:
        """Get summary statistics for a list of tickets.
        
        Args:
            tickets: List of tickets to summarize
            
        Returns:
            Dictionary with summary statistics
        """
        summary = {
            "total": len(tickets),
            "by_status": {},
            "by_assignee": {},
            "by_group": {}
        }
        
        for ticket in tickets:
            # Count by status
            status = ticket.status
            summary["by_status"][status] = summary["by_status"].get(status, 0) + 1
            
            # Count by assignee
            if ticket.assignee_id:
                assignee_id = ticket.assignee_id
                summary["by_assignee"][assignee_id] = summary["by_assignee"].get(assignee_id, 0) + 1
            
            # Count by group
            if ticket.group_id:
                group_id = ticket.group_id
                summary["by_group"][group_id] = summary["by_group"].get(group_id, 0) + 1
        
        return summary