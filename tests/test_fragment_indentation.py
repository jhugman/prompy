"""
Test for fragment indentation preservation.
"""

from unittest.mock import MagicMock

from prompy.prompt_context import PromptContext
from prompy.prompt_file import PromptFile
from prompy.prompt_render import PromptRender


def test_indentation_preservation():
    """Test that fragments are rendered with the same indentation as their reference."""
    # Setup prompt files
    main_file = PromptFile(
        slug="main",
        markdown_template=(
            "1. List 1, item 1\n"
            "2. List 1, item 2, it contains a sublist.\n"
            "  {{ @list2 }}\n"
            "3. List 1, item 3\n"
        ),
    )

    list2_file = PromptFile(
        slug="list2",
        markdown_template="- List 2, item 1\n- List 2, item 2",
        arguments={},
    )

    # Setup context
    mock_context = MagicMock(spec=PromptContext)
    mock_context.load_slug.return_value = list2_file

    # Create renderer
    renderer = PromptRender(main_file)

    # Render
    result = renderer.render(mock_context)

    # Expected result with proper indentation
    expected = (
        "1. List 1, item 1\n"
        "2. List 1, item 2, it contains a sublist.\n"
        "  - List 2, item 1\n"
        "  - List 2, item 2\n"
        "3. List 1, item 3"
    )

    # Assert
    assert result == expected
    mock_context.load_slug.assert_called_once_with("list2")


def test_nested_indentation():
    """Test that nested fragments maintain proper indentation."""
    # Setup prompt files
    main_file = PromptFile(
        slug="main",
        markdown_template=(
            "Main list:\n1. Item 1\n2. Item 2\n  {{ @sublist1 }}\n3. Item 3\n"
        ),
    )

    sublist1_file = PromptFile(
        slug="sublist1",
        markdown_template=(
            "- Sublist 1, item 1\n"
            "- Sublist 1, item 2\n"
            "  {{ @sublist2 }}\n"
            "- Sublist 1, item 3\n"
        ),
        arguments={},
    )

    sublist2_file = PromptFile(
        slug="sublist2",
        markdown_template="* Sublist 2, item 1\n* Sublist 2, item 2",
        arguments={},
    )

    # Setup context
    mock_context = MagicMock(spec=PromptContext)
    mock_context.load_slug.side_effect = lambda slug: {
        "sublist1": sublist1_file,
        "sublist2": sublist2_file,
    }[slug]

    # Create renderer
    renderer = PromptRender(main_file)

    # Render
    result = renderer.render(mock_context)

    # Expected result with proper nested indentation
    expected = (
        "Main list:\n"
        "1. Item 1\n"
        "2. Item 2\n"
        "  - Sublist 1, item 1\n"
        "  - Sublist 1, item 2\n"
        "    * Sublist 2, item 1\n"
        "    * Sublist 2, item 2\n"
        "  - Sublist 1, item 3\n"
        "3. Item 3"
    )

    # Assert
    assert result == expected
    assert mock_context.load_slug.call_count == 2
