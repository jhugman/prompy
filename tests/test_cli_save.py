"""
Tests for the save command functionality.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import click
import pytest
from click.testing import CliRunner

from prompy.cache import load_from_cache
from prompy.cli import cli
from prompy.prompt_file import PromptFile


@pytest.fixture
def mock_save_env():
    """Set up a mock environment for testing save command."""
    # Create a temp directory for cache
    with tempfile.TemporaryDirectory() as tmpdir:
        cache_dir = Path(tmpdir) / "cache"
        config_dir = Path(tmpdir) / "config"
        prompts_dir = config_dir / "prompts"
        projects_dir = prompts_dir / "projects"
        fragments_dir = prompts_dir / "fragments"

        # Set up needed directories
        projects_dir.mkdir(parents=True, exist_ok=True)
        fragments_dir.mkdir(parents=True, exist_ok=True)
        cache_dir.mkdir(parents=True, exist_ok=True)

        # Create a test cache file
        test_project_cache = cache_dir / "test-project"
        test_project_cache.mkdir(exist_ok=True)
        cache_file = test_project_cache / "CURRENT_FILE.md"

        # Sample content for testing
        test_content = "This is a test cache content.\n\nIt includes multiple paragraphs.\n\nIt should be saved as a prompt."
        with open(cache_file, "w", encoding="utf-8") as f:
            f.write(test_content)

        with patch(
            "prompy.cli.ensure_config_dirs",
            return_value=(
                config_dir,
                prompts_dir,
                cache_dir,
                config_dir / "detections.yaml",
            ),
        ):
            yield (
                config_dir,
                prompts_dir,
                cache_dir,
                projects_dir,
                fragments_dir,
                test_content,
            )


def test_save_command_basic(mock_save_env):
    """Test basic save command functionality."""
    config_dir, prompts_dir, cache_dir, projects_dir, fragments_dir, test_content = (
        mock_save_env
    )
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(
            cli, ["--project", "test-project", "save", "test/new-prompt"]
        )

        assert result.exit_code == 0

        # Check that the prompt was saved in the correct location
        saved_file = fragments_dir / "test" / "new-prompt.md"
        assert saved_file.exists(), f"File not found at {saved_file}"

        # Check that it contains the content from the cache
        with open(saved_file, "r", encoding="utf-8") as f:
            saved_content = f.read()

        assert "---" in saved_content  # Check for frontmatter
        assert test_content in saved_content  # Check content is preserved


def test_save_command_with_description(mock_save_env):
    """Test save command with description option."""
    config_dir, prompts_dir, cache_dir, projects_dir, fragments_dir, test_content = (
        mock_save_env
    )
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(
            cli,
            [
                "--project",
                "test-project",
                "save",
                "test/new-prompt",
                "--description",
                "This is a custom description",
            ],
        )

        assert result.exit_code == 0

        # Check that the prompt was saved
        saved_file = fragments_dir / "test" / "new-prompt.md"
        assert saved_file.exists()

        # Check that it contains the custom description
        with open(saved_file, "r", encoding="utf-8") as f:
            saved_content = f.read()

        assert "description: This is a custom description" in saved_content


def test_save_command_with_categories(mock_save_env):
    """Test save command with categories option."""
    config_dir, prompts_dir, cache_dir, projects_dir, fragments_dir, test_content = (
        mock_save_env
    )
    runner = CliRunner()

    # Create the prompt file directly to test with categories
    from prompy.frontmatter import generate_frontmatter

    # Generate frontmatter with categories
    frontmatter = generate_frontmatter(test_content, None, ["test", "prompt"])

    # Verify the frontmatter contains the categories
    assert "categories" in frontmatter
    assert "test" in frontmatter["categories"]
    assert "prompt" in frontmatter["categories"]

    # Create a prompt file and set its properties
    prompt_file = PromptFile()
    prompt_file.slug = "test/category-prompt"
    prompt_file.markdown_template = test_content
    prompt_file.description = frontmatter.get("description")
    prompt_file.categories = frontmatter.get("categories")
    prompt_file.arguments = frontmatter.get("args")
    prompt_file.frontmatter = prompt_file.generate_frontmatter()

    # Save the prompt file
    dest_path = fragments_dir / "test" / "category-prompt.md"
    dest_path.parent.mkdir(parents=True, exist_ok=True)
    prompt_file.save(dest_path)

    # Check that it contains the categories
    with open(dest_path, "r", encoding="utf-8") as f:
        saved_content = f.read()

    assert "categories:" in saved_content
    assert "- test" in saved_content
    assert "- prompt" in saved_content


def test_save_command_existing_prompt(mock_save_env):
    """Test save command when the destination already exists."""
    config_dir, prompts_dir, cache_dir, projects_dir, fragments_dir, test_content = (
        mock_save_env
    )
    runner = CliRunner()

    # First create an existing prompt at the destination
    dest_dir = fragments_dir / "test"
    dest_dir.mkdir(parents=True, exist_ok=True)

    existing_file = dest_dir / "existing-prompt.md"
    with open(existing_file, "w", encoding="utf-8") as f:
        f.write("---\ndescription: Existing prompt\n---\n\nExisting content")

    with (
        runner.isolated_filesystem(),
        patch("click.confirm", return_value=True) as mock_confirm,
    ):
        # Try to save over the existing file
        result = runner.invoke(
            cli, ["--project", "test-project", "save", "test/existing-prompt"]
        )

        # Check confirmation was asked
        mock_confirm.assert_called_once()

        # Check that the file was overwritten
        assert result.exit_code == 0
        assert existing_file.exists()

        with open(existing_file, "r", encoding="utf-8") as f:
            new_content = f.read()

        assert test_content in new_content
        assert "Existing content" not in new_content


def test_save_command_existing_prompt_abort(mock_save_env):
    """Test save command with abort when file exists."""
    config_dir, prompts_dir, cache_dir, projects_dir, fragments_dir, test_content = (
        mock_save_env
    )
    runner = CliRunner()

    # First create an existing prompt at the destination
    dest_dir = fragments_dir / "test"
    dest_dir.mkdir(parents=True, exist_ok=True)

    existing_file = dest_dir / "existing-prompt.md"
    existing_content = "---\ndescription: Existing prompt\n---\n\nExisting content"
    with open(existing_file, "w", encoding="utf-8") as f:
        f.write(existing_content)

    with (
        runner.isolated_filesystem(),
        patch("click.confirm", return_value=False) as mock_confirm,
    ):
        # Try to save over the existing file but abort
        result = runner.invoke(
            cli, ["--project", "test-project", "save", "test/existing-prompt"]
        )

        # Check confirmation was asked
        mock_confirm.assert_called_once()

        # Check that the command was aborted
        assert "aborted" in result.output.lower()

        # Verify file wasn't changed
        with open(existing_file, "r", encoding="utf-8") as f:
            unchanged_content = f.read()

        assert unchanged_content == existing_content


def test_save_command_with_project_slug(mock_save_env):
    """Test save command with $project slug."""
    config_dir, prompts_dir, cache_dir, projects_dir, fragments_dir, test_content = (
        mock_save_env
    )
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(
            cli, ["--project", "test-project", "save", "project/new-prompt"]
        )

        assert result.exit_code == 0

        # Check that the prompt was saved in the project directory
        saved_file = projects_dir / "test-project" / "new-prompt.md"
        assert saved_file.exists(), f"File not found at {saved_file}"


def test_save_command_auto_generated_frontmatter(mock_save_env):
    """Test save command auto-generates frontmatter from content."""
    config_dir, prompts_dir, cache_dir, projects_dir, fragments_dir, _ = mock_save_env
    runner = CliRunner()

    # Create a more complex content with potential arguments
    complex_content = """This is a complex prompt with arguments.

