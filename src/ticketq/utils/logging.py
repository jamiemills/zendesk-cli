"""Logging utilities for ticketq."""

import logging
import sys
from pathlib import Path


def setup_logging(
    level: str = "INFO",
    log_file: Path | None = None,
    verbose: bool = False,
    format_string: str | None = None,
) -> None:
    """Set up logging for ticketq.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR)
        log_file: Path to log file (optional)
        verbose: Enable verbose console output
        format_string: Custom log format string
    """
    # Convert string level to logging constant
    numeric_level = getattr(logging, level.upper(), logging.INFO)

    # Default format
    if format_string is None:
        if verbose:
            format_string = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
        else:
            format_string = "%(levelname)s: %(message)s"

    # Configure root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture everything

    # Clear existing handlers
    root_logger.handlers.clear()

    # Console handler
    console_handler = logging.StreamHandler(sys.stderr)
    console_formatter = logging.Formatter(format_string)
    console_handler.setFormatter(console_formatter)

    # Set console level based on verbose flag
    if verbose:
        console_handler.setLevel(numeric_level)
    else:
        # Only show warnings and errors unless in verbose mode
        console_handler.setLevel(logging.WARNING)

    root_logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        try:
            # Ensure parent directory exists
            log_file.parent.mkdir(parents=True, exist_ok=True)

            file_handler = logging.FileHandler(log_file)
            file_formatter = logging.Formatter(
                "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
            )
            file_handler.setFormatter(file_formatter)
            file_handler.setLevel(logging.DEBUG)  # Log everything to file

            root_logger.addHandler(file_handler)

        except Exception as e:
            # Don't fail if we can't set up file logging
            logging.warning(f"Could not set up file logging: {e}")

    # Set specific logger levels
    logging.getLogger("urllib3").setLevel(logging.WARNING)
    logging.getLogger("requests").setLevel(logging.WARNING)

    # TicketQ logger for our own messages
    ticketq_logger = logging.getLogger("ticketq")
    ticketq_logger.setLevel(numeric_level)
