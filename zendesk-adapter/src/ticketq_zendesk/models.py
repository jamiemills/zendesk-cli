"""Model mappers for converting between Zendesk data and generic models."""

from datetime import datetime
from typing import Any, Dict

from ticketq.models import Ticket, User, Group


def parse_zendesk_datetime(datetime_str: str) -> datetime:
    """Parse Zendesk datetime string to datetime object.
    
    Args:
        datetime_str: Zendesk datetime string (ISO format)
        
    Returns:
        Parsed datetime object
    """
    # Remove 'Z' suffix and parse
    if datetime_str.endswith('Z'):
        datetime_str = datetime_str[:-1] + '+00:00'
    
    try:
        return datetime.fromisoformat(datetime_str.replace('Z', '+00:00'))
    except ValueError:
        # Fallback for different formats
        try:
            return datetime.strptime(datetime_str.replace('Z', ''), '%Y-%m-%dT%H:%M:%S')
        except ValueError:
            # Last resort - use current time
            return datetime.now()


class ZendeskTicketMapper:
    """Maps between Zendesk ticket data and generic Ticket models."""
    
    def to_generic(self, zendesk_data: Dict[str, Any]) -> Ticket:
        """Convert Zendesk ticket data to generic Ticket model.
        
        Args:
            zendesk_data: Raw Zendesk ticket data
            
        Returns:
            Generic Ticket instance
        """
        # Extract common fields
        ticket_id = str(zendesk_data.get("id", ""))
        title = zendesk_data.get("subject", "")
        description = zendesk_data.get("description", "")
        status = self._normalize_status(zendesk_data.get("status", ""))
        
        # Parse dates
        created_at = parse_zendesk_datetime(zendesk_data.get("created_at", ""))
        updated_at = parse_zendesk_datetime(zendesk_data.get("updated_at", ""))
        
        # Handle assignee and group IDs
        assignee_id = zendesk_data.get("assignee_id")
        assignee_id = str(assignee_id) if assignee_id else None
        
        group_id = zendesk_data.get("group_id")
        group_id = str(group_id) if group_id else None
        
        # Build URL
        url = zendesk_data.get("url", "")
        
        # Store Zendesk-specific data
        adapter_specific_data = {
            "priority": zendesk_data.get("priority"),
            "type": zendesk_data.get("type"),
            "tags": zendesk_data.get("tags", []),
            "external_id": zendesk_data.get("external_id"),
            "via": zendesk_data.get("via", {}),
            "custom_fields": zendesk_data.get("custom_fields", []),
            "satisfaction_rating": zendesk_data.get("satisfaction_rating"),
            "sharing_agreement_ids": zendesk_data.get("sharing_agreement_ids", []),
            "followup_ids": zendesk_data.get("followup_ids", []),
            "forum_topic_id": zendesk_data.get("forum_topic_id"),
            "problem_id": zendesk_data.get("problem_id"),
            "has_incidents": zendesk_data.get("has_incidents", False),
            "due_at": zendesk_data.get("due_at"),
            "brand_id": zendesk_data.get("brand_id"),
            "allow_channelback": zendesk_data.get("allow_channelback", False),
            "allow_attachments": zendesk_data.get("allow_attachments", True),
        }
        
        return Ticket(
            id=ticket_id,
            title=title,
            description=description,
            status=status,
            created_at=created_at,
            updated_at=updated_at,
            assignee_id=assignee_id,
            group_id=group_id,
            url=url,
            adapter_name="zendesk",
            adapter_specific_data=adapter_specific_data
        )
    
    def _normalize_status(self, zendesk_status: str) -> str:
        """Normalize Zendesk status to common status values.
        
        Args:
            zendesk_status: Zendesk-specific status
            
        Returns:
            Normalized status
        """
        # Zendesk statuses map directly to our common statuses
        status_map = {
            "new": "new",
            "open": "open", 
            "pending": "pending",
            "hold": "hold",
            "solved": "solved",
            "closed": "closed"
        }
        
        return status_map.get(zendesk_status.lower(), zendesk_status)


class ZendeskUserMapper:
    """Maps between Zendesk user data and generic User models."""
    
    def to_generic(self, zendesk_data: Dict[str, Any]) -> User:
        """Convert Zendesk user data to generic User model.
        
        Args:
            zendesk_data: Raw Zendesk user data
            
        Returns:
            Generic User instance
        """
        user_id = str(zendesk_data.get("id", ""))
        name = zendesk_data.get("name", "")
        email = zendesk_data.get("email", "")
        
        # Convert group IDs to strings
        group_ids = zendesk_data.get("group_ids", [])
        group_ids = [str(gid) for gid in group_ids if gid is not None]
        
        # Store Zendesk-specific data
        adapter_specific_data = {
            "active": zendesk_data.get("active", True),
            "verified": zendesk_data.get("verified", False),
            "shared": zendesk_data.get("shared", False),
            "locale": zendesk_data.get("locale"),
            "locale_id": zendesk_data.get("locale_id"),
            "time_zone": zendesk_data.get("time_zone"),
            "last_login_at": zendesk_data.get("last_login_at"),
            "phone": zendesk_data.get("phone"),
            "shared_phone_number": zendesk_data.get("shared_phone_number"),
            "photo": zendesk_data.get("photo"),
            "role": zendesk_data.get("role"),
            "role_type": zendesk_data.get("role_type"),
            "custom_role_id": zendesk_data.get("custom_role_id"),
            "moderator": zendesk_data.get("moderator", False),
            "ticket_restriction": zendesk_data.get("ticket_restriction"),
            "only_private_comments": zendesk_data.get("only_private_comments", False),
            "restricted_agent": zendesk_data.get("restricted_agent", True),
            "suspended": zendesk_data.get("suspended", False),
            "chat_only": zendesk_data.get("chat_only", False),
            "shared_agent": zendesk_data.get("shared_agent", False),
            "signature": zendesk_data.get("signature"),
            "details": zendesk_data.get("details"),
            "notes": zendesk_data.get("notes"),
            "organization_id": zendesk_data.get("organization_id"),
            "default_group_id": zendesk_data.get("default_group_id"),
            "alias": zendesk_data.get("alias"),
            "created_at": zendesk_data.get("created_at"),
            "updated_at": zendesk_data.get("updated_at"),
            "url": zendesk_data.get("url"),
            "user_fields": zendesk_data.get("user_fields", {}),
        }
        
        return User(
            id=user_id,
            name=name,
            email=email,
            group_ids=group_ids,
            adapter_name="zendesk",
            adapter_specific_data=adapter_specific_data
        )


class ZendeskGroupMapper:
    """Maps between Zendesk group data and generic Group models."""
    
    def to_generic(self, zendesk_data: Dict[str, Any]) -> Group:
        """Convert Zendesk group data to generic Group model.
        
        Args:
            zendesk_data: Raw Zendesk group data
            
        Returns:
            Generic Group instance
        """
        group_id = str(zendesk_data.get("id", ""))
        name = zendesk_data.get("name", "")
        description = zendesk_data.get("description")
        
        # Store Zendesk-specific data
        adapter_specific_data = {
            "default": zendesk_data.get("default", False),
            "deleted": zendesk_data.get("deleted", False),
            "created_at": zendesk_data.get("created_at"),
            "updated_at": zendesk_data.get("updated_at"),
            "url": zendesk_data.get("url"),
        }
        
        return Group(
            id=group_id,
            name=name,
            description=description,
            adapter_name="zendesk",
            adapter_specific_data=adapter_specific_data
        )