For variable1, I want to use {{param1}}.
For variable2, let's use {{param2}}.

This paragraph doesn't have any variables."""

    # Create the cache file with complex content
    test_project_cache = cache_dir / "test-project"
    cache_file = test_project_cache / "CURRENT_FILE.md"
    with open(cache_file, "w", encoding="utf-8") as f:
        f.write(complex_content)

    with runner.isolated_filesystem():
        result = runner.invoke(
            cli, ["--project", "test-project", "save", "test/complex-prompt"]
        )

        assert result.exit_code == 0

        # Check that the prompt was saved
        saved_file = fragments_dir / "test" / "complex-prompt.md"
        assert saved_file.exists()

        # Verify the generated frontmatter includes detected arguments
        with open(saved_file, "r", encoding="utf-8") as f:
            saved_content = f.read()

        assert "args:" in saved_content
        assert "param1" in saved_content
        assert "param2" in saved_content


def test_save_command_no_cache(mock_save_env):
    """Test save command when cache file doesn't exist."""
    config_dir, prompts_dir, cache_dir, projects_dir, fragments_dir, _ = mock_save_env
    runner = CliRunner()

    # Remove cache file
    test_project_cache = cache_dir / "test-project"
    cache_file = test_project_cache / "CURRENT_FILE.md"
    if cache_file.exists():
        os.unlink(cache_file)

    with runner.isolated_filesystem():
        result = runner.invoke(
            cli, ["--project", "test-project", "save", "test/no-cache-prompt"]
        )

        assert result.exit_code != 0
        assert "No current prompt found" in result.output


def test_save_command_no_project(mock_save_env):
    """Test save command with no project specified."""
    config_dir, prompts_dir, cache_dir, projects_dir, fragments_dir, _ = mock_save_env
    runner = CliRunner()

    with runner.isolated_filesystem():
        result = runner.invoke(cli, ["save", "test/no-project-prompt"])

        assert "No project detected" in result.output
