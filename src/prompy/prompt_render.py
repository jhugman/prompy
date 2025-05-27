"""
Module for rendering prompt templates with fragment resolution using Jinja2.
"""

import re
from dataclasses import dataclass
from typing import Any, Dict, List, Match, Optional, Set, Tuple, Union, cast

from jinja2 import Environment, Template, TemplateSyntaxError

from .jinja_extension import create_jinja_environment
from .prompt_context import PromptContext
from .prompt_file import PromptFile


@dataclass
class RenderError:
    """
    Class representing an error during rendering.

    Attributes:
        message: Error message
        position: Position in the source text where the error occurred
        line: Line number where the error occurred
        slug: The slug of the prompt file being rendered when the error occurred
    """

    message: str
    position: int
    line: Optional[int] = None
    slug: Optional[str] = None


class PromptRender:
    """
    A class for rendering prompt templates with fragment resolution using Jinja2.
    """

    def __init__(self, prompt_file: PromptFile):
        """
        Initialize a PromptRender instance.

        Args:
            prompt_file: The prompt file to render
        """
        self.prompt_file = prompt_file

    def render(self, context: PromptContext) -> str:
        """
        Render the template with fragment resolution using Jinja2.

        Args:
            context: The prompt context for resolving fragments

        Returns:
            str: The rendered template

        Raises:
            ValueError: If a fragment can't be resolved or there's a cycle
        """
        # Create a Jinja2 environment with our custom extension
        env = create_jinja_environment(context)

        # Add the current prompt file slug to the fragment stack to detect cycles
        env.globals["_fragment_stack"] = [self.prompt_file.slug]

        # Get the template content
        template_content = self.prompt_file.markdown_template.strip()
        arguments = self.prompt_file.arguments or {}
        # Create a Jinja2 template from the processed template content
        try:
            template = env.from_string(template_content)
        except TemplateSyntaxError as e:
            # Convert Jinja2 syntax error to a more specific error
            raise ValueError(f"Template syntax error at line {e.lineno}: {e.message}")

        # Render the template with the arguments
        try:
            return template.render(arguments)
        except ValueError as e:
            # Re-raise ValueError errors (like cyclic references)
            raise
        except Exception as e:
            # Convert other exceptions to a more specific error
            raise ValueError(f"Error rendering template: {str(e)}")
