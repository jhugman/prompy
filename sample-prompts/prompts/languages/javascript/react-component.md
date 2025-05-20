---
description: Template for creating a new JavaScript component
categories: [javascript, react]
arguments:
  component_name: The name of the component
  props: Description of component props (optional)
---

{{ @fragments/code-header(task="Create React Component", context="I need a new React component built with modern best practices.") }}

## Component Details
Name: {{component_name}}
{% if props %}Props: {{props}}{% endif %}

Please implement this component with:
1. Functional component syntax
2. React hooks for state management (if needed)
3. Proper TypeScript typing
4. Styled-components for styling
5. Jest/React Testing Library tests

{{ @fragments/code-footer() }}
