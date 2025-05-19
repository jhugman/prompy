---
description: Template for generating unit tests
categories: [testing, python]
arguments:
  file: The file to generate tests for
---

<<<<<<< HEAD
{{
  @fragments/code-header(
    task="Unit Test Generation",
    context="I need comprehensive unit tests for my code."
  )
}}
=======
@fragments/code-header(task="Unit Test Generation", context="I need comprehensive unit tests for my code.")
>>>>>>> 142bbdf (PROMPT 13: Complete documentation and distribution setup)

## File to Test
{{file}}

Please generate unit tests that:
1. Test all functions and methods
2. Include edge cases and error conditions
3. Achieve high test coverage
4. Follow testing best practices for Python
5. Use pytest as the testing framework

<<<<<<< HEAD
{{ @fragments/code-footer() }}
=======
@fragments/code-footer
>>>>>>> 142bbdf (PROMPT 13: Complete documentation and distribution setup)
