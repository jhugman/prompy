"""
Tests for prompt file functionality.
"""

import re
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import pytest
import yaml

from prompy.prompt_context import PromptContext
from prompy.prompt_file import PromptFile
from prompy.prompt_files import PromptFiles


def test_parse_frontmatter():
    """Test parsing YAML frontmatter from a string."""
    # Test with valid frontmatter
    content = """---
description: Test prompt
categories: [test, example]
args:
  name: default
  required:
---

This is the content."""

    data, frontmatter_str, content_str = PromptFile.parse_frontmatter(content)

    assert "description" in data
    assert data["description"] == "Test prompt"
    assert "categories" in data
    assert data["categories"] == ["test", "example"]
    assert "args" in data
    assert data["args"]["name"] == "default"
    assert data["args"]["required"] is None
    assert "This is the content." in content_str

    # Test with no frontmatter
    content = "This is content with no frontmatter."
    data, frontmatter_str, content_str = PromptFile.parse_frontmatter(content)

    assert data == {}
    assert frontmatter_str == ""
    assert content_str == content

    # Test with empty frontmatter
    content = """---
---

Content after empty frontmatter."""
    data, frontmatter_str, content_str = PromptFile.parse_frontmatter(content)

    assert data == {}
    assert frontmatter_str == ""
    assert "Content after empty frontmatter." in content_str


def test_prompt_file_load():
    """Test loading a prompt file from disk."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a test prompt file
        temp_path = Path(tmpdir) / "test_prompt.md"
        content = """---
description: Test prompt
categories: [test]
args:
  name: default
  required:
---

This is a test prompt."""

        with open(temp_path, "w") as f:
            f.write(content)

        # Load the file
        prompt_file = PromptFile.load(temp_path)

        # Check attributes
        assert prompt_file.slug == "test_prompt"
        assert prompt_file.description == "Test prompt"
        assert prompt_file.categories == ["test"]
        assert prompt_file.arguments is not None
        assert prompt_file.arguments["name"] == "default"
        assert prompt_file.arguments["required"] is None
        assert "This is a test prompt." in prompt_file.markdown_template

        # Test loading a non-existent file
        with pytest.raises(FileNotFoundError):
            PromptFile.load(Path(tmpdir) / "nonexistent.md")


def test_prompt_file_save():
    """Test saving a prompt file to disk."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Create a prompt file
        prompt_file = PromptFile()
        prompt_file.slug = "test_save"
        prompt_file.description = "Test save functionality"
        prompt_file.categories = ["test", "save"]
        prompt_file.arguments = {"arg1": "value1", "arg2": None}
        prompt_file.frontmatter = """description: Test save functionality
categories: [test, save]
args:
  arg1: value1
  arg2:"""
        prompt_file.markdown_template = "This is test content."

        # Save the file
        save_path = Path(tmpdir) / "test_save.md"
        prompt_file.save(save_path)

        # Check if file exists
        assert save_path.exists()

        # Load the file back and compare
        loaded_file = PromptFile.load(save_path)
        assert loaded_file.description == prompt_file.description
        assert loaded_file.categories == prompt_file.categories
        assert "arg1" in loaded_file.arguments
        assert loaded_file.arguments["arg1"] == "value1"
        assert "arg2" in loaded_file.arguments
        assert loaded_file.arguments["arg2"] is None
        assert (
            loaded_file.markdown_template.strip()
            == prompt_file.markdown_template.strip()
        )


def test_is_fragment():
    """Test is_fragment functionality."""
    # Test with no arguments (valid fragment)
    prompt_file = PromptFile()
    prompt_file.arguments = None
    assert prompt_file.is_fragment() is False

    # Test with all defaulted arguments (valid fragment)
    prompt_file = PromptFile()
    prompt_file.arguments = {"arg1": "default1", "arg2": "default2"}
    assert prompt_file.is_fragment() is False

    # Test with required arguments (not a valid fragment)
    prompt_file = PromptFile()
    prompt_file.arguments = {"arg1": "default1", "required_arg": None}
    assert prompt_file.is_fragment() is True


