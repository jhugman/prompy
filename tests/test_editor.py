"""
Tests for the editor module.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from prompy.editor import (
    add_help_comments,
    find_editor,
    launch_editor,
    remove_help_comments,
)
from prompy.prompt_context import PromptContext
from prompy.prompt_file import PromptFile
from prompy.prompt_files import PromptFiles


class TestEditorDetection:
    """Tests for editor detection functionality."""

    def test_editor_env_var(self):
        """Test that the EDITOR environment variable is used if set."""
        with patch.dict(os.environ, {"EDITOR": "/usr/bin/test-editor"}):
            assert find_editor() == "/usr/bin/test-editor"

    def test_visual_env_var(self):
        """Test that the VISUAL environment variable is used if EDITOR is not set."""
        with patch.dict(os.environ, {"EDITOR": "", "VISUAL": "/usr/bin/test-visual"}):
            assert find_editor() == "/usr/bin/test-visual"

    def test_editor_env_var_with_args(self):
        """Test that the EDITOR environment variable that contains args"""
        with patch.dict(os.environ, {"EDITOR": "code -w"}):
            # The function should return the entire command string
            assert find_editor() == "code -w"

    @patch("subprocess.run")
    def test_common_editors(self, mock_run):
        """Test that common editors are checked if no environment variables are set."""
        # Mock that 'vim' is found
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        with patch.dict(os.environ, {"EDITOR": "", "VISUAL": ""}):
            assert find_editor() in ["nano", "vim", "emacs", "vi"]
            mock_run.assert_called()

    @patch("subprocess.run")
    def test_editor_fallback(self, mock_run):
        """Test that the function falls back to nano if no editors are found."""
        # Mock that no editors are found
        mock_result = MagicMock()
        mock_result.returncode = 1
        mock_run.return_value = mock_result

        with patch.dict(os.environ, {"EDITOR": "", "VISUAL": ""}):
            assert find_editor() == "nano"


class TestEditorLaunching:
    """Tests for editor launching functionality."""

    @patch("subprocess.run")
    def test_launch_editor_success(self, mock_run):
        """Test that the editor is launched successfully."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        with patch("prompy.editor.find_editor", return_value="test-editor"):
            assert launch_editor("test-file.md") == 0
            mock_run.assert_called_once_with(
                ["test-editor", "test-file.md"], check=False
            )

    @patch("subprocess.run")
    def test_launch_editor_failure(self, mock_run):
        """Test that errors are handled when launching the editor."""
        mock_run.side_effect = Exception("Command failed")

        with patch("prompy.editor.find_editor", return_value="test-editor"):
            with pytest.raises(RuntimeError):
                launch_editor("test-file.md")

    @patch("subprocess.run")
    def test_launch_editor_with_args(self, mock_run):
        """Test that the EDITOR environment variable with arguments is properly parsed."""
        mock_result = MagicMock()
        mock_result.returncode = 0
        mock_run.return_value = mock_result

        with patch("prompy.editor.find_editor", return_value="code -w"):
            assert launch_editor("test-file.md") == 0
            mock_run.assert_called_once_with(
                ["code", "-w", "test-file.md"], check=False
            )


class TestHelpComments:
    """Tests for help comments functionality."""

    def test_add_help_comments_empty_content(self):
        """Test adding help comments to empty content."""
        # Create a mock context and prompt files
        context = PromptContext(project_name="test-project", language="python")

        # Add a test prompt file
        test_file = PromptFile(slug="project/test", description="Test description")
        prompt_files = PromptFiles(
            project_name="test-project",
            language_name="python",
            projects={test_file.slug: test_file},
        )

        content = ""
        result = add_help_comments(content, prompt_files)

        assert "PROMPY AVAILABLE FRAGMENTS" in result
        assert "PROJECT FRAGMENTS (project: test-project)" in result
        assert "@project/test" in result
        assert "Test description" in result
        assert "This comment section will be removed from the final prompt" in result

    def test_add_help_comments_existing_content(self):
        """Test adding help comments to existing content."""
        context = PromptContext(project_name="test-project", language="python")
        prompt_files = PromptFiles()

        content = "This is existing content.\n"
        result = add_help_comments(content, prompt_files)

        assert result.startswith("This is existing content.")
        assert "PROMPY AVAILABLE FRAGMENTS" in result
        assert "SYNTAX:" in result

    def test_remove_help_comments(self):
        """Test removing help comments."""
        content = """This is some content.

<!--
PROMPY AVAILABLE FRAGMENTS:
--------------------------

PROJECT FRAGMENTS (project: test):
  @project/test
    Test description

SYNTAX:
  @fragment-name(arg1, key=value)
  @path/to/fragment
  @project/fragment
  @language/fragment

This comment section will be removed from the final prompt.
-->"""

        result = remove_help_comments(content)

        assert result == "This is some content."
        assert "PROMPY AVAILABLE FRAGMENTS" not in result

    def test_remove_help_comments_no_comments(self):
        """Test removing help comments when there are none."""
        content = "This is some content without help comments."

        result = remove_help_comments(content)

        assert result == content
