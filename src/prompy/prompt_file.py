"""
Module for handling prompt files and their representation.
"""

import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import yaml


# Configure PyYAML to use literal style for strings containing special characters
def _literal_str_representer(dumper, data):
    # Use literal style for strings with newlines, special chars or if they
    # end with ellipsis
    if "\n" in data or "..." in data:
        return dumper.represent_scalar("tag:yaml.org,2002:str", data, style="|")
    return dumper.represent_scalar("tag:yaml.org,2002:str", data)


# Register the custom string representer
yaml.add_representer(str, _literal_str_representer)


class PromptFile:
    """
    A class representing a file on disk, as edited by users.

    Prompt files have front matter, which is in YAML.
    The markdown content can contain fragment references.
    """

    def __init__(
        self,
        *,
        slug: str = "",
        description: Optional[str] = None,
        categories: Optional[List[str]] = None,
        arguments: Optional[Dict[str, Optional[str]]] = None,
        frontmatter: str = "",
        markdown_template: str = "",
    ) -> None:
        """
        Initialize a PromptFile.

        Args:
            slug: The slug identifier for the prompt file
            description: Optional description of the prompt
            categories: Optional list of categories for the prompt
            arguments: Optional dictionary of argument names and default values
            frontmatter: Raw frontmatter string
            markdown_template: The markdown content template
        """
        self.slug: str = slug
        self.description: Optional[str] = description
        self.categories: Optional[List[str]] = categories
        self.arguments: Optional[Dict[str, Optional[str]]] = arguments
        self.frontmatter: str = frontmatter
        self.markdown_template: str = markdown_template

    @staticmethod
    def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str, str]:
        """
        Parse YAML frontmatter from a string.

        Args:
            content (str): The content to parse

        Returns:
            Tuple[Dict[str, Any], str, str]: Parsed data, raw frontmatter
                string, and content string
        """
        # Check for frontmatter (content between --- markers)
        frontmatter_match = re.match(
            r"^---\s*\n(.*?)\n---\s*\n(.*)", content, re.DOTALL
        )
        if not frontmatter_match:
            # No frontmatter, return empty dict and the original content
            return {}, "", content

        # Extract frontmatter and markdown content
        frontmatter_text = frontmatter_match.group(1)
        markdown_content = frontmatter_match.group(2)

        # Parse frontmatter YAML
        try:
            frontmatter_data = yaml.safe_load(frontmatter_text)
            if frontmatter_data is None:
                # Empty frontmatter
                frontmatter_data = {}
        except yaml.YAMLError:
            # Invalid YAML, return empty dict
            frontmatter_data = {}

        return frontmatter_data, frontmatter_text, markdown_content

    @classmethod
    def load(cls, path: Path, slug: Optional[str] = None) -> "PromptFile":
        """
        Load a prompt file from a path.

        Args:
            path (Path): The path to the prompt file

        Returns:
            PromptFile: The loaded prompt file

        Raises:
            FileNotFoundError: If the file does not exist
            ValueError: If the file has invalid frontmatter
        """
        if not path.exists():
            raise FileNotFoundError(f"Prompt file not found: {path}")

        # Read file content
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        # Default values
        prompt_file = cls(
            slug=slug or path.stem,  # Use filename as default slug
            markdown_template=content,
        )

        # Parse frontmatter
        frontmatter_data, frontmatter_text, markdown_content = cls.parse_frontmatter(
            content
        )

        # Store original frontmatter text
        prompt_file.frontmatter = frontmatter_text
        prompt_file.markdown_template = markdown_content

        # Extract specific fields
        prompt_file.description = frontmatter_data.get("description")
        prompt_file.categories = frontmatter_data.get("categories")

        # Handle arguments
        args = frontmatter_data.get("args", frontmatter_data.get("argumentss", {}))
        if args:
            prompt_file.arguments = {}
            for key, value in args.items():
                prompt_file.arguments[key] = value

        return prompt_file

    @property
    def rendered_frontmatter(self) -> str:
        """
        Generate YAML frontmatter based on the prompt file attributes.

        Returns:
            str: YAML frontmatter for the prompt file
        """
        # Start with the frontmatter data as a dict
        frontmatter_data = {}

        # Add key attributes
        if self.description:
            frontmatter_data["description"] = self.description

        if self.categories:
            frontmatter_data["categories"] = self.categories

        if self.arguments:
            frontmatter_data["args"] = self.arguments

        # Convert to YAML with improved readability
        return yaml.dump(
            frontmatter_data,
            sort_keys=False,
            default_style=None,
            default_flow_style=False,
            width=80,
            allow_unicode=True,
        ).strip()

    def generate_frontmatter(self) -> str:
        """
        Generate YAML frontmatter string based on the prompt file attributes.

        This is an alias for rendered_frontmatter to support the CLI command.

        Returns:
            str: YAML frontmatter for the prompt file
        """
        return self.rendered_frontmatter

    def save(self, path: Path) -> None:
        """
        Save the prompt file to a path.

        Args:
            path (Path): The path to save the file to

        Raises:
            IOError: If the file cannot be written
        """
        # Ensure the parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Prepare content with frontmatter
        content = f"---\n{self.frontmatter}\n---\n\n{self.markdown_template}"

        # Write to file
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def is_fragment(self) -> bool:
        """
        Returns True if the prompt file can be used as a fragment.

        Returns:
            bool: True if this is a valid fragment
        """
        # A fragment is valid if it has arguments and all required arguments
        # have defaults, or if it has no arguments
        if self.arguments is None:
            return False

        # Check if all required arguments have default values
        for value in self.arguments.values():
            if value is None:  # Required argument without default
                return True

        return False
