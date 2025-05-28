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
        snippet_column: Optional[int] = None,
        file_path: Optional[str] = None,
    ):
        """Initialize a Prompy error with enhanced context.

        Args:
            message: The main error message
            details: Additional error details
            suggestion: A helpful suggestion for fixing the error
            snippet: The code snippet where the error occurred
            snippet_line: Line number in the snippet where the error occurred (1-based)
            snippet_context: Number of lines of context to show around the error
            snippet_column: Column number where the error occurred (1-based)
            file_path: Path to the file where the error occurred
        """
        super().__init__(message)
        self.message = message
        self.details = details
        self.suggestion = suggestion
        self.snippet = snippet
        self.snippet_line = snippet_line
        self.snippet_context = snippet_context
        self.snippet_column = snippet_column
        self.file_path = file_path
        self.line_number = snippet_line  # Store line number for formatting

    def __str__(self) -> str:
        """Format the error message with all available context."""
        parts = []

        # Start with the message
        parts.append(self.message)

        # Add details if present, with a blank line before them
        if self.details:
            parts.append(self.details)

        # Add the snippet info if available
        if self.snippet and self.snippet_line is not None:
            parts.append(self._format_snippet())

        # Add suggestion if present
        if self.suggestion:
            suggestions = ["Suggestion:", "  " + self.suggestion]
            parts.append("\n".join(suggestions))

        # Join all parts with newlines
        return "\n".join(part for part in parts if part)

    def _format_snippet(self) -> str:
        """Format the code snippet with line numbers and highlight the error line and column."""
        if not self.snippet or self.snippet_line is None:
            return ""

        lines = self.snippet.splitlines()
        result = ["Code context:"]

        # Determine which lines to show based on the context setting
        start_line = max(
            0, self.snippet_line - 1 - self.snippet_context
        )  # Convert to 0-based
        end_line = min(len(lines), self.snippet_line + self.snippet_context)

        # Format the lines with line numbers
        max_lineno_width = len(str(end_line + 1))  # +1 for 1-based line numbers
        gutter_width = max_lineno_width + 3  # 3 for " | "

        for i in range(start_line, end_line):
            current_line = lines[i]
            line_number = i + 1  # Convert to 1-based line numbers
            line_prefix = f"{line_number:>{max_lineno_width}} | "

            # Style the lines and add them to the result
            if i == self.snippet_line - 1:  # -1 to convert to 0-based
                # Add the error line with highlighting
                result.append(f"{line_prefix}{current_line}")

                # Add marker arrow for precise error location
                if self.snippet_column is not None:
                    # Create column-specific marker
                    marker = (
                        " " * (self.snippet_column - 1) + "^"
                    )  # -1 for 0-based column
                    marker_prefix = " " * gutter_width
                    result.append(f"{marker_prefix}{marker} Error occurs here")
                else:
                    # Create a general error indicator
                    marker_prefix = " " * gutter_width
                    result.append(f"{marker_prefix}{'~' * 10} ERROR")
            else:
                # Add context line without highlighting
                result.append(f"{line_prefix}{current_line}")

        return "\n".join(result)

    @staticmethod
    def extract_error_context(
        content: str,
        error_line: int,
        error_col: Optional[int] = None,
        num_context_lines: int = 2,
    ) -> Tuple[str, int]:
        """Extract relevant context around an error location from content.

        Args:
            content: The full content string
            error_line: The line number where the error occurred (0-based)
            error_col: The column where the error occurred (optional)
            num_context_lines: Number of lines of context to include before and after

        Returns:
            A tuple of (extracted context, new line number within context)
        """
        lines = content.splitlines()

        # Calculate the range of lines to include
        start_line = max(0, error_line - num_context_lines)
        end_line = min(len(lines), error_line + num_context_lines + 1)

        # Extract the relevant lines
        context = lines[start_line:end_line]

        # Calculate the new error line number within the context
        new_error_line = error_line - start_line

        return "\n".join(context), new_error_line


