"""
Tests for the cache module.
"""

import os
import sys
from pathlib import Path
from unittest.mock import mock_open, patch

import pytest

from prompy.cache import (
    append_to_cache,
    clear_cache,
    ensure_cache_dir,
    get_cache_file_path,
    load_from_cache,
    read_from_stdin,
    save_to_cache,
)


def test_ensure_cache_dir(tmp_path):
    """Test that ensure_cache_dir creates the appropriate directories."""
    cache_dir = tmp_path / "cache"
    project_name = "test-project"

    result = ensure_cache_dir(cache_dir, project_name)

    assert result == cache_dir / project_name
    assert result.exists()
    assert result.is_dir()


def test_get_cache_file_path(tmp_path):
    """Test that get_cache_file_path returns the correct path."""
    cache_dir = tmp_path / "cache"
    project_name = "test-project"

    result = get_cache_file_path(cache_dir, project_name)

    assert result == cache_dir / project_name / "CURRENT_FILE.md"
    # The directory should be created but not the file
    assert (cache_dir / project_name).exists()
    assert not result.exists()


def test_load_from_cache_success(tmp_path):
    """Test loading from an existing cache file."""
    cache_dir = tmp_path / "cache"
    project_name = "test-project"

    # Create the cache file
    project_cache_dir = cache_dir / project_name
    project_cache_dir.mkdir(parents=True)
    cache_file = project_cache_dir / "CURRENT_FILE.md"

    test_content = "Test content"
    with open(cache_file, "w", encoding="utf-8") as f:
        f.write(test_content)

    success, content = load_from_cache(cache_dir, project_name)

    assert success is True
    assert content == test_content


def test_load_from_cache_no_project():
    """Test loading from cache with no project name."""
    cache_dir = Path("/fake/path")  # Won't be used
    project_name = ""

    success, content = load_from_cache(cache_dir, project_name)

    assert success is False
    assert content == ""


def test_load_from_cache_nonexistent_file(tmp_path):
    """Test loading from a nonexistent cache file."""
    cache_dir = tmp_path / "cache"
    project_name = "test-project"

    success, content = load_from_cache(cache_dir, project_name)

    assert success is False
    assert content == ""


def test_save_to_cache_success(tmp_path):
    """Test saving to cache successfully."""
    cache_dir = tmp_path / "cache"
    project_name = "test-project"
    test_content = "Test content"

    result = save_to_cache(cache_dir, project_name, test_content)

    assert result is True

    # Verify the content was written correctly
    cache_file = cache_dir / project_name / "CURRENT_FILE.md"
    assert cache_file.exists()
    with open(cache_file, "r", encoding="utf-8") as f:
        content = f.read()
    assert content == test_content


def test_save_to_cache_no_project():
    """Test saving to cache with no project name."""
    cache_dir = Path("/fake/path")  # Won't be used
    project_name = ""
    test_content = "Test content"

    result = save_to_cache(cache_dir, project_name, test_content)

    assert result is False


def test_clear_cache_success(tmp_path):
    """Test clearing the cache successfully."""
    cache_dir = tmp_path / "cache"
    project_name = "test-project"

    # Create the cache file
    project_cache_dir = cache_dir / project_name
    project_cache_dir.mkdir(parents=True)
    cache_file = project_cache_dir / "CURRENT_FILE.md"

    with open(cache_file, "w", encoding="utf-8") as f:
        f.write("Test content")

    result = clear_cache(cache_dir, project_name)

    assert result is True
    assert not cache_file.exists()


def test_clear_cache_no_project():
    """Test clearing cache with no project name."""
    cache_dir = Path("/fake/path")  # Won't be used
    project_name = ""

    result = clear_cache(cache_dir, project_name)

    assert result is False


def test_clear_cache_nonexistent_file(tmp_path):
    """Test clearing a nonexistent cache file."""
    cache_dir = tmp_path / "cache"
    project_name = "test-project"

    result = clear_cache(cache_dir, project_name)

    assert result is True  # No file to delete is still a success


def test_append_to_cache_success(tmp_path):
    """Test appending to cache successfully."""
    cache_dir = tmp_path / "cache"
    project_name = "test-project"

    # Create the cache file with initial content
    project_cache_dir = cache_dir / project_name
    project_cache_dir.mkdir(parents=True)
    cache_file = project_cache_dir / "CURRENT_FILE.md"

    initial_content = "Initial content"
    with open(cache_file, "w", encoding="utf-8") as f:
        f.write(initial_content)

    append_content = "Appended content"
    result = append_to_cache(cache_dir, project_name, append_content)

    assert result is True

    # Verify the content was appended correctly
    with open(cache_file, "r", encoding="utf-8") as f:
        content = f.read()
    assert content == f"{initial_content}\n\n{append_content}"


def test_append_to_cache_empty_file(tmp_path):
    """Test appending to an empty cache file."""
    cache_dir = tmp_path / "cache"
    project_name = "test-project"

    append_content = "Appended content"
    result = append_to_cache(cache_dir, project_name, append_content)

    assert result is True

    # Verify the content was written correctly
    cache_file = cache_dir / project_name / "CURRENT_FILE.md"
    with open(cache_file, "r", encoding="utf-8") as f:
        content = f.read()
    assert content == append_content


def test_append_to_cache_no_project():
    """Test appending to cache with no project name."""
    cache_dir = Path("/fake/path")  # Won't be used
    project_name = ""
    append_content = "Appended content"

    result = append_to_cache(cache_dir, project_name, append_content)

    assert result is False


def test_append_to_cache_no_content(tmp_path):
    """Test appending empty content to cache."""
    cache_dir = tmp_path / "cache"
    project_name = "test-project"
    append_content = ""

    result = append_to_cache(cache_dir, project_name, append_content)

    assert result is False


def test_read_from_stdin_tty():
    """Test reading from stdin when it's a TTY."""
    with patch.object(sys.stdin, "isatty", return_value=True):
        result = read_from_stdin()
        assert result is None


def test_read_from_stdin_not_tty():
    """Test reading from stdin when it's not a TTY."""
    with (
        patch.object(sys.stdin, "isatty", return_value=False),
        patch.object(sys.stdin, "read", return_value="Input from stdin"),
    ):
        result = read_from_stdin()
        assert result == "Input from stdin"
