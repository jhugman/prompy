"""
Test module for the preprocess_template function in the Jinja2 extension.
"""

from prompy.jinja_extension import preprocess_template


def test_preprocess_template_simple_include_no_brackets():
    """Test preprocessing a template with a simple include without brackets."""
    template = "Here is a fragment reference: {{ @fragment }}"
    result = preprocess_template(template)
    expected = (
        'Here is a fragment reference: {{ include_fragment("fragment", indent="") }}'
    )
    assert result == expected


def test_preprocess_template_simple_include_with_brackets():
    """Test preprocessing a template with a simple include with brackets but no arguments."""
    template = "Here is a fragment reference: {{ @fragment() }}"
    result = preprocess_template(template)
    # The regex pattern in the preprocess_template function leaves the empty parens content
    expected = (
        'Here is a fragment reference: {{ include_fragment("fragment", indent="") }}'
    )
    assert result == expected


def test_preprocess_template_include_with_string_args():
    """Test preprocessing a template with an include that has string arguments."""
    template = (
        "Here is a fragment reference: {{ @fragment(arg1='value1', arg2='value2') }}"
    )
    result = preprocess_template(template)
    expected = "Here is a fragment reference: {{ include_fragment(\"fragment\", arg1='value1', arg2='value2', indent=\"\") }}"
    assert result == expected


def test_preprocess_template_include_with_variable_args():
    """Test preprocessing a template with an include that has variable arguments."""
    template = "Here is a fragment reference: {{ @fragment(arg1=var1, arg2=var2) }}"
    result = preprocess_template(template)
    expected = 'Here is a fragment reference: {{ include_fragment("fragment", arg1=var1, arg2=var2, indent="") }}'
    assert result == expected


def test_preprocess_template_with_indentation():
    """Test preprocessing a template with indented include."""
    template = "List:\n  - Item 1\n   {{ @fragment }}\n  - Item 3"
    result = preprocess_template(template)
    expected = 'List:\n  - Item 1\n   {{ include_fragment("fragment", indent="   ") }}\n  - Item 3'
    assert result == expected


def test_preprocess_template_with_complex_indentation():
    """Test preprocessing a template with complex indented include."""
    template = "List:\n    - Item 1\n      {{ @fragment(param='test') }}\n    - Item 3"
    result = preprocess_template(template)
    expected = 'List:\n    - Item 1\n      {{ include_fragment("fragment", param=\'test\', indent="      ") }}\n    - Item 3'
    assert result == expected


def test_preprocess_template_nested_includes_as_args():
    """Test preprocessing a template with an include that has other includes as values."""
    template = "Here is a fragment reference: {{ @fragment(arg1=@other_fragment) }}"
    result = preprocess_template(template)
    expected = 'Here is a fragment reference: {{ include_fragment("fragment", arg1=include_fragment("other_fragment", indent=""), indent="") }}'
    assert result == expected


def test_preprocess_template_with_nested_includes():
    """Test preprocessing a template with multiple nested includes."""
    template = "{{ @outer(content=@inner(value='test')) }}"
    result = preprocess_template(template)
    # The function doesn't recursively process nested includes in arguments
    expected = '{{ include_fragment("outer", content=include_fragment("inner", value=\'test\', indent=""), indent="") }}'
    assert result == expected


def test_preprocess_template_with_nested_includes_and_indentation():
    """Test preprocessing a template with multiple nested includes."""
    template = "A list:\n  {{ @outer(content=@inner(value='test')) }}"
    result = preprocess_template(template)
    # The function doesn't recursively process nested includes in arguments
    expected = 'A list:\n  {{ include_fragment("outer", content=include_fragment("inner", value=\'test\', indent=""), indent="  ") }}'
    assert result == expected


def test_preprocess_template_with_multi_nested_includes_and_indentation():
    """Test preprocessing a template with multiple nested includes."""
    template = "A list:\n  {{ @outer(content=@inner(value=@innerest)) }}"
    result = preprocess_template(template)
    # The function doesn't recursively process nested includes in arguments
    expected = 'A list:\n  {{ include_fragment("outer", content=include_fragment("inner", value=include_fragment("innerest", indent=""), indent=""), indent="  ") }}'
    assert result == expected


def test_preprocess_template_multiple_references():
    """Test preprocessing a template with multiple fragment references."""
    template = "First: {{ @fragment1 }}\nSecond: {{ @fragment2(arg='value') }}"
    result = preprocess_template(template)
    expected = 'First: {{ include_fragment("fragment1", indent="") }}\nSecond: {{ include_fragment("fragment2", arg=\'value\', indent="") }}'
    assert result == expected


def test_preprocess_template_complex_path():
    """Test preprocessing a template with a fragment that has a complex path."""
    template = "Here is a fragment reference: {{ @fragments/subfolder/fragment }}"
    result = preprocess_template(template)
    expected = 'Here is a fragment reference: {{ include_fragment("fragments/subfolder/fragment", indent="") }}'
    assert result == expected


def test_preprocess_template_mixed_references():
    """Test preprocessing a template with a mix of fragment references and regular expressions."""
    template = "Regular: {{ variable }}\nFragment: {{ @fragment }}\nMixed: {{ variable + @fragment }}"
    result = preprocess_template(template)
    expected = 'Regular: {{ variable }}\nFragment: {{ include_fragment("fragment", indent="") }}\nMixed: {{ variable + include_fragment("fragment", indent="") }}'
    assert result == expected


def test_preprocess_template_real_mixed():
    """Test preprocessing a template with a mix of fragment references and regular expressions."""
    template = (
        "{{@prompt/improve(prompt=@rules/avoid-mocks, slug='rules/avoid-mocks1')}}"
    )
    result = preprocess_template(template)
    expected = '{{ include_fragment("prompt/improve", prompt=include_fragment("rules/avoid-mocks", indent=""), slug=\'rules/avoid-mocks1\', indent="") }}'
    assert result == expected
