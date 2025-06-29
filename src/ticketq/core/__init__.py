"""Core components for ticketq plugin system."""

from .factory import AdapterFactory
from .registry import AdapterRegistry

__all__ = [
    "AdapterRegistry",
    "AdapterFactory",
]
