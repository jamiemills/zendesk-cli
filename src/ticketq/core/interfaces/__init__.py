"""Core interfaces for ticketing system adapters."""

from .adapter import BaseAdapter
from .auth import BaseAuth
from .client import BaseClient
from .models import BaseGroupModel, BaseTicketModel, BaseUserModel

__all__ = [
    "BaseAdapter",
    "BaseAuth",
    "BaseClient",
    "BaseTicketModel",
    "BaseUserModel",
    "BaseGroupModel",
]
