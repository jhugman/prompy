"""
Module for handling collections of prompt files.
"""

from typing import Dict, List, Optional

from prompy.prompt_file import PromptFile


class PromptFiles:
    """
    Collection of prompt files for providing help and available slugs.
    Organizes prompts into categories for easier access and display.
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
        Generate help text for available prompts and fragments.

        Args:
            slug_prefix: Prefix to add before each slug (e.g., "@" for editor comments)
            include_syntax: Whether to include syntax help at the end
            include_header: Whether to include the header section at the top
            use_dashes: Whether to include divider dashes after the header
            inline_description: Whether to put descriptions on the same line as slugs (e.g., "slug - description")
                              rather than indented on the next line
            category_filter: Optional category name to filter prompts by

        Returns:
            str: Formatted help text
        """
        help_text = ""

        # Add header if requested
        if include_header:
            help_text += "PROMPY AVAILABLE FRAGMENTS:\n"
            if use_dashes:
                help_text += "--------------------------\n"
            help_text += "\n"

        # Group files by category for task files
        task_files = []
        other_files = []

        # Identify task files from fragment prompts
        for slug, prompt_file in self._fragment_prompts.items():
            if not prompt_file.is_fragment():
                task_files.append((slug, prompt_file))
            else:
                other_files.append((slug, prompt_file))

        # Define sections to display
        sections = [
            {
                "title": (
                    f"PROJECT FRAGMENTS (project: {self._project_name})"
                    if self._project_name
                    else "PROJECT FRAGMENTS"
                ),
                "items": (
                    sorted(self._project_prompts.items())
                    if self._project_prompts
                    else []
                ),
            },
            {
                "title": (
                    f"LANGUAGE FRAGMENTS (language: {self._language_name})"
                    if self._language_name
                    else "LANGUAGE FRAGMENTS"
                ),
                "items": (
                    sorted(self._language_prompts.items())
                    if self._language_prompts
                    else []
                ),
            },
            {"title": "TASKS", "items": sorted(task_files) if task_files else []},
            {"title": "FRAGMENTS", "items": sorted(other_files) if other_files else []},
        ]

        # Add each section
        for section in sections:
            section_items = []

            # Apply category filter if specified
            if category_filter:
                section_items = []
                for slug, prompt_file in section["items"]:
                    # Include prompt if it has matching category or if no categories are defined
                    if prompt_file.categories and category_filter.lower() in [
                        cat.lower() for cat in prompt_file.categories
                    ]:
                        section_items.append((slug, prompt_file))
            else:
                section_items = section["items"]

            if not section_items:
                continue

            help_text += f"{section['title']}:\n"

            for slug, prompt_file in section_items:
                args_str = self._format_arguments(prompt_file.arguments)

                # Format the output
                if prompt_file.description and inline_description:
                    # For detailed output - include description
                    help_text += (
                        f"  {slug_prefix}{slug}{args_str} — {prompt_file.description}\n"
                    )

                    # Add categories if available and in detailed mode
                    if prompt_file.categories:
                        categories_str = ", ".join(prompt_file.categories)
                        help_text += f"    Categories: {categories_str}\n"
                else:
                    # For simple output - just show the slug
                    help_text += f"  {slug_prefix}{slug}{args_str}\n"
                    if prompt_file.description:
                        help_text += f"    {prompt_file.description}\n"

                    # Add categories if available and not in inline description mode
                    if prompt_file.categories and not inline_description:
                        categories_str = ", ".join(prompt_file.categories)
                        help_text += f"    Categories: {categories_str}\n"

            help_text += "\n"

        # Add syntax help if requested
        if include_syntax:
            help_text += "SYNTAX:\n"
            help_text += "  @fragment-name(arg1, key=value)\n"
            help_text += "  @path/to/fragment\n"
            help_text += "  @project/fragment\n"
            help_text += "  @language/fragment\n\n"

        return help_text

    def _format_arguments(self, args: Optional[Dict[str, Optional[str]]]) -> str:
        """
        Format arguments for display in help text.

        Args:
            args (Optional[Dict[str, Optional[str]]]): Argument names and default values

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
