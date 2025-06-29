"""Zendesk authentication implementation."""

import logging
from typing import Any

from ticketq.core.interfaces.auth import BaseAuth
from ticketq.models.exceptions import AuthenticationError, ConfigurationError

logger = logging.getLogger(__name__)


class ZendeskAuth(BaseAuth):
    """Zendesk-specific authentication implementation."""

    def __init__(self, config: dict[str, Any]) -> None:
        """Initialize Zendesk authentication.

        Args:
            config: Zendesk authentication configuration
                Expected keys: domain, email, api_token
        """
        self.domain = config.get("domain", "")
        self.email = config.get("email", "")
        self.api_token = config.get("api_token", "")
        self._authenticated = False
        self._current_user = None

        # Validate required fields
        if not all([self.domain, self.email, self.api_token]):
            raise ConfigurationError(
                "Zendesk authentication requires domain, email, and api_token",
                suggestions=[
                    "Run 'tq configure zendesk' to set up authentication",
                    "Check your configuration file has all required fields",
                    "Verify your API token is not empty",
                ],
            )

    def authenticate(self) -> bool:
        """Perform authentication test with Zendesk.

        Returns:
            True if authentication successful, False otherwise

        Raises:
            AuthenticationError: If authentication fails
        """
        try:
            # Import here to avoid circular dependencies
            import base64

            import requests

            # Create basic auth header
            credentials = f"{self.email}/token:{self.api_token}"
            encoded_credentials = base64.b64encode(credentials.encode()).decode()

            headers = {
                "Authorization": f"Basic {encoded_credentials}",
                "Content-Type": "application/json",
                "User-Agent": "TicketQ/0.1.0 (Zendesk Adapter)",
            }

            # Test authentication by getting current user
            url = f"https://{self.domain}/api/v2/users/me.json"
            response = requests.get(url, headers=headers, timeout=10)

            if response.status_code == 200:
                self._authenticated = True
                self._current_user = response.json().get("user", {})
                logger.debug("Zendesk authentication successful")
                return True
            elif response.status_code == 401:
                raise AuthenticationError(
                    "zendesk",
                    "Invalid credentials",
                    suggestions=[
                        "Check your email and API token are correct",
                        "Verify your Zendesk domain is correct",
                        "Ensure your API token is active",
                        "Check if your account has API access enabled",
                    ],
                )
            else:
                raise AuthenticationError(
                    "zendesk",
                    f"Authentication failed: HTTP {response.status_code}",
                    suggestions=[
                        "Check Zendesk service status",
                        "Verify your domain is accessible",
                        "Try again in a few moments",
                    ],
                )

        except requests.RequestException as e:
            raise AuthenticationError(
                "zendesk",
                f"Network error during authentication: {e}",
                suggestions=[
                    "Check your internet connection",
                    "Verify Zendesk domain is accessible",
                    "Check firewall and proxy settings",
                ],
                original_error=e,
            )
        except Exception as e:
            raise AuthenticationError(
                "zendesk",
                f"Unexpected error during authentication: {e}",
                original_error=e,
            )

    def is_authenticated(self) -> bool:
        """Check if currently authenticated.

        Returns:
            True if authenticated, False otherwise
        """
        return self._authenticated

    def get_auth_headers(self) -> dict[str, str]:
        """Get authentication headers for API requests.

        Returns:
            Dictionary of headers to include in requests
        """
        import base64

        credentials = f"{self.email}/token:{self.api_token}"
        encoded_credentials = base64.b64encode(credentials.encode()).decode()

        return {
            "Authorization": f"Basic {encoded_credentials}",
            "Content-Type": "application/json",
            "User-Agent": "TicketQ/0.1.0 (Zendesk Adapter)",
        }

    def refresh_authentication(self) -> bool:
        """Refresh authentication if supported.

        For Zendesk API tokens, no refresh is needed.

        Returns:
            True if refresh successful, False otherwise
        """
        # API tokens don't need refresh, just re-test
        try:
            return self.authenticate()
        except AuthenticationError:
            return False

    def get_current_user_info(self) -> dict[str, Any] | None:
        """Get information about the currently authenticated user.

        Returns:
            User information dictionary, None if not authenticated
        """
        if self.is_authenticated() and self._current_user:
            return self._current_user.copy()
        return None

    def validate_config(self) -> bool:
        """Validate the authentication configuration.

        Returns:
            True if configuration is valid, False otherwise
        """
        # Check required fields are present and non-empty
        if not self.domain or not self.email or not self.api_token:
            return False

        # Basic domain validation
        if not self.domain.endswith(".zendesk.com"):
            logger.warning("Domain should end with .zendesk.com")
            return False

        # Basic email validation
        if "@" not in self.email:
            logger.warning("Email should contain @ symbol")
            return False

        # API token should be reasonably long
        if len(self.api_token) < 10:
            logger.warning("API token seems too short")
            return False

        return True
