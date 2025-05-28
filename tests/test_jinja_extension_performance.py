"""
Test module for performance optimizations in the Jinja2 extension.
"""

from unittest.mock import MagicMock

import pytest
from jinja2 import Environment

from prompy.jinja_extension import PrompyExtension, preprocess_template
from prompy.prompt_context import PromptContext
from prompy.prompt_file import PromptFile
from prompy.prompt_render import PromptRender
from tests.jinja_test_support import create_test_extension


def test_prompt_render_creation():
    """Test that PromptRender instances are created efficiently."""
    # Create a test prompt file
    prompt_file = PromptFile(
        slug="test",
        description="Test prompt",
        markdown_template="Test template content",
    )

    # Create renderer
    renderer = PromptRender(prompt_file)

    # Access env property twice to test caching
    env1 = renderer.env
    env2 = renderer.env

    # Verify we got the same environment instance
    assert env1 is env2


def test_prompt_render_caching(benchmark):
    """Test caching in the PromptRender class."""
    prompt_file = PromptFile(
        slug="test",
        description="Test prompt",
        markdown_template="{{ @fragment1 }} {{ @fragment2 }}",
    )

    renderer = PromptRender(prompt_file)
    mock_context = MagicMock(spec=PromptContext)

    # Mock fragment loading
    fragment1 = PromptFile(
        slug="fragment1",
        description="Fragment 1",
        markdown_template="Fragment 1 content",
    )
    fragment2 = PromptFile(
        slug="fragment2",
        description="Fragment 2",
        markdown_template="Fragment 2 content",
    )

    def mock_load_slug(slug: str) -> PromptFile:
        if slug == "fragment1":
            return fragment1
        elif slug == "fragment2":
            return fragment2
        raise ValueError(f"Unknown fragment: {slug}")

    mock_context.load_slug.side_effect = mock_load_slug

    # First render to warm up caches
    renderer.render(mock_context)

    # Benchmark subsequent renders
    def run_render():
        renderer.render(mock_context)

    benchmark(run_render)


def test_preprocessor_regex_performance(benchmark):
    """Test the performance of regex pattern matching."""
    template = """
    Here is a complex template:
    {{ @fragment1(arg1="value1") }}
    {{ @fragment2(arg1=@nested(param="value")) }}
    {{ @fragment3 }}
    """

    def run_preprocess():
        return preprocess_template(template)

    # Benchmark the preprocessing
    result = benchmark(run_preprocess)

    # Verify the content is correctly processed
    assert 'include_fragment("fragment1"' in result
    assert 'include_fragment("fragment2"' in result
    assert 'include_fragment("fragment3"' in result


def test_complex_fragment_resolution(benchmark):
    """Test performance of complex fragment resolution with nested references."""
    env = Environment(extensions=[PrompyExtension])
    mock_context = MagicMock(spec=PromptContext)

    # Setup test fragments
    fragments = {
        "fragment1": PromptFile(
            slug="fragment1",
            description="Fragment 1",
            markdown_template="Fragment 1 with {{ arg1 }}, {{ arg2 }}, and {{ arg3 }}",
        ),
        "nested1": PromptFile(
            slug="nested1", description="Nested 1", markdown_template="Nested 1 content"
        ),
        "nested2": PromptFile(
            slug="nested2",
            description="Nested 2",
            markdown_template="Nested 2 with {{ param }}",
        ),
        "deepnested": PromptFile(
            slug="deepnested",
            description="Deep nested",
            markdown_template="Deep nested content",
        ),
    }

    def mock_load_slug(slug: str) -> PromptFile:
        if slug in fragments:
            return fragments[slug]
        raise ValueError(f"Unknown fragment: {slug}")

    mock_context.load_slug.side_effect = mock_load_slug
    env.globals["_prompy_context"] = mock_context
    env.globals["_fragment_stack"] = []

    template = """
    {{ @fragment1(
        arg1=@nested1(),
        arg2=@nested2(param=@deepnested()),
        arg3="value"
    ) }}
    """

    def run_resolution():
        return preprocess_template(template)

    # Benchmark the resolution
    result = benchmark(run_resolution)

    # Verify all fragments are properly resolved
    assert 'include_fragment("fragment1"' in result
    assert 'include_fragment("nested1"' in result
    assert 'include_fragment("nested2"' in result
    assert 'include_fragment("deepnested"' in result


def test_deep_nested_fragment_performance(benchmark):
    """Test performance with deeply nested fragment references."""
    env = Environment(extensions=[PrompyExtension])
    mock_context = MagicMock(spec=PromptContext)

    # Setup test fragments
    fragments = {
        "level1": PromptFile(
            slug="level1",
            description="Level 1",
            markdown_template="Level 1 with {{ param1 }} and {{ param2 }}",
        ),
        "level2": PromptFile(
            slug="level2",
            description="Level 2",
            markdown_template="Level 2 with {{ param2 }}",
        ),
        "level3": PromptFile(
            slug="level3",
            description="Level 3",
            markdown_template="Level 3 with {{ param3 }}",
        ),
        "level4": PromptFile(
            slug="level4",
            description="Level 4",
            markdown_template="Level 4 with {{ value }}",
        ),
        "level2_alt": PromptFile(
            slug="level2_alt",
            description="Level 2 Alt",
            markdown_template="Level 2 Alt with {{ value }}",
        ),
        "level3_alt": PromptFile(
            slug="level3_alt",
            description="Level 3 Alt",
            markdown_template="Level 3 Alt content",
        ),
    }

    def mock_load_slug(slug: str) -> PromptFile:
        if slug in fragments:
            return fragments[slug]
        raise ValueError(f"Unknown fragment: {slug}")

    mock_context.load_slug.side_effect = mock_load_slug
    env.globals["_prompy_context"] = mock_context
    env.globals["_fragment_stack"] = []

    # Create a template with multiple levels of nesting
    template = """
    {{ @level1(
        param1=@level2(
            param2=@level3(
                param3=@level4(value="test")
            )
        ),
        param2=@level2_alt(value=@level3_alt())
    ) }}
    """

    def run_deep_resolution():
        return preprocess_template(template)

    # Benchmark deep resolution
    result = benchmark(run_deep_resolution)

    # Verify deep nesting is resolved
    assert 'include_fragment("level1"' in result
    assert 'include_fragment("level2"' in result
    assert 'include_fragment("level3"' in result
    assert 'include_fragment("level4"' in result
    assert 'include_fragment("level2_alt"' in result
    assert 'include_fragment("level3_alt"' in result
