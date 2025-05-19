"""
Cache management for Prompy.

This module handles the management of one-off prompt caches.
"""

import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Optional, Tuple

logger = logging.getLogger(__name__)


def ensure_cache_dir(cache_dir: Path, project_name: str) -> Path:
    """
    Ensure that the cache directory for the specified project exists.

    Args:
        cache_dir: Base cache directory
        project_name: Name of the project

    Returns:
        Path: Path to the project's cache directory
    """
    project_cache_dir = cache_dir / project_name
    project_cache_dir.mkdir(parents=True, exist_ok=True)
    return project_cache_dir


def get_cache_file_path(cache_dir: Path, project_name: str) -> Path:
    """
    Get the path to the current cache file for the project.

    Args:
        cache_dir: Base cache directory
        project_name: Name of the project

    Returns:
        Path: Path to the current cache file
    """
    return ensure_cache_dir(cache_dir, project_name) / "CURRENT_FILE.md"


def load_from_cache(cache_dir: Path, project_name: str) -> Tuple[bool, str]:
    """
    Load content from the cache file if it exists.

    Args:
        cache_dir: Base cache directory
        project_name: Name of the project

    Returns:
        Tuple[bool, str]: (success, content)
    """
    if not project_name:
        return False, ""

    cache_file = get_cache_file_path(cache_dir, project_name)

    if cache_file.exists():
        try:
            with open(cache_file, "r", encoding="utf-8") as f:
                content = f.read()
            return True, content
        except Exception as e:
            logger.error(f"Error loading from cache: {e}")
            return False, ""

    return False, ""


def save_to_cache(cache_dir: Path, project_name: str, content: str) -> bool:
    """
    Save content to the cache file.

    Args:
        cache_dir: Base cache directory
        project_name: Name of the project
        content: Content to save

    Returns:
        bool: True if successful, False otherwise
    """
    if not project_name:
        return False

    cache_file = get_cache_file_path(cache_dir, project_name)

    try:
        with open(cache_file, "w", encoding="utf-8") as f:
            f.write(content)
        return True
    except Exception as e:
        logger.error(f"Error saving to cache: {e}")
        return False


def clear_cache(cache_dir: Path, project_name: str) -> bool:
    """
    Clear the cache file for the project.

    Args:
        cache_dir: Base cache directory
        project_name: Name of the project

    Returns:
        bool: True if successful, False otherwise
    """
    if not project_name:
        return False

    cache_file = get_cache_file_path(cache_dir, project_name)

    if cache_file.exists():
        try:
            os.remove(cache_file)
            return True
        except Exception as e:
            logger.error(f"Error clearing cache: {e}")
            return False

    return True  # No cache to clear is still a success


def append_to_cache(cache_dir: Path, project_name: str, content: str) -> bool:
    """
    Append content to the cache file.

    Args:
        cache_dir: Base cache directory
        project_name: Name of the project
        content: Content to append

    Returns:
        bool: True if successful, False otherwise
    """
    if not project_name or not content:
        return False

    # Load existing content first
    success, existing_content = load_from_cache(cache_dir, project_name)

    # Prepare the content to write
    if success and existing_content:
        new_content = existing_content.rstrip() + "\n\n" + content
    else:
        new_content = content

    # Save the combined content
    return save_to_cache(cache_dir, project_name, new_content)


def read_from_stdin() -> Optional[str]:
    """
    Read content from stdin if available.

    Returns:
        Optional[str]: Content from stdin or None if stdin is a terminal
    """
    if sys.stdin.isatty():
        return None

    return sys.stdin.read()
