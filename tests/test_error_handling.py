"""
Tests for error handling functionality.
"""

import logging
import sys

import click
import pytest
from click.testing import CliRunner

from prompy.error_handling import (
    CyclicReferenceError,
    FragmentNotFoundError,
    MissingArgumentError,
    PrompyError,
    handle_error,
)


def test_prompy_error_basic():
    """Test basic PrompyError functionality."""
    # Test with just a message
    error = PrompyError("Error message")
    assert str(error) == "Error message"
    assert error.message == "Error message"
    assert error.details is None

    # Test with message and details
    error = PrompyError("Error message", "Error details")
    assert str(error) == "Error message\nError details"
    assert error.message == "Error message"
    assert error.details == "Error details"


def test_fragment_not_found_error():
    """Test FragmentNotFoundError formatting."""
    error = FragmentNotFoundError(
        fragment_slug="test/fragment",
        search_paths=["/path/to/fragment1.md", "/path/to/fragment2.md"],
        file_path="/path/to/source.md",
        line_number=42,
    )

    # Check the error message
    error_str = str(error)
    assert "Missing prompt fragment '@test/fragment'" in error_str
    assert "in file: /path/to/source.md" in error_str
    assert "at line: 42" in error_str
    assert "searched paths:" in error_str
    assert "- /path/to/fragment1.md" in error_str
    assert "- /path/to/fragment2.md" in error_str


def test_cyclic_reference_error():
    """Test CyclicReferenceError formatting."""
    error = CyclicReferenceError(
        cycle_path=["a", "b", "c", "a"],
        start_file="/path/to/fragment.md",
        line_number=10,
    )

    # Check the error message
    error_str = str(error)
    assert "Cyclic reference detected '@a' -> '@b' -> '@c' -> '@a'" in error_str
    assert "in file: /path/to/fragment.md" in error_str
    assert "starting at line: 10" in error_str
    assert "- a" in error_str
    assert "- b" in error_str
    assert "- c" in error_str


def test_missing_argument_error():
    """Test MissingArgumentError formatting."""
    error = MissingArgumentError(
        fragment_slug="test/fragment",
        argument_name="required_arg",
        file_path="/path/to/source.md",
        line_number=42,
    )

    # Check the error message
    error_str = str(error)
    assert (
        "Missing required argument 'required_arg' for fragment '@test/fragment'"
        in error_str
    )
    assert "in file: /path/to/source.md" in error_str
    assert "at line: 42" in error_str


class MockContext:
    def __init__(self, debug=False):
        self.obj = {"debug": debug}


def test_handle_error(capsys, monkeypatch):
    """Test error handling function."""
    # Create a fake context
    ctx = MockContext(debug=False)

    # Mock sys.exit to not actually exit during tests
    def mock_exit(code):
        pass

    monkeypatch.setattr(sys, "exit", mock_exit)

    # Test handling a basic error
    handle_error(PrompyError("Test error"), ctx)
    captured = capsys.readouterr()
    assert "Error: Test error" in captured.err

    # Test handling error with details
    handle_error(PrompyError("Test error", "With details"), ctx)
    captured = capsys.readouterr()
    assert "Error: Test error" in captured.err
    assert "With details" in captured.err

    # Test with debug mode enabled
    ctx = MockContext(debug=True)
    handle_error(PrompyError("Debug error"), ctx)
    captured = capsys.readouterr()
    assert "Error: Debug error" in captured.err


def test_error_handling_in_cli():
    """Test error handling integration with CLI"""
    runner = CliRunner()

    @click.command()
    @click.pass_context
    def test_command(ctx):
        from prompy.error_handling import PrompyError, handle_error

        error = PrompyError("Test CLI error", "Details about the error")
        handle_error(error, ctx, exit_code=None)  # Don't exit in test

    result = runner.invoke(test_command, obj={"debug": False})
    assert "Error: Test CLI error" in result.output
    assert "Details about the error" in result.output
