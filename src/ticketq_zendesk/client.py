"""Zendesk client implementation."""

import logging
from typing import Any

import requests
from requests.adapters import HTTPAdapter
from urllib3.util.retry import Retry

from ticketq.core.interfaces.auth import BaseAuth
from ticketq.core.interfaces.client import BaseClient
from ticketq.models import Group, Ticket, User
from ticketq.models.exceptions import (
    APIError,
    NetworkError,
    RateLimitError,
    TimeoutError,
)

from .models import ZendeskGroupMapper, ZendeskTicketMapper, ZendeskUserMapper

logger = logging.getLogger(__name__)


class ZendeskClient(BaseClient):
    """Zendesk-specific client implementation."""

    def __init__(self, auth: BaseAuth) -> None:
        """Initialize Zendesk client.

        Args:
            auth: Zendesk authentication instance
        """
        self.auth = auth
        self.base_url = f"https://{auth.domain}/api/v2"

        # Initialize HTTP session with retry logic
        self.session = requests.Session()
        self._setup_session()

        # Mappers for converting Zendesk data to generic models
        self.ticket_mapper = ZendeskTicketMapper()
        self.user_mapper = ZendeskUserMapper()
        self.group_mapper = ZendeskGroupMapper()

        # Cache for groups to avoid repeated API calls
        self._groups_cache: dict[str, Group] | None = None

    def _setup_session(self) -> None:
        """Set up HTTP session with retry logic and authentication."""
        # Retry strategy
        retry_strategy = Retry(
            total=3,
            backoff_factor=1,
            status_forcelist=[429, 500, 502, 503, 504],
        )

        # Try new parameter name first, fall back to old one
        try:
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
                allowed_methods=["HEAD", "GET", "OPTIONS"],
            )
        except TypeError:
            # Fallback for older urllib3 versions
            retry_strategy = Retry(
                total=3,
                backoff_factor=1,
                status_forcelist=[429, 500, 502, 503, 504],
                method_whitelist=["HEAD", "GET", "OPTIONS"],
            )

        adapter = HTTPAdapter(max_retries=retry_strategy)
        self.session.mount("http://", adapter)
        self.session.mount("https://", adapter)

        # Set default headers
        self.session.headers.update(self.auth.get_auth_headers())

    def test_connection(self) -> bool:
        """Test connection to Zendesk.

        Returns:
            True if connection successful, False otherwise
        """
        try:
            response = self._make_request("GET", "users/me.json")
            return bool(response.get("user"))
        except Exception as e:
            logger.error(f"Connection test failed: {e}")
            return False

    def get_tickets(
        self,
        status: str | list[str] | None = None,
        assignee_id: str | None = None,
        group_id: str | None = None,
        **kwargs: Any,
    ) -> list[Ticket]:
        """Get tickets with filtering options.

        Args:
            status: Status filter (single value or list)
            assignee_id: Filter by assignee ID
            group_id: Filter by group ID
            **kwargs: Additional Zendesk-specific filters

        Returns:
            List of ticket models
        """
        # Handle multiple statuses by making separate requests
        if isinstance(status, list) and len(status) > 1:
            all_tickets = []
            ticket_ids_seen = set()

            for single_status in status:
                status_tickets = self.get_tickets(
                    status=single_status,
                    assignee_id=assignee_id,
                    group_id=group_id,
                    **kwargs,
                )

                # Deduplicate tickets
                for ticket in status_tickets:
                    if ticket.id not in ticket_ids_seen:
                        all_tickets.append(ticket)
                        ticket_ids_seen.add(ticket.id)

            return sorted(all_tickets, key=lambda t: t.created_at, reverse=True)

        # Build search query
        query_parts = []

        if status:
            status_value = status[0] if isinstance(status, list) else status
            query_parts.append(f"status:{status_value}")

        if assignee_id:
            query_parts.append(f"assignee:{assignee_id}")

        if group_id:
            query_parts.append(f"group:{group_id}")

        # Add Zendesk-specific filters from kwargs
        for key, value in kwargs.items():
            if key in ["priority", "type", "created", "updated"]:
                query_parts.append(f"{key}:{value}")

        query = " ".join(query_parts) if query_parts else "type:ticket"

        return self.search_tickets(query)

    def get_ticket(self, ticket_id: str) -> Ticket | None:
        """Get a specific ticket by ID.

        Args:
            ticket_id: Ticket identifier

        Returns:
            Ticket model or None if not found
        """
        try:
            response = self._make_request("GET", f"tickets/{ticket_id}.json")
            ticket_data = response.get("ticket")

            if ticket_data:
                return self.ticket_mapper.to_generic(ticket_data)
            return None

        except APIError as e:
            if e.context.get("status_code") == 404:
                return None
            raise

    def get_current_user(self) -> User | None:
        """Get current authenticated user information.

        Returns:
            User model or None if not authenticated
        """
        try:
            response = self._make_request("GET", "users/me.json")
            user_data = response.get("user")

            if user_data:
                return self.user_mapper.to_generic(user_data)
            return None

        except Exception as e:
            logger.error(f"Failed to get current user: {e}")
            return None

    def get_user(self, user_id: str) -> User | None:
        """Get user by ID.

        Args:
            user_id: User identifier

        Returns:
            User model or None if not found
        """
        try:
            response = self._make_request("GET", f"users/{user_id}.json")
            user_data = response.get("user")

            if user_data:
                return self.user_mapper.to_generic(user_data)
            return None

        except APIError as e:
            if e.context.get("status_code") == 404:
                return None
            raise

    def get_groups(self) -> list[Group]:
        """Get all available groups/teams.

        Returns:
            List of group models
        """
        try:
            response = self._make_request("GET", "groups.json")
            groups_data = response.get("groups", [])

            groups = []
            for group_data in groups_data:
                group = self.group_mapper.to_generic(group_data)
                groups.append(group)

            return groups

        except Exception as e:
            logger.error(f"Failed to get groups: {e}")
            return []

    def get_group(self, group_id: str) -> Group | None:
        """Get group by ID.

        Args:
            group_id: Group identifier

        Returns:
            Group model or None if not found
        """
        # Check cache first
        if self._groups_cache and group_id in self._groups_cache:
            return self._groups_cache[group_id]

        try:
            response = self._make_request("GET", f"groups/{group_id}.json")
            group_data = response.get("group")

            if group_data:
                group = self.group_mapper.to_generic(group_data)

                # Cache the result
                if self._groups_cache is None:
                    self._groups_cache = {}
                self._groups_cache[group_id] = group

                return group
            return None

        except APIError as e:
            if e.context.get("status_code") == 404:
                return None
            raise

    def search_tickets(self, query: str, **kwargs: Any) -> list[Ticket]:
        """Search tickets using Zendesk search API.

        Args:
            query: Zendesk search query
            **kwargs: Additional search parameters

        Returns:
            List of matching ticket models
        """
        try:
            # Ensure query includes type:ticket
            if "type:ticket" not in query:
                query = f"type:ticket {query}".strip()

            params = {"query": query}
            params.update(kwargs)

            response = self._make_request("GET", "search.json", params=params)

            tickets = []
            for result in response.get("results", []):
                if result.get("result_type") == "ticket":
                    ticket = self.ticket_mapper.to_generic(result)
                    tickets.append(ticket)

            return tickets

        except Exception as e:
            logger.error(f"Search failed: {e}")
            return []

    def _make_request(
        self,
        method: str,
        endpoint: str,
        params: dict[str, Any] | None = None,
        data: dict[str, Any] | None = None,
        timeout: float = 30.0,
    ) -> dict[str, Any]:
        """Make an authenticated request to the Zendesk API.

        Args:
            method: HTTP method
            endpoint: API endpoint (relative to base_url)
            params: Query parameters
            data: Request body data
            timeout: Request timeout in seconds

        Returns:
            Response data as dictionary

        Raises:
            APIError: If API request fails
            NetworkError: If network request fails
            RateLimitError: If rate limited
            TimeoutError: If request times out
        """
        url = f"{self.base_url}/{endpoint}"

        try:
            logger.debug(f"Making {method} request to {endpoint}")

            response = self.session.request(
                method=method, url=url, params=params, json=data, timeout=timeout
            )

            # Handle rate limiting
            if response.status_code == 429:
                retry_after = int(response.headers.get("Retry-After", 60))
                raise RateLimitError(
                    "zendesk",
                    f"Rate limit exceeded, retry after {retry_after} seconds",
                    retry_after=retry_after,
                )

            # Handle other HTTP errors
            if not response.ok:
                error_data = {}
                try:
                    error_data = response.json()
                except:
                    pass

                raise APIError(
                    "zendesk",
                    f"API request failed: {response.status_code} {response.reason}",
                    status_code=response.status_code,
                    response_data=error_data,
                )

            return response.json()

        except requests.exceptions.Timeout as e:
            raise TimeoutError(
                "zendesk",
                f"Request timed out after {timeout} seconds",
                timeout_duration=timeout,
                original_error=e,
            )
        except requests.exceptions.RequestException as e:
            raise NetworkError(
                "zendesk", f"Network request failed: {e}", original_error=e
            )
        except RateLimitError:
            raise  # Re-raise as-is
        except APIError:
            raise  # Re-raise as-is
        except Exception as e:
            raise APIError(
                "zendesk", f"Unexpected error during API request: {e}", original_error=e
            )
