"""
Functions for finding and updating references to fragments in prompt files.
"""

import logging
from pathlib import Path
from typing import Dict, List, Optional

from prompy.fragment_parser import FragmentReference, find_fragment_references
from prompy.prompt_file import PromptContext, PromptFile

logger = logging.getLogger(__name__)


def update_references_in_file(file_path: Path, old_slug: str, new_slug: str) -> bool:
    """
    Update all references to old_slug in the specified file.

    Args:
        file_path: Path to the file to update
        old_slug: Old fragment slug to replace
        new_slug: New fragment slug to use

    Returns:
        bool: True if any changes were made
    """
    try:
        # Load the file
        prompt_file = PromptFile.load(file_path)
        content = prompt_file.markdown_template

        # Find all fragment references
        references = find_fragment_references(content)

        # Check if any references match the old slug
        matches = [
            ref
            for ref in references
            if isinstance(ref, FragmentReference) and ref.slug == old_slug
        ]

        if not matches:
            return False

        # Update each reference
        # We need to work backwards to prevent position shifts
        updates = []
        for ref in sorted(matches, key=lambda r: r.start_pos, reverse=True):
            # Create updated reference text
            old_ref_text = content[ref.start_pos : ref.end_pos]
            new_ref_text = f"@{new_slug}"

            # Add args if present
            if ref.args or ref.kwargs:
                args_parts = []
                # Add positional args
                args_parts.extend([str(arg) for arg in ref.args])
                # Add keyword args
                args_parts.extend(
                    [f"{key}={value}" for key, value in ref.kwargs.items()]
                )
                new_ref_text += f"({', '.join(args_parts)})"

            updates.append((ref.start_pos, ref.end_pos, new_ref_text))

        # Apply updates from end to beginning to maintain position integrity
        modified_content = content
        for start, end, replacement in updates:
            modified_content = (
                modified_content[:start] + replacement + modified_content[end:]
            )

        # Save changes if modifications were made
        if modified_content != content:
            prompt_file.markdown_template = modified_content
            prompt_file.save(file_path)
            return True

    except Exception as e:
        logger.error(f"Error updating references in {file_path}: {e}")

    return False


def update_references(
    prompt_context: PromptContext, old_slug: str, new_slug: str
) -> Dict[str, bool]:
    """
    Update all references to old_slug in all prompt files.

    Args:
        prompt_context: The PromptContext to use for finding files
        old_slug: Old fragment slug to replace
        new_slug: New fragment slug to use

    Returns:
        Dict[str, bool]: Map of file paths to whether they were updated
    """
    # Load all available prompt files
    prompt_files = prompt_context.load_all()

    # Track files that were updated
    updated_files = {}

    # Check for references in all prompt files
    for category in ["_fragment_prompts", "_project_prompts", "_language_prompts"]:
        if hasattr(prompt_files, category):
            prompts = getattr(prompt_files, category)
            for slug, prompt_file in prompts.items():
                # Find the file path for this prompt
                file_path = prompt_context.parse_prompt_slug(slug)
                if file_path and file_path.exists():
                    # Update references in this file
                    updated = update_references_in_file(file_path, old_slug, new_slug)
                    updated_files[str(file_path)] = updated

    return updated_files
