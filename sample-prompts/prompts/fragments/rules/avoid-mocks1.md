---
title: Best Practices for Test Mocking and Patching
description: Guidelines for maintaining resilient test code with minimal mocking
arguments:
  system_name: the system
---

# Mocking and Patching Best Practices

<principles>
When writing tests, follow these core principles about mocking and patching:

1. **Minimize Mocks**: Each additional mock increases brittleness and decreases resilience to change in {{system_name}}.

2. **Edge-Only Mocking**: Only mock or patch components at the boundaries of {{system_name}}, such as:
   - External API calls
   - File system operations
   - Network requests
   - Database connections
   - Process spawning

3. **Prefer Real Implementations**: Use actual implementations for internal components whenever possible.

4. **Use Fixture Directories**: Instead of programmatically creating test files:
   - Store test data in fixture directories
   - Load test data from these fixtures during tests
   - Avoid writing files to disk in test code
</principles>

<reasoning>
When deciding whether to use mocks in tests, follow this thought process:

1. Identify what you're testing and what external dependencies it has
2. Ask: "Is this dependency at the edge of {{system_name}}?"
   - If YES: Consider mocking only if necessary
   - If NO: Avoid mocking; use the real implementation

3. For each potential mock, evaluate:
   - Will mocking make tests more brittle to implementation changes?
   - Will real implementations significantly slow down tests?
   - Is the dependency unpredictable (like network calls)?

4. If you must use test data files:
   - Create them as fixtures in a dedicated directory
   - Version control these fixtures
   - Load them during tests rather than generating them
</reasoning>

<examples>
## Good Example: Edge-Only Mocking

```python
# Testing a function that makes API calls
def test_data_processor():
    # GOOD: Mock only the external API call
    with mock.patch('requests.get') as mock_get:
        mock_get.return_value.json.return_value = {'data': [1, 2, 3]}

        # Use real implementation of internal processing
        result = process_external_data()
        assert result == [2, 4, 6]
```

## Bad Example: Excessive Mocking

```python
# Testing a function with excessive mocks
def test_data_processor_bad():
    # BAD: Mocking internal components
    with mock.patch('module.DataProcessor') as mock_processor:
        with mock.patch('module.DataValidator') as mock_validator:
            with mock.patch('module.DataTransformer') as mock_transformer:
                mock_validator.is_valid.return_value = True
                mock_transformer.transform.return_value = [2, 4, 6]

                result = process_external_data()
                assert result == [2, 4, 6]
                # This test is brittle and will break if internal implementation changes
```

## Good Example: Using Fixture Directories

```python
# Testing with fixture directories
def test_config_parser():
    # GOOD: Load test data from fixture directory
    config_path = os.path.join('tests', 'fixtures', 'configs', 'valid_config.yaml')

    result = parse_config(config_path)
    assert result['feature_enabled'] == True
```

## Bad Example: Creating Files in Tests

```python
# Testing by writing files in test code
def test_config_parser_bad():
    # BAD: Creating test files programmatically
    temp_file = 'temp_config.yaml'
    with open(temp_file, 'w') as f:
        f.write('feature_enabled: true')

    try:
        result = parse_config(temp_file)
        assert result['feature_enabled'] == True
    finally:
        os.remove(temp_file)  # Cleanup that might fail
```
</examples>
