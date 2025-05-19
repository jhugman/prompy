"""
Error handling utilities for Prompy.

This module provides consistent error handling and reporting across the application.
"""

import logging
import sys
from typing import Any, Callable, Dict, List, Optional, Union

import click

logger = logging.getLogger(__name__)


class PrompyError(Exception):
    """Base exception class for Prompy errors."""

    def __init__(self, message: str, details: Optional[str] = None):
        self.message = message
        self.details = details
        super().__init__(message)

    def __str__(self) -> str:
        if self.details:
            return f"{self.message}\n{self.details}"
        return self.message


class FragmentNotFoundError(PrompyError):
    """Exception raised when a fragment reference cannot be found."""

    def __init__(
        self,
        fragment_slug: str,
        search_paths: List[str],
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
    ):
        self.fragment_slug = fragment_slug
        self.search_paths = search_paths
        self.file_path = file_path
        self.line_number = line_number

        message = f"Missing prompt fragment '@{fragment_slug}'"
        details = self._format_details()
        super().__init__(message, details)

    def _format_details(self) -> str:
        """Format detailed error information."""
        details = []

        if self.file_path:
            details.append(f"  in file: {self.file_path}")

        if self.line_number is not None:
            details.append(f"  at line: {self.line_number}")

        details.append("  searched paths:")
        for path in self.search_paths:
            details.append(f"    - {path}")

        return "\n".join(details)


class CyclicReferenceError(PrompyError):
    """Exception raised when a cyclic reference is detected in fragment resolution."""

    def __init__(
        self,
        cycle_path: List[str],
        start_file: Optional[str] = None,
        line_number: Optional[int] = None,
    ):
        self.cycle_path = cycle_path
        self.start_file = start_file
        self.line_number = line_number

        cycle_str = " -> ".join([f"'@{slug}'" for slug in cycle_path])
        message = f"Cyclic reference detected {cycle_str}"
        details = self._format_details()
        super().__init__(message, details)

    def _format_details(self) -> str:
        """Format detailed error information."""
        details = []

        if self.start_file:
            details.append(f"  in file: {self.start_file}")

            for path in self.cycle_path:
                details.append(f"  - {path}")

        if self.line_number is not None:
            details.append(f"  starting at line: {self.line_number}")

        return "\n".join(details)


class MissingArgumentError(PrompyError):
    """Exception raised when a required argument is missing in a fragment reference."""

    def __init__(
        self,
        fragment_slug: str,
        argument_name: str,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
    ):
        self.fragment_slug = fragment_slug
        self.argument_name = argument_name
        self.file_path = file_path
        self.line_number = line_number

        message = f"Missing required argument '{argument_name}' for fragment '@{fragment_slug}'"
        details = self._format_details()
        super().__init__(message, details)

    def _format_details(self) -> str:
        """Format detailed error information."""
        details = []

        if self.file_path:
            details.append(f"  in file: {self.file_path}")

        if self.line_number is not None:
            details.append(f"  at line: {self.line_number}")

        return "\n".join(details)


def handle_error(
    exception: Exception,
    ctx: Optional[click.Context] = None,
    exit_code: int = 1,
    show_traceback: bool = False,
) -> None:
    """
    Handle an exception in a consistent way.

    Args:
        exception: The exception to handle
        ctx: Click context (optional, used to check debug flag)
        exit_code: The exit code to use when exiting (default: 1)
        show_traceback: Whether to show the traceback even if not in debug mode
    """
    # Log the error
    logger.error(str(exception))

    # Check if we should show the full traceback
    debug_mode = ctx and ctx.obj and ctx.obj.get("debug", False)
    if debug_mode or show_traceback:
        logger.exception(exception)

    # Print the error message to stderr
    click.echo(f"Error: {exception}", err=True)

    # Exit with the specified code if not None
    if exit_code is not None:
        sys.exit(exit_code)


# Known limitations and possible future improvements:
#
# 1. Currently, error handling focuses on fragment resolution and CLI errors.
#    Future versions could extend to handle editor integration errors more gracefully.
#
# 2. Error messages could be improved with color coding using libraries like colorama.
#
# 3. A centralized error catalog could be created to ensure consistent error messages
#    across the application.
#
# 4. More specific error types could be added for various situations, such as file access errors,
#    permissions issues, etc.
#
# 5. Error reporting could be enhanced with suggestions for fixing common issues.
