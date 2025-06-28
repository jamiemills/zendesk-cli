"""Custom exceptions for zendesk-cli."""

from __future__ import annotations

from typing import Optional, Dict, Any


class ZendeskCliError(Exception):
    """Base exception for zendesk-cli with enhanced error context."""
    
    def __init__(
        self, 
        message: str, 
        *,
        details: Optional[Dict[str, Any]] = None,
        suggestions: Optional[list[str]] = None
    ):
        super().__init__(message)
        self.details = details or {}
        self.suggestions = suggestions or []
        
    def __str__(self) -> str:
        """Enhanced string representation with suggestions."""
        msg = super().__str__()
        if self.suggestions:
            msg += f"\n\nSuggestions:\n" + "\n".join(f"  • {s}" for s in self.suggestions)
        return msg


class AuthenticationError(ZendeskCliError):
    """Authentication-related errors with helpful suggestions."""
    
    def __init__(self, message: str, **kwargs) -> None:
        suggestions = [
            "Check your API token is correct",
            "Verify your email address", 
            "Run 'zendesk configure' to update credentials"
        ]
        super().__init__(message, suggestions=suggestions, **kwargs)


class APIError(ZendeskCliError):
    """API-related errors with status code context."""
    
    def __init__(
        self, 
        message: str, 
        status_code: Optional[int] = None,
        response_data: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        details = {"status_code": status_code}
        if response_data:
            details["response"] = response_data
            
        suggestions = []
        if status_code == 401:
            suggestions.extend([
                "Check your authentication credentials",
                "Your API token may have expired"
            ])
        elif status_code == 403:
            suggestions.append("You may not have permission to access this resource")
        elif status_code == 429:
            suggestions.append("Rate limit exceeded - please wait and try again")
            
        super().__init__(message, details=details, suggestions=suggestions, **kwargs)
        self.status_code = status_code


class ConfigurationError(ZendeskCliError):
    """Configuration-related errors with helpful suggestions."""
    
    def __init__(self, message: str, **kwargs) -> None:
        suggestions = [
            "Run 'zendesk configure' to set up credentials",
            "Check if configuration file exists and is readable",
            "Verify file permissions on configuration directory"
        ]
        super().__init__(message, suggestions=suggestions, **kwargs)


class ValidationError(ZendeskCliError):
    """Data validation errors."""
    
    def __init__(self, message: str, field: Optional[str] = None, **kwargs) -> None:
        details = {"field": field} if field else {}
        suggestions = [
            "Check input format and try again",
            "Refer to documentation for valid values"
        ]
        super().__init__(message, details=details, suggestions=suggestions, **kwargs)


class NetworkError(ZendeskCliError):
    """Network connectivity errors with retry suggestions."""
    
    def __init__(self, message: str, retry_after: Optional[int] = None, **kwargs) -> None:
        details = {"retry_after": retry_after} if retry_after else {}
        suggestions = [
            "Check your internet connection",
            "Verify Zendesk domain is accessible",
            "Try again in a few moments"
        ]
        if retry_after:
            suggestions.append(f"Wait {retry_after} seconds before retrying")
        super().__init__(message, details=details, suggestions=suggestions, **kwargs)


class KeyringError(ZendeskCliError):
    """Keyring/credential storage errors."""
    
    def __init__(self, message: str, **kwargs) -> None:
        suggestions = [
            "Check if keyring service is available on your system",
            "Try reconfiguring with 'zendesk configure'",
            "On Linux, install python3-keyring or python3-secretstorage"
        ]
        super().__init__(message, suggestions=suggestions, **kwargs)


class RateLimitError(APIError):
    """Rate limiting specific error with retry logic."""
    
    def __init__(self, message: str, retry_after: Optional[int] = None, **kwargs) -> None:
        suggestions = [
            f"Wait {retry_after or 60} seconds before retrying",
            "Reduce API request frequency",
            "Contact Zendesk support if issue persists"
        ]
        super().__init__(
            message, 
            status_code=429, 
            suggestions=suggestions,
            **kwargs
        )
        self.retry_after = retry_after


class TimeoutError(NetworkError):
    """Request timeout specific error."""
    
    def __init__(self, message: str, timeout_duration: Optional[float] = None, **kwargs) -> None:
        details = {"timeout_duration": timeout_duration} if timeout_duration else {}
        suggestions = [
            "Check your internet connection speed",
            "Try again with a more stable connection",
            "Contact Zendesk support if their service is slow"
        ]
        super().__init__(message, details=details, suggestions=suggestions, **kwargs)