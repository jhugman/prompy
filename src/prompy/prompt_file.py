"""
Module for handling prompt files and their representation.
"""

import re
from pathlib import Path
from typing import Any, ClassVar, Dict, List, Optional, Tuple, Union

import yaml


class PromptFile:
    """
    A class representing a file on disk, as edited by users.

    Prompt files have front matter, which is in YAML.
    The markdown content can contain fragment references.
    """

    def __init__(
        self,
        *,
        slug: str = "",
        description: Optional[str] = None,
        categories: Optional[List[str]] = None,
        arguments: Optional[Dict[str, Optional[str]]] = None,
        frontmatter: str = "",
        markdown_template: str = "",
    ) -> None:
        """
        Initialize a PromptFile.

        Args:
            slug: The slug identifier for the prompt file
            description: Optional description of the prompt
            categories: Optional list of categories for the prompt
            arguments: Optional dictionary of argument names and default values
            frontmatter: Raw frontmatter string
            markdown_template: The markdown content template
        """
        self.slug: str = slug
        self.description: Optional[str] = description
        self.categories: Optional[List[str]] = categories
        self.arguments: Optional[Dict[str, Optional[str]]] = arguments
        self.frontmatter: str = frontmatter
        self.markdown_template: str = markdown_template

    @staticmethod
    def parse_frontmatter(content: str) -> Tuple[Dict[str, Any], str, str]:
        """
        Parse YAML frontmatter from a string.

        Args:
            content (str): The content to parse

        Returns:
            Tuple[Dict[str, Any], str, str]: Parsed data, raw frontmatter string, and content string
        """
        # Check for frontmatter (content between --- markers)
        frontmatter_match = re.match(
            r"^---\s*\n(.*?)\n---\s*\n(.*)", content, re.DOTALL
        )
        if not frontmatter_match:
            # No frontmatter, return empty dict and the original content
            return {}, "", content

        # Extract frontmatter and markdown content
        frontmatter_text = frontmatter_match.group(1)
        markdown_content = frontmatter_match.group(2)

        # Parse frontmatter YAML
        try:
            frontmatter_data = yaml.safe_load(frontmatter_text)
            if frontmatter_data is None:
                # Empty frontmatter
                frontmatter_data = {}
        except yaml.YAMLError:
            # Invalid YAML, return empty dict
            frontmatter_data = {}

        return frontmatter_data, frontmatter_text, markdown_content

    @classmethod
    def load(cls, path: Path, slug: Optional[str] = None) -> "PromptFile":
        """
        Load a prompt file from a path.

        Args:
            path (Path): The path to the prompt file

        Returns:
            PromptFile: The loaded prompt file

        Raises:
            FileNotFoundError: If the file does not exist
            ValueError: If the file has invalid frontmatter
        """
        if not path.exists():
            raise FileNotFoundError(f"Prompt file not found: {path}")

        # Read file content
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()

        # Default values
        prompt_file = cls(
            slug=slug or path.stem,  # Use filename as default slug
            markdown_template=content,
        )

        # Parse frontmatter
        frontmatter_data, frontmatter_text, markdown_content = cls.parse_frontmatter(
            content
        )

        # Store original frontmatter text
        prompt_file.frontmatter = frontmatter_text
        prompt_file.markdown_template = markdown_content

        # Extract specific fields
        prompt_file.description = frontmatter_data.get("description")
        prompt_file.categories = frontmatter_data.get("categories")

        # Handle arguments
        args = frontmatter_data.get("args", {})
        if args:
            prompt_file.arguments = {}
            for key, value in args.items():
                prompt_file.arguments[key] = value

        return prompt_file

    @property
    def rendered_frontmatter(self) -> str:
        """
        Generate YAML frontmatter based on the prompt file attributes.

        Returns:
            str: YAML frontmatter for the prompt file
        """
        # Start with the frontmatter data as a dict
        frontmatter_data = {}

        # Add key attributes
        if self.description:
            frontmatter_data["description"] = self.description

        if self.categories:
            frontmatter_data["categories"] = self.categories

        if self.arguments:
            frontmatter_data["args"] = self.arguments

        # Convert to YAML
        return yaml.dump(frontmatter_data, sort_keys=False).strip()

    def generate_frontmatter(self) -> str:
        """
        Generate YAML frontmatter string based on the prompt file attributes.

        This is an alias for rendered_frontmatter to support the CLI command.

        Returns:
            str: YAML frontmatter for the prompt file
        """
        return self.rendered_frontmatter

    def save(self, path: Path) -> None:
        """
        Save the prompt file to a path.

        Args:
            path (Path): The path to save the file to

        Raises:
            IOError: If the file cannot be written
        """
        # Ensure the parent directory exists
        path.parent.mkdir(parents=True, exist_ok=True)

        # Prepare content with frontmatter
        content = f"---\n{self.frontmatter}\n---\n\n{self.markdown_template}"

        # Write to file
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)

    def is_fragment(self) -> bool:
        """
        Returns True if the prompt file can be used as a fragment.

        Returns:
            bool: True if this is a valid fragment
        """
        # A fragment is valid if it has arguments and all required arguments have defaults,
        # or if it has no arguments
        if self.arguments is None:
            return False

        # Check if all required arguments have default values
        for value in self.arguments.values():
            if value is None:  # Required argument without default
                return True

        return False


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
        if slug.startswith("$project"):
            return self._project_prompts.get(slug)
        elif slug.startswith("$language") or slug.startswith("$env"):
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
            help_text += "  @$project/fragment\n"
            help_text += "  @$language/fragment\n\n"

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


