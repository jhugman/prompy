"""
Tests for CLI management commands: list, mv, cp, rm.
"""

import os
from pathlib import Path
from unittest.mock import MagicMock, mock_open, patch

import pytest
from click.testing import CliRunner

from prompy.cli import cli


@pytest.fixture
def mock_management_env(tmp_path, monkeypatch):
    """Fixture to set up a mock environment for management commands."""
    # Create test config and prompts directories
    config_dir = tmp_path / "config"
    prompts_dir = config_dir / "prompts"
    fragments_dir = prompts_dir / "fragments"
    languages_dir = prompts_dir / "languages" / "python"
    projects_dir = prompts_dir / "projects" / "test-project"

    for dir_path in [fragments_dir, languages_dir, projects_dir]:
        dir_path.mkdir(parents=True, exist_ok=True)

    # Create some test prompts
    test_files = {
        fragments_dir
        / "test-fragment.md": "---\ndescription: A test fragment\ncategories: [test, sample]\n---\nTest fragment content",
        fragments_dir
        / "another-fragment.md": "---\ndescription: Another fragment\ncategories: [sample]\n---\nAnother fragment content",
        languages_dir
        / "test-lang-fragment.md": "---\ndescription: A language fragment\ncategories: [python, test]\n---\nTest language content",
        projects_dir
        / "test-project-fragment.md": "---\ndescription: A project fragment\ncategories: [project, test]\n---\nTest project content",
    }

    for file_path, content in test_files.items():
        with open(file_path, "w") as f:
            f.write(content)

    # Mock config detection
    mock_config_dirs = MagicMock(
        return_value=(
            config_dir,
            prompts_dir,
            config_dir / "cache",
            config_dir / "detections.yaml",
        )
    )

    # Mock project detection
    mock_project_dir = MagicMock(return_value=tmp_path / "project")

    # Define a mock for parse_prompt_slug to ensure correct path resolution
    def mock_parse_slug(self, slug, should_exist=True, global_only=False):
        if slug == "test-fragment":
            return fragments_dir / "test-fragment.md"
        elif slug == "another-fragment":
            return fragments_dir / "another-fragment.md"
        elif slug == "renamed-fragment":
            return fragments_dir / "renamed-fragment.md"
        elif slug == "copied-fragment":
            return fragments_dir / "copied-fragment.md"
        elif slug == "$language/test-lang-fragment":
            return languages_dir / "test-lang-fragment.md"
        elif slug == "$project/test-project-fragment":
            return projects_dir / "test-project-fragment.md"
        return None

    # Patch functions that find configs and project directories
    with (
        patch("prompy.cli.ensure_config_dirs", mock_config_dirs),
        patch("prompy.cli.find_project_dir", mock_project_dir),
        patch("prompy.cli.detect_language", return_value="python"),
        patch("prompy.prompt_context.PromptContext.parse_prompt_slug", mock_parse_slug),
    ):
        # Clear any destination files that might interfere with the tests
        for test_path in [
            fragments_dir / "renamed-fragment.md",
            fragments_dir / "copied-fragment.md",
        ]:
            if test_path.exists():
                test_path.unlink()

        yield config_dir, prompts_dir, test_files


def test_list_command_basic(mock_management_env):
    """Test the basic functionality of the list command."""
    config_dir, prompts_dir, test_files = mock_management_env

    runner = CliRunner()
    result = runner.invoke(
        cli, ["--project", "test-project", "--language", "python", "list"]
    )

    assert result.exit_code == 0
    assert "Available prompt fragments" in result.output
    assert "PROJECT FRAGMENTS" in result.output
    assert "LANGUAGE FRAGMENTS" in result.output
    assert "test-fragment" in result.output
    assert "A test fragment" in result.output


def test_list_command_with_category_filter(mock_management_env):
    """Test the list command with category filtering."""
    config_dir, prompts_dir, test_files = mock_management_env

    # Mock the help_text method to ensure category filtering works correctly
    def mock_help_text(
        self,
        *,
        slug_prefix="",
        include_syntax=True,
        include_header=True,
        use_dashes=True,
        inline_description=False,
        category_filter=None,
    ):
        if category_filter == "test":
            # Only include fragments with test category
            return """FRAGMENTS:
  test-fragment — A test fragment
    Categories: test, sample
  test-lang-fragment — A language fragment
    Categories: python, test
  test-project-fragment — A project fragment
    Categories: project, test
"""
        else:
            # Return all fragments
            return """FRAGMENTS:
  test-fragment — A test fragment
    Categories: test, sample
  another-fragment — Another fragment
    Categories: sample
  test-lang-fragment — A language fragment
    Categories: python, test
  test-project-fragment — A project fragment
    Categories: project, test
"""

    with patch("prompy.prompt_files.PromptFiles.help_text", mock_help_text):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--project",
                "test-project",
                "--language",
                "python",
                "list",
                "--category",
                "test",
            ],
        )

        assert result.exit_code == 0
        assert "Filtering prompts by category: test" in result.output
        assert (
            "test-fragment" in result.output
        )  # Should be included (has 'test' category)
        assert (
            "another-fragment" not in result.output
        )  # Should be excluded (doesn't have 'test' category)


