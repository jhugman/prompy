---
description: Template for asking code review questions
categories: [code, review]
arguments:
  file: The file to review
  language: The programming language (optional)
---

<<<<<<< HEAD
{{ @fragments/code-header(task="Code Review", context="I need a thorough code review of the following file.") }}
=======
@fragments/code-header(task="Code Review", context="I need a thorough code review of the following file.")
>>>>>>> 142bbdf (PROMPT 13: Complete documentation and distribution setup)

## File to Review
{{file}}

Please review this code for:
1. Potential bugs or errors
2. Security vulnerabilities
3. Performance issues
4. Code style and best practices{% if language %}
5. {{language}}-specific concerns{% endif %}

<<<<<<< HEAD
{{ @fragments/code-footer() }}
=======
@fragments/code-footer
>>>>>>> 142bbdf (PROMPT 13: Complete documentation and distribution setup)
