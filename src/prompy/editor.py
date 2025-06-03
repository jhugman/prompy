"""
Editor functionality for Prompy.
This module handles the detection and launching of the user's editor,
with colorized console help display.
"""

import os
import subprocess
import sys
from pathlib import Path
from typing import Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.text import Text

from prompy.prompt_files import PromptFiles

# Initialize rich console for terminal output
console = Console()


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
    Open a file in the editor with help displayed in console.

    Args:
        file_path: Path to the file to edit.
        prompt_files: Available prompt files.
        project_name: Optional project name for help display.
        is_new_prompt: Whether this is a new prompt.

    Returns:
        bool: True if the edit was successful, False otherwise.
    """
    # Ensure the file exists for new prompts
    path = Path(file_path)
    if not path.exists() and is_new_prompt:
        # For new files, provide a basic frontmatter structure
        if file_path.endswith(".md"):
            content = "---\ndescription: \ncategories: []\n---\n\n"
        else:
            content = ""

        # Create the file with initial content
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(content)

    # Display help text in console before opening editor
    display_editor_help(project_name, prompt_files, is_new_prompt)

    # Launch the editor with the actual file directly
    return_code = launch_editor(file_path)

    # Clear the help text after editor closes
    clear_editor_help()

    return return_code == 0


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
    Display available prompts and syntax help in the console while editor is active.

    Args:
        project_name: The current project name
        prompt_files: Available prompt files for help text
        is_new_prompt: Whether this is a new prompt
    """
    if not is_terminal_output():
        return

    # Create title
    action = "Creating new prompt" if is_new_prompt else "Editing prompt"
    title_text = f"✏️  {action}"
    if project_name:
        title_text += f" for {project_name}"

    # Display title
    console.print()
    console.print(
        Panel(title_text, style="bright_blue bold", padding=(0, 1))
    )  # Display the help content by rendering directly to the console
    # This avoids formatting conflicts from pre-formatted strings with ANSI codes
    prompt_files.render_help_to_console(
        console,
        slug_prefix="@",
        include_syntax=True,
        include_header=False,  # We have our own header above
        inline_description=True,
    )


def clear_editor_help() -> None:
    """
    Clear the editor help text from the console after editor closes.
    """
    if not is_terminal_output():
        return

    # Clear the screen and move cursor to top
    console.clear()

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
