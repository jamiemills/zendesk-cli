"""Tickets command implementation."""

import logging
from pathlib import Path
from typing import Any

import click
from rich.console import Console
from rich.table import Table

from ...lib.client import TicketQLibrary
from ...models.exceptions import (
    APIError,
    AuthenticationError,
    ConfigurationError,
    NetworkError,
    PluginError,
    RateLimitError,
    TicketQError,
)

logger = logging.getLogger(__name__)


def parse_statuses(status_str: str | None) -> list[str]:
    """Parse comma-separated statuses into a list of valid statuses.

    Args:
        status_str: Comma-separated status values (e.g., "open,pending")

    Returns:
        List of valid status strings

    Raises:
        ValueError: If any status is not valid
    """
    if not status_str:
        return ["open"]  # Default to open

    valid_statuses = {"new", "open", "pending", "hold", "solved", "closed"}
    statuses = [s.strip().lower() for s in status_str.split(",") if s.strip()]

    # Validate all statuses
    invalid_statuses = [s for s in statuses if s not in valid_statuses]
    if invalid_statuses:
        raise ValueError(
            f"Invalid status(es): {', '.join(invalid_statuses)}. "
            f"Valid statuses: {', '.join(sorted(valid_statuses))}"
        )

    return statuses


def create_tickets_table(tickets: list[Any], show_adapter: bool = False) -> Table:
    """Create a Rich table for displaying tickets.

    Args:
        tickets: List of LibraryTicket objects with properties like id, title,
                status, assignee, created_at, updated_at, days_since_created, etc.
        show_adapter: Whether to include adapter name column for multi-adapter scenarios

    Returns:
        Rich Table object ready for console.print() with formatted columns:
        - Ticket # (cyan, no wrap)
        - Status (green)
        - Team Name (yellow)
        - Description (truncated to 80 chars)
        - Opened/Days Since/Updated/Days Since/Link columns
        - Optional Adapter column when show_adapter=True

    Example:
        tickets = tq.get_tickets(status=["open", "pending"])
        table = create_tickets_table(tickets, show_adapter=True)
        console.print(table)
    """
    table = Table(title="🎫 Tickets", show_header=True, header_style="bold blue")

    # Add columns
    table.add_column("Ticket #", style="cyan", no_wrap=True)
    table.add_column("Status", style="green")
    table.add_column("Team", style="yellow", max_width=20)
    table.add_column("Title", style="white", max_width=40)
    table.add_column("Created", style="blue", no_wrap=True)
    table.add_column("Days", style="red", justify="right")
    table.add_column("Updated", style="blue", no_wrap=True)
    table.add_column("Stale", style="red", justify="right")

    if show_adapter:
        table.add_column("Adapter", style="magenta")

    # Add rows
    for ticket in tickets:
        row = [
            f"#{ticket.id}",
            ticket.status.capitalize(),
            ticket.team_name or "Unassigned",
            ticket.title[:40] + "..." if len(ticket.title) > 40 else ticket.title,
            ticket.created_at.strftime("%Y-%m-%d"),
            str(ticket.days_since_created),
            ticket.updated_at.strftime("%Y-%m-%d"),
            str(ticket.days_since_updated),
        ]

        if show_adapter:
            row.append(ticket.adapter_name.capitalize())

        table.add_row(*row)

    return table


def get_tickets_summary(tickets: list[Any]) -> dict[str, Any]:
    """Generate summary statistics for tickets.

    Args:
        tickets: List of LibraryTicket objects

    Returns:
        Dictionary with summary statistics
    """
    if not tickets:
        return {"total": 0, "by_status": {}, "by_adapter": {}}

    by_status: dict[str, int] = {}
    by_adapter: dict[str, int] = {}

    for ticket in tickets:
        # Count by status
        status = ticket.status
        by_status[status] = by_status.get(status, 0) + 1

        # Count by adapter
        adapter = ticket.adapter_name
        by_adapter[adapter] = by_adapter.get(adapter, 0) + 1

    return {
        "total": len(tickets),
        "by_status": by_status,
        "by_adapter": by_adapter,
    }


