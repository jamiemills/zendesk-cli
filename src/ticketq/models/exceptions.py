"""Exception hierarchy for ticketq and adapter-specific errors."""

from typing import Any


class TicketQError(Exception):
    """Base exception for all ticketq-related errors."""

    def __init__(
        self,
        message: str,
        suggestions: list[str] | None = None,
        context: dict[str, Any] | None = None,
        original_error: Exception | None = None,
    ) -> None:
        """Initialize TicketQ error.

        Args:
            message: Human-readable error message
            suggestions: List of actionable suggestions for resolution
            context: Additional context information
            original_error: Original exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.suggestions = suggestions or []
        self.context = context or {}
        self.original_error = original_error

    def __str__(self) -> str:
        """Return formatted error message with suggestions."""
        error_msg = self.message

        if self.suggestions:
            suggestions_text = "\n".join(
                f"  • {suggestion}" for suggestion in self.suggestions
            )
            error_msg += f"\n\nSuggestions:\n{suggestions_text}"

        if self.context:
            context_text = ", ".join(
                f"{key}={value}" for key, value in self.context.items()
            )
            error_msg += f"\n\nContext: {context_text}"

        return error_msg


class AdapterError(TicketQError):
    """Base class for adapter-specific errors."""

    def __init__(
        self,
        adapter_name: str,
        message: str,
        suggestions: list[str] | None = None,
        context: dict[str, Any] | None = None,
        original_error: Exception | None = None,
    ) -> None:
        """Initialize adapter error.

        Args:
            adapter_name: Name of the adapter that caused the error
            message: Human-readable error message
            suggestions: List of actionable suggestions for resolution
            context: Additional context information
            original_error: Original exception that caused this error
        """
        self.adapter_name = adapter_name
        context = context or {}
        context["adapter"] = adapter_name

        super().__init__(
            message=f"[{adapter_name}] {message}",
            suggestions=suggestions,
            context=context,
            original_error=original_error,
        )


class AuthenticationError(AdapterError):
    """Authentication-related errors."""

    def __init__(
        self,
        adapter_name: str,
        message: str = "Authentication failed",
        suggestions: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize authentication error with default suggestions."""
        default_suggestions = [
            "Check your credentials in the configuration",
            f"Verify your {adapter_name} account is active",
            "Try refreshing your authentication tokens",
            f"Run 'tq configure {adapter_name}' to reconfigure",
        ]

        final_suggestions = suggestions or default_suggestions
        super().__init__(
            adapter_name=adapter_name,
            message=message,
            suggestions=final_suggestions,
            **kwargs,
        )


