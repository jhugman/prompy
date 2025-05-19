# Prompy User Guide

This document provides detailed information about using Prompy, a command-line tool for building and managing prompts with reusable fragments.

## Table of Contents

1. [Core Concepts](#core-concepts)
2. [Command Reference](#command-reference)
3. [Prompt Fragments](#prompt-fragments)
4. [Fragment References](#fragment-references)
5. [Language Detection](#language-detection)
6. [Configuration](#configuration)
7. [Advanced Usage](#advanced-usage)

## Core Concepts

### Prompts and Fragments

Prompy uses two key concepts:

1. **One-off Prompts**: Temporary prompts you're working on for immediate use
2. **Reusable Fragments**: Saved prompt templates that can be referenced and reused

### Slugs

Prompts are identified by slugs with the format:
- `$project/name`: Project-specific prompt
- `$language/name`: Language-specific prompt
- `fragments/name`: Generic fragment
- `tasks/name`: Task-specific fragment

### Directory Structure

```
$PROMPY_CONFIG_DIR/
├── prompts/
│   ├── fragments/       # Generic reusable fragments
│   ├── languages/       # Language-specific fragments
│   ├── projects/        # Project-specific fragments
│   └── tasks/           # Task-specific fragments
├── cache/               # Cache for one-off prompts
│   └── $project/        # Project-specific cache
└── detections.yaml      # Language detection rules
```

Project-specific prompts can also be stored in `$PROJECT_DIR/.prompy/`.

## Command Reference

### Global Options

These options apply to all commands:

```bash
prompy [options] [COMMAND]
```

- `--version`: Show the version and exit
- `--help`: Show the help message and exit
- `--debug`: Enable debug logging for detailed error information
- `--language LANG`: Specify the language manually
- `--project PROJECT`: Specify the project manually
- `--global`, `-g`: Use prompts not saved in the project directory

### Working with One-Off Prompts

#### `new` - Start a new prompt

```bash
prompy new [TEMPLATE_SLUG]
```

Creates a new one-off prompt, optionally using an existing prompt as a template. Clears any existing cached prompt for the current project.

Options:
- `TEMPLATE_SLUG`: Optional - an existing prompt to use as a template

Examples:
```bash
prompy new
prompy new fragments/common/base
prompy new python/class
```

#### `edit` - Edit a prompt

```bash
prompy edit [PROMPT_SLUG]
```

Opens a prompt for editing in your default editor. If no slug is specified, edits the current one-off prompt.

Options:
- `PROMPT_SLUG`: Optional - the prompt to edit (if not provided, edits the one-off prompt)

Examples:
```bash
prompy edit
prompy edit fragments/code-review
```

#### `out` - Output a prompt

```bash
prompy out [PROMPT_SLUG] [--file FILE] [--pbcopy]
```

Outputs the final prompt to stdout, a file, or the clipboard.

Options:
- `PROMPT_SLUG`: Optional - the prompt to output (if not provided, outputs the one-off prompt)
- `--file`, `-f`: Output to a file
- `--pbcopy`: Copy to clipboard

Examples:
```bash
prompy out
prompy out fragments/code-review
prompy out --file my-prompt.md
prompy out --pbcopy
```

#### `pbcopy` - Copy to clipboard

```bash
prompy pbcopy [PROMPT_SLUG]
```

Copies a prompt to the clipboard. Shortcut for `prompy out --pbcopy`.

Options:
- `PROMPT_SLUG`: Optional - the prompt to copy (if not provided, copies the one-off prompt)

Examples:
```bash
prompy pbcopy
prompy pbcopy fragments/code-review
```

### Managing Reusable Prompts

#### `list` - List available prompts

```bash
prompy list [--project PROJECT] [--language LANG] [--category CATEGORY] [--format FORMAT]
```

Lists available prompts, filtered by project, language, and category.

Options:
- `--project`: Filter by project
- `--language`: Filter by language
- `--category`: Filter by category
- `--format`: Output format: 'simple' (just slugs) or 'detailed' (with descriptions)

Examples:
```bash
prompy list
prompy list --project myproject
prompy list --language python --category testing
```

#### `save` - Save a prompt

```bash
prompy save PROMPT_SLUG [--description DESC] [--category CAT...] [--force]
```

Saves the current one-off prompt as a reusable prompt fragment.

Options:
- `PROMPT_SLUG`: Where to save the prompt
- `--description`, `-d`: Description of the prompt
- `--category`, `-c`: Categories for the prompt (can be specified multiple times)
- `--force`, `-f`: Overwrite existing prompt without confirmation

Examples:
```bash
prompy save fragments/my-new-prompt
prompy save python/snippets/error-handling --description "Error handling examples" --category errors
```

#### `mv` - Move/rename a prompt

```bash
prompy mv SOURCE_SLUG DEST_SLUG [--force]
```

Moves or renames a prompt from one location to another.

Options:
- `SOURCE_SLUG`: Current location of the prompt
- `DEST_SLUG`: New location for the prompt
- `--force`, `-f`: Overwrite existing prompt without confirmation

Examples:
```bash
prompy mv fragments/old-name fragments/new-name
prompy mv python/old-prompt javascript/new-prompt
```

#### `cp` - Copy a prompt

```bash
prompy cp SOURCE_SLUG DEST_SLUG [--force]
```

Copies a prompt to a new location.

Options:
- `SOURCE_SLUG`: Source location of the prompt
- `DEST_SLUG`: Destination location for the prompt copy
- `--force`, `-f`: Overwrite existing prompt without confirmation

Examples:
```bash
prompy cp fragments/template python/my-template
```

#### `rm` - Remove a prompt

```bash
prompy rm PROMPT_SLUG [--force]
```

Removes a prompt.

Options:
- `PROMPT_SLUG`: Which prompt to remove
- `--force`, `-f`: Remove without confirmation

Examples:
```bash
prompy rm fragments/obsolete-prompt
```

### Configuration and Utilities

#### `detections` - Edit language detection rules

```bash
prompy detections [--validate]
```

Opens the detections.yaml file in your editor for customizing language detection rules.

Options:
- `--validate`: Validate the file format without opening the editor

Examples:
```bash
prompy detections
prompy detections --validate
```

#### `completions` - Generate shell completions

```bash
prompy completions SHELL [--output FILE]
```

Generates shell completion scripts.

Options:
- `SHELL`: Which shell to generate completions for (bash, zsh, or fish)
- `--output`, `-o`: Output file to write the completion script to

Examples:
```bash
prompy completions bash
prompy completions zsh --output ~/.zsh/_prompy
```

## Prompt Fragments

### File Structure

Prompt fragments are stored as markdown files with YAML frontmatter:

```markdown
---
description: A description of the prompt
categories: [category1, category2]
arguments:
  arg1: Description of the first argument
  arg2: Description of the second argument (optional)
---

# Markdown content goes here

This is a template that can use {{arg1}} and {{arg2}} variables.
```

### Arguments

Arguments are passed to templates and can be referenced using Jinja2-style syntax:
- `{{argument_name}}`: Will be replaced with the argument value
- Default values can be provided within the fragment reference

## Fragment References

Reference other fragments using the `@fragment-name` syntax:

```markdown
@fragments/common-header(project="MyProject", description="A tool for managing widgets")

# Main content here

@fragments/code-example(language="python")

@fragments/common-footer
```

### Reference Syntax

The basic syntax is:
```
@slug(arg1="value1", arg2="value2")
```

Arguments can be:
- String literals: `"value"` or `'value'`
- Variables from the parent template: `{{variable}}`
- Omitted (if they have defaults)

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

Prompy can be configured via environment variables:

- `PROMPY_CONFIG_DIR`: Where to store configuration files (default: `~/.config/prompy`)
- `EDITOR`: Which editor to use for editing prompts (default: system default)

## Advanced Usage

### Using STDIN

You can pipe content into Prompy to append to your prompt:

```bash
echo "# Additional information" | prompy new
```

### Multiple Project Support

Prompy supports multiple projects with project-specific prompts:

1. Global prompts in `$PROMPY_CONFIG_DIR/prompts/`
2. Project prompts in `$PROJECT_DIR/.prompts/`

Use the `--global` flag to use only global prompts.
