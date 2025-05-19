"""
Tests for the context module.
"""

from pathlib import Path

import pytest

from prompy.prompt_file import PromptContext


def test_parse_prompt_slug_existence():
    """Test that parse_prompt_slug with should_exist=True returns paths that exist."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdir:
        tmp_path = Path(tmpdir)

        # Create necessary directories
        fragments_dir = tmp_path / "fragments"
        languages_dir = tmp_path / "languages" / "python"
        projects_dir = tmp_path / "projects" / "test-project"

        for dir_path in [fragments_dir, languages_dir, projects_dir]:
            dir_path.mkdir(parents=True, exist_ok=True)

        # Create some sample files
        fragment_file = fragments_dir / "test.md"
        language_file = languages_dir / "test.md"
        project_file = projects_dir / "test.md"

        for file_path, content in [
            (fragment_file, "---\ndescription: Fragment test\n---\nFragment content"),
            (language_file, "---\ndescription: Language test\n---\nLanguage content"),
            (project_file, "---\ndescription: Project test\n---\nProject content"),
        ]:
            with open(file_path, "w") as f:
                f.write(content)

        # Create a PromptContext with the directories
        context = PromptContext(
            project_name="test-project",
            language="python",
            language_dirs=[languages_dir],
            project_dirs=[projects_dir],
            fragment_dirs=[fragments_dir],
        )

        # Load all available prompt files
        prompt_files = context.load_all()

        # For each file in the collection, ensure that parse_prompt_slug returns a path that exists
        for slug in prompt_files.available_slugs():
            path = context.parse_prompt_slug(slug, should_exist=True)
            assert path is not None, f"Path for slug '{slug}' should not be None"
            assert path.exists(), f"Path for slug '{slug}' should exist: {path}"
