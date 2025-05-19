"""
Tests for updating references when fragments are moved.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from prompy.prompt_file import PromptContext, PromptFile
from prompy.references import update_references, update_references_in_file


def test_update_references_in_file(tmp_path):
    """Test updating references in a single file."""
    # Create a test file with references
    file_path = tmp_path / "test_file.md"
    content = """---
description: A file with references
---
This is a test file with multiple references:

@test-fragment
@test-fragment(arg1)
@test-fragment(arg1, key=value)
@other-fragment

And some non-references:
@@test-fragment (escaped)
@missing-fragment
"""
    with open(file_path, "w") as f:
        f.write(content)

    # Update references
    updated = update_references_in_file(file_path, "test-fragment", "new-fragment")

    # Check result
    assert updated is True

    # Read the updated file
    with open(file_path, "r") as f:
        new_content = f.read()

    # Check that references were updated
    assert "@new-fragment" in new_content
    assert "@new-fragment(arg1)" in new_content
    assert "@new-fragment(arg1, key=value)" in new_content
    assert "@other-fragment" in new_content  # Unchanged
    assert "@@test-fragment" in new_content  # Escaped, unchanged
    assert "@missing-fragment" in new_content  # Not matching, unchanged


def test_no_references_to_update(tmp_path):
    """Test when there are no references to update."""
    # Create a test file with no matching references
    file_path = tmp_path / "no_refs.md"
    content = """---
description: A file with no matching references
---
This file has no references to update:

@other-fragment
Some text
"""
    with open(file_path, "w") as f:
        f.write(content)

    # Try to update references
    updated = update_references_in_file(file_path, "test-fragment", "new-fragment")

    # Check result
    assert updated is False

    # Read the file to confirm it's unchanged
    with open(file_path, "r") as f:
        new_content = f.read()

    assert new_content == content


def test_update_references_integration(tmp_path):
    """Test the update_references function that updates all files."""
    # Create test directory structure
    prompts_dir = tmp_path / "prompts"
    fragments_dir = prompts_dir / "fragments"
    fragments_dir.mkdir(parents=True)

    # Create test files
    file1 = fragments_dir / "file1.md"
    file2 = fragments_dir / "file2.md"

    with open(file1, "w") as f:
        f.write("Content with @test-fragment reference")
    with open(file2, "w") as f:
        f.write("Content with @other-fragment and @test-fragment references")

    # Mock PromptContext and PromptFiles
    mock_prompt_context = MagicMock(spec=PromptContext)
    mock_prompt_files = MagicMock()

    # Setup mock for load_all to return our mock prompt_files
    mock_prompt_context.load_all.return_value = mock_prompt_files

    # Setup mock for parse_prompt_slug to return our file paths
    mock_prompt_context.parse_prompt_slug = lambda slug: {
        "file1": file1,
        "file2": file2,
    }.get(slug)

    # Setup mock prompt files
    mock_prompt_files._fragment_prompts = {
        "file1": MagicMock(spec=PromptFile),
        "file2": MagicMock(spec=PromptFile),
    }

    # Mock update_references_in_file to simulate successful updates
    with patch("prompy.references.update_references_in_file") as mock_update:
        # Make file1 update successfully and file2 fail
        mock_update.side_effect = (
            lambda file_path, old_slug, new_slug: file_path == file1
        )

        # Call the function
        results = update_references(
            mock_prompt_context, "test-fragment", "new-fragment"
        )

        # Check results
        assert str(file1) in results
        assert results[str(file1)] is True
        assert str(file2) in results
        assert results[str(file2)] is False
