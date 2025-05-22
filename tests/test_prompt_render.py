"""
Tests for prompt_render.py.
"""

from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from prompy.prompt_context import PromptContext
from prompy.prompt_file import PromptFile
from prompy.prompt_render import PromptRender


class TestPromptRender:
    """Tests for the PromptRender class."""

    def test_simple_render_no_fragments(self):
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

    def test_render_with_fragment(self):
        """Test rendering a template with a single fragment reference."""
        # Setup prompt files
        main_file = PromptFile(
            slug="main", markdown_template="Template: {{ @other-fragment }} here"
        )

        fragment_file = PromptFile(
            slug="other-fragment", markdown_template="fragment content", arguments={}
        )

        # Setup context
        mock_context = MagicMock(spec=PromptContext)
        mock_context.load_slug.return_value = fragment_file

        # Create renderer
        renderer = PromptRender(main_file)

        # Render
        result = renderer.render(mock_context)

        # Assert
        mock_context.load_slug.assert_called_once_with("other-fragment")
        expected = "Template: fragment content here"
        assert result == expected

    def test_render_with_arguments(self):
        """Test rendering a template with arguments."""
        # Setup
        main_file = PromptFile(
            slug="main",
            markdown_template="Template with {{@fragment(arg1='value1', key='value2')}} here",
        )

        fragment_file = PromptFile(
            slug="fragment",
            markdown_template="Fragment with {{ arg1 }} and {{ key }}",
            arguments={"arg1": None, "key": "default"},
        )

        # Setup context to return our fragment
        mock_context = MagicMock(spec=PromptContext)
        mock_context.load_slug.return_value = fragment_file

        # Create renderer
        renderer = PromptRender(main_file)

        # Render
        result = renderer.render(mock_context)

        # Assert
        mock_context.load_slug.assert_called_once_with("fragment")
        assert "Template with Fragment with value1 and value2 here" == result

    def test_nested_fragments(self):
        """Test rendering a template with nested fragments."""
        # Setup
        main_file = PromptFile(
            slug="main", markdown_template="Main template with {{@fragment1}}"
        )

        fragment1_file = PromptFile(
            slug="fragment1",
            markdown_template="Fragment1 with {{@fragment2}}",
            arguments={},
        )

        fragment2_file = PromptFile(
            slug="fragment2", markdown_template="Fragment2 content", arguments={}
        )

        # Mock context to return our fragments
        mock_context = MagicMock(spec=PromptContext)
        mock_context.load_slug.side_effect = lambda slug: {
            "fragment1": fragment1_file,
            "fragment2": fragment2_file,
        }[slug]

        # Create renderer
        renderer = PromptRender(main_file)

        # Render
        result = renderer.render(mock_context)

        # Assert
        assert mock_context.load_slug.call_count == 2
        assert "Main template with Fragment1 with Fragment2 content" == result

    def test_nested_fragments_with_arguments(self):
        """Test rendering a template with nested fragments that have arguments."""
        # Setup
        main_file = PromptFile(
            slug="main",
            markdown_template="Main template with {{@fragment1(param='outer')}}",
        )

        fragment1_file = PromptFile(
            slug="fragment1",
            markdown_template="Fragment1 with param={{param}} and {{@fragment2(inner_param=param)}}",
            arguments={"param": None},  # Required parameter
        )

        fragment2_file = PromptFile(
            slug="fragment2",
            markdown_template="Fragment2 with {{inner_param}}",
            arguments={"inner_param": None},  # Required parameter
        )

        # Mock context to return our fragments
        mock_context = MagicMock(spec=PromptContext)
        mock_context.load_slug.side_effect = lambda slug: {
            "fragment1": fragment1_file,
            "fragment2": fragment2_file,
        }[slug]

        # Create renderer
        renderer = PromptRender(main_file)

        # Render
        result = renderer.render(mock_context)

        # Assert
        assert mock_context.load_slug.call_count == 2
        # The final output should have both fragments resolved with the arguments
        assert (
            "Main template with Fragment1 with param=outer and Fragment2 with outer"
            == result
        )

    def test_cycle_detection(self):
        """Test that the renderer detects cycles in fragment references."""
        # Setup cyclic fragments
        main_file = PromptFile(
            slug="main", markdown_template="Main with {{@fragment1}}"
        )

        fragment1_file = PromptFile(
            slug="fragment1",
            markdown_template="Fragment1 with {{@fragment2}}",
            arguments={},
        )

        fragment2_file = PromptFile(
            slug="fragment2",
            markdown_template="Fragment2 with {{@main}}",  # Cycle back to main
            arguments={},
        )

        # Mock context to return our fragments
        mock_context = MagicMock(spec=PromptContext)
        mock_context.load_slug.side_effect = lambda slug: {
            "main": main_file,
            "fragment1": fragment1_file,
            "fragment2": fragment2_file,
        }[slug]

        # Create renderer
        renderer = PromptRender(main_file)

        # Render and expect an error
        with pytest.raises(ValueError) as excinfo:
            renderer.render(mock_context)

        # Check that the error message mentions the cycle
        assert "Cyclic reference detected" in str(excinfo.value)
        # Check that the error message shows the full cycle path
        assert "@main -> @fragment1 -> @fragment2 -> @main" in str(excinfo.value)

    def test_missing_required_args(self):
        """Test that the renderer validates required arguments."""
        # Setup
        main_file = PromptFile(
            slug="main", markdown_template="Template with {{@fragment}}"
        )

        fragment_file = PromptFile(
            slug="fragment",
            markdown_template="Fragment with {{required_arg}}",
            arguments={"required_arg": None},  # Required arg (no default)
        )

        # Mock context to return our fragment
        mock_context = MagicMock(spec=PromptContext)
        mock_context.load_slug.return_value = fragment_file

        # Create renderer
        renderer = PromptRender(main_file)

        # Render and expect an error
        with pytest.raises(ValueError) as excinfo:
            renderer.render(mock_context)

        # Check that the error message mentions the missing argument
        assert "Missing required argument 'required_arg'" in str(excinfo.value)

    def test_default_args(self):
        """Test that default arguments are applied correctly."""
        # Setup
        main_file = PromptFile(
            slug="main", markdown_template="Template with {{@fragment}}"
        )

        fragment_file = PromptFile(
            slug="fragment",
            markdown_template="Fragment with default {{arg}}",
            arguments={"arg": "default"},  # Arg with default value
        )

        # Mock context to return our fragment
        mock_context = MagicMock(spec=PromptContext)
        mock_context.load_slug.return_value = fragment_file

        # Create renderer
        renderer = PromptRender(main_file)

        # Render
        result = renderer.render(mock_context)

        # Assert no error and fragment content is in the result
        assert "Fragment with default default" in result

    def test_complex_nested_arguments(self):
        """Test rendering with complex nested argument references."""
        # Setup
        main_file = PromptFile(
            slug="main",
            markdown_template="Main with {{@outer(first='value1', second='value2')}}",
        )

        outer_file = PromptFile(
            slug="outer",
            markdown_template="Outer[{{first}}, {{second}}] with {{@inner(param=second)}}",
            arguments={"first": None, "second": None},
        )

        inner_file = PromptFile(
            slug="inner",
            markdown_template="Inner({{param}})",
            arguments={"param": None},
        )

        # Mock context to return our fragments
        mock_context = MagicMock(spec=PromptContext)
        mock_context.load_slug.side_effect = lambda slug: {
            "outer": outer_file,
            "inner": inner_file,
        }[slug]

        # Create renderer
        renderer = PromptRender(main_file)

        # Render the template with the nested fragments
        result = renderer.render(mock_context)

        # Assert that both fragments were resolved
        assert mock_context.load_slug.call_count == 2
        # The final output should have both fragments resolved with the arguments
        expected = "Main with Outer[value1, value2] with Inner(value2)"
        assert result == expected

    def test_real_nested_fragments(self):
        """Test rendering a template with nested fragments using real fragment parser."""
        # Setup
        main_file = PromptFile(
            slug="main", markdown_template="Main template with {{@fragment1}}"
        )

        fragment1_file = PromptFile(
            slug="fragment1",
            markdown_template="Fragment1 with {{@fragment2}}",
            arguments={},
        )

        fragment2_file = PromptFile(
            slug="fragment2", markdown_template="Fragment2 content", arguments={}
        )

        # Mock context to return our fragments
        mock_context = MagicMock(spec=PromptContext)
        mock_context.load_slug.side_effect = lambda slug: {
            "fragment1": fragment1_file,
            "fragment2": fragment2_file,
        }[slug]

        # Create renderer
        renderer = PromptRender(main_file)

        # Render without mocking the fragment_parser
        result = renderer.render(mock_context)

        # Assert
        assert mock_context.load_slug.call_count == 2
        assert result == "Main template with Fragment1 with Fragment2 content"

    def test_real_nested_fragments_with_arguments(self):
        """Test rendering a template with nested fragments and arguments using real fragment parser."""
        # Setup
        main_file = PromptFile(
            slug="main",
            markdown_template="Main template with {{@fragment1(param='outer')}}",
        )

        fragment1_file = PromptFile(
            slug="fragment1",
            markdown_template="Fragment1 with param={{param}} and {{@fragment2(inner_param=param)}}",
            arguments={"param": None},  # Required parameter
        )

        fragment2_file = PromptFile(
            slug="fragment2",
            markdown_template="Fragment2 with {{inner_param}}",
            arguments={"inner_param": None},  # Required parameter
        )

        # Mock context to return our fragments
        mock_context = MagicMock(spec=PromptContext)
        mock_context.load_slug.side_effect = lambda slug: {
            "fragment1": fragment1_file,
            "fragment2": fragment2_file,
        }[slug]

        # Create renderer
        renderer = PromptRender(main_file)

        # Render without mocking the fragment_parser
        result = renderer.render(mock_context)

        # Assert
        assert mock_context.load_slug.call_count == 2
        # The final output should have both fragments resolved with the arguments
        assert (
            result
            == "Main template with Fragment1 with param=outer and Fragment2 with outer"
        )

    def test_real_multiple_fragments(self):
        """Test rendering a template with multiple fragments at the same level using real fragment parser."""
        # Setup
        main_file = PromptFile(
            slug="main",
            markdown_template="Start {{@fragment1}} middle {{@fragment2}} end",
        )

        fragment1_file = PromptFile(
            slug="fragment1", markdown_template="first content", arguments={}
        )

        fragment2_file = PromptFile(
            slug="fragment2", markdown_template="second content", arguments={}
        )

        # Mock context to return our fragments
        mock_context = MagicMock(spec=PromptContext)
        mock_context.load_slug.side_effect = lambda slug: {
            "fragment1": fragment1_file,
            "fragment2": fragment2_file,
        }[slug]

        # Create renderer
        renderer = PromptRender(main_file)

        # Render without mocking the fragment_parser
        result = renderer.render(mock_context)

        # Assert
        assert mock_context.load_slug.call_count == 2
        assert result == "Start first content middle second content end"

    def test_real_complex_multiple_nested_fragments(self):
        """Test rendering with multiple fragments with multiple levels of nesting and arguments."""
        # Setup main template with multiple fragments
        main_file = PromptFile(
            slug="main",
            markdown_template=(
                "Start with {{@fragment1(name='first')}} "
                "then {{@fragment2(value=42)}} "
                "and finally {{@fragment3(items='one')}}"
            ),
        )

        # First fragment with nested reference
        fragment1_file = PromptFile(
            slug="fragment1",
            markdown_template="Fragment1 ({{name}}) contains {{@nested1(inherited=name)}}",
            arguments={"name": None},  # Required parameter
        )

        # Second fragment with no nesting
        fragment2_file = PromptFile(
            slug="fragment2",
            markdown_template="Fragment2 with value={{value}}",
            arguments={"value": "default"},  # Parameter with default
        )

        # Third fragment with nested reference that has its own nesting
        fragment3_file = PromptFile(
            slug="fragment3",
            markdown_template="Fragment3 with {{@nested2(list=items)}}",
            arguments={"items": None},  # Required parameter
        )

        # Nested fragments
        nested1_file = PromptFile(
            slug="nested1",
            markdown_template="Nested1 with {{inherited}}",
            arguments={"inherited": "unknown"},  # Parameter with default
        )

        nested2_file = PromptFile(
            slug="nested2",
            markdown_template="Nested2 listing {{list}} with {{@nested3}}",
            arguments={"list": None},  # Required parameter
        )

        nested3_file = PromptFile(
            slug="nested3",
            markdown_template="Nested3 content",
            arguments={},  # No parameters
        )

        # Mock context to return our fragments
        mock_context = MagicMock(spec=PromptContext)
        mock_context.load_slug.side_effect = lambda slug: {
            "fragment1": fragment1_file,
            "fragment2": fragment2_file,
            "fragment3": fragment3_file,
            "nested1": nested1_file,
            "nested2": nested2_file,
            "nested3": nested3_file,
        }[slug]

        # Create renderer
        renderer = PromptRender(main_file)

        # Render without mocking the fragment_parser
        result = renderer.render(mock_context)

        # Assert
        # Should have loaded each fragment once
        assert mock_context.load_slug.call_count == 6

        # Verify complete result
        expected = (
            "Start with Fragment1 (first) contains Nested1 with first "
            "then Fragment2 with value=42 "
            "and finally Fragment3 with Nested2 listing one with Nested3 content"
        )
        assert result == expected

    def test_real_comma_separated_args(self):
        """Test rendering a fragment with comma-separated values in arguments."""
        # Setup
        main_file = PromptFile(
            slug="main",
            # Let's simplify and use a literal quoted argument
            markdown_template="Main with {{@list_fragment(items='a,b,c')}}",
        )

        list_fragment = PromptFile(
            slug="list_fragment",
            markdown_template="Items: {{ items }}",
            arguments={"items": None},  # Required parameter
        )

        # Mock context to return our fragments
        mock_context = MagicMock(spec=PromptContext)
        mock_context.load_slug.return_value = list_fragment

        # Create renderer
        renderer = PromptRender(main_file)

        # Render without mocking the fragment_parser
        result = renderer.render(mock_context)

        # Assert
        assert mock_context.load_slug.call_count == 1
        # The comma-separated string will be passed directly
        assert "Items: a,b,c" in result
