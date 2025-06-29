"""Adapters command implementation."""

import logging
from pathlib import Path

import click
from rich.console import Console
from rich.table import Table

from ...core.factory import get_factory
from ...core.registry import get_registry
from ...models.exceptions import ConfigurationError, PluginError, TicketQError
from ...utils.config import ConfigManager

logger = logging.getLogger(__name__)


def create_adapters_table(adapters_info: list[dict[str, str]]) -> Table:
    """Create a Rich table for displaying adapters.

    Args:
        adapters_info: List of adapter info dictionaries

    Returns:
        Rich Table object
    """
    table = Table(
        title="🔌 Available Adapters", show_header=True, header_style="bold blue"
    )

    # Add columns
    table.add_column("Name", style="cyan", no_wrap=True)
    table.add_column("Display Name", style="green")
    table.add_column("Version", style="yellow", no_wrap=True)
    table.add_column("Status", style="white")
    table.add_column("Features", style="blue", max_width=40)

    # Add rows
    for adapter_info in adapters_info:
        table.add_row(
            adapter_info["name"],
            adapter_info["display_name"],
            adapter_info["version"],
            adapter_info["status"],
            adapter_info["features"],
        )

    return table


@click.command()
@click.option(
    "--config-path", type=click.Path(), help="Path to configuration directory"
)
@click.option("--test", is_flag=True, help="Test all configured adapters")
@click.option(
    "--install-guide", is_flag=True, help="Show installation guide for adapters"
)
def adapters(config_path: str | None, test: bool, install_guide: bool) -> None:
    """Manage TicketQ adapters and view their status."""

    try:
        # Show installation guide if requested
        if install_guide:
            click.echo("📦 TicketQ Adapter Installation Guide")
            click.echo("=====================================")
            click.echo()
            click.echo(
                "To use TicketQ with different ticketing systems, you need to install adapter packages:"
            )
            click.echo()
            click.echo("🎫 Zendesk:")
            click.echo("   pip install ticketq-zendesk")
            click.echo()
            click.echo("🔧 Jira (coming soon):")
            click.echo("   pip install ticketq-jira")
            click.echo()
            click.echo("📋 ServiceNow (coming soon):")
            click.echo("   pip install ticketq-servicenow")
            click.echo()
            click.echo("After installation, configure an adapter:")
            click.echo("   tq configure --adapter zendesk")
            click.echo()
            click.echo("Then list your tickets:")
            click.echo("   tq tickets")
            return

        # Setup config manager
        config_dir = Path(config_path) if config_path else None
        config_manager = ConfigManager(config_dir)

        # Get available adapters
        registry = get_registry()
        available_adapters = registry.get_available_adapters()

        if not available_adapters:
            click.echo(click.style("❌ No adapters installed", fg="red"))
            click.echo()
            click.echo("💡 Install adapter packages to get started:")
            click.echo("   pip install ticketq-zendesk")
            click.echo()
            click.echo("For more installation options, run:")
            click.echo("   tq adapters --install-guide")
            return

        # Collect adapter information
        adapters_info = []

        for adapter_name in sorted(available_adapters.keys()):
            adapter_class = available_adapters[adapter_name]

            try:
                # Create adapter instance
                adapter_instance = adapter_class()

                # Check if configured
                status = "❌ Not configured"
                try:
                    adapter_config = config_manager.get_adapter_config(adapter_name)
                    if adapter_config and adapter_instance.validate_config(
                        adapter_config
                    ):
                        status = "✅ Configured"
                    else:
                        status = "⚠️ Invalid config"
                except ConfigurationError:
                    status = "❌ Not configured"

                # Test connection if requested
                if test and "✅" in status:
                    try:
                        factory = get_factory()
                        adapter = factory.create_adapter(adapter_name)

                        # Test connection
                        if adapter._client.test_connection():
                            status = "✅ Working"
                        else:
                            status = "❌ Connection failed"
                    except Exception:
                        status = "❌ Connection failed"

                # Format features
                features = ", ".join(adapter_instance.supported_features[:3])
                if len(adapter_instance.supported_features) > 3:
                    features += (
                        f", +{len(adapter_instance.supported_features) - 3} more"
                    )

                adapters_info.append(
                    {
                        "name": adapter_name,
                        "display_name": adapter_instance.display_name,
                        "version": adapter_instance.version,
                        "status": status,
                        "features": features,
                    }
                )

            except Exception as e:
                adapters_info.append(
                    {
                        "name": adapter_name,
                        "display_name": "Unknown",
                        "version": "Unknown",
                        "status": f"❌ Error: {e}",
                        "features": "Unknown",
                    }
                )

        # Display table
        table = create_adapters_table(adapters_info)

        console = Console()
        console.print(table)

        # Show summary
        total_adapters = len(adapters_info)
        configured_adapters = len([a for a in adapters_info if "✅" in a["status"]])

        click.echo(
            f"\n📊 Summary: {configured_adapters}/{total_adapters} adapters configured"
        )

        # Show next steps if no adapters configured
        if configured_adapters == 0:
            click.echo("\n💡 Next steps:")
            click.echo("   1. Configure an adapter: tq configure --adapter <name>")
            click.echo("   2. List tickets: tq tickets")

        # Show available actions
        click.echo("\n🔧 Available actions:")
        click.echo("   • Configure adapter: tq configure --adapter <name>")
        click.echo("   • Test connections: tq adapters --test")
        click.echo("   • Installation guide: tq adapters --install-guide")

    except PluginError as e:
        click.echo(click.style(f"❌ Plugin error: {e}", fg="red"))
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
        logger.exception("Unexpected error in adapters command")
        click.echo(click.style(f"❌ Unexpected error: {e}", fg="red"))
        click.echo("💡 Please report this issue if it persists.")
        raise click.Abort() from e
