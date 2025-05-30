"""
Tests for editor mocking functionality.

This file contains all tests for the editor mocking utilities, including:
1. Basic tests for the EditorMock class and its methods
2. Advanced tests for different ways of mocking the editor
3. Integration tests with edit_file_with_comments
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Import our editor mocking utility
from utils.editor_mock import EditorMock

from prompy.prompt_context import PromptContext
from prompy.prompt_file import PromptFile
from prompy.prompt_files import PromptFiles


class TestEditorMockUtility:
    """Tests for the core editor mocking utility functionality."""

    def test_mock_editor_with_content(self):
        """Test that the mock editor works with direct content."""
        mock_content = "This is mock edited content."

        # Create a temporary file
        with tempfile.NamedTemporaryFile(
            suffix=".md", mode="w", encoding="utf-8", delete=False
        ) as temp_file:
            temp_path = temp_file.name
            temp_file.write("Original content")

        try:
            # Launch editor with mock
            with EditorMock.patch_editor(return_content=mock_content):
                # Local import to ensure we're using the patched version
                from prompy.editor import launch_editor

                return_code = launch_editor(temp_path)

            # Verify results
            assert return_code == 0

            with open(temp_path, "r", encoding="utf-8") as f:
                content = f.read()

            assert content == mock_content
        finally:
            # Clean up
            os.unlink(temp_path)

    def test_mock_editor_with_function(self):
        """Test that the mock editor works with an edit function."""

        def edit_function(content):
            return content + "\nAdditional content added by function."

        # Create a temporary file
        with tempfile.NamedTemporaryFile(
            suffix=".md", mode="w", encoding="utf-8", delete=False
        ) as temp_file:
            temp_path = temp_file.name
            temp_file.write("Original content")

        try:
            # Launch editor with mock
            with EditorMock.patch_editor(edit_function=edit_function):
                # Local import to ensure we're using the patched version
                from prompy.editor import launch_editor

                return_code = launch_editor(temp_path)

            # Verify results
            assert return_code == 0

            with open(temp_path, "r", encoding="utf-8") as f:
                content = f.read()

            assert content == "Original content\nAdditional content added by function."
        finally:
            # Clean up
            os.unlink(temp_path)

    def test_mock_editor_in_edit_file_with_comments(self):
        """Test that the mock editor works with the edit_file_with_comments function."""
        mock_content = "This is mock edited content."

        # Set up context and prompt files
        context = PromptContext(project_name="test-project", language="python")
        prompt_files = PromptFiles()

        # Create a temporary file
        with tempfile.NamedTemporaryFile(
            suffix=".md", mode="w", encoding="utf-8", delete=False
        ) as temp_file:
            temp_path = temp_file.name
            temp_file.write("Original content")

        try:
            # Edit file with comments
            with EditorMock.patch_editor(return_content=mock_content):
                from prompy.editor import edit_file_with_comments

                success = edit_file_with_comments(
                    temp_path,
                    prompt_files,
                    project_name="test-project",
                    is_new_prompt=False,
                )

            # Verify results
            assert success

            with open(temp_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Content should be exactly what the mock editor wrote
            assert content == mock_content
        finally:
            # Clean up
            os.unlink(temp_path)


class TestAdvancedEditorMocking:
    """Tests for advanced editor mocking techniques."""

    def test_patching_subprocess_run(self):
        """Test directly patching subprocess.run to avoid launching an editor."""

        # Create a temporary file
        with tempfile.NamedTemporaryFile(
            suffix=".md", mode="w", encoding="utf-8", delete=False
        ) as temp_file:
            temp_path = temp_file.name
            temp_file.write("Original content")

        try:
            # Patch subprocess.run to prevent launching a real editor
            with patch("subprocess.run") as mock_run:
                mock_result = MagicMock()
                mock_result.returncode = 0
                mock_run.return_value = mock_result

                # With this patch, no real editor will be launched
                # Import inside the patch to ensure we're using the mocked version
                from prompy.editor import launch_editor

                launch_editor(temp_path)

                # Verify that subprocess.run was called
                mock_run.assert_called_once()
        finally:
            # Clean up
            os.unlink(temp_path)

    def test_direct_patch_edit_file_with_comments(self):
        """Test patching edit_file_with_comments directly."""
        mock_content = "This is directly patched content."

        # Set up context and prompt files
        context = PromptContext(project_name="test-project", language="python")

        # Create a temporary file
        with tempfile.NamedTemporaryFile(
            suffix=".md", mode="w", encoding="utf-8", delete=False
        ) as temp_file:
            temp_path = temp_file.name
            temp_file.write("Original content")

        try:
            # Use our direct patch for edit_file_with_comments
            with EditorMock.patch_edit_file_with_comments(return_content=mock_content):
                # Import inside the patch to ensure we're using the mocked version
                from prompy.editor import edit_file_with_comments

                success = edit_file_with_comments(
                    temp_path,
                    context.load_all(),
                    project_name="test-project",
                    is_new_prompt=False,
                )

            # Verify results
            assert success

            with open(temp_path, "r", encoding="utf-8") as f:
                content = f.read()

            assert content == mock_content
        finally:
            # Clean up
            os.unlink(temp_path)
