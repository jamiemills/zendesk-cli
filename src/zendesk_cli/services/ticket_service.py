"""Business logic service for ticket operations."""

from __future__ import annotations

import logging
from typing import List, Dict, Any, Optional, Union

from ..models.ticket import Ticket
from ..models.exceptions import APIError, NetworkError, RateLimitError, TimeoutError
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
        self._groups_cache: Optional[Dict[int, str]] = None
    
    def get_all_tickets(self, status: Union[str, List[str]] = "open") -> List[Ticket]:
        """Get all tickets from Zendesk with specified status(es).
        
        Args:
            status: Status(es) to filter by (default: "open"). Can be a single status or list of statuses.
        
        Returns:
            List of Ticket objects with the specified status(es)
        """
        status_desc = status if isinstance(status, str) else ",".join(status)
        logger.debug(f"Fetching all {status_desc} tickets")
        return self.client.get_tickets(status=status)
    
    def get_all_open_tickets(self) -> List[Ticket]:
        """Get all open tickets from Zendesk.
        
        Returns:
            List of open Ticket objects
        """
        return self.get_all_tickets(status="open")
    
    def get_user_tickets(self, user_id: int, status: Union[str, List[str]] = "open") -> List[Ticket]:
        """Get tickets assigned to a specific user with specified status(es).
        
        Args:
            user_id: ID of the user to get tickets for
            status: Status(es) to filter by (default: "open"). Can be a single status or list of statuses.
            
        Returns:
            List of Ticket objects assigned to the user
        """
        status_desc = status if isinstance(status, str) else ",".join(status)
        logger.debug(f"Fetching {status_desc} tickets for user {user_id}")
        return self.client.get_tickets(assignee_id=user_id, status=status)
    
    def get_group_tickets(self, group_id: int, status: Union[str, List[str]] = "open") -> List[Ticket]:
        """Get tickets assigned to a specific group with specified status(es).
        
        Args:
            group_id: ID of the group to get tickets for
            status: Status(es) to filter by (default: "open"). Can be a single status or list of statuses.
            
        Returns:
            List of Ticket objects assigned to the group
        """
        status_desc = status if isinstance(status, str) else ",".join(status)
        logger.debug(f"Fetching {status_desc} tickets for group {group_id}")
        return self.client.get_tickets(group_id=group_id, status=status)
    
    def get_multiple_groups_tickets(self, group_ids: List[int], status: Union[str, List[str]] = "open") -> List[Ticket]:
        """Get tickets assigned to multiple groups with specified status(es).
        
        Args:
            group_ids: List of group IDs to get tickets for
            status: Status(es) to filter by (default: "open"). Can be a single status or list of statuses.
            
        Returns:
            List of Ticket objects assigned to any of the specified groups
        """
        status_desc = status if isinstance(status, str) else ",".join(status)
        logger.debug(f"Fetching {status_desc} tickets for groups {group_ids}")
        
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
        logger.debug("Fetching current user information")
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
    
    def _get_groups_mapping(self) -> Dict[int, str]:
        """Get mapping of group IDs to group names.
        
        Returns:
            Dictionary mapping group IDs to group names
        """
        if self._groups_cache is not None:
            return self._groups_cache
        
        try:
            logger.debug("Fetching groups information")
            response_data = self.client._make_request("GET", "groups.json")
            
            groups_mapping = {}
            for group_data in response_data.get("groups", []):
                groups_mapping[group_data["id"]] = group_data["name"]
            
            self._groups_cache = groups_mapping
            logger.debug(f"Cached {len(groups_mapping)} groups")
            return groups_mapping
            
        except (APIError, NetworkError, TimeoutError, RateLimitError) as e:
            logger.warning(f"Failed to fetch groups: {e}")
            # Return empty dict to use fallback naming
            return {}
    
    def _get_team_name(self, group_id: Optional[int]) -> str:
        """Get team name for a group ID.
        
        Args:
            group_id: Group ID to resolve
            
        Returns:
            Team name or fallback string
        """
        if group_id is None:
            return "Unassigned"
        
        groups_mapping = self._get_groups_mapping()
        
        if group_id in groups_mapping:
            return groups_mapping[group_id]
        elif groups_mapping:  # We have groups data but this ID is unknown
            return f"Unknown Group ({group_id})"
        else:  # No groups data available (API failed)
            return f"Group {group_id}"
    
    def get_tickets_with_team_names(self, status: Union[str, List[str]] = "open") -> List[Dict[str, Any]]:
        """Get tickets with resolved team names.
        
        Args:
            status: Status(es) to filter by (default: "open"). Can be a single status or list of statuses.
            
        Returns:
            List of dictionaries with 'ticket' and 'team_name' keys
        """
        status_desc = status if isinstance(status, str) else ",".join(status)
        logger.debug(f"Fetching {status_desc} tickets with team names")
        
        tickets = self.client.get_tickets(status=status)
        
        enriched_tickets = []
        for ticket in tickets:
            team_name = self._get_team_name(ticket.group_id)
            enriched_tickets.append({
                "ticket": ticket,
                "team_name": team_name
            })
        
        return enriched_tickets
    
    def get_tickets_for_group_name(self, group_name: str, status: Union[str, List[str]] = "open") -> List[Dict[str, Any]]:
        """Get tickets for a specific group by name.
        
        Args:
            group_name: Name of the group to filter by
            status: Status(es) to filter by (default: "open"). Can be a single status or list of statuses.
            
        Returns:
            List of dictionaries with 'ticket' and 'team_name' keys
        """
        status_desc = status if isinstance(status, str) else ",".join(status)
        logger.debug(f"Fetching {status_desc} tickets for group '{group_name}'")
        
        # Find group ID for the given name
        groups_mapping = self._get_groups_mapping()
        group_id = None
        
        for gid, gname in groups_mapping.items():
            if gname == group_name:
                group_id = gid
                break
        
        if group_id is None:
            logger.warning(f"Group '{group_name}' not found")
            return []
        
        tickets = self.client.get_tickets(group_id=group_id, status=status)
        
        enriched_tickets = []
        for ticket in tickets:
            enriched_tickets.append({
                "ticket": ticket,
                "team_name": group_name
            })
        
        return enriched_tickets