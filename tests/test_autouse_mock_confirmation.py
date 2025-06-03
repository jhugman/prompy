"""
Tests to confirm that the autouse fixture correctly prevents editors from launching.
"""

import os
import tempfile


def test_autouse_mock_prevents_actual_editor():
    """
    Test that the autouse fixture prevents actual editors from launching.

    This test is not in a class that would be skipped by the
    mock_editor_autouse fixture, so it should use the default mock.
    """
    # Import inside the test to ensure we get the patched version
    from prompy.editor import launch_editor

    # Create a temporary file
    with tempfile.NamedTemporaryFile(
        suffix=".md", mode="w", encoding="utf-8", delete=False
    ) as temp_file:
        temp_path = temp_file.name
        temp_file.write("Original content")

    try:
        # This should use the mocked version from the autouse fixture
        return_code = launch_editor(temp_path)

        # Verify the editor was mocked
        assert return_code == 0

        with open(temp_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Confirm the content was modified by the mock and not a real editor
        assert content == "This is the default edited content from the autouse fixture."
    finally:
        os.unlink(temp_path)