@click.command()
@click.option("--assignee-only", is_flag=True, help="Show only tickets assigned to you")
@click.option(
    "--group",
    type=str,
    help="Filter tickets by group ID(s) or name(s). Use comma-separated values for multiple groups",
)
@click.option(
    "--status",
    type=str,
    help='Filter tickets by status. Use comma-separated values for multiple statuses (e.g., "open,pending"). Default: open',
)
@click.option(
    "--sort-by",
    type=click.Choice(
        [
            "id",
            "title",
            "status",
            "team",
            "created_at",
            "updated_at",
            "days_created",
            "days_updated",
        ],
        case_sensitive=False,
    ),
    help="Sort results by column. Default: created_at (newest first)",
)
@click.option(
    "--csv",
    type=click.Path(),
    help="Export results to CSV file (includes full descriptions, not truncated)",
)
@click.option(
    "--config-path", type=click.Path(), help="Path to configuration directory"
)
@click.option(
    "--adapter",
    type=str,
    help="Override adapter selection (e.g., zendesk, jira, servicenow)",
)
@click.pass_context
def tickets(
    ctx: click.Context,
    assignee_only: bool,
    group: str | None,
    status: str | None,
    sort_by: str | None,
    csv: str | None,
    config_path: str | None,
    adapter: str | None,
) -> None:
    """List tickets from your ticketing system."""

    def progress_callback(message: str) -> None:
        """Progress callback for long operations."""
        if ctx.obj and ctx.obj.get("verbose"):
            click.echo(f"🔄 {message}")

    try:
        # Get adapter override from global context or local option
        adapter_name = adapter or (ctx.obj and ctx.obj.get("adapter"))

        # Parse statuses (supports comma-separated values)
        try:
            ticket_statuses = parse_statuses(status)
        except ValueError as e:
            click.echo(click.style(f"❌ Error: {e}", fg="red"))
            raise click.Abort() from e

        # Create TicketQ library instance
        try:
            config_dir = Path(config_path) if config_path else None
            tq = TicketQLibrary.from_config(
                adapter_name=adapter_name,
                config_path=config_dir,
                progress_callback=progress_callback,
            )
        except ConfigurationError as e:
            click.echo(click.style(f"❌ Configuration error: {e}", fg="red"))
            if hasattr(e, "suggestions") and e.suggestions:
                click.echo("\n💡 Suggestions:")
                for suggestion in e.suggestions:
                    click.echo(f"   • {suggestion}")
            raise click.Abort() from e
        except PluginError as e:
            click.echo(click.style(f"❌ Plugin error: {e}", fg="red"))
            if hasattr(e, "suggestions") and e.suggestions:
                click.echo("\n💡 Suggestions:")
                for suggestion in e.suggestions:
                    click.echo(f"   • {suggestion}")
            raise click.Abort() from e

        # Show which adapter we're using
        adapter_info = tq.get_adapter_info()
        if not adapter_name:  # Only show if auto-detected
            click.echo(f"🔌 Using {adapter_info['display_name']} adapter")

        # Build filter description for display
        status_desc = (
            f"{','.join(ticket_statuses)} " if ticket_statuses != ["open"] else ""
        )

        # Parse groups if provided
        groups_list = None
        if group:
            groups_list = [g.strip() for g in group.split(",") if g.strip()]

        # Fetch tickets
        click.echo(f"📋 Fetching {status_desc}tickets...")

        ticket_list = tq.get_tickets(
            status=ticket_statuses,
            assignee_only=assignee_only,
            groups=groups_list,
            sort_by=sort_by,
            include_team_names=True,
        )

        # Display results
        if not ticket_list:
            click.echo(
                click.style(
                    f"✅ No {','.join(ticket_statuses)} tickets found!", fg="green"
                )
            )
            return

        # Export to CSV if requested
        if csv:
            try:
                tq.export_to_csv(ticket_list, csv)
                click.echo(
                    click.style(
                        f"✅ Exported {len(ticket_list)} tickets to {csv}", fg="green"
                    )
                )
            except Exception as e:
                click.echo(click.style(f"❌ Failed to export CSV: {e}", fg="red"))
                raise click.Abort() from e

        # Show whether to display adapter column (useful if multiple adapters configured)
        show_adapter = len({t.adapter_name for t in ticket_list}) > 1

        # Create and display table
        table = create_tickets_table(ticket_list, show_adapter=show_adapter)

        click.echo(
            f"\n📊 Found {len(ticket_list)} {','.join(ticket_statuses)} ticket(s):"
        )

        # Use Rich console to properly render the table
        console = Console()
        console.print(table)

        # Show summary
        summary = get_tickets_summary(ticket_list)
        click.echo("\n📈 Summary:")
        click.echo(f"   Total: {summary['total']} tickets")

        if summary["by_status"]:
            status_info = ", ".join(
                f"{status}: {count}" for status, count in summary["by_status"].items()
            )
            click.echo(f"   Status: {status_info}")

        if show_adapter and summary["by_adapter"]:
            adapter_summary = ", ".join(
                f"{adapter}: {count}"
                for adapter, count in summary["by_adapter"].items()
            )
            click.echo(f"   Adapters: {adapter_summary}")

    except AuthenticationError as e:
        click.echo(click.style(f"🔐 Authentication error: {e}", fg="red"))
        if hasattr(e, "suggestions") and e.suggestions:
            click.echo("\n💡 Suggestions:")
            for suggestion in e.suggestions:
                click.echo(f"   • {suggestion}")
        raise click.Abort() from e
    except RateLimitError as e:
        click.echo(click.style(f"⏳ Rate limited: {e}", fg="yellow"))
        if hasattr(e, "retry_after") and e.retry_after:
            click.echo(f"   Please wait {e.retry_after} seconds before retrying.")
        if hasattr(e, "suggestions") and e.suggestions:
            click.echo("\n💡 Suggestions:")
            for suggestion in e.suggestions:
                click.echo(f"   • {suggestion}")
        raise click.Abort() from e
    except NetworkError as e:
        click.echo(click.style(f"🌐 Network error: {e}", fg="red"))
        if hasattr(e, "suggestions") and e.suggestions:
            click.echo("\n💡 Suggestions:")
            for suggestion in e.suggestions:
                click.echo(f"   • {suggestion}")
        raise click.Abort() from e
    except APIError as e:
        click.echo(click.style(f"🔧 API error: {e}", fg="red"))
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
        logger.exception("Unexpected error in tickets command")
        click.echo(click.style(f"❌ Unexpected error: {e}", fg="red"))
        click.echo("💡 Please report this issue if it persists.")
        raise click.Abort() from e
