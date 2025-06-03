"""
Functions for creating and managing PromptContext instances.
"""

from pathlib import Path
from typing import Optional

import click

from prompy.prompt_context import PromptContext


def from_click_context(ctx: click.Context) -> PromptContext:
    project_name = ctx.obj.get("project")
    detected_language = ctx.obj.get("language")
    config_dir = ctx.obj.get("config_dir")
    project_dir = ctx.obj.get("project_dir")

    return create_prompt_context(
        config_dir=config_dir,
        project_dir=project_dir,
        project_name=project_name,
        language=detected_language,
    )


def create_prompt_context(
    config_dir: Path,
    project_dir: Optional[Path] = None,
    project_name: Optional[str] = None,
    language: Optional[str] = None,
) -> PromptContext:
    """
    Create a PromptContext with appropriate directories for language, project and
    fragments.

    Args:
        config_dir (Optional[Path]): Optional config directory, will be detected if
            not provided
        project_dir (Optional[Path]): Optional project directory, will be detected if
            not provided
        project (Optional[str]): Optional project name, will be detected if not
            provided
        language (Optional[str]): Optional language name, will be detected if not
            provided

    Returns:
        PromptContext: A configured prompt context
    """

    # Get config directory from environment if not provided
    global_prompts = config_dir / "prompts"

    # Set up local prompts directory if project root exists
    language_dirs = []
    project_dirs = []
    fragment_dirs = []
    if project_dir is not None and project_dir.exists():
        local_prompts = project_dir / ".prompy"
        if local_prompts.exists():
            language_dirs.append(local_prompts / "environment")
            project_dirs.append(local_prompts / "project")
            fragment_dirs.append(local_prompts / "fragments")

    if language:
        language_dirs.append(global_prompts / "languages" / language)

    if project_name:
        project_dirs.append(global_prompts / "projects" / project_name)

    fragment_dirs.append(global_prompts / "fragments")

    # Create and return the PromptContext
    return PromptContext(
        project_name=project_name,
        language=language,
        language_dirs=language_dirs,
        project_dirs=project_dirs,
        fragment_dirs=fragment_dirs,
    )
