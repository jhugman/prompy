"""
Tests for the frontmatter module.
"""

from prompy.frontmatter import (
    extract_arguments_from_content,
    extract_description_from_content,
    generate_frontmatter,
)


def test_extract_arguments_from_content_with_variables():
    """Test extracting arguments from content with variables."""
    content = "This prompt uses {{variable_name}} and {{another_variable}}."
    args = extract_arguments_from_content(content)

    assert args is not None
    assert "variable_name" in args
    assert "another_variable" in args
    assert args["variable_name"] is None
    assert args["another_variable"] is None


def test_extract_arguments_from_content_with_no_variables():
    """Test extracting arguments from content without variables."""
    content = "This prompt has no variables."
    args = extract_arguments_from_content(content)

    assert args is None


def test_extract_arguments_from_content_filters_template_inclusions():
    """Test that common words are filtered out."""
    content = "Set up a $project in {{@language/foo}} with {{@bar-baz}} variables."
    args = extract_arguments_from_content(content)

    assert args is None  # All found variables are in the common_words list


def test_extract_arguments_from_content_mixed():
    """Test with both common words and actual variables."""
    content = "Set up a $project in {{@language}} with {{ custom_variable }}."
    args = extract_arguments_from_content(content)

    assert args is not None
    assert "custom_variable" in args
    assert "project" not in args
    assert "language" not in args


def test_generate_frontmatter_with_provided_description():
    """Test generating frontmatter with a provided description."""
    content = "This is the content.\nMore content."
    description = "Custom description"
    categories = ["test", "example"]

    frontmatter = generate_frontmatter(content, description, categories)

    assert frontmatter["description"] == "Custom description"
    assert frontmatter["categories"] == ["test", "example"]
    assert "args" not in frontmatter


def test_generate_frontmatter_description_first_sentence():
    """Test that description is generated from first sentence."""
    content = "Do one thing. It is good."

    frontmatter = generate_frontmatter(content)

    assert frontmatter["description"] == "Do one thing"


def test_extract_description_from_content_numbered_list():
    """Test that description works with numbered lists."""
    content = "1. Do some thing\n2. Do the next"

    description = extract_description_from_content(content)

    assert description == "Do some thing"


def test_extract_description_from_content_actual_content():
    """Test that description works with numbered lists."""
    content = """
{{ @rules/all }}

{{ @steps/init-shell }}

`foo_method` and `bar_method` is not being sufficiently tested. Please generate
tests to test at least the following:
"""

    description = extract_description_from_content(content)

    assert (
        description == "`foo_method` and `bar_method` is not being sufficiently tested"
    )


def test_extract_description_from_content_with_template_2cr():
    """Test that description works with template inclusion."""
    content = "{{ @template-inclusion }}\n\nDo the thing, then another."

    description = extract_description_from_content(content)

    assert description == "Do the thing, then another"


def test_extract_description_from_content_with_template_1cr():
    """Test that description works with template inclusion."""
    content = "{{ @template-inclusion }}\nDo the thing, then another."

    description = extract_description_from_content(content)

    assert description == "Do the thing, then another"


def test_generate_frontmatter_description_with_muliple_templates():
    """Test that description works with template inclusion."""
    content = (
        "{{ @template-inclusion }} {{ @template-inclusion1 }}{{ variable }}"
        "Do the thing, then another."
    )

    description = extract_description_from_content(content)

    assert description == "Do the thing, then another"


def test_extract_description_from_content_long_description_truncation():
    """Test that long descriptions are truncated."""
    content = (
        "This is a very long first sentence that should be truncated because "
        "it exceeds the maximum length limit for descriptions in the "
        "frontmatter generation process."
    )

    description = extract_description_from_content(content)
    assert len(description) <= 80
    assert description.endswith("…")


def test_generate_frontmatter_with_arguments():
    """Test that arguments are included in frontmatter."""
    content = "This prompt uses {{ variable_name}} and {{another_variable }}."

    frontmatter = generate_frontmatter(content)

    assert "args" in frontmatter
    assert "variable_name" in frontmatter["args"]
    assert "another_variable" in frontmatter["args"]
