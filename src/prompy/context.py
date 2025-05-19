"""
Functions for creating and managing PromptContext instances.
"""

import os
from pathlib import Path
from typing import List, Optional

from prompy.config import detect_language, find_project_dir, get_config_dir
from prompy.prompt_file import PromptContext


def create_prompt_context(
    config_dir: Optional[Path] = None,
    project_dir: Optional[Path] = None,
    project: Optional[str] = None,
    language: Optional[str] = None,
) -> PromptContext:
    """
    Create a PromptContext with appropriate directories for language, project and fragments.

    Args:
        config_dir (Optional[Path]): Optional config directory, will be detected if not provided
        project_dir (Optional[Path]): Optional project directory, will be detected if not provided
        project (Optional[str]): Optional project name, will be detected if not provided
        language (Optional[str]): Optional language name, will be detected if not provided

    Returns:
        PromptContext: A configured prompt context
    """
    # Find project root directory and get its name if not provided
    root = project_dir if project_dir is not None else find_project_dir()
    project_name = project if project is not None else (root.name if root else None)

    # Detect language if not specified
    detected_language = language if language is not None else detect_language(root)

    # Get config directory from environment if not provided
    config_dir = config_dir if config_dir is not None else get_config_dir()
    global_prompts = config_dir / "prompts"

    # Set up local prompts directory if project root exists
    language_dirs = []
    project_dirs = []
    fragment_dirs = []
    if root is not None and root.exists():
        local_prompts = root / ".prompy"
        if local_prompts.exists():
            language_dirs.append(local_prompts / "environment")
            project_dirs.append(local_prompts / "project")
            fragment_dirs.append(local_prompts / "fragments")

    if detected_language:
        language_dirs.append(global_prompts / "languages" / detected_language)

    if project_name:
        project_dirs.append(global_prompts / "projects" / project_name)

    fragment_dirs.append(global_prompts / "fragments")

    # Create and return the PromptContext
    return PromptContext(
        project_name=project_name,
        language=detected_language,
        language_dirs=language_dirs,
        project_dirs=project_dirs,
        fragment_dirs=fragment_dirs,
    )
