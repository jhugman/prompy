"""
Tests for enhanced editor features.
"""

import os
import tempfile
from unittest.mock import MagicMock, patch

from prompy.editor import (
    clear_editor_help,
    display_editor_help,
    display_editor_success,
    edit_file_with_comments,
    is_terminal_output,
)
from prompy.prompt_file import PromptFile
from prompy.prompt_files import PromptFiles


class TestTerminalDetection:
    """Tests for terminal output detection."""

    def test_is_terminal_output_test_environment(self):
        """Test that terminal output is disabled in test environment."""
        # In test environment, should return False
        assert not is_terminal_output()

    @patch.dict("sys.modules", {"pytest": None})
    @patch("sys.stdout.isatty", return_value=True)
    def test_is_terminal_output_terminal(self, mock_isatty):
        """Test that terminal output is enabled in real terminal."""
        assert is_terminal_output()

    @patch.dict("sys.modules", {"pytest": None})
    @patch("sys.stdout.isatty", return_value=False)
    def test_is_terminal_output_redirected(self, mock_isatty):
        """Test that terminal output is disabled when redirected."""
        assert not is_terminal_output()

    @patch.dict("sys.modules", {"pytest": None})
    def test_is_terminal_output_no_isatty(self):
        """Test handling when stdout has no isatty method."""
        # Mock stdout to not have isatty method
        mock_stdout = MagicMock()
        del mock_stdout.isatty  # Remove the isatty attribute

        with patch("sys.stdout", mock_stdout):
            # Should return False when no isatty method exists
            assert not is_terminal_output()


class TestEditorHelpDisplay:
    """Tests for editor help display functionality."""

    def test_display_editor_help_test_environment(self):
        """Test that display_editor_help does nothing in test environment."""
        # Create mock prompt files
        prompt_files = PromptFiles(
            project_name="test-project",
            language_name="python",
            projects={},
            languages={},
            fragments={},
        )

        # Should not raise any exceptions and should not output anything
        display_editor_help("test-project", prompt_files, False)

    @patch("prompy.editor.is_terminal_output", return_value=True)
    @patch("prompy.editor.console")
    def test_display_editor_help_terminal(self, mock_console, mock_terminal):
        """Test display_editor_help in terminal environment."""
        # Create mock prompt files with help text
        test_file = PromptFile(slug="project/test", description="Test description")
        prompt_files = PromptFiles(
            project_name="test-project",
            language_name="python",
            projects={"project/test": test_file},
            languages={},
            fragments={},
        )

        display_editor_help("test-project", prompt_files, False)

        # Should have called console.print multiple times:
        # 1. Empty line, 2. Title panel, 3. Help text content
        assert mock_console.print.call_count >= 2

        # Check that a Panel was passed in one of the calls
        panel_found = False
        for call in mock_console.print.call_args_list:
            if call[0] and hasattr(call[0][0], "renderable"):
                panel_found = True
                break
        assert panel_found, "Expected a Panel object in one of the console.print calls"

    @patch("prompy.editor.is_terminal_output", return_value=True)
    @patch("prompy.editor.console")
    def test_display_editor_help_new_prompt(self, mock_console, mock_terminal):
        """Test display_editor_help for new prompt."""
        prompt_files = PromptFiles(
            project_name="test-project",
            language_name="python",
            projects={},
            languages={},
            fragments={},
        )

        display_editor_help("test-project", prompt_files, True)

        # Should have called console.print multiple times
        assert mock_console.print.call_count >= 2

        # Check that one of the calls contains "Creating new prompt" in the
        # panel content
        title_found = False
        for call in mock_console.print.call_args_list:
            if call[0] and hasattr(call[0][0], "renderable"):
                panel = call[0][0]
                panel_content = str(panel.renderable)
                if "Creating new prompt" in panel_content:
                    title_found = True
                    break
        assert title_found, "Expected 'Creating new prompt' in panel content"

    @patch("prompy.editor.is_terminal_output", return_value=True)
    @patch("prompy.editor.console")
    def test_display_editor_help_editing_prompt(self, mock_console, mock_terminal):
        """Test display_editor_help for editing existing prompt."""
        prompt_files = PromptFiles(
            project_name="test-project",
            language_name="python",
            projects={},
            languages={},
            fragments={},
        )

        display_editor_help("test-project", prompt_files, False)

        # Should have called console.print multiple times
        assert mock_console.print.call_count >= 2

        # Check that one of the calls contains "Editing prompt" in the panel content
        title_found = False
        for call in mock_console.print.call_args_list:
            if call[0] and hasattr(call[0][0], "renderable"):
                panel = call[0][0]
                panel_content = str(panel.renderable)
                if "Editing prompt" in panel_content:
                    title_found = True
                    break
        assert title_found, "Expected 'Editing prompt' in panel content"


