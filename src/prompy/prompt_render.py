"""
Module for rendering prompt templates with fragment resolution using Jinja2.
"""

import re
from dataclasses import dataclass
from functools import lru_cache
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
        self._env: Optional[Environment] = None
        self._template_cache: Dict[str, Template] = {}

    @property
    def env(self) -> Environment:
        """
        Get or create the Jinja2 environment.

        Returns:
            Environment: The configured Jinja2 environment
        """
        if self._env is None:
            self._env = create_jinja_environment(self._get_context())
        return self._env

    @lru_cache(maxsize=128)
    def _get_context(self) -> PromptContext:
        """
        Get or create the prompt context. Results are cached.

        Returns:
            PromptContext: The prompt context for resolving fragments
        """
        return PromptContext()

    def _get_template(self, content: str) -> Template:
        """
        Get or create a template instance from the cache.

        Args:
            content: The template content

        Returns:
            Template: The compiled template
        """
        template = self._template_cache.get(content)
        if template is None:
            try:
                template = self.env.from_string(content)
                self._template_cache[content] = template
            except TemplateSyntaxError as e:
                # Convert Jinja2 syntax error to a more specific error
                raise ValueError(
                    f"Template syntax error at line {e.lineno}: {e.message}"
                )
        return template

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
        # Add the current prompt file slug to the fragment stack to detect cycles
        self.env.globals["_fragment_stack"] = [self.prompt_file.slug]

        # Set the prompt context in the environment
        self.env.globals["_prompy_context"] = context

        # Get the template content
        template_content = self.prompt_file.markdown_template.strip()
        arguments = self.prompt_file.arguments or {}

        # Get or create template from cache
        template = self._get_template(template_content)

        # Render the template with the arguments
        try:
            return template.render(arguments)
        except ValueError as e:
            # Re-raise ValueError errors (like cyclic references)
            raise
        except Exception as e:
            # Convert other exceptions to a more specific error
            raise ValueError(f"Error rendering template: {str(e)}")
