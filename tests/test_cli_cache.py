"""
Tests for CLI cache integration.
"""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from prompy.cli import cli


@pytest.fixture
def mock_cache_env(tmp_path, monkeypatch):
    """Fixture to set up a mock cache environment."""
    # Create cache directories
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    # Create a project cache dir
    project_cache_dir = cache_dir / "test-project"
    project_cache_dir.mkdir()

    # Mock the ensure_config_dirs function
    with (
        patch(
            "prompy.cli.ensure_config_dirs",
            return_value=(
                tmp_path,
                tmp_path / "prompts",
                cache_dir,
                tmp_path / "detections.yaml",
            ),
        ) as mock_config,
        patch("prompy.cli.edit_file_with_comments", return_value=True) as mock_edit,
        patch.dict(os.environ, {"EDITOR": "nano"}),
    ):
        yield mock_config, mock_edit, cache_dir


def test_new_command_with_cache(mock_cache_env):
    """Test that the new command creates a cache file."""
    mock_config, mock_edit, cache_dir = mock_cache_env
    runner = CliRunner()

    with runner.isolated_filesystem():
        # Run the new command
        result = runner.invoke(cli, ["--project", "test-project", "new"])

        assert result.exit_code == 0
        assert "New prompt cached for test-project" in result.output

        # Check that the cache file was created
        cache_file = cache_dir / "test-project" / "CURRENT_FILE.md"
        assert cache_file.exists()


def test_new_command_with_stdin(mock_cache_env):
    """Test that the new command appends stdin content."""
    mock_config, mock_edit, cache_dir = mock_cache_env
    runner = CliRunner()

    with runner.isolated_filesystem():
        # Run the new command with stdin
        stdin_content = "Content from stdin"
        result = runner.invoke(
            cli, ["--project", "test-project", "new"], input=stdin_content
        )

        assert result.exit_code == 0
        assert "Appended content from stdin" in result.output

        # Check that the cache file contains the stdin content
        cache_file = cache_dir / "test-project" / "CURRENT_FILE.md"
        with open(cache_file, "r", encoding="utf-8") as f:
            content = f.read()
        assert stdin_content in content


def test_new_command_clears_existing_cache(mock_cache_env):
    """Test that new command clears any existing cache."""
    mock_config, mock_edit, cache_dir = mock_cache_env
    runner = CliRunner()

    with runner.isolated_filesystem():
        # Create an existing cache file
        cache_file = cache_dir / "test-project" / "CURRENT_FILE.md"
        with open(cache_file, "w", encoding="utf-8") as f:
            f.write("Existing content")

        # Run the new command
        result = runner.invoke(cli, ["--project", "test-project", "new"])

        assert result.exit_code == 0

        # Check that the cache file was cleared
        with open(cache_file, "r", encoding="utf-8") as f:
            content = f.read()
        assert content == ""  # Should be empty


def test_edit_command_with_existing_cache(mock_cache_env):
    """Test that edit command uses existing cache."""
    mock_config, mock_edit, cache_dir = mock_cache_env
    runner = CliRunner()

    with runner.isolated_filesystem():
        # Create an existing cache file
        cache_file = cache_dir / "test-project" / "CURRENT_FILE.md"
        test_content = "Existing content"
        with open(cache_file, "w", encoding="utf-8") as f:
            f.write(test_content)

        # Run the edit command
        result = runner.invoke(cli, ["--project", "test-project", "edit"])

        assert result.exit_code == 0
        assert (
            "Editing current one-off prompt for project: test-project" in result.output
        )

        # The file should have been edited with the existing content
        mock_edit.assert_called_once()
        assert cache_file.exists()


def test_edit_command_creates_cache_if_missing(mock_cache_env):
    """Test that edit command creates a cache file if it doesn't exist."""
    mock_config, mock_edit, cache_dir = mock_cache_env
    runner = CliRunner()

    with runner.isolated_filesystem():
        # Ensure the cache file doesn't exist
        cache_file = cache_dir / "test-project" / "CURRENT_FILE.md"
        if cache_file.exists():
            os.unlink(cache_file)

        # Run the edit command
        result = runner.invoke(cli, ["--project", "test-project", "edit"])

        assert result.exit_code == 0
        assert (
            "Editing current one-off prompt for project: test-project" in result.output
        )

        # The file should have been created and edited
        assert cache_file.exists()


def test_edit_command_with_stdin(mock_cache_env):
    """Test that edit command appends stdin content to existing cache."""
    mock_config, mock_edit, cache_dir = mock_cache_env
    runner = CliRunner()

    with runner.isolated_filesystem():
        # Create an existing cache file
        cache_file = cache_dir / "test-project" / "CURRENT_FILE.md"
        existing_content = "Existing content"
        with open(cache_file, "w", encoding="utf-8") as f:
            f.write(existing_content)

        # Run the edit command with stdin
        stdin_content = "Content from stdin"
        result = runner.invoke(
            cli, ["--project", "test-project", "edit"], input=stdin_content
        )

        assert result.exit_code == 0
        assert "Appended content from stdin" in result.output

        # The file should have both contents
        with open(cache_file, "r", encoding="utf-8") as f:
            content = f.read()
        assert existing_content in content
        assert stdin_content in content
