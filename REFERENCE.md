# Command and Configuration Reference

This document provides reference information including command-line options, directory structure, and environment variables.

The typical command flow for using the tool is:

1. Create a prompt: `prompy new`
2. Edit the prompt in your editor
3. Output the prompt: `prompy out` or `prompy pbcopy` to copy to clipboard
4. Save for reuse: `prompy save fragment-name`

For more detailed usage examples, see the [User Guide](user_guide.md).

## Command Reference

### Global Options

These options apply to all commands:

```bash
prompy [options] [COMMAND]
```

- `--version`: Show the version and exit
- `--help`: Show the help message and exit
- `--debug`: Enable debug logging
- `--language LANG`: Specify the language manually
- `--project PROJECT`: Specify the project manually
- `--global`, `-g`: Use prompts not saved in the project directory

If no command is specified, Prompy will behave as if 'edit' was called.

### Working with One-Off Prompts

#### `new` - Start a new prompt

```bash
prompy new [STARTER_SLUG] [--save NEW_PROMPT_SLUG]
```

Creates a new one-off prompt, optionally using an existing prompt as a template. Clears any existing cached prompt for the current project.

Options:
- `STARTER_SLUG`: Optional - an existing prompt to use as a starting point
- `--save NEW_PROMPT_SLUG`: Optional - save the prompt with the specified slug

Examples:
```bash
prompy new
prompy new generic/run-all-tests
prompy new 'project/init-shell'
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

If no output option is specified, the prompt is printed to standard output.

Examples:
```bash
prompy out
prompy out code-review
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
prompy pbcopy code-review
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
- `--format`: Output format: 'simple' (just slugs) or 'detailed' (with descriptions, default)

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
prompy save my-new-prompt
prompy save 'language/snippets/error-handling' --description "Error handling examples" --category errors
```

#### `mv` - Move/rename a prompt

```bash
prompy mv SOURCE_SLUG DEST_SLUG [--force]
```

Moves or renames a prompt from one location to another.

This command also updates references to the moved prompt in other prompt files.

Options:
- `SOURCE_SLUG`: Current location of the prompt
- `DEST_SLUG`: New location for the prompt
- `--force`, `-f`: Overwrite existing prompt without confirmation

Examples:
```bash
prompy mv old-name new-name
prompy mv 'project/init-shell' 'language/init-shell-uv'
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
prompy cp template my-template
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
If the file doesn't exist, it will be created with default rules.

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

If no output file is specified, the completion script will be printed to stdout along with installation instructions.

Examples:
```bash
prompy completions bash
prompy completions zsh --output ~/.zsh/_prompy
```

## Directory Structure

```
$PROMPY_CONFIG_DIR/
├── prompts/
│   ├── languages/       # Language-specific fragments
│   │   ├── python/
│   │   ├── rust/
│   │   └── <language>/
│   ├── projects/        # Project-specific fragments
│   │   └── <my-project>/
│   └── fragments/       # Generic reusable fragments
├── cache/               # Cache for one-off prompts
│   └── <my-project>/    # Project-specific cache
└── detections.yaml      # Language detection rules
```

Project-specific prompts can also be stored in `$PROJECT_DIR/.prompy/`. This optional directory is
structured slightly differently:

```
$PROJECT_DIR/
└── .prompy
    ├── project/       # Generic reusable fragments
    ├── environment/       # Language-specific fragments
    └── fragments/           # Task-specific fragments
```

The `$PROJECT_DIR` is defined as the first directory with the `.git` directory, starting with the current directory, then walking back up to the root.

If the `$PROJECT_DIR` contains a directory called `.prompy`, then files are saved there.

## Language Detection Configuration

Language detection is configured in the `detections.yaml` file, which can be edited with the `detections` command.

The file structure uses the following format:

```yaml
python:
  file_patterns:
    - "*.py"
    - "requirements.txt"
  dir_patterns:
    - ".venv"
    - "__pycache__"
  content_patterns:
    - "import "
    - "def "
  weight: 1.0

javascript:
  file_patterns:
    - "*.js"
    - "*.jsx"
    - "package.json"
  dir_patterns:
    - "node_modules"
  content_patterns:
    - "import "
    - "export "
  weight: 1.0
```

For each language, you can define:
- `file_patterns`: List of file patterns (glob) that indicate this language
- `dir_patterns`: List of directory patterns (glob) that indicate this language
- `content_patterns`: List of strings to look for in file contents
- `weight`: Optional weight multiplier for this language (default: 1.0)

## Prompt File Format

### Front matter

Prompt fragments are stored as markdown files with YAML front matter:

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

The front matter section contains metadata about the prompt:
- `description`: A short description of what the prompt does
- `categories`: A list of categories for organization and filtering
- `arguments`: Parameters that can be passed when referencing this fragment

## Environment Variables

The application can be configured via environment variables:

- `PROMPY_CONFIG_DIR`: Where to store configuration files (default: `~/.config/prompy`)
- `EDITOR`: Which editor to use for editing prompts (default: system default)
