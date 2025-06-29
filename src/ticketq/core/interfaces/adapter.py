"""Abstract adapter interface for ticketing systems."""

from abc import ABC, abstractmethod
from typing import Any

from .auth import BaseAuth
from .client import BaseClient


class BaseAdapter(ABC):
    """Abstract base class for ticketing system adapters.

    The TicketQ adapter pattern allows seamless integration with different
    ticketing systems through a unified interface. Each adapter handles:

    - Authentication with the target system
    - API client creation and management
    - Data model mapping from system-specific to common formats
    - Status normalisation across different systems

    Lifecycle:
        1. Factory creates adapter instance using __init__()
        2. Configuration is validated via validate_config()
        3. Authentication is created via create_auth()
        4. Client is created via create_client()
        5. Factory stores references in _auth, _client, _config
        6. Adapter is ready for operations via client methods

    Example Implementation:
        class MySystemAdapter(BaseAdapter):
            @property
            def name(self) -> str:
                return "mysystem"

            @property
            def display_name(self) -> str:
                return "My Ticketing System"

            def create_auth(self, config: dict) -> BaseAuth:
                return MySystemAuth(
                    domain=config["domain"],
                    token=config["api_token"]
                )

            def create_client(self, auth: BaseAuth) -> BaseClient:
                return MySystemClient(auth)

            def validate_config(self, config: dict) -> bool:
                required = ["domain", "api_token"]
                return all(key in config for key in required)
    """

    # These attributes are set by the factory after initialization
    _auth: BaseAuth
    _client: BaseClient
    _config: dict[str, Any]

    @property
    @abstractmethod
    def name(self) -> str:
        """Adapter name (e.g., 'zendesk', 'jira', 'servicenow')."""
        pass

    @property
    @abstractmethod
    def display_name(self) -> str:
        """Human-readable adapter name."""
        pass

    @property
    @abstractmethod
    def version(self) -> str:
        """Adapter version."""
        pass

    @property
    @abstractmethod
    def supported_features(self) -> list[str]:
        """List of supported features.

        Common features: 'tickets', 'users', 'groups', 'search', 'export'
        """
        pass

    @abstractmethod
    def get_auth_class(self) -> type[BaseAuth]:
        """Get the authentication class for this adapter.

        Returns:
            Auth class that implements BaseAuth
        """
        pass

    @abstractmethod
    def get_client_class(self) -> type[BaseClient]:
        """Get the client class for this adapter.

        Returns:
            Client class that implements BaseClient
        """
        pass

    @abstractmethod
    def create_auth(self, config: dict[str, Any]) -> BaseAuth:
        """Create authentication instance.

        Args:
            config: Authentication configuration

        Returns:
            Authentication instance
        """
        pass

    @abstractmethod
    def create_client(self, auth: BaseAuth) -> BaseClient:
        """Create client instance.

        Args:
            auth: Authentication instance

        Returns:
            Client instance
        """
        pass

    @abstractmethod
    def validate_config(self, config: dict[str, Any]) -> bool:
        """Validate adapter-specific configuration.

        Args:
            config: Configuration to validate

        Returns:
            True if valid, False otherwise
        """
        pass

    @abstractmethod
    def get_config_schema(self) -> dict[str, Any]:
        """Get JSON schema for adapter configuration.

        Returns:
            JSON schema dictionary
        """
        pass

    @abstractmethod
    def get_default_config(self) -> dict[str, Any]:
        """Get default configuration template.

        Returns:
            Default configuration dictionary
        """
        pass

    @abstractmethod
    def normalize_status(self, status: str) -> str:
        """Normalize adapter-specific status to common status.

        Args:
            status: Adapter-specific status

        Returns:
            Normalized status
        """
        pass

    @abstractmethod
    def denormalize_status(self, status: str) -> str:
        """Convert common status to adapter-specific status.

        Args:
            status: Common status

        Returns:
            Adapter-specific status
        """
        pass

    def get_adapter_specific_operations(self) -> dict[str, Any]:
        """Get adapter-specific operations not covered by base interface.

        Returns:
            Dictionary of operation name to method mappings
        """
        return {}

    def supports_feature(self, feature: str) -> bool:
        """Check if adapter supports a specific feature.

        Args:
            feature: Feature name to check

        Returns:
            True if supported, False otherwise
        """
        return feature in self.supported_features