class FragmentNotFoundError(PrompyError):
    """Exception raised when a fragment reference cannot be found."""

    def __init__(
        self,
        fragment_slug: str,
        search_paths: List[str],
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        column_number: Optional[int] = None,
        template_content: Optional[str] = None,
    ):
        """Initialize a FragmentNotFoundError.

        Args:
            fragment_slug: The slug of the fragment that wasn't found
            search_paths: Paths that were searched for the fragment
            file_path: Path to the file where the error occurred
            line_number: Line number where the error occurred
            column_number: Column number where the error occurred
            template_content: Original template content for context
        """
        self.fragment_slug = fragment_slug
        self.search_paths = search_paths
        self.file_path = file_path  # Initialize before _format_details
        self.line_number = line_number  # Store line number for formatting

        message = f"Can't find prompt fragment '@{fragment_slug}'"
        details = self._format_details()
        suggestion = self._generate_suggestion()

        # Extract snippet if available
        snippet = None
        snippet_line = None
        if template_content and line_number is not None:
            snippet, snippet_line = self.extract_error_context(
                template_content,
                line_number - 1,
                column_number,  # Convert to 0-based
            )

        super().__init__(
            message=message,
            details=details,
            suggestion=suggestion,
            snippet=snippet,
            snippet_line=line_number,
            snippet_column=column_number,
            file_path=file_path,
        )

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

    def _generate_suggestion(self) -> str:
        """Generate a helpful suggestion based on the error."""
        suggestions = [
            f"Check if the fragment '@{self.fragment_slug}' exists in one of the prompt directories.",
            "Try running 'prompy list' to see available fragments.",
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
        """Initialize a CyclicReferenceError.

        Args:
            cycle_path: The path of fragment references forming the cycle
            start_file: Path to the file where the cycle starts
            line_number: Line number where the cycle was detected
            template_content: Original template content for context
        """
        self.cycle_path = cycle_path
        self.file_path = start_file  # Set file_path for _format_details
        self.line_number = line_number  # Store line number for formatting

        cycle_str = " -> ".join(
            f"@{slug}" for slug in cycle_path
        )  # Added single quotes
        message = f"Cyclic reference detected {cycle_str}"
        details = self._format_details()
        suggestion = self._generate_suggestion()

        # Extract snippet if available
        snippet = None
        snippet_line = None
        if template_content and line_number is not None:
            snippet, snippet_line = self.extract_error_context(
                template_content,
                line_number - 1,  # Convert to 0-based
            )

        super().__init__(
            message=message,
            details=details,
            suggestion=suggestion,
            snippet=snippet,
            snippet_line=line_number,
            file_path=start_file,
        )

    def _format_details(self) -> str:
        """Format detailed error information."""
        details = []

        if self.file_path:
            details.append(f"  in file: {self.file_path}")

        if self.line_number is not None:
            details.append(f"  starting at line: {self.line_number}")

        # Add the path details
        for path in self.cycle_path:
            details.append(f"  - {path}")

        return "\n".join(details)

    def _generate_suggestion(self) -> str:
        """Generate a helpful suggestion based on the error."""
        suggestions = [
            "Break the cycle by removing one of the references in the chain or restructuring your templates.",
            "Consider moving shared content to a separate fragment that others can include.",
        ]
        return " ".join(suggestions)


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
        """Initialize a MissingArgumentError.

        Args:
            fragment_slug: The fragment with missing arguments
            argument_name: The name of the missing argument
            file_path: Path to the file where the error occurred
            line_number: Line number where the error occurred
            template_content: Original template content for context
            required_args: List of all required arguments
        """
        self.fragment_slug = fragment_slug
        self.argument_name = argument_name
        self.file_path = file_path  # Initialize before _format_details
        self.line_number = line_number  # Store line number for formatting
        self.required_args = required_args or []

        message = f"Missing required argument '{argument_name}' for fragment '@{fragment_slug}'"
        details = self._format_details()
        suggestion = self._generate_suggestion()

        # Extract snippet if available
        snippet = None
        snippet_line = None
        if template_content and line_number is not None:
            snippet, snippet_line = self.extract_error_context(
                template_content,
                line_number - 1,  # Convert to 0-based
            )

        super().__init__(
            message=message,
            details=details,
            suggestion=suggestion,
            snippet=snippet,
            snippet_line=line_number,
            file_path=file_path,
        )

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
        suggestions = []

        # Basic usage example
        correct_usage = f"@{self.fragment_slug}({self.argument_name}=value)"
        suggestions.append(f"Add the missing argument: {correct_usage}")

        # If we have required args, show complete example
        if self.required_args:
            example_args = ", ".join(f"{arg}=value" for arg in self.required_args)
            complete_usage = f"@{self.fragment_slug}({example_args})"
            suggestions.append(f"Complete example: {complete_usage}")

        return " ".join(suggestions)


class PrompyTemplateSyntaxError(PrompyError):
    """Exception raised when a template has invalid syntax."""

    def __init__(
        self,
        error_msg: str,
        file_path: Optional[str] = None,
        line_number: Optional[int] = None,
        column_number: Optional[int] = None,
        template_content: Optional[str] = None,
    ):
        """Initialize a TemplateSyntaxError.

        Args:
            error_msg: The specific syntax error message
            file_path: Path to the file where the error occurred
            line_number: Line number where the error occurred
            column_number: Column number where the error occurred
            template_content: Original template content for context
        """
        self.file_path = file_path  # Initialize before _format_details
        self.line_number = line_number  # Store line number for formatting
        message = f"Template syntax error: {error_msg}"
        details = self._format_details()
        suggestion = self._generate_suggestion(error_msg)

        # Extract snippet if available
        snippet = None
        snippet_line = None
        if template_content and line_number is not None:
            snippet, snippet_line = self.extract_error_context(
                template_content,
                line_number - 1,
                column_number,  # Convert to 0-based
            )

        super().__init__(
            message=message,
            details=details,
            suggestion=suggestion,
            snippet=snippet,
            snippet_line=line_number,
            snippet_column=column_number,
            file_path=file_path,
        )

    def _format_details(self) -> str:
        """Format detailed error information."""
        details = []

        if self.file_path:
            details.append(f"  in file: {self.file_path}")

        if self.line_number is not None:
            details.append(f"  at line: {self.line_number}")

        return "\n".join(details)

    def _generate_suggestion(self, error_msg: str) -> str:
        """Generate a helpful suggestion based on the syntax error message."""
        # Common syntax error patterns and their suggestions
        error_patterns = {
            "unexpected '}'": "Make sure all curly braces are properly matched. Check for missing opening '{' characters.",
            "unexpected end of template": "The template may be missing a closing tag or brace. Check for unclosed blocks.",
            "expected name or number": "A variable name or numeric value was expected here. Check the syntax.",
            "missing closing quote": "Add the missing closing quote to the string.",
            "missing bracket": "Add the missing bracket to complete the expression.",
            "missing parenthesis": "Add the missing parenthesis to complete the function call or expression.",
        }

        # Find matching patterns and return appropriate suggestions
        for pattern, suggestion in error_patterns.items():
            if pattern in error_msg.lower():
                return suggestion

        # Default suggestion if no specific pattern matches
        return "Check the syntax at the indicated location and ensure it follows template language rules."


def handle_error(
    exception: Exception,
    ctx: Optional[click.Context] = None,
    exit_code: int = 1,
    show_traceback: bool = False,
) -> None:
    """Handle an exception in a consistent way.

    This function provides rich error reporting with syntax highlighting,
    contextual snippets, and helpful suggestions for fixing common issues.

    Args:
        exception: The exception to handle
        ctx: Click context (optional, used to check debug/diagnose flags)
        exit_code: The exit code to use when exiting (default: 1)
        show_traceback: Whether to show the traceback even if not in debug mode
    """

    # Check debug/diagnose modes
    debug_mode = ctx and ctx.obj and ctx.obj.get("debug", False)
    diagnose_mode = ctx and ctx.obj and ctx.obj.get("diagnose", False)

    if debug_mode or show_traceback:
        logger.exception(exception)

    # Print error with enhanced formatting
    if isinstance(exception, PrompyError):
        # File location (if available)
        if getattr(exception, "file_path", None):
            click.echo(
                click.style("File: ", fg="bright_black")
                + click.style(exception.file_path, fg="bright_black", underline=True),
                err=True,
            )

        # Error header
        click.echo(
            click.style("Error: ", fg="red", bold=True)
            + click.style(exception.message, fg="red"),
            err=True,
        )

        # Details section
        if exception.details:
            click.echo(exception.details, err=True)

        # Code snippet with location markers
        if exception.snippet:
            click.echo("", err=True)  # Empty line for readability
            click.echo(
                click.style("Code context:", fg="bright_black", bold=True), err=True
            )

            lines = exception.snippet.splitlines()
            start_line = max(
                0, (exception.snippet_line or 0) - (exception.snippet_context or 2)
            )
            end_line = min(
                len(lines),
                (exception.snippet_line or 0) + (exception.snippet_context or 2) + 1,
            )

            # Calculate gutter width for line numbers
            max_lineno_width = len(str(end_line))
            gutter_width = max_lineno_width + 3  # space for " | "

            for i in range(start_line, end_line):
                line = lines[i]
                line_number = i + 1  # Convert to 1-based line numbers
                line_prefix = f"{line_number:>{max_lineno_width}} | "

                # Highlight the error line
                if line_number == (exception.snippet_line or 0):
                    # Show the line with error highlighting
                    click.echo(
                        click.style(line_prefix, fg="bright_black")
                        + click.style(line, fg="yellow", bold=True),
                        err=True,
                    )

                    # Show precise column marker if available
                    if exception.snippet_column is not None:
                        marker = " " * (exception.snippet_column - 1) + "^"
                        marker_prefix = " " * gutter_width
                        click.echo(
                            click.style(marker_prefix + marker, fg="red", bold=True)
                            + click.style(" Error occurs here", fg="red"),
                            err=True,
                        )
                    else:
                        # Show general error marker
                        marker_prefix = " " * gutter_width
                        click.echo(
                            click.style(
                                marker_prefix + "~" * 10 + " ERROR", fg="red", bold=True
                            ),
                            err=True,
                        )
                else:
                    # Show context line without highlighting
                    click.echo(
                        click.style(line_prefix, fg="bright_black") + line, err=True
                    )

        # Suggestion section
        if exception.suggestion:
            click.echo("", err=True)  # Empty line for readability
            click.echo(
                click.style("💡 ", fg="green")
                + click.style("Suggestion:", fg="green", bold=True),
                err=True,
            )
            # Word wrap the suggestion for better readability
            suggestion_lines = textwrap.wrap(
                exception.suggestion,
                width=80,
                initial_indent="  ",
                subsequent_indent="  ",
            )
            for line in suggestion_lines:
                click.echo(click.style(line, fg="green"), err=True)

        # Diagnostic information
        if diagnose_mode:
            click.echo("", err=True)
            click.echo(
                click.style("Diagnostic Information:", fg="blue", bold=True), err=True
            )
            click.echo(
                click.style("  Exception type: ", fg="blue")
                + click.style(exception.__class__.__name__, fg="bright_blue"),
                err=True,
            )
            # Add any additional diagnostic information here

    else:
        # For non-PrompyError exceptions, use simple formatting
        click.echo(
            click.style("Error: ", fg="red", bold=True)
            + click.style(str(exception), fg="red"),
            err=True,
        )

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
