"""Main CLI entry point for TicketQ."""

import logging
import sys
from pathlib import Path

# Try to import CLI dependencies, gracefully handle missing ones
try:
    import click
except ImportError:
    print("CLI dependencies not installed. Install with: pip install ticketq[cli]")
    sys.exit(1)

try:
    from ..utils.logging import setup_logging
    from .commands.adapters import adapters
    from .commands.configure import configure
    from .commands.tickets import tickets
except ImportError as e:
    print(f"Failed to import CLI modules: {e}")
    print("Install CLI dependencies with: pip install ticketq[cli]")
    sys.exit(1)


@click.group()
@click.option("--verbose", "-v", is_flag=True, help="Enable verbose output")
@click.option("--log-file", type=click.Path(), help="Log file path")
@click.option(
    "--adapter",
    type=str,
    help="Override adapter selection (e.g., zendesk, jira, servicenow)",
)
@click.version_option(version="0.1.0", prog_name="ticketq")
def main(verbose: bool, log_file: str, adapter: str) -> None:
    """TicketQ - Universal command-line tool for ticketing systems.

    TicketQ supports multiple ticketing platforms through adapters:
    - Zendesk (install: pip install ticketq-zendesk)
    - Jira (coming soon)
    - ServiceNow (coming soon)

    Get started by configuring an adapter:
        tq configure

    Or configure a specific adapter:
        tq configure --adapter zendesk

    Then list your tickets:
        tq tickets

    View available adapters:
        tq adapters
    """
    # Setup logging
    log_level = "DEBUG" if verbose else "WARNING"
    log_path = Path(log_file) if log_file else None
    setup_logging(level=log_level, log_file=log_path, verbose=verbose)

    logger = logging.getLogger(__name__)
    logger.debug("Starting TicketQ")

    # Store adapter override in context for commands to use
    ctx = click.get_current_context()
    ctx.ensure_object(dict)
    ctx.obj["adapter"] = adapter


# Add commands to the main group
main.add_command(tickets)
main.add_command(configure)
main.add_command(adapters)


if __name__ == "__main__":
    main()
