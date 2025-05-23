# Prompy User Guide

This document provides detailed information about using Prompy, a command-line tool for building and managing prompts with reusable fragments.

> For command reference, directory structure, and environment variables, see [Reference](reference.md).

## Table of Contents

1. [Core Concepts](#core-concepts)
2. [A worked example](#a-worked-example)
3. [More advanced](#more-advanced)
4. [Prompt Fragments](#prompt-fragments)
5. [Fragment References](#fragment-references)
6. [Language Detection](#language-detection)
7. [Advanced Usage](#advanced-usage)

## Core Concepts

`Prompy` provides a simple templating engine optimized for combining markdown files with a simple, but
expressive syntax.

It also provides some management of these files, on a per project, or per user basis.

### Prompts and Fragments

The files, known as prompt fragments, can be divided into two sets:

1. **One-off Prompts**: Temporary prompts you're working on for immediate use
2. **Reusable Fragments**: Saved prompt templates that can be referenced and reused

### Slugs

Prompts are identified by slugs with the format:
- `project/name`: Project-specific prompt
- `language/name`: Language-specific prompt
- `fragments/name`: Generic fragment

## A worked example

To start, we'll make a new prompt fragment which we want to tell the agent in several places:

```markdown
You know when you are finished when all tests pass.
```

To make the tutorial easier to follow, you can copy this command:

```sh
echo "You know when you are finished when all tests pass." | prompy new --save generic/all-tests-pass
```

This saves the markdown into a prompt called `generic/all-tests-pass`.

Now you can start a new prompt with the following command:

```sh
prompy new
```

This will open an editor, which you can paste the following:

```markdown
1. Implement some functionality.
2. {{ @generic/all-tests-pass() }}
```

Once you save and quit the editor, you can use the shell command to get the expanded prompt:

```sh
prompy out
```

This will render:

```markdown
1. Implement some functionality.
2. You know when you are finished when all tests pass.
```

You can get this into your clipboard and paste it into your prompt box.

```sh
prompy out --pbcopy
```

or just:

```sh
prompy pbcopy
```

We can save this prompt for later re-use:

```sh
prompy save implement-my-feature
```

## More advanced

Now we have a fragment of a prompt put into another. These can be nested arbitrarily deep.

Let's say that the running the tests requires a set up step, which only is needed once per prompt. From experience, Copilot gets confused if the steps aren't added: it gets there in the end, but spends a long time finding out what we could have told it.

We can define a project specific set up. In our example, we use `uv`. So let's define a prompt for the project:

```markdown
uv venv && uv sync --all-extras && source .venv/bin/activate
```

We can launch an editor to paste the above command into:

```sh
prompy new
```

Then save it as a project specific file:

```sh
prompy save 'project/init-shell'
```

OR, we can do the whole thing with:

```sh
echo "uv venv && uv sync --all-extras && source .venv/bin/activate" | prompy new --save 'project/init-shell'
```

Let's make another prompt fragment to tell the LLM to use this:

```sh
echo 'Run the following command first: `{{ @project/init-shell() }}`' | prompy new --save generic/init-shell
```

Now, let's go back to our original example prompt:

```sh
prompy edit implement-my-feature
```

```markdown
1. {{ @generic/init-shell() }}
2. Implement some functionality.
3. {{ @generic/all-tests-pass() }}
```

Finally, we can run:

```sh
prompy out implement-my-feature
```

This expands to something you can paste into a LLM prompt.

```markdown
1. Run the following command first: `uv venv && uv sync --all-extras && source .venv/bin/activate`
2. Implement some functionality.
3. You know when you are finished when all tests pass.
```

# More advanced examples can be found below

The `$PROJECT_DIR` is defined as the first directory with the `.git` directory, starting with the current directory, then walking back up to the root.

If the `$PROJECT_DIR` contains a directory called `.prompy`, then files are saved there.

## Prompt Fragments

### File Structure

Prompt fragments are stored as markdown files with YAML frontmatter:

```markdown
---
description: A description of the prompt
categories: [category1, category2]
arguments:
  arg1: Default value
  arg2: # required
---

# Markdown content goes here

This is a template that can use $arg1 and $arg2 variables.
```

### Arguments

Arguments are passed to templates and can be referenced:
- `$argument_name`: Will be replaced with the argument value
- Default values can be provided within the fragment reference

## Fragment References

Reference other fragments using the Jinja2 syntax:

```markdown
{{ @fragments/common-header(project="MyProject", description="A tool for managing widgets") }}

# Main content here with Jinja2 features
{% for example in ["basic", "advanced"] %}
  ## {{ example|capitalize }} Example
  {{ @fragments/code-example(language="python", type=example) }}
{% endfor %}

{{ @fragments/common-footer() }}
```

### Reference Syntax

The basic syntax is:
```
{{ @slug(arg1="value1", arg2="value2") }}
```

Arguments can be:
- String literals: `"value"` or `'value'`
- Variables from the parent template: `variable`
- Omitted (if they have defaults)
- Other fragments for nested inclusion: e.g.
    `@another-fragment`, `@another-fragment-with-arguments(arg1='foo')`

### Jinja2 Features

With the Jinja2-enhanced syntax, you can use powerful templating features:

#### Conditionals

```markdown
{% if advanced_user %}
  {{ @fragments/advanced-instructions() }}
{% else %}
  {{ @fragments/basic-instructions() }}
{% endif %}
```

#### Loops

```markdown
{% for language in ["python", "javascript", "rust"] %}
  ## {{ language|capitalize }} Example
  {{ @fragments/code-example(language=language) }}
{% endfor %}
```

#### Variables

```markdown
{% set project_name = "MyProject" %}
{{ @fragments/common-header(project=project_name) }}
```

## Language Detection

Language detection is configured in the `detections.yaml` file:

```yaml
rules:
  python:
    extensions: [".py", ".pyx"]
    filenames: ["Pipfile", "setup.py", "requirements.txt"]
    content_patterns: ["import", "from .* import", "def"]

  javascript:
    extensions: [".js", ".jsx", ".mjs"]
    filenames: ["package.json", "webpack.config.js"]
    content_patterns: ["import .* from", "export", "const", "let"]
```

## Configuration

See [Reference](reference.md#environment-variables) for configuration options and environment variables.

## Advanced Usage

### Using STDIN

You can pipe content into Prompy to append to your prompt:

```bash
echo "# Additional information" | prompy new
```

### Multiple Project Support

Prompy supports multiple projects with project-specific prompts:

1. Global prompts in `$PROMPY_CONFIG_DIR/prompy/`
2. Project prompts in `$PROJECT_DIR/.prompy/`

Use the `--global` flag to use only global prompts.
