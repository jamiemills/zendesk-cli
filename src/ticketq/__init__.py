"""TicketQ - Universal ticketing system CLI and library.

TicketQ provides a unified interface for interacting with various ticketing
systems like Zendesk, Jira, ServiceNow, and others through pluggable adapters.
"""

__version__ = "0.1.0"

# Import library interface for external consumers
# Import core components
from .core import AdapterFactory, AdapterRegistry
from .lib import (
    LibraryGroup,
    LibraryTicket,
    LibraryUser,
    TicketQLibrary,
)

# Import exceptions for error handling
from .models import (
    AdapterError,
    APIError,
    AuthenticationError,
    ConfigurationError,
    NetworkError,
    PluginError,
    RateLimitError,
    TicketQError,
    TimeoutError,
    ValidationError,
)

__all__ = [
    # Version
    "__version__",
    # Library interface
    "TicketQLibrary",
    # Data models
    "LibraryTicket",
    "LibraryUser",
    "LibraryGroup",
    # Exceptions
    "TicketQError",
    "AdapterError",
    "AuthenticationError",
    "ConfigurationError",
    "APIError",
    "NetworkError",
    "RateLimitError",
    "TimeoutError",
    "ValidationError",
    "PluginError",
    # Core components
    "AdapterRegistry",
    "AdapterFactory",
]
