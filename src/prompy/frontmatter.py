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
        # Extract first line or paragraph for description
        first_paragraph = content.split("\n\n")[0].strip()
        # Limit to first sentence or first X characters
        potential_desc = first_paragraph.split(".")[0].strip()
        if len(potential_desc) > 80:
            potential_desc = potential_desc[:77] + "..."
        frontmatter["description"] = potential_desc

    # Add categories if provided
    if categories and len(categories) > 0:
        frontmatter["categories"] = categories

    # Extract potential arguments
    args = extract_arguments_from_content(content)
    if args:
        frontmatter["args"] = args

    return frontmatter


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
        r"\$([a-zA-Z_][a-zA-Z0-9_]*)",  # $variable_name
        r"\$\{([a-zA-Z_][a-zA-Z0-9_]*)\}",  # ${variable_name}
    ]

    # Find all potential argument names
    arg_names: Set[str] = set()
    for pattern in patterns:
        matches = re.findall(pattern, content)
        arg_names.update(matches)

    # Filter out common words that aren't likely to be arguments
    common_words = {"project", "language", "env"}
    arg_names = {name for name in arg_names if name not in common_words}

    if not arg_names:
        return None

    # Create argument dictionary with None defaults
    args = {name: None for name in arg_names}
    return args
