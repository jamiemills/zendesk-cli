"""Configure command implementation."""

import logging
from pathlib import Path
from typing import Any

import click

from ...core.factory import get_factory
from ...core.registry import get_registry
from ...models.exceptions import (
    AuthenticationError,
    ConfigurationError,
    PluginError,
    TicketQError,
)
from ...utils.config import ConfigManager

logger = logging.getLogger(__name__)


def prompt_for_config(adapter_name: str, schema: dict[str, Any]) -> dict[str, Any]:
    """Prompt user for configuration values based on schema.

    Args:
        adapter_name: Name of the adapter
        schema: JSON schema for configuration

    Returns:
        Dictionary with user-provided configuration
    """
    config = {}
    properties = schema.get("properties", {})
    required = schema.get("required", [])

    click.echo(f"\n🔧 Configuring {adapter_name.capitalize()} adapter")
    click.echo("Enter your configuration details:")

    for field, field_schema in properties.items():
        description = field_schema.get("description", field)
        is_required = field in required

        # Determine if field is sensitive (like password/token)
        is_sensitive = any(
            keyword in field.lower()
            for keyword in ["password", "token", "secret", "key"]
        )

        prompt_text = f"{description}"
        if is_required:
            prompt_text += " (required)"

        value = click.prompt(
            prompt_text,
            hide_input=is_sensitive,
            show_default=False,
            default="" if not is_required else None,
        )

        if value:  # Only store non-empty values
            config[field] = value

    return config


def test_adapter_connection(adapter_name: str, config: dict[str, Any]) -> bool:
    """Test connection for an adapter.

    Args:
        adapter_name: Name of the adapter
        config: Configuration dictionary

    Returns:
        True if connection successful, False otherwise
    """
    try:
        factory = get_factory()
        adapter = factory.create_adapter(adapter_name, config)

        # Test authentication
        adapter._auth.authenticate()

        # Test basic API call
        client = adapter._client
        user_info = client.get_current_user()

        if user_info:
            click.echo(
                click.style(
                    f"✅ Successfully connected as {user_info.name} ({user_info.email})",
                    fg="green",
                )
            )
        else:
            click.echo(click.style("✅ Connection successful", fg="green"))

        return True

    except AuthenticationError as e:
        click.echo(click.style(f"❌ Authentication failed: {e}", fg="red"))
        return False
    except Exception as e:
        click.echo(click.style(f"❌ Connection test failed: {e}", fg="red"))
        return False


