"""Main CLI entry point for zendesk-cli."""

import click
import logging
from pathlib import Path

from .commands.tickets import tickets
from .commands.configure import configure
from ..utils.logging import setup_logging


@click.group()
@click.option(
    '--verbose', '-v',
    is_flag=True,
    help='Enable verbose output'
)
@click.option(
    '--log-file',
    type=click.Path(),
    help='Log file path'
)
@click.version_option(version="0.1.0", prog_name="zendesk-cli")
def main(verbose: bool, log_file: str) -> None:
    """Zendesk CLI - Manage your Zendesk tickets from the command line.
    
    This tool allows you to:
    - List open tickets assigned to you or your groups
    - Configure your Zendesk credentials securely
    - Display tickets in a beautiful table format
    
    Get started by running:
        zendesk configure
    
    Then list your tickets with:
        zendesk tickets
    """
    # Setup logging
    log_level = "DEBUG" if verbose else "INFO"
    log_path = Path(log_file) if log_file else None
    setup_logging(level=log_level, log_file=log_path, verbose=verbose)
    
    logger = logging.getLogger(__name__)
    logger.debug("Starting zendesk-cli")


# Add commands to the main group
main.add_command(tickets)
main.add_command(configure)


if __name__ == "__main__":
    main()