def test_list_command_simple_format(mock_management_env):
    """Test the list command with simple format."""
    config_dir, prompts_dir, test_files = mock_management_env

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--project",
            "test-project",
            "--language",
            "python",
            "list",
            "--format",
            "simple",
        ],
    )

    assert result.exit_code == 0
    assert "Available prompt fragments" in result.output
    # In simple format, descriptions should not be included on the same line
    assert "— A test fragment" not in result.output
    assert "test-fragment" in result.output


def test_mv_command(mock_management_env):
    """Test the mv command."""
    config_dir, prompts_dir, test_files = mock_management_env

    # Create a mock confirm that always returns True
    with patch("click.confirm", return_value=True):
        runner = CliRunner()
        # Move a fragment to a new location
        result = runner.invoke(
            cli,
            [
                "--project",
                "test-project",
                "--language",
                "python",
                "mv",
                "test-fragment",
                "renamed-fragment",
            ],
        )

        assert result.exit_code == 0
        assert "Moved 'test-fragment' to 'renamed-fragment'" in result.output

        # Verify the file was moved
        source_path = prompts_dir / "fragments" / "test-fragment.md"
        dest_path = prompts_dir / "fragments" / "renamed-fragment.md"
        assert not source_path.exists()
        assert dest_path.exists()


def test_mv_command_existing_destination(mock_management_env):
    """Test the mv command with an existing destination."""
    config_dir, prompts_dir, test_files = mock_management_env

    # First mock confirm to return False (cancel the operation)
    with patch("click.confirm", return_value=False):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--project",
                "test-project",
                "--language",
                "python",
                "mv",
                "test-fragment",
                "another-fragment",  # Destination exists
            ],
        )

        assert result.exit_code == 0
        assert "Move operation cancelled" in result.output

        # Both files should still exist
        source_path = prompts_dir / "fragments" / "test-fragment.md"
        dest_path = prompts_dir / "fragments" / "another-fragment.md"
        assert source_path.exists()
        assert dest_path.exists()

    # Now mock confirm to return True (proceed with overwrite)
    with patch("click.confirm", return_value=True):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--project",
                "test-project",
                "--language",
                "python",
                "mv",
                "test-fragment",
                "another-fragment",  # Destination exists
            ],
        )

        assert result.exit_code == 0
        assert "Moved 'test-fragment' to 'another-fragment'" in result.output

        # Source file should be gone, destination should exist
        source_path = prompts_dir / "fragments" / "test-fragment.md"
        dest_path = prompts_dir / "fragments" / "another-fragment.md"
        assert not source_path.exists()
        assert dest_path.exists()


def test_mv_command_force_flag(mock_management_env):
    """Test the mv command with the force flag."""
    config_dir, prompts_dir, test_files = mock_management_env

    # With --force flag, no confirmation should be needed
    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--project",
            "test-project",
            "--language",
            "python",
            "mv",
            "--force",
            "test-fragment",
            "another-fragment",  # Force overwrite
        ],
    )

    assert result.exit_code == 0
    assert "Moved 'test-fragment' to 'another-fragment'" in result.output

    # Source file should be gone, destination should exist
    source_path = prompts_dir / "fragments" / "test-fragment.md"
    dest_path = prompts_dir / "fragments" / "another-fragment.md"
    assert not source_path.exists()
    assert dest_path.exists()


