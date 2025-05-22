# filepath: /Users/jhugman/workspaces/personal/prompy/src/prompy/editor.py
"""
Editor functionality for Prompy.
This module handles the detection and launching of the user's editor,
as well as the creation of help comments.
"""

import os
import subprocess
import tempfile
from pathlib import Path
from typing import Callable, List, Optional, Tuple

from prompy.prompt_context import PromptContext
from prompy.prompt_files import PromptFiles

# Constant for marking help text that should be removed after editing
HELP_TEXT_MARKER = "This comment section will be removed from the final prompt."

# Start and end markers for help text sections
HELP_START_MARKER = "<!--\n"
HELP_END_MARKER = f"{HELP_TEXT_MARKER}\n-->"


def find_editor() -> str:
    """
    Find the user's preferred editor.

    Returns:
        str: Path to the editor executable.
    """
    # Check for EDITOR environment variable
    editor = os.environ.get("EDITOR")
    if editor:
        return editor

    # Check for VISUAL environment variable (often used for GUI editors)
    editor = os.environ.get("VISUAL")
    if editor:
        return editor

    # Check for common editors
    common_editors = ["nano", "vim", "emacs", "vi"]
    for editor in common_editors:
        try:
            # Check if the editor is in the PATH
            result = subprocess.run(
                ["which", editor], capture_output=True, text=True, check=False
            )
            if result.returncode == 0:
                return editor
        except FileNotFoundError:
            continue

    # Fall back to nano or vi, which are likely to be installed
    return "nano"


def launch_editor(file_path: str) -> int:
    """
    Launch the user's preferred editor with the specified file.

    Args:
        file_path: Path to the file to edit.

    Returns:
        int: Return code from the editor process.
    """
    editor_cmd = find_editor()

    try:
        # Split the editor command into parts if it includes arguments
        editor_parts = editor_cmd.split()
        editor_command = editor_parts[0]
        editor_args = editor_parts[1:] if len(editor_parts) > 1 else []

        # Launch the editor and wait for it to complete
        result = subprocess.run(
            [editor_command] + editor_args + [file_path], check=False
        )
        return result.returncode
    except Exception as e:
        raise RuntimeError(f"Failed to launch editor: {e}")


def edit_file_with_comments(
    file_path: str,
    prompt_files: PromptFiles,
) -> bool:
    """
    Open a file in the editor with help comments added.

    Args:
        file_path: Path to the file to edit.
        prompt_context: Context for resolving prompt slugs.
        prompt_files: Available prompt files.

    Returns:
        bool: True if the edit was successful, False otherwise.
    """
    # Load current content or create empty content with default structure
    path = Path(file_path)
    try:
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()
    except FileNotFoundError:
        # For new files, provide a basic frontmatter structure
        if file_path.endswith(".md"):
            content = "---\ndescription: \ncategories: []\n---\n\n"
        else:
            content = ""

    content_with_comments = add_help_comments(content, prompt_files)

    # Write to a temporary file
    with tempfile.NamedTemporaryFile(
        suffix=".md", mode="w", encoding="utf-8", delete=False
    ) as temp_file:
        temp_path = temp_file.name
        temp_file.write(content_with_comments)

    try:
        # Launch the editor
        return_code = launch_editor(temp_path)
        if return_code != 0:
            return False

        # Read the edited content and remove help comments
        with open(temp_path, "r", encoding="utf-8") as f:
            edited_content = f.read()

        final_content = remove_help_comments(edited_content)

        # Write back to the original file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(final_content)

        return True
    finally:
        # Clean up the temporary file
        try:
            os.unlink(temp_path)
        except FileNotFoundError:
            pass


def add_help_comments(content: str, prompt_files: PromptFiles) -> str:
    """
    Add helpful comments to the content for the editor.

    Args:
        content: The original content.
        prompt_context: Context for resolving prompt slugs.
        prompt_files: Available prompt files.

    Returns:
        str: Content with help comments added.
    """
    # Get the help text from PromptFiles with appropriate parameters
    help_text = prompt_files.help_text(
        slug_prefix="@",
        include_syntax=True,
        include_header=True,
        inline_description=True,  # Use inline description format for consistency with CLI
    )

    # Wrap in HTML comments with marker for more reliable removal
    help_section = [
        HELP_START_MARKER,
        help_text.rstrip(),
        HELP_END_MARKER,
    ]

    # Return the combined content
    if content.strip():
        return content.rstrip() + "\n\n" + "\n".join(help_section)
    else:
        return "\n".join(help_section)


def remove_help_comments(content: str) -> str:
    """
    Remove the help comments section from the content.

    Args:
        content: The content with help comments.

    Returns:
        str: Content with help comments removed.
    """
    import re

    # First, try to find the full comment section using our start and end markers
    start_idx = content.find(HELP_START_MARKER)
    end_idx = -1
    if start_idx >= 0:
        # Look for the closing tag after the start marker
        content_after_start = content[start_idx:]
        end_tag_idx = content_after_start.find("-->")
        if end_tag_idx >= 0:
            end_idx = start_idx + end_tag_idx + 3  # 3 for "-->"

    # If we found valid comment markers, remove everything between them
    if start_idx >= 0 and end_idx > start_idx:
        return content[:start_idx].rstrip()

    # Special case: if the content contains part of the help text marker
    # but doesn't have the complete section, we should still remove all text after
    # the partial marker
    if "<!--\nPROMPY AVAILABLE FRAGMENTS:" in content:
        fragment_idx = content.find("<!--\nPROMPY AVAILABLE FRAGMENTS:")
        return content[:fragment_idx].rstrip()

    # No markers found, return content as is
    return content
