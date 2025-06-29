"""Zendesk CLI - A command-line tool and library for managing Zendesk tickets."""

__version__ = "0.1.0"

# Import library interface for external consumers
from .lib import (
    ZendeskLibrary,
    LibraryTicket,
    LibraryUser,
    LibraryGroup,
    ZendeskCliError,
    AuthenticationError,
    APIError,
    ConfigurationError,
    NetworkError,
    RateLimitError,
    TimeoutError,
    ValidationError,
    KeyringError,
)

__all__ = [
    # Library interface
    "ZendeskLibrary",
    
    # Data models
    "LibraryTicket",
    "LibraryUser",
    "LibraryGroup",
    
    # Exceptions
    "ZendeskCliError",
    "AuthenticationError",
    "APIError",
    "ConfigurationError",
    "NetworkError",
    "RateLimitError",
    "TimeoutError",
    "ValidationError",
    "KeyringError",
    
    # Version
    "__version__",
]