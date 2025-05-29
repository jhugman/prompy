"""
Tests for CLI output formatting enhancements.
"""

import json
import os
from pathlib import Path
from unittest.mock import MagicMock, patch

import click
import pytest
from click.testing import CliRunner

from prompy.cli import cli


@pytest.fixture
def mock_format_env(tmp_path, monkeypatch):
    """Fixture to set up a mock environment for format testing."""
    # Create cache directories
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir()

    # Create prompts directory
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir()

    # Create test project prompts
    project_prompts_dir = prompts_dir / "projects" / "test-project"
    project_prompts_dir.mkdir(parents=True)

    test_prompts = {
        "test-prompt1.md": {
            "description": "A test prompt with categories",
            "categories": ["test", "example"],
            "content": "Test content 1",
        },
        "test-prompt2.md": {
            "description": "Another test prompt",
            "categories": ["example"],
            "content": "Test content 2",
        },
    }

    for name, data in test_prompts.items():
        prompt_file = project_prompts_dir / name
        prompt_content = f"""---
description: {data["description"]}
categories: {data["categories"]}
---
{data["content"]}"""
        prompt_file.parent.mkdir(parents=True, exist_ok=True)
        prompt_file.write_text(prompt_content)

    with (
        patch(
            "prompy.cli.ensure_config_dirs",
            return_value=(
                tmp_path,
                prompts_dir,
                cache_dir,
                tmp_path / "detections.yaml",
            ),
        ),
        patch.dict(os.environ, {"EDITOR": "nano"}),
    ):
        yield tmp_path, prompts_dir, cache_dir


def test_list_json_format(mock_format_env):
    """Test the list command with JSON output format."""
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--project", "test-project", "list", "--json"],
    )

    assert result.exit_code == 0
    data = json.loads(result.output)

    assert "prompts" in data
    assert "metadata" in data
    assert data["metadata"]["project"] == "test-project"
    assert len(data["prompts"]) > 0

    # Verify prompt structure
    prompt = data["prompts"][0]
    assert "slug" in prompt
    assert "description" in prompt
    assert "categories" in prompt


def test_list_with_category_filter(mock_format_env):
    """Test the list command with category filtering."""
    runner = CliRunner()
    result = runner.invoke(
        cli,
        ["--project", "test-project", "list", "--category", "test"],
    )

    assert result.exit_code == 0
    assert "Available prompt fragments" in result.output
    assert "test-prompt1" in result.output  # Has 'test' category
    assert "test-prompt2" not in result.output  # Doesn't have 'test' category


def test_colorized_output(mock_format_env):
    """Test colorized output in terminal."""
    tmp_path, prompts_dir, cache_dir = mock_format_env
    runner = CliRunner()

    test_content = "Test colorized output"
    cache_file = cache_dir / "test-project" / "CURRENT_FILE.md"
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(test_content)

    with patch("sys.stdout.isatty", return_value=True):
        result = runner.invoke(cli, ["--project", "test-project", "out"])
        assert result.exit_code == 0


def test_plain_output_when_redirected(mock_format_env):
    """Test plain output when redirected."""
    tmp_path, prompts_dir, cache_dir = mock_format_env
    runner = CliRunner()

    test_content = "Test plain output"
    cache_file = cache_dir / "test-project" / "CURRENT_FILE.md"
    cache_file.parent.mkdir(parents=True, exist_ok=True)
    cache_file.write_text(test_content)

    with patch("sys.stdout.isatty", return_value=False):
        result = runner.invoke(cli, ["--project", "test-project", "out"])
        assert result.exit_code == 0
        assert test_content in result.output
