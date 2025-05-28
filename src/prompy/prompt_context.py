"""
Module for handling prompt context and resolving paths.
"""

from pathlib import Path
from typing import Dict, List, Optional, Tuple

from prompy.error_handling import FragmentNotFoundError
from prompy.prompt_file import PromptFile
from prompy.prompt_files import PromptFiles


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

    def _find_file_in_directories(
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
        files = [directory / f"{slug_suffix}.md" for directory in directories]

        # If searching for an existing file, check each directory in order
        if should_exist:
            for file_path in files:
                if file_path.exists():
                    return file_path
            files = [str(file) for file in files]
            raise FragmentNotFoundError(fragment_slug=slug_suffix, search_paths=files)
        # If not requiring an existing file, use the first directory
        elif files:
            return files[0]

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
        if self.project_name and (suffix := self._strip_prefix(slug, "project/")):
            # Use project_dirs to search for the file
            return self._find_file_in_directories(
                suffix, self._project_dirs, should_exist, global_only
            )
        elif self.language and (
            suffix := self._strip_prefix(slug, "language/")
            or self._strip_prefix(slug, "$env/")
        ):
            # Use language_dirs to search for the file
            return self._find_file_in_directories(
                suffix, self._language_dirs, should_exist, global_only
            )
        # Check if the slug starts with "fragments/"
        elif slug.startswith("fragments/"):
            # Strip the "fragments/" prefix and search in fragment_dirs
            return self._find_file_in_directories(
                slug[10:],  # Remove 'fragments/' prefix
                self._fragment_dirs,
                should_exist,
                global_only,
            )
        else:
            # For slugs without any special prefixes, search in fragment_dirs as-is
            return self._find_file_in_directories(
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

    def load_slug(self, slug: str, global_only: bool = False) -> PromptFile:
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
        path = self.parse_prompt_slug(slug, True, global_only)
        assert path is not None

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
        project_paths, language_paths, fragment_paths = self._collect_paths(global_only)
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

    def _collect_paths(
        self, global_only: bool
    ) -> Tuple[dict[str, Path], dict[str, Path], dict[str, Path]]:
        # Collect language files (from language/ or $env/)
        if self.language:
            language_files = self._collect_paths_from_directories(
                "language", self._language_dirs, global_only
            )
        else:
            language_files = {}

        # Collect project files (from project/)
        if self.project_name:
            project_files = self._collect_paths_from_directories(
                "project", self._project_dirs, global_only
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

    def available_slugs(self, global_only: bool) -> list[str]:
        # Collect the slugs to path dictionaries. Don't load them, for speed.
        project_paths, language_paths, fragment_paths = self._collect_paths(global_only)

        # Merge all paths into a single dictionary
        all_paths = {}
        all_paths.update(project_paths)
        all_paths.update(language_paths)
        all_paths.update(fragment_paths)

        # Get available slugs directly from path keys
        return list(all_paths.keys())
