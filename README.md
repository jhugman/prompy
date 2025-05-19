# Prompy

A command-line tool for building prompts with reusable fragments. Prompy helps you create, manage, and share prompt templates for AI tools like Copilot or other LLM-based code helpers.

[![Build Status](https://img.shields.io/badge/build-passing-brightgreen.svg)](https://github.com/yourusername/prompy)
[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Features

- 📝 **Template Management**: Create reusable prompt fragments that can reference each other
- 📂 **Project and Language Detection**: Automatically detects the current project and language
- 🔗 **Fragment References**: Include and combine prompt fragments with `@fragment-name` syntax
- ✏️ **Editor Integration**: Opens your preferred editor to customize prompts
- 📋 **Clipboard Support**: Copy final prompts directly to your clipboard
- 🔄 **Caching**: Automatically caches in-progress prompts between sessions
- 🔍 **Powerful CLI**: Complete command-line interface with bash/zsh/fish completions

## Installation

### Using pip

```bash
pip install prompy
```

### From source

```bash
git clone https://github.com/yourusername/prompy.git
cd prompy
pip install .
```

### Shell Completion Setup

Generate shell completion scripts:

```bash
# For bash
prompy completions bash > ~/.prompy-completion.bash
echo 'source ~/.prompy-completion.bash' >> ~/.bashrc

# For zsh
prompy completions zsh > ~/.zsh/_prompy
echo 'fpath=(~/.zsh $fpath)' >> ~/.zshrc
echo 'autoload -U compinit && compinit' >> ~/.zshrc

# For fish
prompy completions fish > ~/.config/fish/completions/prompy.fish
```

## Quick Start

1. Set up your configuration directory:

```bash
export PROMPY_CONFIG_DIR=~/.config/prompy
```

2. Create and edit a new prompt:

```bash
prompy new
```

3. Output your prompt:

```bash
prompy out

# Copy to clipboard
prompy pbcopy
```

## Usage

```bash
prompy [options] [PROMPT_SLUG]      # Traditional usage
prompy <command> [options]          # Subcommand usage
```

### Global Options

- `--version`: Show version information and exit
- `--help`: Show help message and exit
- `--debug`: Enable debug logging for detailed error information
- `--language LANG`: Specify the language manually
- `--project PROJECT`: Specify the project manually
- `--global`, `-g`: Use prompts not saved in the project directory

### Working with One-Off Prompts

```bash
# Start a new prompt (clears any existing cached prompt)
prompy new [TEMPLATE_SLUG]

# Edit the current one-off prompt
prompy edit

# Output the current prompt to stdout
prompy out

# Output the current prompt to a file
prompy out --file output.md

# Copy the current prompt to clipboard
prompy pbcopy
```

### Managing Reusable Prompts

```bash
# List available prompts
prompy list [--project PROJECT] [--language LANG] [--category CATEGORY]

# Edit or create a reusable prompt directly
prompy edit PROMPT_SLUG

# Save the current one-off prompt as a reusable fragment
prompy save PROMPT_SLUG [--description DESC] [--category CAT]

# Move/rename a prompt
prompy mv SOURCE_SLUG DEST_SLUG [--force]

# Copy a prompt to a new location
prompy cp SOURCE_SLUG DEST_SLUG [--force]

# Remove a prompt
prompy rm PROMPT_SLUG [--force]

# Edit language detection rules
prompy detections [--validate]
```

### Shell Completion

```bash
# Generate shell completion script
prompy completions SHELL [--output FILE]
```

## Configuration

Prompy uses the following directory structure:

```
$PROMPY_CONFIG_DIR/
├── prompts/             # Global prompt fragments
│   ├── fragments/       # Generic reusable fragments
│   ├── languages/       # Language-specific fragments
│   ├── projects/        # Project-specific fragments
│   └── tasks/           # Task-specific fragments
├── cache/               # Cache for one-off prompts
│   └── $project/        # Project-specific cache
└── detections.yaml      # Language detection rules
```

Project-specific prompts can also be stored in:

```
$PROJECT_DIR/.prompts/   # Project-specific prompt fragments
```

### Prompt Files

Prompt files consist of YAML frontmatter and markdown content:

```markdown
---
description: A helpful prompt for generating tests
categories: [testing, python]
arguments:
  file: The file to generate tests for
  language: The programming language (defaults to python)
---
Write tests for the {{file}} file in {{language}}.
Include unit tests for each function.
```

### Fragment References

Reference other prompt fragments using `@fragment-name` syntax:

```markdown
# My Custom Prompt

@common/header(project="MyProject")

Please implement the following:
1. A function to parse user input
2. Error handling for invalid inputs
3. @common/testing-requirements

@common/footer
```

## Troubleshooting

### Common Issues

1. **Prompy can't find my project**
   - Make sure you're in a git repository or specify `--project` manually
   - Check if your project directory has a `.git` folder

2. **Language detection is incorrect**
   - Specify the language manually with `--language`
   - Customize detection rules with `prompy detections`

3. **Shell completion doesn't work**
   - Ensure completion scripts are properly sourced in your shell config
   - Restart your shell after installing completion scripts

## Development

See [DEVELOPMENT.md](./DEVELOPMENT.md) for detailed development information.
