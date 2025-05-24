"""
Frontmatter generation and utilities for prompt files.
"""

import re
from typing import Dict, List, Optional, Set


def generate_frontmatter(
    content: str,
    description: Optional[str] = None,
    categories: Optional[List[str]] = None,
) -> Dict:
    """
    Generate frontmatter for a prompt file based on content and optional parameters.

    This function analyzes the content to identify potential arguments and
    creates a structured frontmatter dictionary.

    Args:
        content: The markdown content of the prompt
        description: Optional description to use in the frontmatter
        categories: Optional list of categories to include

    Returns:
        Dict: The frontmatter as a dictionary
    """
    # Initialize frontmatter with default values
    frontmatter = {}

    # Add description if provided, otherwise generate one from the first line/paragraph
    if description:
        frontmatter["description"] = description
    else:
        frontmatter["description"] = extract_description_from_content(content)

    # Add categories if provided
    if categories and len(categories) > 0:
        frontmatter["categories"] = categories

    # Extract potential arguments
    args = extract_arguments_from_content(content)
    if args:
        frontmatter["args"] = args

    return frontmatter


def extract_description_from_content(content: str) -> str:
    # Process templates inclusions and variables line by line to avoid regex issues with multiple lines
    lines = []
    for line in content.splitlines():
        # Remove all template and variable patterns
        cleaned_line = re.sub(r"\{\{[^}]*\}\}", "", line)
        if cleaned_line.strip():
            lines.append(cleaned_line)

    if not lines:
        return ""

    # Rejoin the lines and handle paragraphs
    cleaned_content = "\n".join(lines).strip()

    # Split into paragraphs and find the first non-empty one
    paragraphs = [p.strip() for p in cleaned_content.split("\n\n")]
    paragraphs = [p for p in paragraphs if p]

    if not paragraphs:
        return ""

    first_paragraph = paragraphs[0]

    # Handle numbered lists by stripping the number prefix
    if re.match(r"^\d+\.\s+", first_paragraph):
        # Split by newline to get only the first line for numbered lists
        first_line = first_paragraph.split("\n")[0]
        first_paragraph = re.sub(r"^\d+\.\s+", "", first_line)

    # Limit to first sentence or first X characters
    potential_desc = first_paragraph.split(".")[0].strip()
    if len(potential_desc) > 80:
        potential_desc = potential_desc[:77] + "…"
    return potential_desc


def extract_arguments_from_content(content: str) -> Optional[Dict[str, Optional[str]]]:
    """
    Extract potential arguments from prompt content.

    Looks for variable patterns like $variable_name or ${variable_name}
    in the content and creates an arguments dictionary.

    Args:
        content: The prompt content to analyze

    Returns:
        Optional[Dict[str, Optional[str]]]: A dictionary of argument names to default values,
                                         or None if no arguments found
    """
    # Define regex patterns for variable detection
    patterns = [
        r"\{\{\s*([a-zA-Z_][a-zA-Z0-9_]*)\s*\}\}",  # {{ variable_name }}
    ]

    # Find all potential argument names
    arg_names: Set[str] = set()
    for pattern in patterns:
        matches = re.findall(pattern, content)
        arg_names.update(matches)

    # Filter out common words and template inclusions
    common_words = {"project", "language", "env"}
    # Exclude template inclusions (patterns starting with @)
    arg_names = {
        name
        for name in arg_names
        if name not in common_words and not name.startswith("@")
    }

    if not arg_names:
        return None

    # Create argument dictionary with None defaults
    args: Dict[str, Optional[str]] = {name: None for name in arg_names}
    return args
