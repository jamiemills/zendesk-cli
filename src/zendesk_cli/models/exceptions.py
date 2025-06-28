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
    """Configuration-related errors."""
    pass