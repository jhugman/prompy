"""
Tests for error handling functionality.
"""

import sys

import click
from click.testing import CliRunner

from prompy.error_handling import (
    CyclicReferenceError,
    FragmentNotFoundError,
    MissingArgumentError,
    PrompyError,
    PrompyTemplateSyntaxError,
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
    assert "Can't find prompt fragment '@test/fragment'" in error_str
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
    assert "Cyclic reference detected @a -> @b -> @c -> @a" in error_str
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


class MockClickContext(click.Context):
    """Mock Click Context for testing."""

    def __init__(self, **kwargs):
        # Create a mock command
        cmd = click.Command("test")
        super().__init__(cmd)
        self.obj = kwargs


def test_handle_error(capsys, monkeypatch):
    """Test error handling function."""
    # Create a fake context
    ctx = MockClickContext(debug=False)

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
    ctx = MockClickContext(debug=True)
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
        handle_error(error, ctx, exit_code=1)

    result = runner.invoke(test_command, obj={"debug": False})
    assert result.exit_code == 1
    assert "Error: Test CLI error" in result.output
    assert "Details about the error" in result.output


def test_template_syntax_error():
    """Test TemplateSyntaxError formatting."""
    template_content = "Line 1\nLine 2\nLine {{ invalid }\nLine 4\nLine 5"
    error = PrompyTemplateSyntaxError(
        error_msg="unexpected '}'",
        file_path="/path/to/template.md",
        line_number=3,
        column_number=13,
        template_content=template_content,
    )

    # Check the error message
    error_str = str(error)
    assert "Template syntax error: unexpected '}'" in error_str
    assert "in file: /path/to/template.md" in error_str
    assert "Code context:" in error_str
    assert "Line {{ invalid }" in error_str
    assert "Make sure all curly braces are properly matched" in error_str


def test_enhanced_snippet_formatting():
    """Test enhanced snippet formatting with line numbers and error location."""
    content = "Line 1\nLine 2\nLine 3 with error\nLine 4\nLine 5"
    error = PrompyError(
        message="Test error",
        snippet=content,
        snippet_line=3,
        snippet_column=10,
        snippet_context=2,
    )

    # Get formatted output
    output = error._format_snippet()
    lines = output.splitlines()

    # Check that context is included
    assert len(lines) > 5  # Header + context lines + error line + marker
    assert "Line 1" in output
    assert "Line 2" in output
    assert "Line 3 with error" in output
    assert "Line 4" in output
    assert "Line 5" in output

    # Check error marker
    marker_line = [l for l in lines if "^" in l][0]
    assert "Error occurs here" in marker_line


def test_handle_error_formatting(capsys, monkeypatch):
    """Test enhanced error formatting in handle_error function."""
    # Create a fake context with diagnose mode enabled
    ctx = MockClickContext(debug=False, diagnose=True)

    # Mock sys.exit to not actually exit during tests
    def mock_exit(code):
        pass

    monkeypatch.setattr(sys, "exit", mock_exit)

    # Create an error with all formatting features
    error = PrompyError(
        message="Test error",
        details="Additional details",
        suggestion="Try this to fix it",
        snippet="line 1\nline 2\nline with error\nline 4",
        snippet_line=3,
        snippet_column=10,
        file_path="/test/file.md",
    )

    # Handle the error
    handle_error(error, ctx, exit_code=1)
    captured = capsys.readouterr()

    # Check all formatting elements
    assert "File: /test/file.md" in captured.err
    assert "Error: Test error" in captured.err
    assert "Additional details" in captured.err
    assert "Code context:" in captured.err
    assert "line with error" in captured.err
    assert "Suggestion:" in captured.err
    assert "Try this to fix it" in captured.err
    assert "Diagnostic Information:" in captured.err
    assert "Exception type: PrompyError" in captured.err
