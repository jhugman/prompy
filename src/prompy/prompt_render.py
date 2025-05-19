"""
Module for rendering prompt templates with fragment resolution.
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Set

from .fragment_parser import FragmentReference, ParseError, find_fragment_references
from .prompt_file import PromptContext, PromptFile


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
    A class for rendering prompt templates with fragment resolution.
    """

    def __init__(
        self, prompt_file: PromptFile, arguments: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize a PromptRender instance.

        Args:
            prompt_file: The prompt file to render
            arguments: Optional arguments to apply to the template
        """
        self.prompt_file = prompt_file
        self.arguments = arguments or {}

    def render(self, context: PromptContext) -> str:
        """
        Render the template with fragment resolution.

        Args:
            context: The prompt context for resolving fragments

        Returns:
            str: The rendered template

        Raises:
            ValueError: If a fragment can't be resolved or there's a cycle
        """
        # Track fragments being resolved to detect cycles
        fragment_stack: List[str] = [self.prompt_file.slug]
        return self._render_template(
            self.prompt_file.markdown_template.strip(), context, fragment_stack
        )

    def _render_template(
        self, template: str, context: PromptContext, fragment_stack: List[str]
    ) -> str:
        """
        Recursively render a template by resolving fragment references.

        Args:
            template: The template text to render
            context: The prompt context for resolving fragments
            fragment_stack: Stack of fragments being processed for cycle detection

        Returns:
            str: The rendered template

        Raises:
            ValueError: If a fragment can't be resolved or there's a cycle
        """
        # Find all fragment references in the template
        references = find_fragment_references(template)

        # If no references, return the template as is
        if not references:
            return template

        # Process references in reverse order to avoid position shifts
        for ref in sorted(
            references,
            key=lambda x: x.start_pos if hasattr(x, "start_pos") else x.position,
            reverse=True,
        ):
            if isinstance(ref, ParseError):
                # Convert ParseError to a more specific error with line number
                error = ref.with_line(template)
                raise ValueError(f"Parse error at line {error.line}: {error.message}")

            # Handle fragment reference
            fragment_ref = ref
            fragment_slug = fragment_ref.slug

            # Detect cycles
            if fragment_slug in fragment_stack:
                cycle_path = " -> ".join(
                    [f"@{slug}" for slug in fragment_stack + [fragment_slug]]
                )
                raise ValueError(f"Cyclic reference detected: {cycle_path}")

            try:
                # Load the referenced fragment
                fragment_file = context.load_slug(fragment_slug)

                # Validate fragment arguments
                if fragment_file.arguments:
                    self._validate_arguments(fragment_file, fragment_ref)

                # Create argument dict for the fragment
                fragment_args = {}

                # Apply positional arguments
                if fragment_file.arguments:
                    arg_names = list(fragment_file.arguments.keys())
                    for i, arg_value in enumerate(fragment_ref.args):
                        if i < len(arg_names):
                            fragment_args[arg_names[i]] = arg_value

                # Apply keyword arguments
                fragment_args.update(fragment_ref.kwargs)

                # Apply default arguments for any missing arguments
                if fragment_file.arguments:
                    for arg_name, default_value in fragment_file.arguments.items():
                        if arg_name not in fragment_args and default_value is not None:
                            fragment_args[arg_name] = default_value

                # First, substitute argument variables in the template
                template_with_args = fragment_file.markdown_template.strip()
                for arg_name, arg_value in fragment_args.items():
                    # Replace $arg_name with the argument value
                    template_with_args = template_with_args.replace(
                        f"${arg_name}", str(arg_value)
                    )

                # Create a new PromptRender for the fragment with its arguments
                fragment_render = PromptRender(fragment_file, fragment_args)

                # Recursively render the fragment, adding it to the stack
                rendered_content = fragment_render._render_template(
                    template_with_args, context, fragment_stack + [fragment_slug]
                )

                # Replace the reference with the rendered content
                template = (
                    template[: fragment_ref.start_pos]
                    + rendered_content
                    + template[fragment_ref.end_pos :]
                )

            except FileNotFoundError:
                # Handle missing fragment
                raise ValueError(f"Missing fragment: @{fragment_slug}")

        return template

    def _validate_arguments(
        self, fragment_file: PromptFile, fragment_ref: FragmentReference
    ) -> None:
        """
        Validate that all required arguments are provided.

        Args:
            fragment_file: The prompt file being rendered
            fragment_ref: The fragment reference with arguments

        Raises:
            ValueError: If a required argument is missing
        """
        if not fragment_file.arguments:
            return

        # Check that all required arguments (those without defaults) are provided
        arg_names = list(fragment_file.arguments.keys())
        provided_args = set(fragment_ref.kwargs.keys()).union(
            set(
                arg_names[i] for i in range(min(len(fragment_ref.args), len(arg_names)))
            )
        )

        for arg_name, default_value in fragment_file.arguments.items():
            if default_value is None and arg_name not in provided_args:
                raise ValueError(
                    f"Missing required argument '{arg_name}' for fragment @{fragment_file.slug}"
                )
