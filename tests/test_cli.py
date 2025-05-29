"""
Tests for the CLI module.
"""

import os
import subprocess
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest
from click.testing import CliRunner

from prompy import __version__
from prompy.cli import cli


def test_version_flag():
    """Test that the --version flag prints the version and exits."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--version"])
    assert result.exit_code == 0
    assert f"Prompy version {__version__}" in result.output


def test_help_flag():
    """Test that the --help flag prints help information and exits."""
    runner = CliRunner()
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Prompy: A command-line tool" in result.output


def test_no_command_invokes_edit(mock_cli_env):
    """Test that running with no command invokes the edit command."""
    runner = CliRunner()
    # Use our fixture to set up all necessary mocks
    mock_edit, mock_config = mock_cli_env

    # Need to set the project to avoid errors
    result = runner.invoke(cli, ["--project", "test-project"])
    assert result.exit_code == 0
    assert "Editing current one-off prompt for project: test-project" in result.output
    # Verify that the edit function was called
    mock_edit.assert_called_once()


def test_new_command(mock_cli_env):
    """Test that the new command works."""
    runner = CliRunner()
    # Use our fixture to set up all necessary mocks
    mock_edit, mock_config = mock_cli_env

    with runner.isolated_filesystem():
        # The --project option must come before the subcommand
        result = runner.invoke(
            cli, ["--project", "test-project", "new"], catch_exceptions=False
        )
        print(f"Output: {result.output}")
        print(f"Exit code: {result.exit_code}")
        if hasattr(result, "exception") and result.exception:
            print(f"Exception: {result.exception}")
        assert result.exit_code == 0
        assert "New prompt cached for test-project" in result.output


def test_edit_command(mock_cli_env):
    """Test that the edit command works."""
    runner = CliRunner()
    # Use our fixture to set up all necessary mocks
    mock_edit, mock_config = mock_cli_env

    with runner.isolated_filesystem():
        # The --project option must come before the subcommand
        result = runner.invoke(cli, ["--project", "test-project", "edit"])
        assert result.exit_code == 0
        assert (
            "Editing current one-off prompt for project: test-project" in result.output
        )
        assert "Prompt saved successfully" in result.output


def test_out_command():
    """Test that the out command works."""
    runner = CliRunner()
    # Use a non-existent project name to ensure no cache file is found
    result = runner.invoke(cli, ["--project", "non-existent-project", "out"])
    assert result.exit_code == 1  # Error exit code
    assert "No current prompt found" in result.output
    assert (
        "Try specifying a prompt slug or providing content via stdin" in result.output
    )


def test_save_command():
    """Test that the save command works."""
    runner = CliRunner()
    # Mock a non-existent cache path and ensure it fails appropriately
    with patch("prompy.cli.load_from_cache", return_value=(False, None)):
        result = runner.invoke(cli, ["--project", "test-project", "save", "test/slug"])
        assert "No current prompt found" in result.output


def test_list_command():
    """Test that the list command works."""
    runner = CliRunner()
    result = runner.invoke(cli, ["list"])
    assert result.exit_code == 0
    assert "Available prompt fragments" in result.output


def test_mv_command():
    """Test that the mv command works."""
    runner = CliRunner()
    # The mv command should fail with an error code when files don't exist
    result = runner.invoke(cli, ["mv", "source/slug", "dest/slug"])
    assert result.exit_code == 1
    assert "Can't find prompt fragment '@source/slug'" in result.output
    assert "💡 Suggestion:" in result.output


def test_rm_command():
    """Test that the rm command works."""
    runner = CliRunner()
    with patch("prompy.prompt_context.PromptContext.parse_prompt_slug") as mock_parse:
        # Mock the parse_prompt_slug to return a valid path
        mock_path = Path("/fake/path/test/slug.md")
        mock_parse.return_value = mock_path
        with patch.object(Path, "exists") as mock_exists:
            mock_exists.return_value = True
            # Simulate 'no' at the confirmation prompt
            result = runner.invoke(cli, ["rm", "test/slug"], input="n\n")
            assert result.exit_code == 1  # Operation canceled should return error code
            assert "Remove operation aborted" in result.output
            assert "💡 Suggestion:" in result.output
            assert "--force" in result.output


def test_detections_command():
    """Test that the detections command works."""
    pytest.skip(reason="Unsure if detections is useful")
    mock_detections = {"python": {"file_patterns": ["*.py"], "dir_patterns": [".venv"]}}
    runner = CliRunner()
    with (
        patch("prompy.cli.yaml.safe_load", return_value=mock_detections),
        patch("prompy.cli.yaml.dump"),
        patch("prompy.cli.Path.exists", return_value=True),
        patch("prompy.editor.edit_file_with_comments", return_value=True),
        patch("prompy.cli.open", mock_open(read_data="# content")),
    ):
        result = runner.invoke(cli, ["detections"], catch_exceptions=False)
        assert result.exit_code == 0
        assert "✅ Detections configuration updated and validated" in result.output


def test_edit_command_with_editor():
    """Test that the edit command uses the editor functionality."""
    # Set up all needed mocks
    mock_edit_file = MagicMock(return_value=True)
    mock_parse_slug = MagicMock()

    # Create a file path mock that exists
    mock_path = MagicMock()
    mock_path.exists.return_value = True
    mock_parse_slug.return_value = mock_path

    runner = CliRunner()
    with runner.isolated_filesystem():
        with (
            patch("prompy.editor.edit_file_with_comments", mock_edit_file),
            patch(
                "prompy.prompt_context.PromptContext.parse_prompt_slug", mock_parse_slug
            ),
            patch(
                "prompy.cli.ensure_config_dirs",
                return_value=(
                    Path("config"),
                    Path("config/prompts"),
                    Path("config/cache"),
                    Path("config/detections.yaml"),
                ),
            ),
        ):
            result = runner.invoke(
                cli,
                [
                    "--project",
                    "test-project",
                    "--debug",
                    "edit",
                    "test-project/test-prompt",
                ],
            )

            assert result.exit_code == 0
            assert "Editing prompt" in result.output
            assert "Prompt saved successfully" in result.output
            mock_edit_file.assert_called_once()


def test_new_command_with_editor(mock_cli_env):
    """Test that the new command uses the editor functionality."""
    runner = CliRunner()
    # Use our fixture to set up all necessary mocks
    mock_edit, mock_config = mock_cli_env

    with runner.isolated_filesystem():
        # The --project option must come before the subcommand
        result = runner.invoke(cli, ["--project", "test-project", "new"])

        assert result.exit_code == 0
        assert "New prompt cached for test-project" in result.output
        mock_edit.assert_called_once()
