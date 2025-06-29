"""Plugin registry for discovering and managing ticketing system adapters."""

import logging

try:
    from importlib.metadata import entry_points
except ImportError:
    # Python < 3.8 compatibility
    from importlib_metadata import (
        entry_points,  # type: ignore[import-not-found,no-redef]
    )

from ..models.exceptions import PluginError
from .interfaces.adapter import BaseAdapter

logger = logging.getLogger(__name__)


class AdapterRegistry:
    """Registry for discovering and managing ticketing system adapters."""

    ENTRY_POINT_GROUP = "ticketq.adapters"

    def __init__(self) -> None:
        """Initialize the adapter registry."""
        self._adapters: dict[str, type[BaseAdapter]] = {}
        self._loaded = False

    def discover_adapters(self) -> None:
        """Discover adapters using entry points."""
        if self._loaded:
            return

        logger.debug("Discovering adapters via entry points")

        try:
            # Get entry points for ticketq adapters
            eps = entry_points()

            # Handle different importlib.metadata versions
            if hasattr(eps, "select"):
                # Python 3.10+
                adapter_eps = eps.select(group=self.ENTRY_POINT_GROUP)
            else:
                # Python < 3.10
                adapter_eps = eps.get(self.ENTRY_POINT_GROUP, [])  # type: ignore[arg-type]

            for ep in adapter_eps:
                try:
                    logger.debug(f"Loading adapter: {ep.name}")
                    adapter_class = ep.load()

                    # Validate that it's a proper adapter
                    if not issubclass(adapter_class, BaseAdapter):
                        logger.warning(
                            f"Adapter {ep.name} does not inherit from BaseAdapter, skipping"
                        )
                        continue

                    self._adapters[ep.name] = adapter_class
                    logger.info(f"Registered adapter: {ep.name}")

                except Exception as e:
                    logger.error(f"Failed to load adapter {ep.name}: {e}")
                    # Don't raise here, just skip problematic adapters

        except Exception as e:
            logger.error(f"Failed to discover adapters: {e}")
            # Continue with empty registry rather than failing completely

        self._loaded = True
        logger.debug(f"Discovery complete. Found {len(self._adapters)} adapters")

    def register_adapter(self, name: str, adapter_class: type[BaseAdapter]) -> None:
        """Manually register an adapter.

        Args:
            name: Adapter name
            adapter_class: Adapter class

        Raises:
            PluginError: If adapter is invalid
        """
        if not issubclass(adapter_class, BaseAdapter):
            raise PluginError(
                f"Adapter {name} must inherit from BaseAdapter", plugin_name=name
            )

        self._adapters[name] = adapter_class
        logger.info(f"Manually registered adapter: {name}")

    def get_adapter_class(self, name: str) -> type[BaseAdapter] | None:
        """Get adapter class by name.

        Args:
            name: Adapter name

        Returns:
            Adapter class or None if not found
        """
        self.discover_adapters()  # Ensure adapters are loaded
        return self._adapters.get(name)

    def list_adapters(self) -> list[str]:
        """Get list of available adapter names.

        Returns:
            List of adapter names
        """
        self.discover_adapters()  # Ensure adapters are loaded
        return list(self._adapters.keys())

    def get_available_adapters(self) -> dict[str, type[BaseAdapter]]:
        """Get dictionary of available adapters.

        Returns:
            Dictionary mapping adapter names to adapter classes
        """
        self.discover_adapters()  # Ensure adapters are loaded
        return self._adapters.copy()

    def get_adapter_info(self, name: str) -> dict[str, str] | None:
        """Get information about an adapter.

        Args:
            name: Adapter name

        Returns:
            Dictionary with adapter information or None if not found
        """
        adapter_class = self.get_adapter_class(name)
        if not adapter_class:
            return None

        # Create a temporary instance to get metadata
        try:
            # Use a minimal config for metadata extraction
            adapter = adapter_class()
            return {
                "name": adapter.name,
                "display_name": adapter.display_name,
                "version": adapter.version,
                "supported_features": ", ".join(adapter.supported_features),
            }
        except Exception as e:
            logger.warning(f"Could not get info for adapter {name}: {e}")
            return {
                "name": name,
                "display_name": name.title(),
                "version": "unknown",
                "supported_features": "unknown",
            }

    def is_adapter_available(self, name: str) -> bool:
        """Check if an adapter is available.

        Args:
            name: Adapter name

        Returns:
            True if adapter is available, False otherwise
        """
        return self.get_adapter_class(name) is not None

    def reload_adapters(self) -> None:
        """Force reload of all adapters."""
        self._adapters.clear()
        self._loaded = False
        self.discover_adapters()


# Global registry instance
_registry = AdapterRegistry()


def get_registry() -> AdapterRegistry:
    """Get the global adapter registry.

    Returns:
        Global AdapterRegistry instance
    """
    return _registry