def test_prompt_files_collection():
    """Test the PromptFiles collection."""
    # Create some test prompt files
    file1 = PromptFile(
        slug="test/file1",
        description="File 1 description",
    )
    file2 = PromptFile(
        slug="$project/file2",
        description="Project file description",
        arguments={"arg1": "default"},
    )

    file3 = PromptFile(
        slug="$language/file3",
        description="Language file description",
    )

    # Create collection
    collection = PromptFiles(
        fragments={file1.slug: file1},
        projects={file2.slug: file2},
        languages={file3.slug: file3},
    )

    # Test getting files
    assert collection.get_file("test/file1") == file1
    assert collection.get_file("$project/file2") == file2
    assert collection.get_file("nonexistent") is None

    # Test available slugs
    slugs = collection.available_slugs()
    assert "test/file1" in slugs
    assert "$project/file2" in slugs
    assert "$language/file3" in slugs

    # Test help text generation
    help_text = collection.help_text()
    assert "PROMPY AVAILABLE FRAGMENTS:" in help_text
    assert "$project/file2(arg1=default)" in help_text
    assert "Project file description" in help_text
    assert "$language/file3" in help_text
    assert "Language file description" in help_text


def test_prompt_context():
    """Test the PromptContext class."""
    with tempfile.TemporaryDirectory() as tmpdir:
        # Set up directories
        tmp_path = Path(tmpdir)
        config_dir = tmp_path / "config"
        prompts_dir = config_dir / "prompts"
        projects_dir = prompts_dir / "projects"
        languages_dir = prompts_dir / "languages"
        fragments_dir = prompts_dir / "fragments"

        # Create necessary directories
        projects_dir.mkdir(parents=True)
        languages_dir.mkdir(parents=True)
        fragments_dir.mkdir(parents=True)

        # Create a project directory
        project_root = tmp_path / "project"
        project_root.mkdir()
        local_prompts_dir = project_root / ".prompy"
        local_prompts_dir.mkdir()

        # Create some prompt files
        project_file = projects_dir / "test.md"
        with open(project_file, "w") as f:
            f.write("---\ndescription: Project test\n---\nProject content")

        language_file = languages_dir / "python" / "test.md"
        language_file.parent.mkdir()
        with open(language_file, "w") as f:
            f.write("---\ndescription: Language test\n---\nLanguage content")

        fragment_file = fragments_dir / "test.md"
        with open(fragment_file, "w") as f:
            f.write("---\ndescription: Fragment test\n---\nFragment content")

        local_file = local_prompts_dir / "local.md"
        with open(local_file, "w") as f:
            f.write("---\ndescription: Local test\n---\nLocal content")

        # Create a context
        context = PromptContext(
            project_name="myproject",
            language="python",
            project_dirs=[local_prompts_dir, projects_dir],
            language_dirs=[languages_dir / "python"],
            fragment_dirs=[fragments_dir],
        )

        # Test parse_prompt_slug
        assert context.parse_prompt_slug("$language/test") == language_file
        assert context.parse_prompt_slug("fragments/test") == fragment_file
        assert context.parse_prompt_slug("$project/test") == project_file
        assert context.parse_prompt_slug("nonexistent") is None

        # Test load_slug
        project_prompt = context.load_slug("$project/test")
        assert project_prompt.description == "Project test"

        language_prompt = context.load_slug("$language/test")
        assert language_prompt.description == "Language test"

        with pytest.raises(FileNotFoundError):
            context.load_slug("nonexistent")

        # Test load_all
        all_prompts = context.load_all()
        assert "$project/test" in all_prompts.available_slugs()
        assert "$language/test" in all_prompts.available_slugs()
        assert "test" in all_prompts.available_slugs()

        # Check that project and language variables were correctly substituted
        project_file = all_prompts.get_file("$project/test")
        assert project_file is not None
        assert project_file.description == "Project test"

        language_file = all_prompts.get_file("$language/test")
        assert language_file is not None
        assert language_file.description == "Language test"