class PromptContext:
    """
    A collection of directories used for resolving prompts.
    """

    def __init__(
        self,
        project_name: Optional[str] = None,
        language: Optional[str] = None,
        language_dirs: List[Path] = [],
        project_dirs: List[Path] = [],
        fragment_dirs: List[Path] = [],
    ):
        """
        Initialize a PromptContext.

        Args:
            project_name (Optional[str]): The project name
            language (Optional[str]): The detected language
            language_dirs (List[Path]): List of directories to search for language prompts
            project_dirs (List[Path]): List of directories to search for project prompts
            fragment_dirs (List[Path]): List of directories to search for fragment prompts
        """
        self.project_name = project_name
        self.language = language

        # Set up search directories
        self._fragment_dirs = fragment_dirs if fragment_dirs is not None else []
        self._project_dirs = project_dirs if project_dirs is not None else []
        self._language_dirs = language_dirs if language_dirs is not None else []

    def _search_directories(
        self,
        slug_suffix: str,
        directories: List[Path],
        should_exist: bool,
        global_only: bool = False,
    ) -> Optional[Path]:
        """
        Search for a file in multiple directories.

        Args:
            slug_suffix (str): The suffix part of the slug (without prefix)
            directories (List[Path]): List of directories to search
            should_exist (bool): If True, search for existing file; if False, return a path in the first directory
            global_only (bool): If True, only look at the last directory in the list

        Returns:
            Optional[Path]: Path to the file if found or created, or None if no path is available
        """
        # If global_only is True, only use the last directory in the list
        search_dirs = [directories[-1]] if global_only and directories else directories

        # If searching for an existing file, check each directory in order
        if should_exist:
            for directory in search_dirs:
                # For fragment directories, use the path directly
                file_path = directory / f"{slug_suffix}.md"
                if file_path.exists():
                    return file_path
            return None
        # If not requiring an existing file, use the first directory
        elif search_dirs:
            directory = search_dirs[0]
            return directory / f"{slug_suffix}.md"

        return None

    def parse_prompt_slug(
        self, slug: str, should_exist: bool = True, global_only: bool = False
    ) -> Optional[Path]:
        """
        Parse a prompt slug and resolve it to a file path.

        Args:
            slug (str): The prompt slug
            should_exist (bool): If True, search for existing file; if False, return a path even if it doesn't exist
            global_only (bool): If True, only look at the global directories

        Returns:
            Optional[Path]: The resolved file path, or None if not found
        """
        # Handle special variables in the slug
        if self.project_name and (suffix := self._strip_prefix(slug, "$project/")):
            # Use project_dirs to search for the file
            return self._search_directories(
                suffix, self._project_dirs, should_exist, global_only
            )
        elif self.language and (
            suffix := self._strip_prefix(slug, "$language/")
            or self._strip_prefix(slug, "$env/")
        ):
            # Use language_dirs to search for the file
            return self._search_directories(
                suffix, self._language_dirs, should_exist, global_only
            )
        # Check if the slug starts with "fragments/"
        elif slug.startswith("fragments/"):
            # Strip the "fragments/" prefix and search in fragment_dirs
            return self._search_directories(
                slug[10:],  # Remove 'fragments/' prefix
                self._fragment_dirs,
                should_exist,
                global_only,
            )
        else:
            # For slugs without any special prefixes, search in fragment_dirs as-is
            return self._search_directories(
                slug, self._fragment_dirs, should_exist, global_only
            )

    def _strip_prefix(self, slug: str, prefix: str) -> Optional[str]:
        """
        If slug starts with prefix, return the slug stripped of its prefix.
        Otherwise, return None.
        """
        if slug.startswith(prefix):
            return slug.removeprefix(prefix)
        return None

    def load_slug(
        self, slug: str, should_exist: bool = True, global_only: bool = False
    ) -> PromptFile:
        """
        Parse a prompt slug and load it as a PromptFile.

        Args:
            slug (str): The prompt slug
            should_exist (bool): If True, search for existing file; if False, return a path even if it doesn't exist
            global_only (bool): If True, only look at the global directories

        Returns:
            PromptFile: The loaded prompt file

        Raises:
            FileNotFoundError: If the slug doesn't resolve to a valid file
        """
        path = self.parse_prompt_slug(slug, should_exist, global_only)
        if path is None:
            raise FileNotFoundError(f"Could not find prompt file for slug: {slug}")

        prompt_file = PromptFile.load(path, slug=slug)
        return prompt_file

    def load_all(self, global_only: bool = False) -> PromptFiles:
        """
        Find and load all available prompt files.

        Args:
            global_only (bool): If True, only use global directories

        Returns:
            PromptFiles: Collection of all prompt files
        """
        project_paths, language_paths, fragment_paths = self.collect_paths(global_only)
        return PromptFiles(
            project_name=self.project_name,
            language_name=self.language,
            projects=self._dict_paths_to_files(project_paths),
            languages=self._dict_paths_to_files(language_paths),
            fragments=self._dict_paths_to_files(fragment_paths),
        )

    def _dict_paths_to_files(self, paths: dict[str, Path]) -> dict[str, PromptFile]:
        """
        Convert a dictionary of slug->path mappings to a dictionary of slug->PromptFile.

        Args:
            paths (dict[str, Path]): Dictionary mapping slugs to file paths

        Returns:
            dict[str, PromptFile]: Dictionary mapping slugs to loaded PromptFile objects
        """
        return {slug: PromptFile.load(path, slug=slug) for slug, path in paths.items()}

    def collect_paths(
        self, global_only: bool
    ) -> Tuple[dict[str, Path], dict[str, Path], dict[str, Path]]:
        # Collect language files (from $language/ or $env/)
        if self.language:
            language_files = self._collect_paths_from_directories(
                "$language", self._language_dirs, global_only
            )
        else:
            language_files = {}

        # Collect project files (from $project/)
        if self.project_name:
            project_files = self._collect_paths_from_directories(
                "$project", self._project_dirs, global_only
            )
        else:
            project_files = {}

        # Collect fragment files (using "fragments/" prefix)
        fragment_files = self._collect_paths_from_directories(
            "",
            self._fragment_dirs,
            global_only,  # but don't use a prefix.
        )

        return project_files, language_files, fragment_files

    def _collect_paths_from_directory(
        self, slug_prefix: str, directory: Path
    ) -> Dict[str, Path]:
        """
        Make a dictionary of slugs to PromptFiles based on the markdown files found by recursively looking in the directory.

        Args:
            slug_prefix (str): Prefix to prepend to each slug
            directory (Path): Directory to search for markdown files

        Returns:
            Dict[str, PromptFile]: Dictionary of slugs to PromptFiles
        """
        files = {}

        if not directory.exists():
            return files

        for path in directory.glob("**/*.md"):
            try:
                # Get relative path from the directory
                rel_path = path.relative_to(directory)

                # Create slug from path parts
                slug_parts = list(rel_path.parts)
                slug_parts[-1] = slug_parts[-1].replace(
                    ".md", ""
                )  # Remove .md extension

                # Build the complete slug with prefix
                slug = (
                    f"{slug_prefix}/{'/'.join(slug_parts)}"
                    if slug_prefix
                    else "/".join(slug_parts)
                )

                # Add to the dictionary
                files[slug] = path
            except Exception as e:
                # Skip files that can't be loaded
                continue

        return files

    def _collect_paths_from_directories(
        self, slug_prefix: str, directories: List[Path], global_only: bool = False
    ) -> Dict[str, Path]:
        """
        Collect files from a list of directories into a single dictionary.

        Args:
            slug_prefix (str): Prefix to prepend to each slug
            directories (List[Path]): List of directories to search
            global_only (bool): If True, only use the last directory in the list

        Returns:
            Dict[str, PromptFile]: Dictionary of slugs to PromptFiles
        """
        files = {}

        # If global_only is True, only use the last directory
        if global_only and directories:
            dirs_to_search = [directories[-1]]
        else:
            # Search directories in reverse order so files from earlier dirs can override later ones
            dirs_to_search = list(reversed(directories))

        for directory in dirs_to_search:
            # Collect files from this directory
            directory_files = self._collect_paths_from_directory(slug_prefix, directory)

            # Add to the combined dictionary, potentially overriding earlier entries
            files.update(directory_files)

        return files
