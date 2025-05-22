"""
Functions for finding and updating references to fragments in prompt files.

This module implements functions to find and update @slug references in templates.
Supports both Jinja2-style ({{ @slug }}) and legacy-style (@slug) references.
"""

import logging
import re
from pathlib import Path
from typing import Dict, List, Optional, Pattern, Set, Union

from .prompt_context import PromptContext
from .prompt_file import PromptFile

logger = logging.getLogger(__name__)

# Regular expression to find fragment references in Jinja2 template expressions
# This matches: {{ @slug }} or {{ @slug(args) }}
JINJA_FRAGMENT_REF_PATTERN: Pattern = re.compile(
    r"{{(.*?)@([a-zA-Z0-9_\-/$]+)(\(.*?\))?.*?}}"
)


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

        # Find all references (both Jinja2 and legacy style)
        matches = []

        # Check for Jinja2-style references
        for match in re.finditer(JINJA_FRAGMENT_REF_PATTERN, content):
            # Extract the slug from the match
            slug = match.group(2)
            if slug == old_slug:
                # Store the match information
                matches.append(
                    {
                        "start": match.start(),
                        "end": match.end(),
                        "full_match": match.group(0),
                        "args": match.group(3) or "",
                        "is_jinja": True,
                    }
                )

        if not matches:
            return False

        # Update each reference
        # We need to work backwards to prevent position shifts
        updates = []
        for match in sorted(matches, key=lambda m: m["start"], reverse=True):
            # Create updated reference text
            old_ref_text = match["full_match"]
            if match["is_jinja"]:
                # Jinja style: {{ @old-slug(...) }} -> {{ @new-slug(...) }}
                new_ref_text = old_ref_text.replace(f"@{old_slug}", f"@{new_slug}")
            else:
                # Legacy style: @old-slug(...) -> @new-slug(...)
                new_ref_text = f"@{new_slug}{match['args']}"

            updates.append((match["start"], match["end"], new_ref_text))

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
