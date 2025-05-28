"""
Module for rendering prompt templates with fragment resolution using Jinja2.
"""

import re
import time
from dataclasses import dataclass
from functools import lru_cache
from typing import Any, Dict, List, Match, Optional, Set, Tuple, Union, cast

from jinja2 import Environment, Template, TemplateSyntaxError

from prompy.error_handling import PrompyTemplateSyntaxError

from .diagnostics import FragmentResolutionNode, diagnostics_manager
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
        diagnostics_manager.start_operation("render", slug=self.prompt_file.slug)

        try:
            # Create a root node for the resolution tree
            resolution_root = FragmentResolutionNode(slug=self.prompt_file.slug)
            self.env.globals["_resolution_node"] = resolution_root
            self.env.globals["_resolution_tracking"] = True

            # Add the current prompt file slug to the fragment stack to detect cycles
            self.env.globals["_fragment_stack"] = [self.prompt_file.slug]

            # Store a set of all referenced slugs for diagnostics (used for visualization)
            self.env.globals["_referenced_slugs"] = set()

            # Set the prompt context in the environment
            self.env.globals["_prompy_context"] = context

            # Get the template content
            template_content = self.prompt_file.markdown_template.strip()
            arguments = self.prompt_file.arguments or {}

            diagnostics_manager.add_event(
                "template_loaded",
                slug=self.prompt_file.slug,
                content_length=len(template_content),
            )

            # Get or create template from cache
            start_time = time.time()
            template = self._get_template(template_content)
            template_compile_time = time.time() - start_time

            diagnostics_manager.add_event(
                "template_compiled",
                slug=self.prompt_file.slug,
                duration=template_compile_time,
            )

            # Record arguments in the root node
            resolution_root.arguments = arguments.copy()

            # Render the template with the arguments
            try:
                start_time = time.time()
                result = template.render(arguments)
                render_time = time.time() - start_time

                # Update resolution node with duration
                resolution_root.duration = render_time

                # Record the resolution tree
                diagnostics_manager.record_fragment_resolution(resolution_root)

                diagnostics_manager.add_event(
                    "template_rendered",
                    slug=self.prompt_file.slug,
                    duration=render_time,
                    result_length=len(result),
                    referenced_slugs=list(
                        self.env.globals.get("_referenced_slugs", set())
                    ),
                )

                return result
            except ValueError as e:
                # Mark the error in the resolution node
                resolution_root.error = str(e)
                diagnostics_manager.record_fragment_resolution(resolution_root)

                # Re-raise ValueError errors (like cyclic references)
                raise
            except Exception as e:
                # Mark the error in the resolution node
                resolution_root.error = str(e)
                diagnostics_manager.record_fragment_resolution(resolution_root)

                # Convert other exceptions to a more specific error
                raise ValueError(f"Error rendering template: {str(e)}")
        finally:
            diagnostics_manager.end_operation("render", slug=self.prompt_file.slug)
