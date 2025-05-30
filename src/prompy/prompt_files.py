"""
Module for managing collections of prompt files.
"""

import logging
from typing import Dict, List, Optional

import click
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from prompy.prompt_file import PromptFile

logger = logging.getLogger(__name__)
console = Console()


class PromptFiles:
    """
    A collection of prompt files with access methods for help text and prompts.
    """

    def __init__(
        self,
        project_name: Optional[str] = None,
        language_name: Optional[str] = None,
        languages: Dict[str, PromptFile] = {},
        projects: Dict[str, PromptFile] = {},
        fragments: Dict[str, PromptFile] = {},
    ) -> None:
        """
        Initialize an empty collection of prompt files.
        """
        self._project_name = project_name
        self._language_name = language_name

        self._fragment_prompts: Dict[str, PromptFile] = fragments
        self._project_prompts: Dict[str, PromptFile] = projects
        self._language_prompts: Dict[str, PromptFile] = languages

    def get_file(self, slug: str) -> Optional[PromptFile]:
        """
        Get a prompt file by slug.

        Args:
            slug (str): The slug to look up

        Returns:
            Optional[PromptFile]: The prompt file, or None if not found
        """
        if slug.startswith("project"):
            return self._project_prompts.get(slug)
        elif slug.startswith("language") or slug.startswith("$env"):
            return self._language_prompts.get(slug)
        else:
            return self._fragment_prompts.get(slug)

    def get_prompt_file(self, slug: str) -> Optional[PromptFile]:
        """
        Get a prompt file by its slug.

        Args:
            slug: The slug of the prompt file.

        Returns:
            PromptFile if found, None otherwise.
        """
        # Check project prompts first
        if slug in self._project_prompts:
            return self._project_prompts[slug]
        # Then language prompts
        if slug in self._language_prompts:
            return self._language_prompts[slug]
        # Finally fragment prompts
        if slug in self._fragment_prompts:
            return self._fragment_prompts[slug]
        return None

    def available_slugs(self) -> List[str]:
        """
        Get a list of available slugs.

        Returns:
            List[str]: List of available slugs
        """
        return (
            list(self._project_prompts.keys())
            + list(self._language_prompts.keys())
            + list(self._fragment_prompts.keys())
        )

    def help_text(
        self,
        *,
        slug_prefix: str = "",
        include_syntax: bool = True,
        include_header: bool = True,
        use_dashes: bool = True,
        inline_description: bool = False,
        category_filter: Optional[str] = None,
    ) -> str:
        """
        Generate formatted help text for available prompts.

        Args:
            slug_prefix: Optional prefix to add to slug names
            include_syntax: Whether to include syntax help
            include_header: Whether to include syntax help
            use_dashes: Whether to use dashed lines for sections
            inline_description: Whether to include descriptions inline
            category_filter: Optional category to filter prompts by

        Returns:
            str: Formatted help text
        """
        # Create string buffer for rich output
        from io import StringIO

        output = StringIO()
        temp_console = Console(file=output, force_terminal=True)

        # Use the render_help_to_console method to avoid code duplication
        self.render_help_to_console(
            temp_console,
            slug_prefix=slug_prefix,
            include_syntax=include_syntax,
            include_header=include_header,
            inline_description=inline_description,
            category_filter=category_filter,
        )

        return output.getvalue()

    def render_help_to_console(
        self,
        target_console: Console,
        *,
        slug_prefix: str = "",
        include_syntax: bool = True,
        include_header: bool = True,
        inline_description: bool = False,
        category_filter: Optional[str] = None,
    ) -> None:
        """
        Render formatted help directly to a given console.

        Args:
            target_console: The Rich console to render to
            slug_prefix: Optional prefix to add to slug names
            include_syntax: Whether to include syntax help
            include_header: Whether to include syntax help
            inline_description: Whether to include descriptions inline
            category_filter: Optional category to filter prompts by
        """
        # Group files by category for task files
        task_files = []
        other_files = []

        # Identify task files from fragment prompts
        for slug, prompt_file in self._fragment_prompts.items():
            # Skip if category filter is active and doesn't match
            if category_filter and (
                not prompt_file.categories
                or category_filter not in prompt_file.categories
            ):
                continue

            if not prompt_file.is_fragment():
                task_files.append((slug, prompt_file))
            else:
                other_files.append((slug, prompt_file))

        # Define sections to display
        sections = [
            {
                "title": f"Project Fragments {f'({self._project_name})' if self._project_name else ''}",
                "style": "blue",
                "items": (
                    sorted(self._project_prompts.items())
                    if self._project_prompts
                    else []
                ),
            },
            {
                "title": f"Language Fragments {f'({self._language_name})' if self._language_name else ''}",
                "style": "blue",
                "items": (
                    sorted(self._language_prompts.items())
                    if self._language_prompts
                    else []
                ),
            },
            {
                "title": "Tasks",
                "style": "blue",
                "items": sorted(task_files) if task_files else [],
            },
            {
                "title": "Fragments",
                "style": "blue",
                "items": sorted(other_files) if other_files else [],
            },
        ]

        if include_header:
            header = Text("PROMPY AVAILABLE FRAGMENTS", style="bold blue")
            target_console.print(header)
            target_console.print()

        # Add each section
        for section in sections:
            items = section["items"]
            if not items:
                continue

            # Filter items by category if specified
            if category_filter:
                items = [
                    (slug, pf)
                    for slug, pf in items
                    if pf.categories and category_filter in pf.categories
                ]

            if not items:  # Skip empty sections after filtering
                continue

            # Create panel for section
            title = Text(section["title"].upper(), style=f"bold {section['style']}")

            # Create table for prompts
            table = Table(
                show_header=False,
                show_lines=False,
                box=None,
                padding=(0, 2),
                collapse_padding=True,
            )

            # Columns depend on display mode
            if inline_description:
                table.add_column("Prompt", style="bright_white")
                table.add_column("Description", style="bright_black")
                table.add_column("Categories", style="dim")
            else:
                table.add_column("Prompt", style="bright_white")
                if not inline_description:
                    table.add_column("Description", style="bright_black")

            # Add items to table
            for slug, prompt_file in items:
                args_str = self._format_arguments(prompt_file.arguments)
                prompt_text = f"{slug_prefix}{slug}{args_str}"

                if inline_description:
                    categories = (
                        ", ".join(prompt_file.categories)
                        if prompt_file.categories
                        else ""
                    )
                    table.add_row(
                        prompt_text,
                        prompt_file.description or "",
                        categories,
                    )
                else:
                    if prompt_file.description:
                        table.add_row(prompt_text, prompt_file.description)
                    else:
                        table.add_row(prompt_text)

            # Create and print panel containing the table
            panel = Panel(table, title=title, style="blue")
            target_console.print(panel)
            target_console.print()

        # Add syntax help if requested
        if include_syntax:
            syntax_table = Table(
                show_header=False,
                show_lines=False,
                box=None,
                padding=(0, 2),
            )
            syntax_table.add_row("@fragment-name(arg1, key=value)", style="yellow")
            syntax_table.add_row("@path/to/fragment", style="yellow")
            syntax_table.add_row("@project/fragment", style="yellow")
            syntax_table.add_row("@language/fragment", style="yellow")

            syntax_panel = Panel(
                syntax_table,
                title=Text("SYNTAX", style="bold blue"),
                style="blue",
            )
            target_console.print(syntax_panel)

    def _format_arguments(self, args: Optional[Dict[str, Optional[str]]]) -> str:
        """
        Format arguments for display in help text.

        Args:
            args: Argument names and default values

        Returns:
            str: Formatted arguments string
        """
        if not args:
            return ""

        arg_parts = []
        for name, default in args.items():
            if default is None:
                arg_parts.append(name)
            else:
                arg_parts.append(f"{name}={default}")

        return f"({', '.join(arg_parts)})"