class TestEditorHelpClear:
    """Tests for editor help clearing functionality."""

    def test_clear_editor_help_test_environment(self):
        """Test that clear_editor_help does nothing in test environment."""
        # Should not raise any exceptions
        clear_editor_help()

    @patch("prompy.editor.is_terminal_output", return_value=True)
    @patch("prompy.editor.console")
    def test_clear_editor_help_terminal(self, mock_console, mock_terminal):
        """Test clear_editor_help in terminal environment."""
        clear_editor_help()

        # Should have called console.clear and console.print once each
        mock_console.clear.assert_called_once()
        mock_console.print.assert_called_once()


class TestEditorSuccessDisplay:
    """Tests for editor success message display."""

    def test_display_editor_success_test_environment(self):
        """Test display_editor_success in test environment."""
        with patch("click.echo") as mock_echo:
            display_editor_success("Test message")
            # Should fall back to click.echo in test environment
            mock_echo.assert_called_once_with("Test message")

    @patch("prompy.editor.is_terminal_output", return_value=True)
    @patch("prompy.editor.console")
    def test_display_editor_success_terminal(self, mock_console, mock_terminal):
        """Test display_editor_success in terminal environment."""
        display_editor_success("Test message")

        # Should have called console.print
        mock_console.print.assert_called_once()
        # Check that the message contains our text
        args = mock_console.print.call_args[0]
        text = args[0]
        assert "Test message" in str(text)


