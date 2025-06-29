"""Generic ticket model with adapter-specific extensions support."""

import json
from datetime import datetime
from typing import Any

from ..core.interfaces.models import BaseTicketModel


class Ticket(BaseTicketModel):
    """Generic ticket model that can be extended by adapters.

    This model provides common ticket fields while allowing adapters
    to store additional data in the adapter_specific_data field.
    """

    def __init__(
        self,
        id: str,
        title: str,
        description: str,
        status: str,
        created_at: datetime,
        updated_at: datetime,
        assignee_id: str | None = None,
        group_id: str | None = None,
        url: str = "",
        adapter_name: str = "",
        adapter_specific_data: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize a generic ticket.

        Args:
            id: Unique ticket identifier
            title: Ticket title/subject
            description: Ticket description/content
            status: Current ticket status
            created_at: Ticket creation timestamp
            updated_at: Last update timestamp
            assignee_id: ID of assigned user
            group_id: ID of assigned group/team
            url: Direct link to ticket
            adapter_name: Name of the adapter that created this ticket
            adapter_specific_data: Additional adapter-specific data
            **kwargs: Additional fields stored in adapter_specific_data
        """
        self._id = str(id)
        self._title = title
        self._description = description
        self._status = status
        self._created_at = created_at
        self._updated_at = updated_at
        self._assignee_id = assignee_id
        self._group_id = group_id
        self._url = url
        self._adapter_name = adapter_name

        # Combine explicit adapter_specific_data with kwargs
        self._adapter_specific_data = adapter_specific_data or {}
        self._adapter_specific_data.update(kwargs)

        # Cache for computed properties
        self._team_name: str | None = None

    @property
    def id(self) -> str:
        """Unique ticket identifier."""
        return self._id

    @property
    def title(self) -> str:
        """Ticket title/subject."""
        return self._title

    @property
    def description(self) -> str:
        """Ticket description/content."""
        return self._description

    @property
    def status(self) -> str:
        """Current ticket status."""
        return self._status

    @property
    def created_at(self) -> datetime:
        """Ticket creation timestamp."""
        return self._created_at

    @property
    def updated_at(self) -> datetime:
        """Last update timestamp."""
        return self._updated_at

    @property
    def assignee_id(self) -> str | None:
        """ID of assigned user."""
        return self._assignee_id

    @property
    def group_id(self) -> str | None:
        """ID of assigned group/team."""
        return self._group_id

    @property
    def url(self) -> str:
        """Direct link to ticket."""
        return self._url

    @property
    def adapter_name(self) -> str:
        """Name of the adapter that created this ticket."""
        return self._adapter_name

    @property
    def adapter_specific_data(self) -> dict[str, Any]:
        """Adapter-specific data that doesn't fit common model."""
        return self._adapter_specific_data.copy()

    @property
    def short_description(self) -> str:
        """Get truncated description for display."""
        return (
            self.description[:50] + "..."
            if len(self.description) > 50
            else self.description
        )

    @property
    def days_since_created(self) -> int:
        """Calculate days since ticket creation."""
        return (datetime.now() - self.created_at).days

    @property
    def days_since_updated(self) -> int:
        """Calculate days since last update."""
        return (datetime.now() - self.updated_at).days

    @property
    def team_name(self) -> str | None:
        """Team/group name (resolved by services)."""
        return self._team_name

    @team_name.setter
    def team_name(self, value: str | None) -> None:
        """Set team/group name."""
        self._team_name = value

    def get_adapter_field(self, field_name: str, default: Any = None) -> Any:
        """Get a field from adapter-specific data.

        Args:
            field_name: Name of the field to retrieve
            default: Default value if field doesn't exist

        Returns:
            Field value or default
        """
        return self._adapter_specific_data.get(field_name, default)

    def set_adapter_field(self, field_name: str, value: Any) -> None:
        """Set a field in adapter-specific data.

        Args:
            field_name: Name of the field to set
            value: Value to set
        """
        self._adapter_specific_data[field_name] = value

    def has_adapter_field(self, field_name: str) -> bool:
        """Check if adapter-specific field exists.

        Args:
            field_name: Name of the field to check

        Returns:
            True if field exists, False otherwise
        """
        return field_name in self._adapter_specific_data

    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        data = {
            "id": self.id,
            "title": self.title,
            "description": self.description,
            "short_description": self.short_description,
            "status": self.status,
            "created_at": self.created_at.isoformat(),
            "updated_at": self.updated_at.isoformat(),
            "assignee_id": self.assignee_id,
            "group_id": self.group_id,
            "url": self.url,
            "adapter_name": self.adapter_name,
            "days_since_created": self.days_since_created,
            "days_since_updated": self.days_since_updated,
            "team_name": self.team_name,
            "adapter_specific_data": self.adapter_specific_data,
        }
        return data

    def to_json(self) -> str:
        """Convert to JSON string."""
        return json.dumps(self.to_dict(), indent=2, default=str)

    def __str__(self) -> str:
        """String representation."""
        return (
            f"Ticket(id={self.id}, status={self.status}, title='{self.title[:30]}...')"
        )

    def __repr__(self) -> str:
        """Developer representation."""
        return (
            f"Ticket(id={self.id}, title='{self.title}', "
            f"status='{self.status}', adapter='{self.adapter_name}')"
        )

    def __eq__(self, other: object) -> bool:
        """Check equality based on ID and adapter."""
        if not isinstance(other, Ticket):
            return False
        return self.id == other.id and self.adapter_name == other.adapter_name

    def __hash__(self) -> int:
        """Hash based on ID and adapter."""
        return hash((self.id, self.adapter_name))
