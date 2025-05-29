"""
Output functionality for Prompy.

This module handles different output methods for rendered prompts,
including stdout, clipboard, and file output.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import click
import pyperclip
from rich.console import Console
from rich.markdown import Markdown
from rich.panel import Panel
from rich.text import Text

logger = logging.getLogger(__name__)
console = Console()


def is_output_redirected() -> bool:
    """
    Detect if stdout is being redirected to a file or pipe.
    Also handles Click test runner redirects.
    """
    try:
        return not sys.stdout.isatty()
    except AttributeError:
        # Handle cases where stdout might not have isatty (like in tests)
        return True


def output_to_stdout(content: str) -> bool:
    """
    Output content to stdout.

    Args:
        content: The content to output

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        # If output is redirected, just write plain text
        if is_output_redirected():
            sys.stdout.write(content)
            if content and not content.endswith("\n"):
                sys.stdout.write("\n")
        else:
            # Use rich formatting for terminal
            panel = create_rich_output(content, "stdout")
            console.print(panel)

        sys.stdout.flush()
        return True
    except Exception as e:
        logger.error(f"Error writing to stdout: {e}")
        return False


def is_test_environment() -> bool:
    """Check if we're running in a test environment."""
    return "pytest" in sys.modules


def output_to_clipboard(content: str) -> bool:
    """
    Copy content to the clipboard.

    Args:
        content: The content to copy to clipboard

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        pyperclip.copy(content)
        # Show success message
        msg = (
            "📋 Prompt copied to clipboard"
            if not is_output_redirected()
            else "Prompt copied to clipboard."
        )
        click.echo(msg)
        return True
    except Exception as e:
        logger.error(f"Error copying to clipboard: {e}")
        return False


def output_to_file(content: str, file_path: str) -> bool:
    """
    Write content to a file.

    Args:
        content: The content to write
        file_path: Path to the output file

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        Path(file_path).write_text(content)
        # Show success message
        msg = (
            f"💾 Prompt saved to {file_path}"
            if not is_output_redirected()
            else f"Prompt output to file: {file_path}"
        )
        click.echo(msg)
        return True
    except Exception as e:
        logger.error(f"Error writing to file {file_path}: {e}")
        return False


def create_rich_output(content: str, output_type: str = "stdout") -> Panel:
    """
    Create a rich panel containing the prompt content.

    Args:
        content: The content to display
        output_type: Type of output ("stdout", "clipboard", or "file")

    Returns:
        Panel: A rich panel containing the formatted content
    """
    # Create a Markdown object with subtle styling
    md = Markdown(
        content.rstrip(),
        code_theme="one-dark",  # More subtle code theme
    )

    # Create subtitle based on output type with consistent emoji
    subtitle = Text()
    if output_type == "clipboard":
        subtitle.append("📋 Copied to clipboard", style="bright_blue")
    elif output_type == "file":
        subtitle.append("💾 Saved to file", style="bright_blue")
    else:
        subtitle = None

    # Create the panel with formatted markdown
    return Panel(
        md,
        title=Text("📝 PROMPT", style="bold bright_blue"),  # More contextual emoji
        subtitle=subtitle,
        border_style="bright_blue",  # Brighter border to frame content
        padding=(1, 2),
        highlight=True,
    )


def output_content(
    content: str, output_file: Optional[str] = None, clipboard: bool = False
) -> bool:
    """
    Output content using the specified method.

    Args:
        content: The content to output
        output_file: Optional file path to output to
        clipboard: Whether to copy to clipboard

    Returns:
        bool: True if successful, False otherwise
    """
    # Determine output method
    if clipboard:
        success = output_to_clipboard(content)
        if not success:
            logger.warning("Failed to copy to clipboard. Falling back to stdout.")
            success = output_to_stdout(content)
        return success
    elif output_file:
        return output_to_file(content, output_file)
    else:
        return output_to_stdout(content)
