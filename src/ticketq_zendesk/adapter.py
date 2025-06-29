"""Zendesk adapter implementation for TicketQ."""

from typing import Any

from ticketq.core.interfaces.adapter import BaseAdapter
from ticketq.core.interfaces.auth import BaseAuth
from ticketq.core.interfaces.client import BaseClient

from .auth import ZendeskAuth
from .client import ZendeskClient


class ZendeskAdapter(BaseAdapter):
    """Zendesk adapter for TicketQ."""

    @property
    def name(self) -> str:
        """Adapter name."""
        return "zendesk"

    @property
    def display_name(self) -> str:
        """Human-readable adapter name."""
        return "Zendesk"

    @property
    def version(self) -> str:
        """Adapter version."""
        return "0.1.0"

    @property
    def supported_features(self) -> list[str]:
        """List of supported features."""
        return [
            "tickets",
            "users",
            "groups",
            "search",
            "export",
            "authentication",
            "filtering",
            "sorting",
        ]

    def get_auth_class(self) -> type[BaseAuth]:
        """Get the authentication class for this adapter."""
        return ZendeskAuth

    def get_client_class(self) -> type[BaseClient]:
        """Get the client class for this adapter."""
        return ZendeskClient

    def create_auth(self, config: dict[str, Any]) -> BaseAuth:
        """Create authentication instance."""
        return ZendeskAuth(config)

    def create_client(self, auth: BaseAuth) -> BaseClient:
        """Create client instance."""
        return ZendeskClient(auth)

    def validate_config(self, config: dict[str, Any]) -> bool:
        """Validate adapter-specific configuration."""
        required_fields = ["domain", "email", "api_token"]

        # Check all required fields are present
        for field in required_fields:
            if field not in config or not config[field]:
                return False

        # Validate domain format
        domain = config["domain"]
        if not domain.endswith(".zendesk.com"):
            return False

        # Validate email format
        email = config["email"]
        if "@" not in email:
            return False

        # Validate API token length
        api_token = config["api_token"]
        if len(api_token) < 10:
            return False

        return True

    def get_config_schema(self) -> dict[str, Any]:
        """Get JSON schema for adapter configuration."""
        return {
            "type": "object",
            "properties": {
                "domain": {
                    "type": "string",
                    "description": "Zendesk domain (e.g., company.zendesk.com)",
                    "pattern": r"^[a-zA-Z0-9\-]+\.zendesk\.com$",
                },
                "email": {
                    "type": "string",
                    "description": "Your Zendesk email address",
                    "format": "email",
                },
                "api_token": {
                    "type": "string",
                    "description": "Your Zendesk API token",
                    "minLength": 10,
                },
            },
            "required": ["domain", "email", "api_token"],
            "additionalProperties": False,
        }

    def get_default_config(self) -> dict[str, Any]:
        """Get default configuration template."""
        return {
            "domain": "your-company.zendesk.com",
            "email": "your-email@company.com",
            "api_token": "your-api-token-here",
        }

    def normalize_status(self, status: str) -> str:
        """Normalize Zendesk status to common status."""
        # Zendesk statuses are already in common format
        status_map = {
            "new": "new",
            "open": "open",
            "pending": "pending",
            "hold": "hold",
            "solved": "solved",
            "closed": "closed",
        }

        return status_map.get(status.lower(), status)

    def denormalize_status(self, status: str) -> str:
        """Convert common status to Zendesk status."""
        # Common statuses map directly to Zendesk
        status_map = {
            "new": "new",
            "open": "open",
            "pending": "pending",
            "hold": "hold",
            "solved": "solved",
            "closed": "closed",
        }

        return status_map.get(status.lower(), status)

    def get_adapter_specific_operations(self) -> dict[str, Any]:
        """Get Zendesk-specific operations."""
        return {
            "get_satisfaction_ratings": self._get_satisfaction_ratings,
            "get_ticket_metrics": self._get_ticket_metrics,
            "get_organizations": self._get_organizations,
            "search_advanced": self._search_advanced,
        }

    def _get_satisfaction_ratings(
        self, client: ZendeskClient, ticket_id: str
    ) -> dict[str, Any]:
        """Get satisfaction ratings for a ticket (Zendesk-specific)."""
        try:
            response = client._make_request(
                "GET", f"tickets/{ticket_id}/satisfaction_rating.json"
            )
            return response.get("satisfaction_rating", {})
        except Exception:
            return {}

    def _get_ticket_metrics(
        self, client: ZendeskClient, ticket_id: str
    ) -> dict[str, Any]:
        """Get ticket metrics (Zendesk-specific)."""
        try:
            response = client._make_request("GET", f"tickets/{ticket_id}/metrics.json")
            return response.get("ticket_metric", {})
        except Exception:
            return {}

    def _get_organizations(self, client: ZendeskClient) -> list[dict[str, Any]]:
        """Get organizations (Zendesk-specific)."""
        try:
            response = client._make_request("GET", "organizations.json")
            return response.get("organizations", [])
        except Exception:
            return []

    def _search_advanced(
        self,
        client: ZendeskClient,
        query: str,
        sort_by: str = None,
        sort_order: str = None,
    ) -> list[dict[str, Any]]:
        """Advanced search with sorting (Zendesk-specific)."""
        try:
            params = {"query": query}
            if sort_by:
                params["sort_by"] = sort_by
            if sort_order:
                params["sort_order"] = sort_order

            response = client._make_request("GET", "search.json", params=params)
            return response.get("results", [])
        except Exception:
            return []
