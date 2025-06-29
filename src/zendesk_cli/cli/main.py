"""Main CLI entry point for zendesk-cli."""

import logging
import sys
from pathlib import Path

# Try to import CLI dependencies, gracefully handle missing ones
try:
    import click
except ImportError:
    print("CLI dependencies not installed. Install with: pip install zendesk-cli[cli]")
    sys.exit(1)

try:
    from .commands.tickets import tickets
    from .commands.configure import configure
    from ..utils.logging import setup_logging
except ImportError as e:
    print(f"Failed to import CLI modules: {e}")
    print("Install CLI dependencies with: pip install zendesk-cli[cli]")
    sys.exit(1)


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
    log_level = "DEBUG" if verbose else "WARNING"
    log_path = Path(log_file) if log_file else None
    setup_logging(level=log_level, log_file=log_path, verbose=verbose)
    
    logger = logging.getLogger(__name__)
    logger.debug("Starting zendesk-cli")


# Add commands to the main group
main.add_command(tickets)
main.add_command(configure)


if __name__ == "__main__":
    main()