def test_mv_command_updates_references(mock_management_env):
    """Test that the mv command updates references in other prompt files."""
    config_dir, prompts_dir, test_files = mock_management_env

    # First, create a file with references to another fragment
    ref_file_path = prompts_dir / "fragments" / "with-references.md"
    with open(ref_file_path, "w") as f:
        f.write(
            """---
description: File with references
---
This is a test file with references to @test-fragment.
Another reference: @test-fragment(arg1, key="value").
"""
        )  # Mock the update_references function and click.confirm
        with (
            patch("prompy.cli.update_references") as mock_update,
            patch("click.confirm", return_value=True),
        ):
            # Set up the mock to return data indicating success
            mock_update.return_value = {str(ref_file_path): True}

            runner = CliRunner()
            result = runner.invoke(
                cli,
                [
                    "--project",
                    "test-project",
                    "--language",
                    "python",
                    "mv",
                    "test-fragment",
                    "renamed-fragment",
                ],
                catch_exceptions=False,
            )

            # Print debug info
            print(f"Command output: {result.output}")

        assert result.exit_code == 0
        assert "Moved 'test-fragment' to 'renamed-fragment'" in result.output
        assert "Updated 1 file(s) with references" in result.output

        # Verify the mock was called correctly
        mock_update.assert_called_once()
        args = mock_update.call_args[0]
        assert args[1] == "test-fragment"  # old slug
        assert args[2] == "renamed-fragment"  # new slug


def test_mv_command_no_references(mock_management_env):
    """Test the mv command when there are no references to update."""
    config_dir, prompts_dir, test_files = mock_management_env

    # Mock the update_references function and click.confirm
    with (
        patch("prompy.cli.update_references") as mock_update,
        patch("click.confirm", return_value=True),
    ):
        # Set up the mock to return data indicating no updates
        mock_update.return_value = {}

        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--project",
                "test-project",
                "--language",
                "python",
                "mv",
                "test-fragment",
                "renamed-fragment",
            ],
        )

        assert result.exit_code == 0
        assert "No references to update" in result.output


def test_rm_command(mock_management_env):
    """Test the rm command."""
    config_dir, prompts_dir, test_files = mock_management_env

    # Create a mock confirm that returns True
    with patch("click.confirm", return_value=True):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--project",
                "test-project",
                "--language",
                "python",
                "rm",
                "test-fragment",
            ],
        )

        assert result.exit_code == 0
        assert "Removed prompt: test-fragment" in result.output

        # Verify the file was removed
        file_path = prompts_dir / "fragments" / "test-fragment.md"
        assert not file_path.exists()


def test_rm_command_cancel(mock_management_env):
    """Test cancelling the rm command."""
    config_dir, prompts_dir, test_files = mock_management_env

    # Create a mock confirm that returns False
    with patch("click.confirm", return_value=False):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--project",
                "test-project",
                "--language",
                "python",
                "rm",
                "test-fragment",
            ],
        )

        assert result.exit_code == 0
        assert "Remove operation cancelled" in result.output

        # Verify the file still exists
        file_path = prompts_dir / "fragments" / "test-fragment.md"
        assert file_path.exists()


def test_rm_command_force(mock_management_env):
    """Test the rm command with force flag."""
    config_dir, prompts_dir, test_files = mock_management_env

    runner = CliRunner()
    result = runner.invoke(
        cli,
        [
            "--project",
            "test-project",
            "--language",
            "python",
            "rm",
            "--force",
            "test-fragment",  # No confirmation needed
        ],
    )

    assert result.exit_code == 0
    assert "Removed prompt: test-fragment" in result.output

    # Verify the file was removed
    file_path = prompts_dir / "fragments" / "test-fragment.md"
    assert not file_path.exists()


def test_cp_command(mock_management_env):
    """Test the cp command."""
    config_dir, prompts_dir, test_files = mock_management_env

    # Mock click.confirm to handle any confirmations
    with patch("click.confirm", return_value=True):
        runner = CliRunner()
        result = runner.invoke(
            cli,
            [
                "--project",
                "test-project",
                "--language",
                "python",
                "cp",
                "test-fragment",
                "copied-fragment",
            ],
        )

    assert result.exit_code == 0
    assert "Copied 'test-fragment' to 'copied-fragment'" in result.output

    # Verify both files exist
    source_path = prompts_dir / "fragments" / "test-fragment.md"
    dest_path = prompts_dir / "fragments" / "copied-fragment.md"
    assert source_path.exists()
    assert dest_path.exists()

    # Verify content was copied correctly
    with open(source_path) as f:
        source_content = f.read().strip()
    with open(dest_path) as f:
        dest_content = f.read().strip()

    # Extract just the content part after frontmatter
    source_parts = source_content.split("---", 2)
    dest_parts = dest_content.split("---", 2)

    if len(source_parts) > 2 and len(dest_parts) > 2:
        source_markdown = source_parts[2].strip()
        dest_markdown = dest_parts[2].strip()
        assert source_markdown == dest_markdown, "Content portions should match"
    else:
        # Fall back to checking if source content is in destination content
        assert source_content in dest_content, (
            "Source content should be contained in destination content"
        )
