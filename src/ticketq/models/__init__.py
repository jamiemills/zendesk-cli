"""Generic models for ticketing systems with extension support."""

from .exceptions import (
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
from .group import Group
from .ticket import Ticket
from .user import User

__all__ = [
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
    # Models
    "Ticket",
    "User",
    "Group",
]
