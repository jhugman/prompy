"""
Shell completion functions for Prompy CLI.
"""


import click

from prompy.context import from_click_context


def complete_prompt_slug(ctx: click.Context, param: str, incomplete: str):
    """
    Complete the prompt_slug argument with available slugs.

    Args:
        ctx: The current click context
        param: The parameter being completed
        incomplete: The current input being completed

    Returns:
        List of matching slugs
    """
    try:
        global_only = ctx.obj.get("global_only", False)

        # Create prompt context for resolving slugs
        prompt_context = from_click_context(ctx)

        # Get available slugs directly from path keys
        available_slugs = prompt_context.available_slugs(global_only)

        # Filter slugs based on incomplete input
        return [slug for slug in available_slugs if slug.startswith(incomplete)]
    except Exception:
        # In case of any error, return empty list rather than crashing
        return []
