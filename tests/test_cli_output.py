"""
Tests for CLI output commands.
"""

import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest
from click.testing import CliRunner

from prompy.cli import cli


@pytest.fixture
def mock_output_env(tmp_path, monkeypatch):
    """Fixture to set up a mock output environment."""
    # Create cache directories
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    # Create a project cache dir
    project_cache_dir = cache_dir / "test-project"
    project_cache_dir.mkdir()

    # Create a test cache file
    cache_file = project_cache_dir / "CURRENT_FILE.md"
    test_content = "This is test prompt content.\n\nIt has multiple lines.\n"
    with open(cache_file, "w", encoding="utf-8") as f:
        f.write(test_content)

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
        patch(
            "prompy.prompt_render.PromptRender.render", return_value=test_content
        ) as mock_render,
        patch.dict(os.environ, {"EDITOR": "nano"}),
    ):
        yield mock_config, mock_render, cache_dir, test_content


def test_out_command_to_stdout(mock_output_env):
    """Test the out command outputting to stdout."""
    mock_config, mock_render, cache_dir, test_content = mock_output_env
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["--project", "test-project", "out"])

        assert result.exit_code == 0
        assert "This is test prompt content" in result.output


def test_out_command_to_file(mock_output_env):
    """Test the out command outputting to a file."""
    mock_config, mock_render, cache_dir, test_content = mock_output_env
    runner = CliRunner()

    with runner.isolated_filesystem():
        output_file = "output.md"

        with patch("prompy.output.output_to_file", return_value=True) as mock_file:
            result = runner.invoke(
                cli, ["--project", "test-project", "out", "--file", output_file]
            )

            assert result.exit_code == 0
            assert f"Prompt output to file: {output_file}" in result.output
            mock_file.assert_called_once_with(test_content, output_file)


def test_out_command_to_clipboard(mock_output_env):
    """Test the out command outputting to clipboard."""
    mock_config, mock_render, cache_dir, test_content = mock_output_env
    runner = CliRunner()

    with runner.isolated_filesystem():
        with patch(
            "prompy.output.output_to_clipboard", return_value=True
        ) as mock_clipboard:
            result = runner.invoke(
                cli, ["--project", "test-project", "out", "--pbcopy"]
            )

            assert result.exit_code == 0
            assert "Prompt copied to clipboard." in result.output
            mock_clipboard.assert_called_once_with(test_content)


def test_out_command_no_project(mock_output_env):
    """Test the out command with no project specified."""
    mock_config, mock_render, cache_dir, test_content = mock_output_env
    runner = CliRunner()

    with runner.isolated_filesystem():
        # Run without --project flag
        result = runner.invoke(cli, ["out"])

        assert result.exit_code == 0
        assert "No project detected" in result.output


def test_out_command_no_cache(mock_output_env):
    """Test the out command with no cache file."""
    mock_config, mock_render, cache_dir, test_content = mock_output_env
    runner = CliRunner()

    # Remove the cache file
    cache_file = cache_dir / "test-project" / "CURRENT_FILE.md"
    if cache_file.exists():
        os.unlink(cache_file)

    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["--project", "test-project", "out"])

        assert result.exit_code == 0
        assert "No current prompt found" in result.output


def test_pbcopy_command(mock_output_env):
    """Test the pbcopy command."""
    mock_config, mock_render, cache_dir, test_content = mock_output_env
    runner = CliRunner()

    with runner.isolated_filesystem():
        with patch(
            "prompy.output.output_to_clipboard", return_value=True
        ) as mock_clipboard:
            result = runner.invoke(cli, ["--project", "test-project", "pbcopy"])

            assert result.exit_code == 0
            assert "Prompt copied to clipboard." in result.output
            mock_clipboard.assert_called_once_with(test_content)


def test_pbcopy_command_with_slug(mock_output_env):
    """Test the pbcopy command with a prompt slug."""
    mock_config, mock_render, cache_dir, test_content = mock_output_env
    runner = CliRunner()

    with (
        runner.isolated_filesystem(),
        patch("prompy.cli.PromptContext.load_slug") as mock_load_slug,
        patch("prompy.output.output_to_clipboard", return_value=True) as mock_clipboard,
    ):
        # Create a mock prompt file
        mock_prompt = MagicMock()
        mock_prompt.markdown_template = "Mock prompt content"
        mock_load_slug.return_value = mock_prompt

        # Mock the render method to return expected content
        mock_render.return_value = "Rendered content"

        result = runner.invoke(
            cli, ["--project", "test-project", "pbcopy", "some/slug"]
        )

        assert result.exit_code == 0
        assert "Prompt copied to clipboard" in result.output
