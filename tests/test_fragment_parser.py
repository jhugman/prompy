"""
Tests for fragment reference parsing functionality.
"""

from typing import Any, List, Union

import pytest

from prompy.fragment_parser import (
    FragmentReference,
    ParseError,
    find_fragment_references,
    parse_arguments,
    parse_value,
)


def test_parse_value():
    """Test parsing of values from strings."""
    # Test string literals
    assert parse_value('"hello"') == "hello"
    assert parse_value("'world'") == "world"

    # Test numeric literals
    assert parse_value("123") == 123
    assert parse_value("3.14") == 3.14

    # Test boolean literals
    assert parse_value("true") is True
    assert parse_value("false") is False

    # Test fragment references
    assert parse_value("@fragment") == "@fragment"
    assert parse_value("@path/to/fragment") == "@path/to/fragment"

    # Test plain strings
    assert parse_value("hello") == "hello"


def test_parse_arguments():
    """Test parsing of arguments from strings."""
    # Test empty arguments
    args, kwargs = parse_arguments("")
    assert args == []
    assert kwargs == {}

    # Test positional arguments
    args, kwargs = parse_arguments("1, 'hello', true")
    assert args == [1, "hello", True]
    assert kwargs == {}

    # Test keyword arguments
    args, kwargs = parse_arguments("name='John', age=30, active=true")
    assert args == []
    assert kwargs == {"name": "John", "age": 30, "active": True}

    # Test mixed arguments
    args, kwargs = parse_arguments("'hello', 123, name='John', active=true")
    assert args == ["hello", 123]
    assert kwargs == {"name": "John", "active": True}

    # Test simple nested fragment references
    args, kwargs = parse_arguments("@fragment, key=@other/fragment")
    assert args == ["@fragment"]
    assert kwargs == {"key": "@other/fragment"}


def test_parse_arguments_errors():
    """Test error handling in argument parsing."""
    # Test unclosed quotes
    with pytest.raises(ValueError, match="Unclosed quote"):
        parse_arguments("'hello")


def test_find_simple_fragment_references():
    """Test finding simple fragment references in a template."""
    template = """
This is a template with @fragment references.
It includes @path/to/fragment and @$project/fragment.
"""

    refs = find_fragment_references(template)

    assert len(refs) == 3
    assert isinstance(refs[0], FragmentReference)
    assert refs[0].slug == "fragment"
    assert refs[0].args == []
    assert refs[0].kwargs == {}

    assert refs[1].slug == "path/to/fragment"
    assert refs[2].slug == "$project/fragment"


def test_find_complex_fragment_references():
    """Test finding fragment references with arguments in a template."""
    template = """
This template has @fragment(arg1, key=value) with arguments.
It also has @path/to/fragment('string', 123, active=true).
"""

    refs = find_fragment_references(template)

    assert len(refs) == 2
    assert isinstance(refs[0], FragmentReference)
    assert refs[0].slug == "fragment"
    assert refs[0].args == ["arg1"]
    assert refs[0].kwargs == {"key": "value"}

    assert refs[1].slug == "path/to/fragment"
    assert refs[1].args == ["string", 123]
    assert refs[1].kwargs == {"active": True}


def test_find_nested_fragment_references():
    """Test finding nested fragment references in a template."""
    template = """
This template has a complex reference like @outer(arg="value", key=123).
"""

    refs = find_fragment_references(template)

    assert len(refs) == 1
    assert isinstance(refs[0], FragmentReference)
    assert refs[0].slug == "outer"
    assert refs[0].kwargs == {"key": 123, "arg": "value"}


def test_escaped_fragment_references():
    """Test that escaped fragment references are not parsed."""
    template = """
This template has an escaped reference @@fragment that should not be parsed.
But @fragment should be parsed.
"""

    refs = find_fragment_references(template)

    assert len(refs) == 1
    assert isinstance(refs[0], FragmentReference)
    assert refs[0].slug == "fragment"


def test_error_handling():
    """Test error handling in fragment reference parsing."""
    template = """
This template has an @invalid-fragment(unclosed"string') that should cause an error.
But @valid should still be parsed.
"""

    results = find_fragment_references(template)

    assert len(results) == 2
    assert isinstance(results[0], ParseError)
    assert "Unclosed quote" in results[0].message

    assert isinstance(results[1], FragmentReference)
    assert results[1].slug == "valid"


def test_line_number_calculation():
    """Test calculation of line numbers for parse errors."""
    template = """Line 1
Line 2
Line 3 with @invalid(error" here)
Line 4 with @valid
"""

    results = find_fragment_references(template)
    error = next(r for r in results if isinstance(r, ParseError))

    error_with_line = error.with_line(template)
    assert error_with_line.line == 3
