"""
Module for parsing fragment references in prompt templates.

This module implements parsing for the syntax:
@fragment-name(arg1, key=value)
"""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple, Union


@dataclass
class FragmentReference:
    """
    Class representing a parsed fragment reference.

    Attributes:
        slug: The fragment slug (e.g., "fragment-name", "$project/fragment")
        args: Positional arguments
        kwargs: Keyword arguments
        start_pos: Start position in the source text
        end_pos: End position in the source text
    """

    slug: str
    args: List[Any]
    kwargs: Dict[str, Any]
    start_pos: int
    end_pos: int

    @property
    def source_text(self) -> str:
        """
        Get the original source text of the reference.
        """
        args_str = ""
        if self.args or self.kwargs:
            parts = []
            # Add positional args
            parts.extend([str(arg) for arg in self.args])
            # Add keyword args
            parts.extend([f"{key}={value}" for key, value in self.kwargs.items()])
            args_str = f"({', '.join(parts)})"

        return f"@{self.slug}{args_str}"


@dataclass
class ParseError:
    """
    Class representing a parse error.

    Attributes:
        message: Error message
        position: Position in the source text where the error occurred
        line: Line number where the error occurred
    """

    message: str
    position: int
    line: Optional[int] = None

    def with_line(self, source_text: str) -> "ParseError":
        """
        Add line number information to the error.

        Args:
            source_text: The source text to calculate the line number from

        Returns:
            ParseError: A new ParseError with line number information
        """
        # Calculate line number based on position
        line = source_text[: self.position].count("\n") + 1
        return ParseError(self.message, self.position, line)


def find_fragment_references(
    template: str,
) -> List[Union[FragmentReference, ParseError]]:
    """
    Find all fragment references in a template.

    Args:
        template: The template text to parse

    Returns:
        List[Union[FragmentReference, ParseError]]: List of fragment references or parse errors
    """
    # Regular expression for fragment reference without arguments
    # @slug-name or @path/to/fragment or @$variable/fragment
    simple_ref_pattern = r"@([a-zA-Z0-9_\-/$]+)"

    # Regular expression for fragment reference with arguments
    # @slug-name(args) or @path/to/fragment(args)
    complex_ref_pattern = r"@([a-zA-Z0-9_\-/$]+)(\(.*?\))"

    results = []  # Find simple references (without arguments)
    for match in re.finditer(simple_ref_pattern, template):
        # Check for escaped references (@@fragment)
        if match.start() > 0 and template[match.start() - 1] == "@":
            continue

        # Check if this is actually a complex reference (has parentheses)
        if match.end() < len(template) and template[match.end()] == "(":
            continue  # Skip and let the complex pattern handle it

        slug = match.group(1)
        reference = FragmentReference(
            slug=slug, args=[], kwargs={}, start_pos=match.start(), end_pos=match.end()
        )
        results.append(reference)  # Find complex references (with arguments)
    for match in re.finditer(complex_ref_pattern, template):
        # Check for escaped references (@@fragment)
        if match.start() > 0 and template[match.start() - 1] == "@":
            continue

        slug = match.group(1)
        args_str = match.group(2)[1:-1]  # Remove the parentheses

        try:
            args, kwargs = parse_arguments(args_str)
            reference = FragmentReference(
                slug=slug,
                args=args,
                kwargs=kwargs,
                start_pos=match.start(),
                end_pos=match.end(),
            )
            results.append(reference)
        except ValueError as e:
            # Create parse error if arguments can't be parsed
            error = ParseError(
                message=str(e),
                position=match.start() + len(slug) + 2,  # Position after '@slug('
            )
            results.append(error)

    # Sort by start position to preserve order
    results.sort(
        key=lambda x: x.start_pos if isinstance(x, FragmentReference) else x.position
    )

    return results


def parse_arguments(args_str: str) -> Tuple[List[Any], Dict[str, Any]]:
    """
    Parse arguments from a string.

    Args:
        args_str: String containing arguments (e.g., 'arg1, key=value')

    Returns:
        Tuple[List[Any], Dict[str, Any]]: Positional arguments and keyword arguments

    Raises:
        ValueError: If the arguments can't be parsed
    """
    if not args_str.strip():
        return [], {}

    args = []
    kwargs = {}

    # State variables for parsing
    in_quotes = False
    quote_char = None
    current_token = ""
    nested_level = 0
    key = None

    i = 0
    while i < len(args_str):
        char = args_str[i]

        # Handle quotes
        if char in ['"', "'"]:
            if in_quotes and char == quote_char and (i == 0 or args_str[i - 1] != "\\"):
                # End of quoted string
                in_quotes = False
                # Don't add the closing quote to the token
            elif not in_quotes and (i == 0 or args_str[i - 1] != "\\"):
                # Start of quoted string
                in_quotes = True
                quote_char = char
                # Don't add the opening quote to the token
            else:
                # Quoted character
                current_token += char
        # Handle nested fragment references
        elif (
            char == "@"
            and i + 1 < len(args_str)
            and args_str[i + 1] not in [" ", ",", ")"]
        ):
            # This could be a nested fragment reference
            current_token += char
            # Only increase nested level for actual nested references, not arguments
            if nested_level == 0 and "@" not in current_token[:-1]:
                # First @ in the token, don't increment nested_level
                pass
            else:
                nested_level += 1
        # Handle nested parentheses in fragment references
        elif char == "(" and nested_level > 0:
            current_token += char
            nested_level += 1
        elif char == ")" and nested_level > 0:
            current_token += char
            nested_level -= 1
        # Handle argument separators and assignments
        elif char == "=" and not in_quotes and nested_level == 0:
            key = current_token.strip()
            current_token = ""
        elif char == "," and not in_quotes and nested_level == 0:
            if key is not None:
                # Add keyword argument
                kwargs[key] = parse_value(current_token.strip())
                key = None
            elif current_token.strip():
                # Add positional argument
                args.append(parse_value(current_token.strip()))
            current_token = ""
        else:
            # Regular character
            current_token += char

        i += 1

    # Handle the last argument
    if key is not None:
        # Last keyword argument
        kwargs[key] = parse_value(current_token.strip())
    elif current_token.strip():
        # Last positional argument
        args.append(parse_value(current_token.strip()))

    # Check for unclosed quotes
    if in_quotes:
        raise ValueError(f"Unclosed quote: {quote_char}")

    # For simple nested fragment references like @fragment, don't check for unclosed parentheses
    # as they might not have parentheses

    return args, kwargs


def parse_value(value: str) -> Any:
    """
    Parse a string value into the appropriate type.

    Args:
        value: String value to parse

    Returns:
        Any: Parsed value (string, number, boolean, or FragmentReference)
    """
    # Check for fragment reference
    if value.startswith("@") and not value.startswith("@@"):
        # This is a nested fragment reference, return as is
        return value

    # Check for string literals
    if (value.startswith('"') and value.endswith('"')) or (
        value.startswith("'") and value.endswith("'")
    ):
        return value[1:-1]

    # Check for boolean literals
    if value.lower() == "true":
        return True
    if value.lower() == "false":
        return False

    # Check for numeric literals
    try:
        if "." in value:
            return float(value)
        else:
            return int(value)
    except ValueError:
        # Not a number, return as string
        return value
