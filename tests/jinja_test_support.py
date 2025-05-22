"""
Test module for the Jinja2 integration.
"""

from unittest.mock import MagicMock, patch

import pytest
from jinja2 import Environment

from prompy.jinja_extension import PrompyExtension, create_jinja_environment
from prompy.prompt_context import PromptContext
from prompy.prompt_file import PromptFile
from prompy.prompt_render import PromptRender


def test_jinja_environment_creation():
    """Test creating a Jinja2 environment."""
    # Setup
    mock_context = MagicMock(spec=PromptContext)

    # Create environment
    env = create_jinja_environment(mock_context)

    # Assertions
    assert isinstance(env, Environment)
    assert PrompyExtension in [type(ext) for ext in env.extensions.values()]
    assert "_prompy_context" in env.globals
    assert "_fragment_stack" in env.globals
    assert env.globals["_prompy_context"] == mock_context
    assert env.globals["_fragment_stack"] == []


def test_slug_extension_preprocessing():
    """Test the SlugExtension token processing."""
    # Setup
    mock_context = MagicMock(spec=PromptContext)
    env = create_jinja_environment(mock_context)

    # Test simple template rendering with @slug
    template_source = "Template with {{ @fragment }} here"
    template = env.from_string(template_source)

    # Mock the include_fragment method
    original_include = env.globals["include_fragment"]
    env.globals["include_fragment"] = lambda slug, *args, **kwargs: f"INCLUDED-{slug}"

    # Render the template
    result = template.render()

    # Restore the original include_fragment method
    env.globals["include_fragment"] = original_include

    # Check that the @fragment was processed correctly
    assert result == "Template with INCLUDED-fragment here"


def test_render_simple_template():
    """Test rendering a template with no fragment references."""
    # Setup
    prompt_file = PromptFile(
        slug="test",
        markdown_template="This is a simple template with no fragments.",
    )

    # Create a PromptRender instance
    renderer = PromptRender(prompt_file)

    # Mock context
    mock_context = MagicMock(spec=PromptContext)

    # Render
    result = renderer.render(mock_context)

    # Assert
    assert result == "This is a simple template with no fragments."
    # No fragment lookups should have happened
    mock_context.load_slug.assert_not_called()


def test_render_with_fragment():
    """Test rendering a template with a single fragment reference."""
    # Setup
    main_file = PromptFile(
        slug="main", markdown_template="Template: {{ @other-fragment }} here"
    )

    fragment_file = PromptFile(
        slug="other-fragment", markdown_template="fragment content", arguments={}
    )

    # Setup context
    mock_context = MagicMock(spec=PromptContext)
    mock_context.load_slug.return_value = fragment_file

    # Setup environment context access
    def get_context_item(key, default=None):
        if key == "_prompy_context":
            return mock_context
        elif key == "_fragment_stack":
            return []
        return default

    # Patch the Environment.context.get method
    with patch("jinja2.runtime.Context.get", side_effect=get_context_item):
        # Create renderer
        renderer = PromptRender(main_file)

        # Render
        result = renderer.render(mock_context)

        # Assert
        mock_context.load_slug.assert_called_once_with("other-fragment")
        expected = "Template: fragment content here"
        assert result == expected


def test_render_with_arguments():
    """Test rendering a template with arguments."""
    # Setup
    main_file = PromptFile(
        slug="main",
        markdown_template="Template with {{ @fragment(arg1='value1', key='value2') }} here",
    )

    fragment_file = PromptFile(
        slug="fragment",
        markdown_template="Fragment with {{ arg1 }} and {{ key }}",
        arguments={"arg1": None, "key": "default"},
    )

    # Setup context
    mock_context = MagicMock(spec=PromptContext)
    mock_context.load_slug.return_value = fragment_file

    # Setup environment context access
    def get_context_item(key, default=None):
        if key == "_prompy_context":
            return mock_context
        elif key == "_fragment_stack":
            return []
        return default

    # Patch the Environment.context.get method
    with patch("jinja2.runtime.Context.get", side_effect=get_context_item):
        # Create renderer
        renderer = PromptRender(main_file)

        # Render
        result = renderer.render(mock_context)

        # Assert
        mock_context.load_slug.assert_called_once_with("fragment")
        expected = "Template with Fragment with value1 and value2 here"
        assert result == expected


def test_cycle_detection():
    """Test cycle detection in fragment references."""
    # Setup cyclical references
    main_file = PromptFile(
        slug="main", markdown_template="Template with {{ @fragment1 }}"
    )

    fragment1_file = PromptFile(
        slug="fragment1", markdown_template="Fragment1 with {{ @fragment2 }}"
    )

    fragment2_file = PromptFile(
        slug="fragment2", markdown_template="Fragment2 with {{ @main }}"
    )

    # Setup context to return our fragments
    mock_context = MagicMock(spec=PromptContext)
    mock_context.load_slug.side_effect = lambda slug: {
        "main": main_file,
        "fragment1": fragment1_file,
        "fragment2": fragment2_file,
    }[slug]

    # Setup environment context access for different stack states
    stack_states = {
        "initial": [],
        "with_main": ["main"],
        "with_main_fragment1": ["main", "fragment1"],
    }

    current_stack = stack_states["initial"]

    def get_context_item(key, default=None):
        if key == "_prompy_context":
            return mock_context
        elif key == "_fragment_stack":
            return current_stack
        return default

    # Create renderer
    renderer = PromptRender(main_file)

    # Patch the Environment.context.get method to simulate stack changes
    with patch("jinja2.runtime.Context.get", side_effect=get_context_item):
        # Expect a ValueError for cycle detection
        with pytest.raises(ValueError) as excinfo:
            result = renderer.render(mock_context)

        # Check that the error message mentions the cycle
        assert "Cyclic reference detected" in str(excinfo.value)