class ConfigurationError(TicketQError):
    """Configuration-related errors."""

    def __init__(
        self,
        message: str = "Configuration error",
        config_file: str | None = None,
        suggestions: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize configuration error with default suggestions."""
        default_suggestions = [
            "Check your configuration file exists and is readable",
            "Verify configuration file format is valid",
            "Run 'tq configure' to set up configuration",
            "Check file permissions on configuration directory",
        ]

        context = kwargs.get("context", {})
        if config_file:
            context["config_file"] = config_file
        kwargs["context"] = context

        final_suggestions = suggestions or default_suggestions
        super().__init__(message=message, suggestions=final_suggestions, **kwargs)


class APIError(AdapterError):
    """API-related errors from ticketing systems."""

    def __init__(
        self,
        adapter_name: str,
        message: str = "API request failed",
        status_code: int | None = None,
        response_data: dict[str, Any] | None = None,
        suggestions: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize API error with response information."""
        context = kwargs.get("context", {})
        if status_code:
            context["status_code"] = status_code
        if response_data:
            context["response_data"] = response_data
        kwargs["context"] = context

        default_suggestions = [
            f"Check {adapter_name} service status",
            "Verify your API permissions",
            "Check network connectivity",
            "Try again in a few moments",
        ]

        # Add status-specific suggestions
        if status_code == 401:
            default_suggestions.insert(0, "Check your authentication credentials")
        elif status_code == 403:
            default_suggestions.insert(0, "Check your API permissions")
        elif status_code == 404:
            default_suggestions.insert(0, "Verify the resource exists")
        elif status_code == 429:
            default_suggestions.insert(0, "Rate limit exceeded - wait before retrying")
        elif status_code and status_code >= 500:
            default_suggestions.insert(
                0, f"{adapter_name} server error - try again later"
            )

        final_suggestions = suggestions or default_suggestions
        super().__init__(
            adapter_name=adapter_name,
            message=message,
            suggestions=final_suggestions,
            **kwargs,
        )


class NetworkError(AdapterError):
    """Network connectivity errors."""

    def __init__(
        self,
        adapter_name: str,
        message: str = "Network connection failed",
        suggestions: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize network error with default suggestions."""
        default_suggestions = [
            "Check your internet connection",
            f"Verify {adapter_name} service is accessible",
            "Check firewall and proxy settings",
            "Try again in a few moments",
        ]

        final_suggestions = suggestions or default_suggestions
        super().__init__(
            adapter_name=adapter_name,
            message=message,
            suggestions=final_suggestions,
            **kwargs,
        )


class RateLimitError(APIError):
    """Rate limiting errors."""

    def __init__(
        self,
        adapter_name: str,
        message: str = "Rate limit exceeded",
        retry_after: int | None = None,
        suggestions: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize rate limit error with retry information."""
        context = kwargs.get("context", {})
        if retry_after:
            context["retry_after"] = retry_after
        kwargs["context"] = context

        default_suggestions = [
            (
                f"Wait {retry_after} seconds before retrying"
                if retry_after
                else "Wait before retrying"
            ),
            "Reduce request frequency",
            "Consider using pagination for large requests",
        ]

        final_suggestions = suggestions or default_suggestions
        super().__init__(
            adapter_name=adapter_name,
            message=message,
            status_code=429,
            suggestions=final_suggestions,
            **kwargs,
        )


class TimeoutError(AdapterError):
    """Request timeout errors."""

    def __init__(
        self,
        adapter_name: str,
        message: str = "Request timed out",
        timeout_duration: float | None = None,
        suggestions: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize timeout error with duration information."""
        context = kwargs.get("context", {})
        if timeout_duration:
            context["timeout_duration"] = timeout_duration
        kwargs["context"] = context

        default_suggestions = [
            "Try again with a longer timeout",
            "Check network connectivity",
            f"Verify {adapter_name} service is responsive",
            "Consider breaking large requests into smaller ones",
        ]

        final_suggestions = suggestions or default_suggestions
        super().__init__(
            adapter_name=adapter_name,
            message=message,
            suggestions=final_suggestions,
            **kwargs,
        )


class ValidationError(TicketQError):
    """Data validation errors."""

    def __init__(
        self,
        message: str = "Validation failed",
        field_name: str | None = None,
        field_value: Any | None = None,
        suggestions: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize validation error with field information."""
        context = kwargs.get("context", {})
        if field_name:
            context["field_name"] = field_name
        if field_value is not None:
            context["field_value"] = field_value
        kwargs["context"] = context

        default_suggestions = [
            "Check input data format and values",
            "Verify required fields are provided",
            "Check data types match expected formats",
        ]

        final_suggestions = suggestions or default_suggestions
        super().__init__(message=message, suggestions=final_suggestions, **kwargs)


class PluginError(TicketQError):
    """Plugin loading and management errors."""

    def __init__(
        self,
        message: str = "Plugin error",
        plugin_name: str | None = None,
        suggestions: list[str] | None = None,
        **kwargs: Any,
    ) -> None:
        """Initialize plugin error with plugin information."""
        context = kwargs.get("context", {})
        if plugin_name:
            context["plugin_name"] = plugin_name
        kwargs["context"] = context

        default_suggestions = [
            "Check plugin is properly installed",
            "Verify plugin compatibility with ticketq version",
            "Check plugin entry points are correctly configured",
            "Try reinstalling the plugin",
        ]

        final_suggestions = suggestions or default_suggestions
        super().__init__(message=message, suggestions=final_suggestions, **kwargs)
