"""Tickets command implementation."""

import click
import logging
import csv
from pathlib import Path
from typing import Optional
from rich.console import Console

from ...services.auth_service import AuthService
from ...services.ticket_service import TicketService
from ...models.exceptions import (
    ZendeskCliError, 
    ConfigurationError, 
    NetworkError, 
    RateLimitError,
    TimeoutError,
    KeyringError
)
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


def parse_groups(group_str: str, ticket_service: TicketService) -> list[int]:
    """Parse comma-separated group IDs or names into a list of group IDs.
    
    Args:
        group_str: Comma-separated group IDs or names
        ticket_service: TicketService to resolve group names
        
    Returns:
        List of group IDs as integers
        
    Raises:
        ValueError: If any group cannot be resolved
    """
    groups = [g.strip() for g in group_str.split(',') if g.strip()]
    group_ids = []
    
    for group in groups:
        # Try to parse as integer first (group ID)
        try:
            group_ids.append(int(group))
        except ValueError:
            # Not an integer, try to resolve as group name
            groups_mapping = ticket_service._get_groups_mapping()
            group_id = None
            
            # Search for group name (case-insensitive)
            for gid, gname in groups_mapping.items():
                if gname.lower() == group.lower():
                    group_id = gid
                    break
            
            if group_id is None:
                available_groups = list(groups_mapping.values()) if groups_mapping else []
                raise ValueError(
                    f"Group '{group}' not found. Available groups: {', '.join(available_groups) if available_groups else 'Unable to fetch group list'}"
                )
            
            group_ids.append(group_id)
    
    return group_ids