@click.command()
@click.option(
    "--adapter",
    type=str,
    help="Adapter to configure (e.g., zendesk, jira, servicenow). If not specified, will prompt.",
)
@click.option(
    "--config-path", type=click.Path(), help="Path to configuration directory"
)
@click.option("--test", is_flag=True, help="Test connection after configuration")
@click.option("--list-adapters", is_flag=True, help="List available adapters and exit")
def configure(
    adapter: str | None, config_path: str | None, test: bool, list_adapters: bool
) -> None:
    """Configure TicketQ adapters for accessing ticketing systems."""

    try:
        # List adapters if requested
        if list_adapters:
            registry = get_registry()
            available_adapters = registry.get_available_adapters()

            if not available_adapters:
                click.echo(
                    "❌ No adapters available. Install adapter packages (e.g., pip install ticketq-zendesk)"
                )
                return

            click.echo("📦 Available adapters:")
            for adapter_name in sorted(available_adapters.keys()):
                adapter_class = available_adapters[adapter_name]
                try:
                    instance = adapter_class()
                    click.echo(
                        f"   • {adapter_name}: {instance.display_name} v{instance.version}"
                    )
                    features = ", ".join(instance.supported_features)
                    click.echo(f"     Features: {features}")
                except Exception as e:
                    click.echo(f"   • {adapter_name}: (error loading: {e})")
            return

        # Get available adapters
        registry = get_registry()
        available_adapters = registry.get_available_adapters()

        if not available_adapters:
            click.echo(
                click.style(
                    "❌ No adapters available. Install adapter packages (e.g., pip install ticketq-zendesk)",
                    fg="red",
                )
            )
            raise click.Abort()

        # Prompt for adapter if not provided
        if not adapter:
            adapter_names = sorted(available_adapters.keys())
            if len(adapter_names) == 1:
                adapter = adapter_names[0]
                click.echo(f"🔌 Using {adapter} adapter (only one available)")
            else:
                click.echo("📦 Available adapters:")
                for i, name in enumerate(adapter_names, 1):
                    adapter_class = available_adapters[name]
                    try:
                        instance = adapter_class()
                        click.echo(f"   {i}. {name}: {instance.display_name}")
                    except Exception:
                        click.echo(f"   {i}. {name}")

                choice = click.prompt(
                    "Select adapter number", type=click.IntRange(1, len(adapter_names))
                )
                adapter = adapter_names[choice - 1]

        # Validate adapter exists
        if adapter not in available_adapters:
            click.echo(
                click.style(
                    f"❌ Adapter '{adapter}' not found. Available: {', '.join(available_adapters.keys())}",
                    fg="red",
                )
            )
            raise click.Abort()

        # Create adapter instance to get schema
        try:
            adapter_class = available_adapters[adapter]
            adapter_instance = adapter_class()
            schema = adapter_instance.get_config_schema()
        except Exception as e:
            click.echo(
                click.style(f"❌ Failed to load adapter '{adapter}': {e}", fg="red")
            )
            raise click.Abort() from e

        # Setup config manager
        config_dir = Path(config_path) if config_path else None
        config_manager = ConfigManager(config_dir)

        # Check if adapter already configured
        existing_config = None
        try:
            existing_config = config_manager.get_adapter_config(adapter)
            if existing_config:
                click.echo(f"ℹ️  {adapter.capitalize()} adapter is already configured")
                if not click.confirm("Do you want to reconfigure it?"):
                    return
        except ConfigurationError:
            pass  # No existing config

        # Get configuration from user
        config = prompt_for_config(adapter, schema)

        if not config:
            click.echo("❌ No configuration provided")
            return

        # Validate configuration
        if not adapter_instance.validate_config(config):
            click.echo(click.style("❌ Invalid configuration provided", fg="red"))
            return

        # Save configuration
        try:
            config_manager.save_adapter_config(adapter, config)
            click.echo(
                click.style(f"✅ Configuration saved for {adapter} adapter", fg="green")
            )
        except Exception as e:
            click.echo(click.style(f"❌ Failed to save configuration: {e}", fg="red"))
            raise click.Abort() from e

        # Test connection if requested
        if test:
            click.echo("\n🔍 Testing connection...")
            if test_adapter_connection(adapter, config):
                click.echo(click.style("✅ Configuration test successful!", fg="green"))
            else:
                click.echo(click.style("❌ Configuration test failed", fg="red"))
                click.echo(
                    "💡 You may need to check your credentials or network connection"
                )
        else:
            click.echo("💡 Run 'tq configure --test' to test your configuration")

    except PluginError as e:
        click.echo(click.style(f"❌ Plugin error: {e}", fg="red"))
        if hasattr(e, "suggestions") and e.suggestions:
            click.echo("\n💡 Suggestions:")
            for suggestion in e.suggestions:
                click.echo(f"   • {suggestion}")
        raise click.Abort() from e
    except ConfigurationError as e:
        click.echo(click.style(f"❌ Configuration error: {e}", fg="red"))
        if hasattr(e, "suggestions") and e.suggestions:
            click.echo("\n💡 Suggestions:")
            for suggestion in e.suggestions:
                click.echo(f"   • {suggestion}")
        raise click.Abort() from e
    except TicketQError as e:
        click.echo(click.style(f"❌ Error: {e}", fg="red"))
        if hasattr(e, "suggestions") and e.suggestions:
            click.echo("\n💡 Suggestions:")
            for suggestion in e.suggestions:
                click.echo(f"   • {suggestion}")
        raise click.Abort() from e
    except Exception as e:
        logger.exception("Unexpected error in configure command")
        click.echo(click.style(f"❌ Unexpected error: {e}", fg="red"))
        click.echo("💡 Please report this issue if it persists.")
        raise click.Abort() from e
