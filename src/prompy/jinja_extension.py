"""
Module for Jinja2 extension to support Prompy's fragment inclusion syntax.
"""

import re
from typing import Any, cast

from jinja2 import Environment
from jinja2.ext import Extension

from .prompt_context import PromptContext


def preprocess_template(source: str) -> str:
    """
    Preprocess a template string to transform @slug references.

    This replaces {{ @slug }} with {{ include_fragment("slug") }}
    and {{ @slug(args) }} with {{ include_fragment("slug", args) }}

    Args:
        source: The source template

    Returns:
        The preprocessed template
    """
    # Find all {{ ... }} expressions first
    expr_pattern = r"{{(.*?)}}"

    def process_nested_args(args_text: str) -> str:
        """
        Process arguments that might contain nested references.

        Args:
            args_text: The arguments text to process

        Returns:
            The processed arguments with nested references transformed
        """
        # Pattern for prompt references in arguments that handles nested parentheses
        ref_pattern = r"@([a-zA-Z0-9_\-/=]+)(?:\(([^()]*(?:\([^()]*\)[^()]*)*)\))?"

        # Simple pattern for name=value arguments
        arg_pattern = r"([a-zA-Z0-9_]+)\s*=\s*(@[a-zA-Z0-9_\-/=]+(?:\([^()]*(?:\([^()]*\)[^()]*)*\))?)"

        # First, replace any @ref in argument values
        def replace_arg_refs(match):
            arg_name = match.group(1)
            ref_value = match.group(2)

            # Process the reference value
            processed_value = re.sub(ref_pattern, replace_ref, ref_value)
            return f"{arg_name}={processed_value}"

        # Replace @refs with include_fragment calls
        def replace_ref(match):
            slug = match.group(1)
            args = match.group(2)

            if args:
                # Process nested args recursively
                processed_args = process_nested_args(args)
                return f'include_fragment("{slug}", {processed_args}, indent="")'
            else:
                return f'include_fragment("{slug}", indent="")'

        # First process any name=@ref arguments
        args_text = re.sub(arg_pattern, replace_arg_refs, args_text)

        # Then process any standalone @refs
        return re.sub(ref_pattern, replace_ref, args_text)

    def process_expression(match: re.Match) -> str:
        expr = match.group(1).strip()
        match_start = match.start()
        line_start = source.rfind("\n", 0, match_start) + 1
        line_prefix = source[line_start:match_start]

        # Determine if this expression is the first non-whitespace on a line
        is_first_on_line = line_prefix.strip() == ""
        indent_prefix = (
            "".join(c for c in line_prefix if c in " \t") if is_first_on_line else ""
        )

        # Pattern to find @refs with optional argument list that can handle nested parentheses
        ref_pattern = r"@([a-zA-Z0-9_\-/=]+)(?:\(([^()]*(?:\([^()]*\)[^()]*)*)\))?"

        # Process the expression to replace @refs
        processed = expr

        for match in re.finditer(ref_pattern, expr):
            ref_start = match.start()
            ref_text = match.group(0)
            slug = match.group(1)
            args_text = match.group(2)

            # Determine if this reference is part of an argument value
            # by looking for an equals sign before the reference without parenthesis balance
            is_arg_value = False
            eq_pos = expr[:ref_start].rfind("=")
            if eq_pos >= 0:
                # Count parentheses between = and the reference
                open_parens = expr[eq_pos:ref_start].count("(")
                close_parens = expr[eq_pos:ref_start].count(")")
                if open_parens > close_parens:
                    is_arg_value = True

            # Use empty indent for arg values, otherwise use indentation from line
            ref_indent = "" if is_arg_value else indent_prefix

            if args_text:
                # Process any nested references in the arguments
                processed_args = process_nested_args(args_text)
                replacement = f'include_fragment("{slug}", {processed_args}, indent="{ref_indent}")'
            else:
                replacement = f'include_fragment("{slug}", indent="{ref_indent}")'

            # Replace just this reference in the processed expression
            processed = (
                processed[: match.start()] + replacement + processed[match.end() :]
            )

        return f"{{{{ {processed} }}}}"

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

    def include_fragment(self, __slug: str, *args: Any, **kwargs: Any) -> str:
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
        if __slug in fragment_stack:
            cycle_path = " -> ".join([f"@{s}" for s in fragment_stack + [__slug]])
            raise ValueError(f"Cyclic reference detected: {cycle_path}")

        try:
            # Load the referenced fragment
            fragment_file = context.load_slug(__slug)

            # Update the fragment stack to track the inclusion
            new_stack = fragment_stack + [__slug]

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

            if fragment_file.arguments:
                # Apply positional arguments if fragment has argument definitions
                arg_names = list(fragment_file.arguments.keys())
                for i, arg_value in enumerate(args):
                    if i < len(arg_names):
                        vars_context[arg_names[i]] = arg_value

                # Apply default arguments for any missing arguments
                for arg_name, default_value in fragment_file.arguments.items():
                    if arg_name not in vars_context and default_value is not None:
                        vars_context[arg_name] = default_value
                    elif arg_name not in vars_context and default_value is None:
                        # Required argument is missing
                        raise ValueError(
                            f"Missing required argument '{arg_name}' for fragment @{__slug}"
                        )

            # Render the fragment with the context
            result = fragment_template.render(vars_context)

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
            raise ValueError(f"Missing fragment: @{__slug}")
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
