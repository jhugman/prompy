"""
Module for Jinja2 extension to support Prompy's fragment inclusion syntax.
"""

import re
from typing import Any, Dict, List, Optional, Pattern, Set, Tuple, Union, cast

from jinja2 import Environment, Template, TemplateSyntaxError
from jinja2.ext import Extension
from jinja2.lexer import Token, TokenStream
from jinja2.loaders import BaseLoader
from jinja2.nodes import Call, Const, Node
from jinja2.parser import Parser

from .prompt_file import PromptContext, PromptFile


def preprocess_template(source: str) -> str:
    """
    Preprocess a template string to transform @slug references.

    This replaces {{ @slug }} with {{ include_fragment("slug") }}
    and {{ @slug(args) }} with {{ include_fragment("slug", args) }}

    Args:
        source: The source template

    Returns:
        The preprocessed template
    """  # Find all {{ ... }} expressions first
    expr_pattern = r"{{(.*?)}}"

    def process_expression(match: re.Match) -> str:
        expr = match.group(1)

        # Find position of match in source to determine indentation
        match_start = match.start()
        line_start = source.rfind("\n", 0, match_start) + 1
        indent = source[line_start:match_start]

        # Clean indentation (only keep whitespace)
        indent_prefix = "".join(c for c in indent if c in " \t")

        # Store the indentation as a global for this fragment reference
        # Detect if this expression contains a fragment reference
        has_fragment = re.search(r"@[a-zA-Z0-9_\-/$]+", expr)

        # Replace @slug references in this expression
        processed = re.sub(
            r"@([a-zA-Z0-9_\-/$]+)(\(.*?\))?",
            lambda m: (
                f'include_fragment("{m.group(1)}", indent="{indent_prefix}")'
                if not m.group(2)
                else f'include_fragment("{m.group(1)}", {m.group(2)[1:-1]}, indent="{indent_prefix}")'
            ),
            expr,
        )
        return f"{{{{{processed}}}}}"

    processed_source = re.sub(expr_pattern, process_expression, source, flags=re.DOTALL)

    return processed_source


class PrompyExtension(Extension):
    """
    A Jinja2 extension that adds support for @slug references in templates.

    This extension processes expressions like {{ @fragments/common-header(project="MyProject") }}
    by transforming them into a function call that loads and renders the referenced fragment.
    """

    # Define the tags this extension is interested in
    tags = set()  # We're not adding custom tags, just modifying expression behavior

    # Extension identifier (required for extensions)
    identifier = "prompy.slug"

    def __init__(self, environment: Environment) -> None:
        """Initialize the extension."""
        super().__init__(environment)

        # Register our include_fragment function as a global function
        environment.globals["include_fragment"] = self.include_fragment

    def preprocess(self, source, name, filename=None):
        """
        Preprocess the template source before it gets parsed.
        This is the proper extension hook for preprocessing.
        """
        return preprocess_template(source)

    def include_fragment(self, slug: str, *args: Any, **kwargs: Any) -> str:
        """
        Include a fragment by slug.

        This is registered as a global function and called when @slug references are processed.

        Args:
            slug: The fragment slug
            *args: Positional arguments for the fragment
            **kwargs: Keyword arguments for the fragment

        Returns:
            The rendered fragment content
        """
        # In Jinja2, the context is passed through the render call chain
        # so we need to access it from kwargs or use a thread-local variable

        # Extract indent from kwargs if present
        indent_prefix = kwargs.pop("indent", "")

        # For our implementation, we'll use globals in the environment
        context = self.environment.globals.get("_prompy_context")
        if not context:
            raise ValueError("Prompy context not available in Jinja2 environment")

        # Get fragment stack from globals to track fragment inclusion
        fragment_stack = self.environment.globals.get("_fragment_stack", [])

        # Detect cycles
        if slug in fragment_stack:
            cycle_path = " -> ".join([f"@{s}" for s in fragment_stack + [slug]])
            raise ValueError(f"Cyclic reference detected: {cycle_path}")

        try:
            # Load the referenced fragment
            fragment_file = context.load_slug(slug)

            # Update the fragment stack to track the inclusion
            new_stack = fragment_stack + [slug]

            # Save the original stack
            original_stack = self.environment.globals.get("_fragment_stack", [])

            # Update the stack in the environment
            self.environment.globals["_fragment_stack"] = new_stack

            # Create a new template with the fragment content
            # The template source will be automatically preprocessed by our extension
            fragment_template = self.environment.from_string(
                fragment_file.markdown_template
            )

            # Create variable context for rendering
            vars_context = {}

            # Add fragment arguments to the context
            vars_context.update(kwargs)

            # Apply positional arguments if fragment has argument definitions
            if fragment_file.arguments:
                arg_names = list(fragment_file.arguments.keys())
                for i, arg_value in enumerate(args):
                    if i < len(arg_names):
                        vars_context[arg_names[i]] = arg_value

            # Apply default arguments for any missing arguments
            if fragment_file.arguments:
                for arg_name, default_value in fragment_file.arguments.items():
                    if arg_name not in vars_context and default_value is not None:
                        vars_context[arg_name] = default_value
                    elif arg_name not in vars_context and default_value is None:
                        # Required argument is missing
                        raise ValueError(
                            f"Missing required argument '{arg_name}' for fragment @{slug}"
                        )

            # Render the fragment with the context
            result = fragment_template.render(**vars_context)

            # Apply indentation if needed and if there's content with multiple lines
            if indent_prefix and "\n" in result:
                # Use Jinja's built-in indent filter
                # This indents all lines after the first line
                result = self.environment.filters["indent"](
                    result, first=False, width=len(indent_prefix)
                )

            # Restore the original stack
            self.environment.globals["_fragment_stack"] = original_stack

            return result

        except FileNotFoundError:
            # Handle missing fragment
            raise ValueError(f"Missing fragment: @{slug}")
        except Exception as e:
            # Ensure we restore the stack even if there's an error
            self.environment.globals["_fragment_stack"] = fragment_stack
            raise


def create_jinja_environment(context: PromptContext) -> Environment:
    """
    Create a Jinja2 environment configured for Prompy.

    Args:
        context: The Prompy context for resolving fragments

    Returns:
        Environment: A configured Jinja2 environment
    """
    env = Environment(
        extensions=[PrompyExtension],
        autoescape=False,  # No HTML escaping for markdown
        trim_blocks=True,
        lstrip_blocks=True,
    )

    # Add the Prompy context to the global environment
    env.globals["_prompy_context"] = context
    env.globals["_fragment_stack"] = []

    return env
