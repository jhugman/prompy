"""
Output functionality for Prompy.

This module handles different output methods for rendered prompts,
including stdout, clipboard, and file output.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

import pyperclip

logger = logging.getLogger(__name__)


def output_to_stdout(content: str) -> bool:
    """
    Output content to stdout.

    Args:
        content: The content to output

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        sys.stdout.write(content)
        # Add a newline if not present
        if content and not content.endswith("\n"):
            sys.stdout.write("\n")
        sys.stdout.flush()
        return True
    except Exception as e:
        logger.error(f"Error writing to stdout: {e}")
        return False


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
        return True
    except Exception as e:
        logger.error(f"Error copying to clipboard: {e}")
        return False


def output_to_file(content: str, file_path: str) -> bool:
    """
    Write content to a file.

    Args:
        content: The content to write
        file_path: Path to the file

    Returns:
        bool: True if successful, False otherwise
    """
    try:
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception as e:
        logger.error(f"Error writing to file {file_path}: {e}")
        return False


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
