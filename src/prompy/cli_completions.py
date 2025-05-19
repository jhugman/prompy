"""
Shell completion functions for Prompy CLI.
"""

from typing import List

import click


def complete_prompt_slug(ctx: click.Context, param: str, incomplete: str):
    """
    Complete the prompt_slug argument with available slugs.

    Args:
        ctx: The current click context
        param: The parameter being completed
        incomplete: The current input being completed

    Returns:
        List of matching slugs
    """
    try:
        from prompy.config import ensure_config_dirs, find_project_dir
        from prompy.context import create_prompt_context

        # Get configuration directory and other essential directories
        config_dir, prompts_dir, cache_dir, _ = ensure_config_dirs()

        # Extract project and language from context if available
        obj = ctx.ensure_object(dict)
        project_name = obj.get("project")
        detected_language = obj.get("language")
        project_dir = obj.get("project_dir")
        global_only = obj.get("global_only", False)

        if not project_name:
            # Try to detect project if not in context
            project_dir = find_project_dir()
            if project_dir:
                project_name = project_dir.name

        # Create prompt context for resolving slugs
        prompt_context = create_prompt_context(
            config_dir=config_dir,
            project_dir=project_dir,
            project=project_name,
            language=detected_language,
        )

        # Load all prompt files
        project_paths, language_paths, fragment_paths = prompt_context.collect_paths(
            global_only
        )

        # Merge all paths into a single dictionary
        all_paths = {}
        all_paths.update(project_paths)
        all_paths.update(language_paths)
        all_paths.update(fragment_paths)

        # Get available slugs directly from path keys
        available_slugs = list(all_paths.keys())

        # Filter slugs based on incomplete input
        return [slug for slug in available_slugs if slug.startswith(incomplete)]
    except Exception:
        # In case of any error, return empty list rather than crashing
        return []
