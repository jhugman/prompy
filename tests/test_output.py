"""
Tests for the output module.
"""

import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from prompy.output import (
    output_content,
    output_to_clipboard,
    output_to_file,
    output_to_stdout,
)


def test_output_to_stdout():
    """Test outputting content to stdout."""
    test_content = "Test content to stdout"

    # Mock both isatty and stdout
    with (
        patch("sys.stdout.isatty", return_value=False),
        patch("sys.stdout.write") as mock_write,
        patch("sys.stdout.flush") as mock_flush,
    ):
        result = output_to_stdout(test_content)

        assert result is True
        mock_write.assert_any_call(test_content)
        mock_flush.assert_called_once()


def test_output_to_stdout_with_error():
    """Test handling errors when outputting to stdout."""
    with patch("sys.stdout.write", side_effect=IOError("Mock error")):
        result = output_to_stdout("Test content")

        assert result is False


def test_output_to_clipboard():
    """Test copying content to clipboard."""
    test_content = "Test content to clipboard"

    with patch("pyperclip.copy") as mock_copy:
        result = output_to_clipboard(test_content)

        assert result is True
        mock_copy.assert_called_once_with(test_content)


def test_output_to_clipboard_with_error():
    """Test handling errors when copying to clipboard."""
    with patch("pyperclip.copy", side_effect=Exception("Mock error")):
        result = output_to_clipboard("Test content")

        assert result is False


def test_output_to_file(tmp_path):
    """Test writing content to a file."""
    test_content = "Test content to file"
    test_file = tmp_path / "test_output.txt"

    result = output_to_file(test_content, str(test_file))

    assert result is True
    assert test_file.exists()

    with open(test_file, "r", encoding="utf-8") as f:
        content = f.read()
        assert content == test_content


def test_output_to_file_with_error():
    """Test handling errors when writing to a file."""
    with patch("builtins.open", side_effect=IOError("Mock error")):
        result = output_to_file("Test content", "/some/file.txt")

        assert result is False


def test_output_content_clipboard_fallback():
    """Test fallback to stdout when clipboard fails."""
    test_content = "Test content"

    with (
        patch(
            "prompy.output.output_to_clipboard", return_value=False
        ) as mock_clipboard,
        patch("prompy.output.output_to_stdout", return_value=True) as mock_stdout,
    ):
        result = output_content(test_content, clipboard=True)

        assert result is True
        mock_clipboard.assert_called_once_with(test_content)
        mock_stdout.assert_called_once_with(test_content)
