"""Abstract client interface for ticketing systems."""

from abc import ABC, abstractmethod
from typing import Any

from .auth import BaseAuth
from .models import BaseGroupModel, BaseTicketModel, BaseUserModel


class BaseClient(ABC):
    """Abstract base class for ticketing system clients."""

    @abstractmethod
    def __init__(self, auth: BaseAuth) -> None:
        """Initialize client with authentication.

        Args:
            auth: Authentication instance
        """
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """Test connection to the ticketing system.

        Returns:
            True if connection successful, False otherwise
        """
        pass

    @abstractmethod
    def get_tickets(
        self,
        status: str | list[str] | None = None,
        assignee_id: str | None = None,
        group_id: str | None = None,
        **kwargs: Any,
    ) -> list[BaseTicketModel]:
        """Get tickets with filtering options.

        Args:
            status: Status filter (single value or list)
            assignee_id: Filter by assignee ID
            group_id: Filter by group ID
            **kwargs: Adapter-specific filters

        Returns:
            List of ticket models
        """
        pass

    @abstractmethod
    def get_ticket(self, ticket_id: str) -> BaseTicketModel | None:
        """Get a specific ticket by ID.

        Args:
            ticket_id: Ticket identifier

        Returns:
            Ticket model or None if not found
        """
        pass

    @abstractmethod
    def get_current_user(self) -> BaseUserModel | None:
        """Get current authenticated user information.

        Returns:
            User model or None if not authenticated
        """
        pass

    @abstractmethod
    def get_user(self, user_id: str) -> BaseUserModel | None:
        """Get user by ID.

        Args:
            user_id: User identifier

        Returns:
            User model or None if not found
        """
        pass

    @abstractmethod
    def get_groups(self) -> list[BaseGroupModel]:
        """Get all available groups/teams.

        Returns:
            List of group models
        """
        pass

    @abstractmethod
    def get_group(self, group_id: str) -> BaseGroupModel | None:
        """Get group by ID.

        Args:
            group_id: Group identifier

        Returns:
            Group model or None if not found
        """
        pass

    @abstractmethod
    def search_tickets(self, query: str, **kwargs: Any) -> list[BaseTicketModel]:
        """Search tickets using system-specific query language.

        Args:
            query: Search query in system-specific format
            **kwargs: Additional search parameters

        Returns:
            List of matching ticket models
        """
        pass
