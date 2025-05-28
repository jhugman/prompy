"""
Error handling utilities for Prompy.

This module provides consistent error handling and reporting across the application.
"""

import logging
import sys
import textwrap
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

import click

logger = logging.getLogger(__name__)


class PrompyError(Exception):
    """Base exception class for Prompy errors."""

    def __init__(
        self,
        message: str,
        details: Optional[str] = None,
        suggestion: Optional[str] = None,
        snippet: Optional[str] = None,
        snippet_line: Optional[int] = None,
        snippet_context: int = 2,
    ):
        self.message = message
        self.details = details
        self.suggestion = suggestion
        self.snippet = snippet
        self.snippet_line = snippet_line
        self.snippet_context = snippet_context
        super().__init__(message)

    def __str__(self) -> str:
        result = [self.message]

        if self.details:
            result.append(self.details)

        if self.snippet and self.snippet_line is not None:
            result.append(self._format_snippet())

        if self.suggestion:
            result.append(f"Suggestion: {self.suggestion}")

        return "\n".join(result)

    def _format_snippet(self) -> str:
        """Format the code snippet with line numbers and highlight the error line."""
        if not self.snippet or self.snippet_line is None:
            return ""

        lines = self.snippet.splitlines()
        result = ["", "Code snippet:"]

        # Determine which lines to show based on the context setting
        start_line = max(0, self.snippet_line - self.snippet_context)
        end_line = min(len(lines), self.snippet_line + self.snippet_context + 1)

        # Format the lines with line numbers
        max_lineno_width = len(str(end_line))

        for i in range(start_line, end_line):
            line = lines[i]
            line_number = i + 1  # Convert to 1-based line numbers
            line_prefix = f"{line_number:>{max_lineno_width}} | "

            if (
                line_number == self.snippet_line + 1
            ):  # +1 because snippet_line is 0-based
                # Highlight the error line
                result.append(f"{line_prefix}{line}")
                # Add a marker arrow under the line
                result.append(" " * max_lineno_width + " | " + "^" * 10 + " ERROR")
            else:
                result.append(f"{line_prefix}{line}")

        return "\n".join(result)


class FragmentNotFoundError(PrompyError):
    """Exception raised when a fragment reference cannot be found."""

    def __init__(
        self,
        fragment_slug: str,
        search_paths: List[str],
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        template_content: Optional[str] = None,
    ):
        self.fragment_slug = fragment_slug
        self.search_paths = search_paths
        self.file_path = file_path
        self.line_number = line_number

        message = f"Missing prompt fragment '@{fragment_slug}'"
        details = self._format_details()

        # Generate a helpful suggestion
        suggestion = self._generate_suggestion()

        # Extract snippet if available
        snippet = None
        snippet_line = None
        if template_content and line_number is not None:
            snippet = template_content
            snippet_line = line_number

        super().__init__(message, details, suggestion, snippet, snippet_line)

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

    def _generate_suggestion(self) -> Optional[str]:
        """Generate a helpful suggestion based on the error."""
        suggestions = [
            f"Check if the fragment '@{self.fragment_slug}' exists in one of the prompt directories.",
            f"Try running 'prompy list' to see available fragments.",
        ]
        return " ".join(suggestions)


class CyclicReferenceError(PrompyError):
    """Exception raised when a cyclic reference is detected in fragment resolution."""

    def __init__(
        self,
        cycle_path: List[str],
        start_file: Optional[str] = None,
        line_number: Optional[int] = None,
        template_content: Optional[str] = None,
    ):
        self.cycle_path = cycle_path
        self.start_file = start_file
        self.line_number = line_number

        cycle_str = " -> ".join([f"'@{slug}'" for slug in cycle_path])
        message = f"Cyclic reference detected {cycle_str}"
        details = self._format_details()

        # Generate a helpful suggestion
        suggestion = self._generate_suggestion()

        # Extract snippet if available
        snippet = None
        snippet_line = None
        if template_content and line_number is not None:
            snippet = template_content
            snippet_line = line_number

        super().__init__(message, details, suggestion, snippet, snippet_line)

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

    def _generate_suggestion(self) -> str:
        """Generate a helpful suggestion based on the error."""
        return "Break the cycle by removing one of the references in the chain or restructuring your templates."


class MissingArgumentError(PrompyError):
    """Exception raised when a required argument is missing in a fragment reference."""

    def __init__(
        self,
        fragment_slug: str,
        argument_name: str,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        template_content: Optional[str] = None,
        required_args: Optional[List[str]] = None,
    ):
        self.fragment_slug = fragment_slug
        self.argument_name = argument_name
        self.file_path = file_path
        self.line_number = line_number
        self.required_args = required_args or []

        message = f"Missing required argument '{argument_name}' for fragment '@{fragment_slug}'"
        details = self._format_details()

        # Generate a helpful suggestion
        suggestion = self._generate_suggestion()

        # Extract snippet if available
        snippet = None
        snippet_line = None
        if template_content and line_number is not None:
            snippet = template_content
            snippet_line = line_number

        super().__init__(message, details, suggestion, snippet, snippet_line)

    def _format_details(self) -> str:
        """Format detailed error information."""
        details = []

        if self.file_path:
            details.append(f"  in file: {self.file_path}")

        if self.line_number is not None:
            details.append(f"  at line: {self.line_number}")

        if self.required_args:
            details.append(f"  required arguments: {', '.join(self.required_args)}")

        return "\n".join(details)

    def _generate_suggestion(self) -> str:
        """Generate a helpful suggestion based on the error."""
        correct_usage = f"@{self.fragment_slug}({self.argument_name}=value)"
        return f"Add the missing argument to your reference: {correct_usage}"


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
    diagnose_mode = ctx and ctx.obj and ctx.obj.get("diagnose", False)

    if debug_mode or show_traceback:
        logger.exception(exception)

    # Print the error message to stderr with nice formatting
    if isinstance(exception, PrompyError):
        # Use color if supported
        click.echo(
            click.style("Error: ", fg="red", bold=True)
            + click.style(exception.message, fg="red"),
            err=True,
        )

        if exception.details:
            click.echo(exception.details, err=True)

        if exception.snippet:
            click.echo("", err=True)
            click.echo("Code snippet:", err=True)
            lines = exception.snippet.splitlines()
            start_line = max(
                0, (exception.snippet_line or 0) - (exception.snippet_context or 2)
            )
            end_line = min(
                len(lines),
                (exception.snippet_line or 0) + (exception.snippet_context or 2) + 1,
            )

            max_lineno_width = len(str(end_line))
            for i in range(start_line, end_line):
                line = lines[i]
                line_number = i + 1  # Convert to 1-based line numbers
                line_prefix = f"{line_number:>{max_lineno_width}} | "

                if (
                    line_number == (exception.snippet_line or 0) + 1
                ):  # +1 because snippet_line is 0-based
                    # Highlight the error line
                    click.echo(
                        click.style(line_prefix, fg="bright_black")
                        + click.style(line, fg="yellow", bold=True),
                        err=True,
                    )
                    # Add a marker arrow under the line
                    click.echo(
                        click.style(
                            " " * max_lineno_width + " | " + "^" * 10 + " ERROR",
                            fg="red",
                            bold=True,
                        ),
                        err=True,
                    )
                else:
                    click.echo(
                        click.style(line_prefix, fg="bright_black") + line, err=True
                    )

        if exception.suggestion:
            click.echo("", err=True)
            click.echo(
                click.style("Suggestion: ", fg="green", bold=True)
                + click.style(exception.suggestion, fg="green"),
                err=True,
            )
    else:
        # For non-PrompyError exceptions, use simple formatting
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