class TestEnhancedEditFileWithComments:
    """Tests for enhanced edit_file_with_comments functionality."""

    @patch("prompy.editor.launch_editor", return_value=0)
    @patch("prompy.editor.display_editor_help")
    @patch("prompy.editor.clear_editor_help")
    def test_edit_file_with_comments_enhanced(
        self, mock_clear, mock_display, mock_launch
    ):
        """Test that edit_file_with_comments uses enhanced features."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(
            suffix=".md", mode="w", encoding="utf-8", delete=False
        ) as temp_file:
            temp_path = temp_file.name
            temp_file.write("Original content")

        try:
            # Create mock prompt files
            prompt_files = PromptFiles(
                project_name="test-project",
                language_name="python",
                projects={},
                languages={},
                fragments={},
            )

            # Call the enhanced function
            result = edit_file_with_comments(
                temp_path,
                prompt_files,
                project_name="test-project",
                is_new_prompt=True,
            )

            # Should return True for success
            assert result

            # Should have called display and clear functions
            mock_display.assert_called_once_with("test-project", prompt_files, True)
            mock_clear.assert_called_once()

            # Should have launched editor
            mock_launch.assert_called_once()

        finally:
            # Clean up
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass

    @patch("prompy.editor.launch_editor", return_value=1)  # Editor failed
    @patch("prompy.editor.display_editor_help")
    @patch("prompy.editor.clear_editor_help")
    def test_edit_file_with_comments_editor_failure(
        self, mock_clear, mock_display, mock_launch
    ):
        """Test edit_file_with_comments when editor fails."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(
            suffix=".md", mode="w", encoding="utf-8", delete=False
        ) as temp_file:
            temp_path = temp_file.name
            temp_file.write("Original content")

        try:
            # Create mock prompt files
            prompt_files = PromptFiles(
                project_name="test-project",
                language_name="python",
                projects={},
                languages={},
                fragments={},
            )

            # Call the enhanced function
            result = edit_file_with_comments(
                temp_path,
                prompt_files,
                project_name="test-project",
                is_new_prompt=False,
            )

            # Should return False for failure
            assert not result

            # Should still have called display and clear functions
            mock_display.assert_called_once_with("test-project", prompt_files, False)
            mock_clear.assert_called_once()

        finally:
            # Clean up
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass

    @patch("prompy.editor.launch_editor", return_value=0)
    @patch("prompy.editor.display_editor_help")
    @patch("prompy.editor.clear_editor_help")
    def test_edit_file_with_comments_new_file(
        self, mock_clear, mock_display, mock_launch
    ):
        """Test edit_file_with_comments with a new file."""
        # Use a non-existent file path
        temp_path = "/tmp/test_new_file.md"

        try:
            # Ensure file doesn't exist
            if os.path.exists(temp_path):
                os.unlink(temp_path)

            # Create mock prompt files
            prompt_files = PromptFiles(
                project_name="test-project",
                language_name="python",
                projects={},
                languages={},
                fragments={},
            )

            # Call the enhanced function
            result = edit_file_with_comments(
                temp_path,
                prompt_files,
                project_name="test-project",
                is_new_prompt=True,
            )

            # Should return True for success
            assert result

            # Should have called display and clear functions
            mock_display.assert_called_once_with("test-project", prompt_files, True)
            mock_clear.assert_called_once()

            # File should now exist
            assert os.path.exists(temp_path)

        finally:
            # Clean up
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass

    @patch("prompy.editor.launch_editor", return_value=0)
    @patch("prompy.editor.display_editor_help")
    @patch("prompy.editor.clear_editor_help")
    def test_edit_file_with_comments_no_project_name(
        self, mock_clear, mock_display, mock_launch
    ):
        """Test edit_file_with_comments without project name."""
        # Create a temporary file
        with tempfile.NamedTemporaryFile(
            suffix=".md", mode="w", encoding="utf-8", delete=False
        ) as temp_file:
            temp_path = temp_file.name
            temp_file.write("Original content")

        try:
            # Create mock prompt files
            prompt_files = PromptFiles(
                project_name=None,
                language_name=None,
                projects={},
                languages={},
                fragments={},
            )

            # Call the enhanced function without project name
            result = edit_file_with_comments(
                temp_path,
                prompt_files,
                project_name=None,
                is_new_prompt=False,
            )

            # Should return True for success
            assert result

            # Should have called display and clear functions with None project
            mock_display.assert_called_once_with(None, prompt_files, False)
            mock_clear.assert_called_once()

        finally:
            # Clean up
            try:
                os.unlink(temp_path)
            except FileNotFoundError:
                pass


class TestEditorIntegrationWithRichFeatures:
    """Integration tests for editor with rich console features."""

    @patch("prompy.editor.is_terminal_output", return_value=False)
    def test_editor_features_disabled_in_test(self, mock_terminal):
        """Test that rich features are properly disabled in test environment."""
        # Create mock prompt files
        prompt_files = PromptFiles(
            project_name="test-project",
            language_name="python",
            projects={},
            languages={},
            fragments={},
        )

        # These should all complete without any output or errors
        display_editor_help("test-project", prompt_files, True)
        clear_editor_help()

        with patch("click.echo") as mock_echo:
            display_editor_success("Test success message")
            mock_echo.assert_called_once_with("Test success message")

    @patch("prompy.editor.is_terminal_output", return_value=True)
    @patch("prompy.editor.console")
    def test_editor_features_enabled_in_terminal(self, mock_console, mock_terminal):
        """Test that rich features are properly enabled in terminal."""
        # Create mock prompt files with some content
        test_file = PromptFile(slug="project/test", description="Test description")
        prompt_files = PromptFiles(
            project_name="test-project",
            language_name="python",
            projects={"project/test": test_file},
            languages={},
            fragments={},
        )

        # These should all use the rich console
        display_editor_help("test-project", prompt_files, True)
        clear_editor_help()
        display_editor_success("Test success message")

        # Should have multiple console.print calls
        assert mock_console.print.call_count >= 3
