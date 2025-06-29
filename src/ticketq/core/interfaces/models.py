"""Abstract base models for ticketing system data."""

from abc import ABC, abstractmethod
from datetime import datetime
from typing import Any


class BaseTicketModel(ABC):
    """Abstract base class for ticket models across different ticketing systems."""

    @property
    @abstractmethod
    def id(self) -> str:
        """Unique ticket identifier."""
        pass

    @property
    @abstractmethod
    def title(self) -> str:
        """Ticket title/subject."""
        pass

    @property
    @abstractmethod
    def description(self) -> str:
        """Ticket description/content."""
        pass

    @property
    @abstractmethod
    def status(self) -> str:
        """Current ticket status."""
        pass

    @property
    @abstractmethod
    def created_at(self) -> datetime:
        """Ticket creation timestamp."""
        pass

    @property
    @abstractmethod
    def updated_at(self) -> datetime:
        """Last update timestamp."""
        pass

    @property
    @abstractmethod
    def assignee_id(self) -> str | None:
        """ID of assigned user."""
        pass

    @property
    @abstractmethod
    def group_id(self) -> str | None:
        """ID of assigned group/team."""
        pass

    @property
    @abstractmethod
    def url(self) -> str:
        """Direct link to ticket."""
        pass

    @property
    @abstractmethod
    def adapter_specific_data(self) -> dict[str, Any]:
        """Adapter-specific data that doesn't fit common model."""
        pass

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        pass

    @abstractmethod
    def to_json(self) -> str:
        """Convert to JSON string."""
        pass


class BaseUserModel(ABC):
    """Abstract base class for user models across different ticketing systems."""

    @property
    @abstractmethod
    def id(self) -> str:
        """Unique user identifier."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """User display name."""
        pass

    @property
    @abstractmethod
    def email(self) -> str:
        """User email address."""
        pass

    @property
    @abstractmethod
    def group_ids(self) -> list[str]:
        """List of group IDs user belongs to."""
        pass

    @property
    @abstractmethod
    def adapter_specific_data(self) -> dict[str, Any]:
        """Adapter-specific data that doesn't fit common model."""
        pass

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        pass


class BaseGroupModel(ABC):
    """Abstract base class for group/team models across different ticketing systems."""

    @property
    @abstractmethod
    def id(self) -> str:
        """Unique group identifier."""
        pass

    @property
    @abstractmethod
    def name(self) -> str:
        """Group display name."""
        pass

    @property
    @abstractmethod
    def description(self) -> str | None:
        """Group description."""
        pass

    @property
    @abstractmethod
    def adapter_specific_data(self) -> dict[str, Any]:
        """Adapter-specific data that doesn't fit common model."""
        pass

    @abstractmethod
    def to_dict(self) -> dict[str, Any]:
        """Convert to dictionary representation."""
        pass
