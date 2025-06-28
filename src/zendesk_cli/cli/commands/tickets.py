"""Tickets command implementation."""

import click
import logging
from typing import Optional
from rich.console import Console

from ...services.auth_service import AuthService
from ...services.ticket_service import TicketService
from ...models.exceptions import ZendeskCliError, ConfigurationError
from ..formatters import TicketTableFormatter

logger = logging.getLogger(__name__)


def parse_group_ids(group_str: str) -> list[int]:
    """Parse comma-separated group IDs into a list of integers.
    
    Args:
        group_str: Comma-separated group IDs (e.g., "123,456,789")
        
    Returns:
        List of group IDs as integers
        
    Raises:
        ValueError: If any group ID is not a valid integer
    """
    try:
        return [int(gid.strip()) for gid in group_str.split(',') if gid.strip()]
    except ValueError as e:
        raise ValueError(f"Invalid group ID format. Please use comma-separated integers (e.g., 123,456,789)") from e


@click.command()
@click.option(
    '--assignee-only', 
    is_flag=True, 
    help='Show only tickets assigned to you'
)
@click.option(
    '--group', 
    type=str, 
    help='Filter tickets by group ID(s). Use comma-separated values for multiple groups (e.g., 123,456,789)'
)
@click.option(
    '--status',
    type=click.Choice(['new', 'open', 'pending', 'hold', 'solved', 'closed'], case_sensitive=False),
    help='Filter tickets by status (default: open)'
)
@click.option(
    '--config-path',
    type=click.Path(),
    help='Path to configuration file'
)
def tickets(assignee_only: bool, group: Optional[str], status: Optional[str], config_path: Optional[str]) -> None:
    """List Zendesk tickets assigned to you or your groups."""
    try:
        # Load configuration
        auth_service = AuthService()
        
        try:
            config = auth_service.load_config(config_path)
        except ConfigurationError:
            click.echo(
                click.style(
                    "❌ No configuration found. Run 'zendesk configure' first.",
                    fg='red'
                )
            )
            raise click.Abort()
        
        # Validate configuration
        if not auth_service.validate_config(config):
            click.echo(
                click.style(
                    "❌ Invalid configuration. Run 'zendesk configure' to fix.",
                    fg='red'
                )
            )
            raise click.Abort()
        
        # Create client and service
        client = auth_service.create_client_from_config(config)
        ticket_service = TicketService(client)
        
        # Default status to "open" if not specified
        ticket_status = status or "open"
        status_desc = f"{ticket_status} " if ticket_status != "open" else ""
        
        # Fetch tickets based on options
        if assignee_only:
            click.echo(f"📋 Fetching {status_desc}tickets assigned to you...")
            user_info = ticket_service.get_current_user_info()
            tickets_list = ticket_service.get_user_tickets(user_info["id"], ticket_status)
        elif group:
            try:
                group_ids = parse_group_ids(group)
                if len(group_ids) == 1:
                    click.echo(f"📋 Fetching {status_desc}tickets for group {group_ids[0]}...")
                    tickets_list = ticket_service.get_group_tickets(group_ids[0], ticket_status)
                else:
                    click.echo(f"📋 Fetching {status_desc}tickets for groups {', '.join(map(str, group_ids))}...")
                    tickets_list = ticket_service.get_multiple_groups_tickets(group_ids, ticket_status)
            except ValueError as e:
                click.echo(click.style(f"❌ Error: {e}", fg='red'))
                raise click.Abort()
        else:
            click.echo(f"📋 Fetching all {status_desc}tickets...")
            tickets_list = ticket_service.get_all_tickets(ticket_status)
        
        # Display results
        if not tickets_list:
            click.echo(
                click.style(
                    f"✅ No {ticket_status} tickets found!",
                    fg='green'
                )
            )
            return
        
        # Format and display table
        formatter = TicketTableFormatter()
        table = formatter.format_tickets_table(tickets_list)
        
        click.echo(f"\n📊 Found {len(tickets_list)} {ticket_status} ticket(s):")
        
        # Use Rich console to properly render the table
        console = Console()
        console.print(table)
        
        # Show summary
        summary = ticket_service.get_tickets_summary(tickets_list)
        click.echo(f"\n📈 Summary:")
        click.echo(f"   Total: {summary['total']} tickets")
        
        if summary['by_status']:
            status_info = ", ".join(f"{status}: {count}" for status, count in summary['by_status'].items())
            click.echo(f"   Status: {status_info}")
            
    except ZendeskCliError as e:
        click.echo(click.style(f"❌ Error: {e}", fg='red'))
        if hasattr(e, 'suggestions') and e.suggestions:
            click.echo("\n💡 Suggestions:")
            for suggestion in e.suggestions:
                click.echo(f"   • {suggestion}")
        raise click.Abort()
    except Exception as e:
        logger.exception("Unexpected error in tickets command")
        click.echo(click.style(f"❌ Unexpected error: {e}", fg='red'))
        raise click.Abort()