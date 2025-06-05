# Prompy

**Build better prompts with reusable, composable fragments.**

Prompy is a command-line tool that helps you create, manage, and share prompt templates for AI coding assistants like GitHub Copilot, ChatGPT, Claude, and other LLM-based tools. Instead of retyping the same instructions or copying prompts between projects, Prompy lets you build a library of reusable prompt fragments that you can mix and match.

[![Python Version](https://img.shields.io/badge/python-3.9%2B-blue.svg)](https://python.org)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

## Why Prompy?

- **Stop repeating yourself**: Save common instructions like "run tests", "follow coding standards", or "initialize the environment" as reusable fragments
- **Context-aware**: Automatically detects your project and programming language to suggest relevant prompts
- **Composable**: Combine small, focused fragments into complex, context-rich prompts
- **Editor-friendly**: Work with your favorite editor to craft prompts, with syntax highlighting for Markdown
- **Project-specific**: Keep project-specific prompts with your code, share common patterns globally

## What does it look like?

Create reusable fragments:
```bash
echo "You know when you are finished when all tests pass." | prompy new --save generic/all-tests-pass
```

Build prompts from fragments:
```markdown
1. Implement some functionality.
2. {{ @generic/all-tests-pass }}
```

Get expanded, ready-to-use prompts:
```bash
prompy out
# Output:
# 1. Implement some functionality.
# 2. You know when you are finished when all tests pass.
```

## Quick Start

### Installation

```bash
pip install prompy
```

### Basic Usage

1. **Create your first prompt fragment**:
   ```bash
   echo "Write comprehensive tests for this code." | prompy new --save generic/write-tests
   ```

2. **Start a new prompt**:
   ```bash
   prompy new
   ```
   This opens your editor. Type:
   ```markdown
   Please refactor this function:
   - Improve readability
   - {{ @generic/write-tests }}
   ```

3. **Get your expanded prompt**:
   ```bash
   prompy out
   # Outputs:
   # Please refactor this function:
   # - Improve readability
   # - Write comprehensive tests for this code.
   ```

4. **Copy to clipboard and paste into your AI tool**:
   ```bash
   prompy pbcopy
   ```

## Core Concepts

### Prompt Fragments
Fragments are reusable pieces of prompts stored as Markdown files. They can be:
- **Generic** (`generic/name`): Useful across any project
- **Language-specific** (`language/python`): Tailored for specific programming languages
- **Project-specific** (`project/name`): Custom to your current project

### Reference Syntax
Use `{{ @fragment-name }}` to include other fragments:
```markdown
{{ @project/setup-instructions }}
Implement a new feature that:
- {{ @language/follows-conventions }}
- {{ @generic/includes-tests }}
```

## Common Use Cases

**Environment Setup**:
```bash
echo "Run: uv sync && source .venv/bin/activate" | prompy new --save project/init-shell
```

**Coding Standards**:
```bash
echo "Follow PEP 8, use type hints, write docstrings" | prompy new --save language/python-standards
```

**Testing Requirements**:
```bash
echo "Include unit tests with >90% coverage" | prompy new --save generic/test-requirements
```

**Complex Prompts**:
```markdown
{{ @project/init-shell }}

Implement a new API endpoint:
- {{ @language/python-standards }}
- {{ @generic/test-requirements }}
- {{ @project/api-conventions }}
```

## Shell Completion Setup

Enable tab completion for a better command-line experience:

```bash
# For bash
prompy completions bash > ~/.prompy-completion.bash
echo 'source ~/.prompy-completion.bash' >> ~/.bashrc

# For zsh
prompy completions zsh > ~/.zsh/completions/_prompy
echo 'fpath=(~/.zsh/completions $fpath)' >> ~/.zshrc

# For fish
prompy completions fish > ~/.config/fish/completions/prompy.fish
```

## Documentation

- **[User Guide](USER_GUIDE.md)**: Detailed tutorials and examples
- **[Reference](REFERENCE.md)**: Complete command and configuration reference
- **[Development](DEVELOPMENT.md)**: Contributing and development setup

## Project Configuration

Prompy automatically detects your project by looking for `.git`, `package.json`, `pyproject.toml`, or other project markers. It organizes prompts in:

```
$PROMPY_CONFIG_DIR/
├── prompts/             # Global prompt fragments
│   ├── fragments/       # Generic reusable fragments
│   ├── languages/       # Language-specific fragments
│   └── projects/        # Project-specific fragments
├── cache/               # Cache for one-off prompts
│   └── $project/        # Project-specific cache
└── detections.yaml      # Language detection rules
```

your-project/.prompy/      # Project-specific prompts (optional)
├── prompts/
│   ├── fragments/         # Language-specific fragments
│   ├── language/          # Language-specific fragments
│   └── project/           # Custom to this project
└── cache/                 # Cache
```

You can also set a custom config directory:
```bash
export PROMPY_CONFIG_DIR=/path/to/your/prompts
```

## Contributing

We welcome contributions! See [DEVELOPMENT.md](DEVELOPMENT.md) for:
- Development environment setup
- Running tests
- Code style guidelines
- How to submit pull requests

## Code of Conduct

This project follows the [Mozilla Community Participation Guidelines](https://www.mozilla.org/en-US/about/governance/policies/participation/). In summary:

## License

This project is licensed under the MIT License - see the LICENSE file for details.
