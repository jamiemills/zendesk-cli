"""Abstract authentication interface for ticketing systems."""

from abc import ABC, abstractmethod
from typing import Any


class BaseAuth(ABC):
    """Abstract base class for authentication across different ticketing systems.

    The authentication layer handles credential management and API authentication
    for each ticketing system. Implementations should:

    - Store credentials securely (using keyring for sensitive data)
    - Provide authentication state validation
    - Handle token refresh if applicable
    - Support different authentication methods (API tokens, OAuth, basic auth)

    Authentication Flow:
        1. Created by adapter with configuration containing credentials
        2. authenticate() called to validate credentials with remote system
        3. get_auth_headers() provides authentication data for API requests
        4. Authentication state maintained for the session

    Example Implementation:
        class ZendeskAuth(BaseAuth):
            def __init__(self, config: dict[str, Any]) -> None:
                self.domain = config["domain"]
                self.email = config["email"]
                self.token = keyring.get_password("ticketq-zendesk", self.email)

            def authenticate(self) -> bool:
                response = requests.get(
                    f"https://{self.domain}/api/v2/users/me.json",
                    auth=(f"{self.email}/token", self.token)
                )
                return response.status_code == 200
    """

    @abstractmethod
    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize authentication with configuration.

        Args:
            config: Authentication configuration specific to the adapter
        """
        pass

    @abstractmethod
    def authenticate(self) -> bool:
        """Perform authentication and return success status.

        Returns:
            True if authentication successful, False otherwise

        Raises:
            AuthenticationError: If authentication fails
        """
        pass

    @abstractmethod
    def is_authenticated(self) -> bool:
        """Check if currently authenticated.

        Returns:
            True if authenticated, False otherwise
        """
        pass

    @abstractmethod
    def get_auth_headers(self) -> dict[str, str]:
        """Get authentication headers for API requests.

        Returns:
            Dictionary of headers to include in requests
        """
        pass

    @abstractmethod
    def refresh_authentication(self) -> bool:
        """Refresh authentication if supported.

        Returns:
            True if refresh successful, False otherwise
        """
        pass

    @abstractmethod
    def get_current_user_info(self) -> dict[str, Any] | None:
        """Get information about the currently authenticated user.

        Returns:
            User information dictionary, None if not authenticated
        """
        pass

    @abstractmethod
    def validate_config(self) -> bool:
        """Validate the authentication configuration.

        Returns:
            True if configuration is valid, False otherwise
        """
        pass
