"""Factory for creating adapter instances with auto-detection."""

import logging
from typing import Any

from ..models.exceptions import ConfigurationError, PluginError
from ..utils.config import ConfigManager
from .interfaces.adapter import BaseAdapter
from .registry import get_registry

logger = logging.getLogger(__name__)


class AdapterFactory:
    """Factory for creating and managing adapter instances."""

    def __init__(self, registry=None, config_manager=None) -> None:
        """Initialize the adapter factory.

        Args:
            registry: Optional registry instance for testing
            config_manager: Optional config manager instance for testing
        """
        self._registry = registry or get_registry()
        self._config_manager = config_manager or ConfigManager()

    def create_adapter(
        self, adapter_name: str | None = None, config: dict[str, Any] | None = None
    ) -> BaseAdapter:
        """Create an adapter instance.

        Args:
            adapter_name: Name of adapter to create. If None, auto-detect from config.
            config: Configuration to use. If None, load from config files.

        Returns:
            Configured adapter instance

        Raises:
            PluginError: If adapter not found or failed to create
            ConfigurationError: If configuration is invalid
        """
        # Auto-detect adapter if not specified
        if adapter_name is None:
            adapter_name = self._detect_adapter()

        # Get adapter class
        adapter_class = self._registry.get_adapter_class(adapter_name)
        if not adapter_class:
            available = self._registry.list_adapters()
            raise PluginError(
                f"Adapter '{adapter_name}' not found",
                plugin_name=adapter_name,
                suggestions=[
                    f"Available adapters: {', '.join(available) if available else 'none'}",
                    f"Install the adapter with: pip install ticketq-{adapter_name}",
                    "Check that the adapter is properly installed",
                ],
            )

        # Load configuration if not provided
        if config is None:
            try:
                config = self._config_manager.get_adapter_config(adapter_name)
            except Exception as e:
                raise ConfigurationError(
                    f"Failed to load configuration for adapter '{adapter_name}'",
                    suggestions=[
                        f"Run 'tq configure {adapter_name}' to set up configuration",
                        f"Check that ~/.config/ticketq/{adapter_name}.json exists",
                        "Verify configuration file format is valid",
                    ],
                    original_error=e,
                ) from None

        # Create adapter instance
        try:
            logger.debug(f"Creating adapter instance: {adapter_name}")
            adapter = adapter_class()

            # Validate configuration
            if not adapter.validate_config(config):
                raise ConfigurationError(
                    f"Invalid configuration for adapter '{adapter_name}'",
                    suggestions=[
                        f"Run 'tq configure {adapter_name}' to reconfigure",
                        "Check configuration file format",
                        "Verify all required fields are present",
                    ],
                )

            # Create authentication and client
            auth = adapter.create_auth(config)
            client = adapter.create_client(auth)

            # Store references for later use
            adapter._auth = auth
            adapter._client = client
            adapter._config = config

            logger.info(f"Successfully created adapter: {adapter_name}")
            return adapter

        except Exception as e:
            if isinstance(e, PluginError | ConfigurationError):
                raise

            raise PluginError(
                f"Failed to create adapter '{adapter_name}': {e}",
                plugin_name=adapter_name,
                suggestions=[
                    "Check adapter installation",
                    "Verify configuration is correct",
                    f"Try reinstalling: pip install --upgrade ticketq-{adapter_name}",
                ],
                original_error=e,
            ) from None

    def _detect_adapter(self) -> str:
        """Auto-detect which adapter to use based on available configurations.

        Returns:
            Name of detected adapter

        Raises:
            ConfigurationError: If no adapter can be detected
        """
        # Get default adapter from main config
        try:
            main_config = self._config_manager.get_main_config()
            default_adapter: str | None = main_config.get("default_adapter")

            if default_adapter:
                # Verify the adapter is available
                if self._registry.is_adapter_available(default_adapter):
                    logger.debug(
                        f"Using default adapter from config: {default_adapter}"
                    )
                    return default_adapter
                else:
                    logger.warning(
                        f"Default adapter '{default_adapter}' not available, auto-detecting"
                    )

        except Exception as e:
            logger.debug(f"Could not load main config: {e}")

        # Try to detect based on available adapter configs
        available_adapters = self._registry.list_adapters()
        configured_adapters = []

        for adapter_name in available_adapters:
            try:
                config = self._config_manager.get_adapter_config(adapter_name)
                if config:  # Non-empty config
                    configured_adapters.append(adapter_name)
            except Exception as e:
                logger.debug(f"Failed to load config for {adapter_name}: {e}")
                continue  # Skip adapters without valid config

        if len(configured_adapters) == 1:
            detected = configured_adapters[0]
            logger.debug(f"Auto-detected adapter: {detected}")
            return detected
        elif len(configured_adapters) > 1:
            # Multiple configured adapters, need user to specify
            raise ConfigurationError(
                "Multiple adapters are configured",
                suggestions=[
                    f"Specify adapter explicitly: tq --adapter {configured_adapters[0]} tickets",
                    "Set default adapter in ~/.config/ticketq/config.json",
                    f"Available configured adapters: {', '.join(configured_adapters)}",
                ],
            )
        else:
            # No configured adapters
            if available_adapters:
                raise ConfigurationError(
                    "No adapters are configured",
                    suggestions=[
                        f"Configure an adapter: tq configure {available_adapters[0]}",
                        f"Available adapters: {', '.join(available_adapters)}",
                        "Run 'tq list-adapters' to see all available adapters",
                    ],
                )
            else:
                raise ConfigurationError(
                    "No adapters are installed",
                    suggestions=[
                        "Install an adapter: pip install ticketq-zendesk",
                        "Check available adapters: pip search ticketq-",
                        "Visit documentation for supported adapters",
                    ],
                )

    def list_available_adapters(self) -> dict[str, dict[str, str]]:
        """Get list of all available adapters with their information.

        Returns:
            Dictionary mapping adapter names to their information
        """
        adapters = {}
        for name in self._registry.list_adapters():
            info = self._registry.get_adapter_info(name)
            if info:
                adapters[name] = info
        return adapters

    def is_adapter_configured(self, adapter_name: str) -> bool:
        """Check if an adapter is configured.

        Args:
            adapter_name: Name of adapter to check

        Returns:
            True if adapter has valid configuration, False otherwise
        """
        try:
            config = self._config_manager.get_adapter_config(adapter_name)
            return bool(config)
        except Exception:
            return False

    def get_configured_adapters(self) -> list[str]:
        """Get list of adapters that have valid configurations.

        Returns:
            List of adapter names with valid configurations
        """
        available_adapters = self._registry.list_adapters()
        configured_adapters = []

        for adapter_name in available_adapters:
            try:
                config = self._config_manager.get_adapter_config(adapter_name)
                if config:  # Non-empty config
                    configured_adapters.append(adapter_name)
            except Exception:
                continue  # Skip adapters without valid config

        return configured_adapters

    def _auto_detect_adapter(self) -> str:
        """Auto-detect which adapter to use based on available configurations.

        This is an alias for _detect_adapter for backward compatibility.

        Returns:
            Name of detected adapter

        Raises:
            ConfigurationError: If no adapter can be detected
        """
        return self._detect_adapter()


# Global factory instance
_factory = AdapterFactory()


def get_factory() -> AdapterFactory:
    """Get the global adapter factory.

    Returns:
        Global AdapterFactory instance
    """
    return _factory
