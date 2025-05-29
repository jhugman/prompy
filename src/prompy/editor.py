"""
Editor functionality for Prompy.
This module handles the detection and launching of the user's editor,
as well as the creation of help comments.
"""

import os
import subprocess
import sys
import tempfile
from pathlib import Path
from typing import Callable, List, Optional, Tuple

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from prompy.prompt_context import PromptContext
from prompy.prompt_files import PromptFiles

# Initialize rich console for terminal output
console = Console()

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
    project_name: Optional[str] = None,
    is_new_prompt: bool = False,
) -> bool:
    """
    Open a file in the editor with help comments added and colorized console help.

    Args:
        file_path: Path to the file to edit.
        prompt_files: Available prompt files.
        project_name: Optional project name for help display.
        is_new_prompt: Whether this is a new prompt.

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
        # Display colorized help text before opening editor
        display_editor_help(project_name, prompt_files, is_new_prompt)

        # Launch the editor
        return_code = launch_editor(temp_path)

        # Clear the help text after editor closes
        clear_editor_help()

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


def is_terminal_output() -> bool:
    """
    Check if output should be displayed in the terminal.
    Returns False if output is redirected or in test environment.
    """
    try:
        # Check for test environment - pytest should exist and not be None
        if "pytest" in sys.modules and sys.modules["pytest"] is not None:
            return False
        # Check if stdout is a terminal
        return sys.stdout.isatty()
    except AttributeError:
        return False


def display_editor_help(
    project_name: Optional[str], prompt_files: PromptFiles, is_new_prompt: bool = False
) -> None:
    """
    Display colorized help text in the console when opening the editor.

    Args:
        project_name: The current project name
        prompt_files: Available prompt files for help text
        is_new_prompt: Whether this is a new prompt
    """
    if not is_terminal_output():
        return

    # Create help content
    help_lines = []

    # Get concise help text
    help_text = prompt_files.help_text(
        slug_prefix="@",
        include_syntax=True,
        include_header=False,  # We'll create our own header
        inline_description=True,
        use_dashes=False,
    )

    # Create title
    action = "Creating new prompt" if is_new_prompt else "Editing prompt"
    title_text = f"✏️  {action}"
    if project_name:
        title_text += f" for {project_name}"

    # Create subtitle with helpful tips
    subtitle = Text()
    subtitle.append(
        "💡 Available fragments will be shown in the editor\n", style="bright_blue"
    )
    subtitle.append("🚀 Save and close the editor when done", style="bright_green")

    # Create the help panel
    panel_content = Text()
    panel_content.append(subtitle)
    panel_content.append("\n")

    # Add concise fragment info if available
    if help_text.strip():
        lines = help_text.strip().split("\n")
        # Show only first few fragments to keep it concise
        for i, line in enumerate(lines[:8]):  # Show max 8 lines
            if line.strip():
                panel_content.append(line + "\n", style="dim")
        if len(lines) > 8:
            panel_content.append("... and more in the editor\n", style="dim italic")

    # Display the panel
    help_panel = Panel(
        panel_content,
        title=title_text,
        border_style="bright_blue",
        padding=(1, 2),
    )

    console.print(help_panel)


def clear_editor_help() -> None:
    """
    Clear the editor help text from the console after editor closes.
    """
    if not is_terminal_output():
        return

    # Move cursor up to overwrite the help panel
    # We need to clear enough lines to cover the help panel
    console.print("\n" * 2, end="")  # Add some spacing

    # Display completion message
    completion_panel = Panel(
        Text("✅ Editor session completed", style="bright_green bold"),
        border_style="bright_green",
        padding=(0, 2),
    )
    console.print(completion_panel)


def display_editor_success(message: str) -> None:
    """
    Display a success message with colorized output.

    Args:
        message: The success message to display
    """
    if not is_terminal_output():
        # Fall back to plain click.echo for non-terminal output
        click.echo(message)
        return

    # Create colorized success message
    success_text = Text()
    success_text.append("✅ ", style="bright_green")
    success_text.append(message, style="bright_white")

    console.print(success_text)
