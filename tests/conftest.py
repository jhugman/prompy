"""
Pytest configuration file.
"""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
# Add the tests directory to the Python path to allow importing from tests
sys.path.insert(0, str(Path(__file__).parent))

# Import our editor mocking utility
from utils.editor_mock import EditorMock


@pytest.fixture
def mock_cli_env():
    """Fixture to set up all necessary mocks for CLI tests."""
    with (
        patch("prompy.cli.edit_file_with_comments", return_value=True) as mock_edit,
        patch(
            "prompy.cli.ensure_config_dirs",
            return_value=(
                Path("config"),
                Path("config/prompts"),
                Path("config/cache"),
                Path("config/detections.yaml"),
            ),
        ) as mock_config,
        patch.dict(os.environ, {"EDITOR": "nano"}),
    ):
        yield mock_edit, mock_config


@pytest.fixture(autouse=True)
def mock_editor_autouse(request, monkeypatch):
    """
    Fixture to automatically mock the editor for all tests.

    This ensures no real editor is ever launched during tests.
    Individual tests can still override this by using EditorMock
    with specific content or edit functions.

    This fixture skips tests that are testing the editor mocking itself,
    as those tests manage their own mocking.
    """
    # Skip for tests in classes that test editor mocking
    skip_classes = ["TestEditorMockUtility", "TestAdvancedEditorMocking"]
    # Skip for tests in files that test editor mocking
    skip_modules = ["test_editor_mocking"]

    if (request.node.cls and request.node.cls.__name__ in skip_classes) or (
        request.module.__name__.split(".")[-1] in skip_modules
    ):
        yield
        return

    # Import here to avoid circular imports
    from prompy import editor

    default_content = "This is the default edited content from the autouse fixture."

    # Define mock function with a more prominent print statement for debugging
    def mock_launch_editor(file_path):
        """Mock implementation of launch_editor."""
        print(f"\nMOCK EDITOR: Using autouse mock for {file_path}")
        try:
            with open(file_path, "r", encoding="utf-8") as f:
                content = f.read()
        except Exception:
            content = ""

        # Write the new content to the file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(default_content)

        return 0  # Success

    # Use monkeypatch instead of direct module attribute modification
    monkeypatch.setattr(editor, "launch_editor", mock_launch_editor)

    # Also patch subprocess.run to prevent any subprocess from being spawned
    # This is a safety measure in case the patching of launch_editor somehow fails
    def mock_subprocess_run(args, *pargs, **kwargs):
        import subprocess

        print(f"\nMOCK SUBPROCESS: Prevented execution of: {args}")
        mock_result = type(
            "MockCompletedProcess", (), {"returncode": 0, "stdout": "", "stderr": ""}
        )
        return mock_result

    import subprocess

    monkeypatch.setattr(subprocess, "run", mock_subprocess_run)

    yield


@pytest.fixture
def mock_editor():
    """Fixture to mock the editor with default edited content."""
    default_content = "This is the default edited content."
    with EditorMock.patch_editor(return_content=default_content):
        yield default_content


@pytest.fixture
def mock_editor_factory():
    """
    Fixture to create customizable editor mocks.

    Returns a function that can be called with custom content or edit function.
    """

    def create_mock(return_content=None, edit_function=None):
        return EditorMock.patch_editor(
            return_content=return_content if return_content is not None else "",
            edit_function=edit_function,
        )

    return create_mock