def export_tickets_to_csv(tickets_with_teams: list[dict], csv_path: str) -> None:
    """Export tickets with team names to a CSV file.
    
    Args:
        tickets_with_teams: List of dicts with 'ticket' and 'team_name' keys
        csv_path: Path to the CSV file to create
    """
    from ...utils.date_utils import format_date_for_display
    
    # Ensure directory exists
    Path(csv_path).parent.mkdir(parents=True, exist_ok=True)
    
    with open(csv_path, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.writer(csvfile, quoting=csv.QUOTE_ALL)
        
        # Write header
        writer.writerow([
            "Ticket #",
            "Status", 
            "Team Name",
            "Description",  # Full description, not truncated
            "Opened",
            "Days Since Opened",
            "Updated", 
            "Days Since Updated",
            "Link"
        ])
        
        # Write data rows
        for item in tickets_with_teams:
            ticket = item["ticket"]
            team_name = item["team_name"]
            
            writer.writerow([
                f"#{ticket.id}",
                ticket.status.capitalize(),
                team_name,
                ticket.description,  # Full description for CSV
                format_date_for_display(ticket.created_at),
                str(ticket.days_since_created),
                format_date_for_display(ticket.updated_at),
                str(ticket.days_since_updated),
                ticket.url
            ])


def sort_tickets_with_teams(tickets_with_teams: list[dict], sort_by: Optional[str]) -> list[dict]:
    """Sort tickets with team names by the specified column.
    
    Args:
        tickets_with_teams: List of dicts with 'ticket' and 'team_name' keys
        sort_by: Column to sort by (ticket, status, team, description, opened, days-opened, updated, days-updated)
        
    Returns:
        Sorted list of tickets with teams
    """
    if not sort_by:
        # Default: sort by opened date (newest first)
        return sorted(tickets_with_teams, key=lambda x: x["ticket"].created_at, reverse=True)
    
    sort_by = sort_by.lower()
    
    if sort_by == "ticket":
        return sorted(tickets_with_teams, key=lambda x: x["ticket"].id)
    elif sort_by == "status":
        return sorted(tickets_with_teams, key=lambda x: x["ticket"].status)
    elif sort_by == "team":
        return sorted(tickets_with_teams, key=lambda x: x["team_name"])
    elif sort_by == "description":
        return sorted(tickets_with_teams, key=lambda x: x["ticket"].description)
    elif sort_by == "opened":
        return sorted(tickets_with_teams, key=lambda x: x["ticket"].created_at, reverse=True)
    elif sort_by == "days-opened":
        return sorted(tickets_with_teams, key=lambda x: x["ticket"].days_since_created, reverse=True)
    elif sort_by == "updated":
        return sorted(tickets_with_teams, key=lambda x: x["ticket"].updated_at, reverse=True)
    elif sort_by == "days-updated":
        return sorted(tickets_with_teams, key=lambda x: x["ticket"].days_since_updated, reverse=True)
    else:
        # Fallback to default
        return sorted(tickets_with_teams, key=lambda x: x["ticket"].created_at, reverse=True)


def parse_statuses(status_str: Optional[str]) -> list[str]:
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
    statuses = [s.strip().lower() for s in status_str.split(',') if s.strip()]
    
    # Validate all statuses
    invalid_statuses = [s for s in statuses if s not in valid_statuses]
    if invalid_statuses:
        raise ValueError(
            f"Invalid status(es): {', '.join(invalid_statuses)}. "
            f"Valid statuses: {', '.join(sorted(valid_statuses))}"
        )
    
    return statuses


@click.command()
@click.option(
    '--assignee-only', 
    is_flag=True, 
    help='Show only tickets assigned to you'
)
@click.option(
    '--group', 
    type=str, 
    help='Filter tickets by group ID(s) or name(s). Use comma-separated values for multiple groups (e.g., "Support Team,Engineering" or 123,456,789)'
)
@click.option(
    '--status',
    type=str,
    help='Filter tickets by status. Use comma-separated values for multiple statuses (e.g., "open,pending" or "hold,closed"). Default: open'
)
@click.option(
    '--sort-by',
    type=click.Choice(['ticket', 'status', 'team', 'description', 'opened', 'days-opened', 'updated', 'days-updated'], case_sensitive=False),
    help='Sort results by column (ticket, status, team, description, opened, days-opened, updated, days-updated). Default: opened (newest first)'
)
@click.option(
    '--csv',
    type=click.Path(),
    help='Output results to CSV file (includes full descriptions, not truncated)'
)
@click.option(
    '--config-path',
    type=click.Path(),
    help='Path to configuration file'
)
def tickets(assignee_only: bool, group: Optional[str], status: Optional[str], sort_by: Optional[str], csv: Optional[str], config_path: Optional[str]) -> None:
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
        
        # Parse statuses (supports comma-separated values)
        try:
            ticket_statuses = parse_statuses(status)
        except ValueError as e:
            click.echo(click.style(f"❌ Error: {e}", fg='red'))
            raise click.Abort()
        
        # Create description for display
        if len(ticket_statuses) == 1 and ticket_statuses[0] == "open":
            status_desc = ""
        else:
            status_desc = f"{','.join(ticket_statuses)} "
            
        # Pass statuses to services (keep as list for multiple, single string for one)
        status_filter = ticket_statuses
        
        # Fetch tickets with team names based on options
        if assignee_only:
            click.echo(f"📋 Fetching {status_desc}tickets assigned to you...")
            user_info = ticket_service.get_current_user_info()
            user_tickets = ticket_service.get_user_tickets(user_info["id"], status_filter)
            # Convert to enriched format with team names
            enriched_tickets = []
            for ticket in user_tickets:
                team_name = ticket_service._get_team_name(ticket.group_id)
                enriched_tickets.append({"ticket": ticket, "team_name": team_name})
            tickets_with_teams = enriched_tickets
        elif group:
            try:
                group_ids = parse_groups(group, ticket_service)
                if len(group_ids) == 1:
                    group_id = group_ids[0]
                    # Get the actual group name for display
                    groups_mapping = ticket_service._get_groups_mapping()
                    group_display_name = groups_mapping.get(group_id, str(group_id))
                    
                    click.echo(f"📋 Fetching {status_desc}tickets for {group_display_name}...")
                    group_tickets = ticket_service.get_group_tickets(group_id, status_filter)
                    # Convert to enriched format with team names
                    enriched_tickets = []
                    for ticket in group_tickets:
                        team_name = ticket_service._get_team_name(ticket.group_id)
                        enriched_tickets.append({"ticket": ticket, "team_name": team_name})
                    tickets_with_teams = enriched_tickets
                else:
                    # Get group names for display
                    groups_mapping = ticket_service._get_groups_mapping()
                    group_names = [groups_mapping.get(gid, str(gid)) for gid in group_ids]
                    
                    click.echo(f"📋 Fetching {status_desc}tickets for {', '.join(group_names)}...")
                    group_tickets = ticket_service.get_multiple_groups_tickets(group_ids, status_filter)
                    # Convert to enriched format with team names
                    enriched_tickets = []
                    for ticket in group_tickets:
                        team_name = ticket_service._get_team_name(ticket.group_id)
                        enriched_tickets.append({"ticket": ticket, "team_name": team_name})
                    tickets_with_teams = enriched_tickets
            except ValueError as e:
                click.echo(click.style(f"❌ Error: {e}", fg='red'))
                raise click.Abort()
        else:
            click.echo(f"📋 Fetching all {status_desc}tickets...")
            tickets_with_teams = ticket_service.get_tickets_with_team_names(status_filter)
        
        # Display results
        if not tickets_with_teams:
            click.echo(
                click.style(
                    f"✅ No {','.join(ticket_statuses)} tickets found!",
                    fg='green'
                )
            )
            return
        
        # Sort tickets by specified column
        tickets_with_teams = sort_tickets_with_teams(tickets_with_teams, sort_by)
        
        # Export to CSV if requested
        if csv:
            try:
                export_tickets_to_csv(tickets_with_teams, csv)
                click.echo(click.style(f"✅ Exported {len(tickets_with_teams)} tickets to {csv}", fg='green'))
                # If CSV export is requested, still show the table unless user doesn't want it
            except Exception as e:
                click.echo(click.style(f"❌ Failed to export CSV: {e}", fg='red'))
                raise click.Abort()
        
        # Format and display table with team names
        formatter = TicketTableFormatter()
        table = formatter.format_tickets_with_teams_table(tickets_with_teams)
        
        click.echo(f"\n📊 Found {len(tickets_with_teams)} {','.join(ticket_statuses)} ticket(s):")
        
        # Use Rich console to properly render the table
        console = Console()
        console.print(table)
        
        # Show summary (extract tickets for summary)
        tickets_list = [item["ticket"] for item in tickets_with_teams]
        summary = ticket_service.get_tickets_summary(tickets_list)
        click.echo(f"\n📈 Summary:")
        click.echo(f"   Total: {summary['total']} tickets")
        
        if summary['by_status']:
            status_info = ", ".join(f"{status}: {count}" for status, count in summary['by_status'].items())
            click.echo(f"   Status: {status_info}")
            
    except RateLimitError as e:
        click.echo(click.style(f"⏳ Rate limited: {e}", fg='yellow'))
        if hasattr(e, 'retry_after') and e.retry_after:
            click.echo(f"   Please wait {e.retry_after} seconds before retrying.")
        if hasattr(e, 'suggestions') and e.suggestions:
            click.echo("\n💡 Suggestions:")
            for suggestion in e.suggestions:
                click.echo(f"   • {suggestion}")
        raise click.Abort()
    except TimeoutError as e:
        click.echo(click.style(f"⏰ Request timed out: {e}", fg='yellow'))
        if hasattr(e, 'suggestions') and e.suggestions:
            click.echo("\n💡 Suggestions:")
            for suggestion in e.suggestions:
                click.echo(f"   • {suggestion}")
        raise click.Abort()
    except NetworkError as e:
        click.echo(click.style(f"🌐 Network error: {e}", fg='red'))
        if hasattr(e, 'suggestions') and e.suggestions:
            click.echo("\n💡 Suggestions:")
            for suggestion in e.suggestions:
                click.echo(f"   • {suggestion}")
        raise click.Abort()
    except KeyringError as e:
        click.echo(click.style(f"🔐 Credential storage error: {e}", fg='red'))
        if hasattr(e, 'suggestions') and e.suggestions:
            click.echo("\n💡 Suggestions:")
            for suggestion in e.suggestions:
                click.echo(f"   • {suggestion}")
        raise click.Abort()
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
        click.echo("💡 Please report this issue if it persists.")
        raise click.Abort()