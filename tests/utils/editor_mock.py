"""
Utilities for mocking the editor functionality during tests.
"""

from typing import Callable, Optional
from unittest.mock import patch


class EditorMock:
    """
    Class for mocking the editor functionality in tests.

    This class provides utility methods to patch the editor functionality
    during tests, preventing actual editors from launching and allowing
    simulated user input instead.
    """

    @staticmethod
    def patch_editor(
        return_content: str = "", edit_function: Optional[Callable] = None
    ):
        """
        Create a context manager for patching the editor.

        Args:
            return_content: Content to return as if the user typed it in the editor.
            edit_function: A function that takes the original content and returns
                           the edited content. If provided, this will be used instead
                           of return_content.

        Returns:
            A context manager that can be used in a with statement to patch the editor.
        """

        def mock_launch_editor(file_path):
            """Mock implementation of launch_editor."""
            print(f"MOCK EDITOR: Using patch_editor mock for {file_path}")
            try:
                with open(file_path, "r", encoding="utf-8") as f:
                    content = f.read()
            except Exception:
                content = ""

            # Apply edit function or use return content
            if edit_function:
                new_content = edit_function(content)
            else:
                new_content = return_content

            # Write the content back to the file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)

            return 0  # Success

        # Create a combined patcher that also handles subprocess
        patchers = []

        # Patch launch_editor
        patchers.append(
            patch("prompy.editor.launch_editor", side_effect=mock_launch_editor)
        )

        # Also patch subprocess.run as a safety net to prevent real editor launches
        def mock_subprocess_run(args, *pargs, **kwargs):

            print(f"MOCK SUBPROCESS: Prevented execution of: {args}")
            mock_result = type(
                "MockCompletedProcess",
                (),
                {"returncode": 0, "stdout": "", "stderr": ""},
            )
            return mock_result

        patchers.append(patch("subprocess.run", side_effect=mock_subprocess_run))

        # Return a context manager that applies all patches
        from contextlib import ExitStack

        def multi_patch():
            stack = ExitStack()
            for patcher in patchers:
                stack.enter_context(patcher)
            return stack

        return multi_patch()

    @staticmethod
    def patch_edit_file_with_comments(
        return_content: str = "", edit_function: Optional[Callable] = None
    ):
        """
        Create a context manager for patching the edit_file_with_comments function.

        This is useful for tests that directly interact with edit_file_with_comments.

        Args:
            return_content: Content to return as if the user typed it in the editor.
            edit_function: A function that takes the original content and returns
                           the edited content. If provided, this will be used instead
                           of return_content.

        Returns:
            A context manager that can be used in a with statement.
        """

        def mock_edit_file_with_comments(
            file_path, prompt_files, project_name=None, is_new_prompt=False
        ):
            # Apply edit function or use return content
            if edit_function:
                try:
                    with open(file_path, "r", encoding="utf-8") as f:
                        content = f.read()
                except Exception:
                    content = ""
                new_content = edit_function(content)
            else:
                new_content = return_content

            # Write the new content to the file
            with open(file_path, "w", encoding="utf-8") as f:
                f.write(new_content)

            return True  # Success

        return patch(
            "prompy.editor.edit_file_with_comments",
            side_effect=mock_edit_file_with_comments,
        )
