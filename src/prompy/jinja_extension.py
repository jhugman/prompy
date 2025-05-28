"""
Module for Jinja2 extension to support Prompy's fragment inclusion syntax.
"""

import re
from typing import Any, cast

from jinja2 import Environment, Template
from jinja2.ext import Extension

from .prompt_context import PromptContext

# Pre-compile regular expressions for better performance
EXPR_PATTERN = re.compile(r"{{(.*?)}}", re.DOTALL)
REF_PATTERN = re.compile(r"@([a-zA-Z0-9_\-/=]+)(?:\(([^()]*(?:\([^()]*\)[^()]*)*)\))?")
ARG_PATTERN = re.compile(
    r"([a-zA-Z0-9_]+)\s*=\s*(@[a-zA-Z0-9_\-/=]+(?:\([^()]*(?:\([^()]*\)[^()]*)*\))?)"
)


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

    def process_nested_args(args_text: str) -> str:
        """
        Process arguments that might contain nested references.

        Args:
            args_text: The arguments text to process

        Returns:
            The processed arguments with nested references transformed
        """

        # Process @refs in argument values
        def replace_arg_refs(match):
            arg_name = match.group(1)
            ref_value = match.group(2)

            # Process the reference value
            processed_value = REF_PATTERN.sub(replace_ref, ref_value)
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
        args_text = ARG_PATTERN.sub(replace_arg_refs, args_text)

        # Then process any standalone @refs
        return REF_PATTERN.sub(replace_ref, args_text)

    def process_expression(match: re.Match) -> str:
        """
        Process a Jinja2 expression, handling any @ref references within it.

        Args:
            match: The regex match object containing the expression

        Returns:
            str: The processed expression with @refs transformed to include_fragment calls
        """
        expr = match.group(1).strip()
        match_start = match.start()
        indent_prefix = _get_line_indent(source, match_start)

        # Process the expression to replace @refs
        processed = expr

        for match in REF_PATTERN.finditer(expr):
            processed = _process_reference(match, expr, processed, indent_prefix)

        return f"{{{{ {processed} }}}}"

    def _get_line_indent(source: str, match_start: int) -> str:
        """
        Get the indentation prefix for the line containing a match.

        Args:
            source: The source text
            match_start: The start position of the match

        Returns:
            str: The indentation prefix or empty string if not first on line
        """
        line_start = source.rfind("\n", 0, match_start) + 1
        line_prefix = source[line_start:match_start]

        # Determine if this expression is the first non-whitespace on a line
        is_first_on_line = line_prefix.strip() == ""
        return "".join(c for c in line_prefix if c in " \t") if is_first_on_line else ""

    def _process_reference(
        match: re.Match, expr: str, processed: str, indent_prefix: str
    ) -> str:
        """
        Process a single @ref reference within an expression.

        Args:
            match: The regex match for the reference
            expr: The full expression text
            processed: The partially processed text
            indent_prefix: The indentation prefix to use

        Returns:
            str: The expression with the reference transformed
        """
        # Find the actual reference in the processed text
        # This ensures we replace at the correct position after earlier replacements
        ref_expr = match.group(0)
        ref_pos = processed.find(ref_expr)
        if ref_pos == -1:
            # Reference has already been transformed
            return processed

        slug = match.group(1)
        args_text = match.group(2)

        # Determine if this reference is an argument value by checking for unbalanced parentheses
        is_arg_value = _is_arg_value(expr, match.start())

        # Use empty indent for arg values, otherwise use indentation from line
        ref_indent = "" if is_arg_value else indent_prefix

        if args_text:
            # Process any nested references in the arguments
            processed_args = process_nested_args(args_text)
            replacement = (
                f'include_fragment("{slug}", {processed_args}, indent="{ref_indent}")'
            )
        else:
            replacement = f'include_fragment("{slug}", indent="{ref_indent}")'

        # Replace just this reference in the processed expression
        return processed[:ref_pos] + replacement + processed[ref_pos + len(ref_expr) :]

    def _is_arg_value(expr: str, ref_start: int) -> bool:
        """
        Determine if a reference is part of an argument value.

        Args:
            expr: The full expression text
            ref_start: The start position of the reference

        Returns:
            bool: True if the reference is part of an argument value
        """
        eq_pos = expr[:ref_start].rfind("=")
        if eq_pos >= 0:
            # Count parentheses between = and the reference
            open_parens = expr[eq_pos:ref_start].count("(")
            close_parens = expr[eq_pos:ref_start].count(")")
            return open_parens > close_parens
        return False

    processed_source = re.sub(EXPR_PATTERN, process_expression, source)

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
        """Initialize the extension with template caching."""
        super().__init__(environment)

        # Register our include_fragment function as a global function
        environment.globals["include_fragment"] = self.include_fragment

        # Initialize template cache for better performance
        # Use WeakKeyDictionary to allow garbage collection of unused templates
        from weakref import WeakKeyDictionary

        self._template_cache = WeakKeyDictionary()

    def _get_cached_template(self, fragment_file) -> Template:
        """
        Get a cached template instance or create a new one.

        Args:
            fragment_file: The prompt file to create a template for

        Returns:
            Template: A Jinja2 template instance
        """
        template = self._template_cache.get(fragment_file)
        if template is None:
            template = self.environment.from_string(fragment_file.markdown_template)
            self._template_cache[fragment_file] = template
        return template

    def preprocess(self, source, name, filename=None):
        """
        Preprocess the template source before it gets parsed.
        This is the proper extension hook for preprocessing.
        """
        return preprocess_template(source)

    def include_fragment(self, __slug: str, *args: Any, **kwargs: Any) -> str:
        """
        Include a fragment by slug with improved caching.

        Args:
            __slug: The fragment slug
            *args: Positional arguments for the fragment
            **kwargs: Keyword arguments for the fragment

        Returns:
            The rendered fragment content
        """
        # Extract indent from kwargs if present
        indent_prefix = kwargs.pop("indent", "")

        # Get context from environment globals
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

            # Get or create template instance from cache
            fragment_template = self._get_cached_template(fragment_file)

            # Create variable context for rendering
            vars_context = self._prepare_template_context(fragment_file, args, kwargs)

            # Render the fragment with the context
            result = fragment_template.render(vars_context)

            # Apply indentation if needed and if there's content with multiple lines
            if indent_prefix and "\n" in result:
                result = self.environment.filters["indent"](
                    result, first=False, width=len(indent_prefix)
                )

            # Restore the original stack
            self.environment.globals["_fragment_stack"] = original_stack

            return result

        except FileNotFoundError:
            raise ValueError(f"Missing fragment: @{__slug}")
        except Exception as e:
            # Ensure we restore the stack even if there's an error
            self.environment.globals["_fragment_stack"] = fragment_stack
            raise

    def _prepare_template_context(self, fragment_file, args, kwargs) -> dict:
        """
        Prepare the template context with arguments.

        Args:
            fragment_file: The prompt file being rendered
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            dict: The template context with variables
        """
        vars_context = {}
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
                        f"Missing required argument '{arg_name}' for fragment @{fragment_file.slug}"
                    )

        return vars_context


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
