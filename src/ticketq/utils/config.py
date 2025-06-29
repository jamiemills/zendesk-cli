"""Multi-adapter configuration management for ticketq."""

import json
import logging
import os
from pathlib import Path
from typing import Any

from ..models.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


class ConfigManager:
    """Manages configuration files for ticketq and its adapters."""

    def __init__(self, config_dir: Path | None = None) -> None:
        """Initialize configuration manager.

        Args:
            config_dir: Custom configuration directory. If None, use default.
        """
        self.config_dir = config_dir or self.get_default_config_dir()
        self.main_config_file = self.config_dir / "config.json"

    @staticmethod
    def get_default_config_dir() -> Path:
        """Get the default configuration directory for the current platform.

        Returns:
            Path to configuration directory
        """
        if os.name == "nt":  # Windows
            config_base = Path(os.environ.get("APPDATA", "~"))
        else:  # Linux/macOS
            config_base = Path(os.environ.get("XDG_CONFIG_HOME", "~/.config"))

        return (config_base / "ticketq").expanduser()

    def ensure_config_dir(self) -> None:
        """Ensure configuration directory exists."""
        self.config_dir.mkdir(parents=True, exist_ok=True)

    def get_main_config(self) -> dict[str, Any]:
        """Get main ticketq configuration.

        Returns:
            Main configuration dictionary

        Raises:
            ConfigurationError: If configuration cannot be loaded
        """
        try:
            if not self.main_config_file.exists():
                logger.debug("Main config file does not exist, returning defaults")
                return self._get_default_main_config()

            with open(self.main_config_file, encoding="utf-8") as f:
                config: dict[str, Any] = json.load(f)

            logger.debug("Loaded main configuration")
            return config

        except json.JSONDecodeError as e:
            raise ConfigurationError(
                f"Invalid JSON in main config file: {e}",
                config_file=str(self.main_config_file),
                suggestions=[
                    "Check JSON syntax in config file",
                    "Remove and reconfigure if corrupted",
                    "Validate JSON format with online tools",
                ],
                original_error=e,
            ) from None
        except Exception as e:
            raise ConfigurationError(
                f"Failed to load main configuration: {e}",
                config_file=str(self.main_config_file),
                suggestions=[
                    "Check file permissions",
                    "Verify file is readable",
                    "Run 'tq configure' to recreate",
                ],
                original_error=e,
            ) from None

    def save_main_config(self, config: dict[str, Any]) -> None:
        """Save main ticketq configuration.

        Args:
            config: Configuration to save

        Raises:
            ConfigurationError: If configuration cannot be saved
        """
        try:
            self.ensure_config_dir()

            with open(self.main_config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)

            logger.debug("Saved main configuration")

        except Exception as e:
            raise ConfigurationError(
                f"Failed to save main configuration: {e}",
                config_file=str(self.main_config_file),
                suggestions=[
                    "Check directory permissions",
                    "Verify disk space is available",
                    "Check file is not locked by another process",
                ],
                original_error=e,
            ) from None

    def get_adapter_config(self, adapter_name: str) -> dict[str, Any]:
        """Get configuration for a specific adapter.

        Args:
            adapter_name: Name of the adapter

        Returns:
            Adapter configuration dictionary

        Raises:
            ConfigurationError: If configuration cannot be loaded
        """
        config_file = self.config_dir / f"{adapter_name}.json"

        try:
            if not config_file.exists():
                logger.debug(f"Config file for {adapter_name} does not exist")
                return {}

            with open(config_file, encoding="utf-8") as f:
                config: dict[str, Any] = json.load(f)

            logger.debug(f"Loaded configuration for {adapter_name}")
            return config

        except json.JSONDecodeError as e:
            raise ConfigurationError(
                f"Invalid JSON in {adapter_name} config file: {e}",
                config_file=str(config_file),
                suggestions=[
                    "Check JSON syntax in config file",
                    f"Run 'tq configure {adapter_name}' to reconfigure",
                    "Validate JSON format with online tools",
                ],
                original_error=e,
            ) from None
        except Exception as e:
            raise ConfigurationError(
                f"Failed to load {adapter_name} configuration: {e}",
                config_file=str(config_file),
                suggestions=[
                    "Check file permissions",
                    "Verify file is readable",
                    f"Run 'tq configure {adapter_name}' to recreate",
                ],
                original_error=e,
            ) from None

    def save_adapter_config(self, adapter_name: str, config: dict[str, Any]) -> None:
        """Save configuration for a specific adapter.

        Args:
            adapter_name: Name of the adapter
            config: Configuration to save

        Raises:
            ConfigurationError: If configuration cannot be saved
        """
        config_file = self.config_dir / f"{adapter_name}.json"

        try:
            self.ensure_config_dir()

            with open(config_file, "w", encoding="utf-8") as f:
                json.dump(config, f, indent=2)

            logger.debug(f"Saved configuration for {adapter_name}")

        except Exception as e:
            raise ConfigurationError(
                f"Failed to save {adapter_name} configuration: {e}",
                config_file=str(config_file),
                suggestions=[
                    "Check directory permissions",
                    "Verify disk space is available",
                    "Check file is not locked by another process",
                ],
                original_error=e,
            ) from None

    def delete_adapter_config(self, adapter_name: str) -> bool:
        """Delete configuration for a specific adapter.

        Args:
            adapter_name: Name of the adapter

        Returns:
            True if config was deleted, False if it didn't exist
        """
        config_file = self.config_dir / f"{adapter_name}.json"

        if config_file.exists():
            config_file.unlink()
            logger.debug(f"Deleted configuration for {adapter_name}")
            return True
        else:
            logger.debug(f"No configuration file found for {adapter_name}")
            return False

    def list_configured_adapters(self) -> list[str]:
        """Get list of adapters that have configuration files.

        Returns:
            List of adapter names with config files
        """
        if not self.config_dir.exists():
            return []

        adapters = []
        for config_file in self.config_dir.glob("*.json"):
            # Skip main config file
            if config_file.name == "config.json":
                continue

            adapter_name = config_file.stem
            adapters.append(adapter_name)

        return sorted(adapters)

    def set_default_adapter(self, adapter_name: str) -> None:
        """Set the default adapter.

        Args:
            adapter_name: Name of the adapter to set as default
        """
        config = self.get_main_config()
        config["default_adapter"] = adapter_name
        self.save_main_config(config)
        logger.info(f"Set default adapter to: {adapter_name}")

    def get_default_adapter(self) -> str | None:
        """Get the default adapter name.

        Returns:
            Default adapter name or None if not set
        """
        config = self.get_main_config()
        return config.get("default_adapter")

    def validate_adapter_config(self, adapter_name: str) -> bool:
        """Validate adapter configuration.

        Args:
            adapter_name: Name of the adapter to validate

        Returns:
            True if configuration is valid, False otherwise
        """
        try:
            config = self.get_adapter_config(adapter_name)
            return bool(config)  # Non-empty config is considered valid
        except Exception:
            return False

    def _get_default_main_config(self) -> dict[str, Any]:
        """Get default main configuration.

        Returns:
            Default main configuration dictionary
        """
        return {
            "default_adapter": None,
            "logging": {
                "level": "INFO",
                "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            },
            "output": {
                "format": "table",  # table, csv, json
                "color": True,
                "pagination": True,
            },
        }
