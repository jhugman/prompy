# Prompy: Prompt Building Tool Specification

## Overview
Prompy is a command-line tool designed to help users build prompts for use with AI tools like Copilot or other LLM-based code helpers. It provides a templating system for creating reusable prompt fragments, opens an editor for user customization, and outputs the final prompt to stdout or directly to the clipboard.

The heart of the system is a templating engine which is a Jinja2 and a custom extension. Getting this templating engine right is important and should be tackled early in the project.

## Core Features
1. **Command-Line Interface**
   - Launches the user's default `$EDITOR` with a pre-populated template
   - Resolves prompt fragment references into a final prompt
   - Outputs the final prompt to stdout or copies it to the clipboard

2. **Prompt Fragments**
   - Use an environment variable `PROMPY_CONFIG_DIR`, default to `~/.config/prompy`
   - Prompts can be stored in `$PROMPY_CONFIG_DIR/prompts/`. Project specific prompts can also be stored in `$PROJECT_DIR/.prompts`.
   - Organized by project, language, and task
   - Include YAML frontmatter for metadata and Markdown for content
   - Can reference other prompt fragments (recursive resolution)

3. **Caching**
   - Uses `$PROMPY_CONFIG_DIR/cache/$project/CURRENT_FILE.md` for in-progress prompts
   - Supports starting fresh with the `new` subcommand.

4. **Error Handling**
   - Detects and reports missing fragments with clear error messages
   - Validates that all required arguments for fragments are provided
   - Detects and reports cycles in fragment references

5. **Project and Language Detection**
   - Detects the current project by walking up directories to find a `.git` folder. The first one with a `.git` directory is known as `PROJECT_DIR`.
   -
   - Language detection rules are configurable in `$PROMPY_CONFIG_DIR/detections.yaml`

## Command-Line Interface

### Usage

Prompy supports both a traditional command format and a subcommand structure:

```
prompy [global-options] [PROMPT_SLUG]      # Traditional usage
prompy <command> [command-options]         # Subcommand usage
```

### Global Options

These options apply to the main command:

- `--version`: Show version information and exit
- `--help`: Show help message and exit
- `--debug`: Enable debug logging for detailed error information
- `--language LANG`: Specify the language manually
- `--project PROJECT`: Specify the project manually

### Subcommands

#### Working with One-Off Prompts

```
prompy new
```
Start a new prompt.

```
prompy save PROMPT_SLUG [options]
```

Save the current one-off prompt as a reusable prompt fragment

- Example: `prompy save project/my-new-prompt`

#### Managing Reusable Prompts

```
prompy list [options]
```

List available prompts filtered by project and language

- Options: `--project`, `--language`, `--debug`
- Example: `prompy list --project myproject --language python`

```
prompy edit PROMPT_SLUG [options]
```

Edit or create a reusable prompt directly

- Options: `--project`, `--language`, `--debug`
- Example: `prompy edit project/existing-prompt`

```
prompy mv SOURCE_SLUG DEST_SLUG [options]
```

Move/rename a prompt from one location to another

- Options: `--project`, `--language`, `--debug`
- Example: `prompy mv project/old-name project/new-name`

```
prompy detections [options]
```

Edit language detection rules

- Options: `--debug`
- Example: `prompy detections`
- `mv PROMPT_SLUG NEW_PROMPT_SUG`: Move the a reusable prompt to the specified location in the config directory
- `rm PROMPT_SLUG`: Removes a prompt from the config directory.
- `detections`: Edit the `$PROMPY_CONFIG_DIR/detections.yaml` file
- `completions SHELL`: Generate shell completions for the given shell

### Examples
- Start editing a new file with a specific starting template:
  ```bash
  prompy new task/refactor
  ```
- Append "Do something" to the existing file and start editing:
  ```bash
  echo "Do something" | prompy new
  ```
- Continue editing the current one-off prompt:
  ```bash
  prompy # OR
  prompy edit
  ```
- Append to the current one-off prompt from stdin:
  ```bash
  echo "After that, do something else" | prompy
  ```
- Copy the resolved one-off prompt to clipboard:
  ```bash
  prompy out --pbcopy
  ```
- Output the resolved one-off prompt to stdout:
  ```bash
  prompy out
  ```
- Output the resolved one-off prompt to a file:
  ```bash
  prompy out output.md
  ```
- Output the resolved one-off prompt to clipboard:
  ```bash
  prompy out --pbcopy
  ```
- Save the current one-off prompt as a reusable prompt:
  ```bash
  prompy save $project/my-prompt
  ```

#### Reusable Prompts
- Edit a reusable prompt:
  ```bash
  prompy edit task/refactor
  ```
- List available prompts for the current project and language:
  ```bash
  prompy list
  ```
- List prompts for a specific language:
  ```bash
  prompy list --language python
  ```
- Output a reusable prompt directly to clipboard, without editing.
  ```bash
  prompy pbcopy task/refactor
  ```
- Move the prompt to a new location:
  ```bash
  prompy mv \$project/refactoring-small \$project/refactoring/small
  ```
- Remove an existing prompt:
  ```bash
  prompy rm \$project/refactoring-small
  ```
- Copy a prompt to a new location:
  ```bash
  prompy cp \$language/refactoring-small \$project/refactoring/small
  ```

## Prompt Fragment Syntax
- `@fragment-name(arg1, key=value)` for fragment inclusion
- `@path/to/fragment` for nested paths
- `@$project/fragment` for project-specific fragments
- `@$language/fragment` for language-specific fragments
- When no arguments are needed: `@fragment-name`

### Arguments for fragments
- `"strings"`, enclosed in `'` or `"`.
- Other fragments, nesting arbitrarily. e.g. `@fragment-name(@$project/other-fragment("foo"), key=value)`

## Directory Structure
```
~/.config/prompy/
  prompts/
    projects/
      project1/
      project2/
    languages/
      python/
      javascript/
    tasks/
      refactor.md
      code-review.md
  cache/
    project1/
      CURRENT_FILE.md
    project2/
      CURRENT_FILE.md
  detections.yaml
```

Using `$project` may also look for a `.prompts` directory of the project root (i.e. the first ancestor of pwd containing a `.git` directory).

## Prompt Fragment File Format
### Example
```yaml
---
description: Template for completion criteria
args:
  tasks: # required argument (no default value)
  name: User # argument with default value of "User"
---
Something something the following commands run cleanly:

{{ tasks }}

Then call out "All done {{ name }}!"
```

## Editor Experience
When opening the editor, a commented section will be displayed at the bottom with helpful information:

```markdown
<!--
PROMPY AVAILABLE FRAGMENTS:
--------------------------

PROJECT FRAGMENTS (my-project):
  @project/integration-tests
    Runs the standard integration test suite
  @project/setup-env(version="latest")
    Sets up the development environment

LANGUAGE FRAGMENTS (detected: python):
  @$language/start
    Command for starting a prompt
  @$language/test
    Task for running a test

TASKS:
  next-prompt
  spec/start
  spec/end

FRAGMENTS:
  @finish-when(tasks)
    Template for completion criteria
  @task/refactor(tasks)
    General code refactoring template

SYNTAX:
  {{ @fragment-name(arg1, key=value) }}
  {{ @path/to/fragment() }}
  {{ @$project/fragment() }}
  {{ @$language/fragment() }}

This comment section will be removed from the final prompt.
-->
```

## Architecture
### Language and Libraries
- **Language**: Python
- **Templating Engine**: Jinja2 (customized syntax for `{{ @fragment-name(arg, key=value) }}`)

### Workflow
1. **Initialization**:
   - Parse command-line arguments
   - Detect project and language if applicable
   - Load the appropriate template or cached file

2. **Editor Session**:
   - Pre-populate the editor with the selected template and help comments
   - Launch the user's default `$EDITOR`
   - Wait for the user to save and exit

3. **Fragment Resolution**:
   - Parse the edited content for fragment references
   - Recursively resolve fragment references
   - Validate required arguments
   - Detect and report cycles

4. **Output**:
   - Render the final prompt
   - Output to stdout, copy to clipboard, or save to file based on options
   - For one-off prompts: process command (--pbcopy, --stdout, --file)
   - For reusable prompts: process PROMPT_SLUG with output command

### One-Off Prompt Handling
1. **Creating New Prompts**:
   - With `--new`: Clear any existing CURRENT_FILE.md
   - With `--new [PROMPT_SLUG]`: Use the specified prompt as a template
   - From stdin with `--new`: Create from piped content

2. **Editing Existing Prompts**:
   - Default behavior (no flags): Open editor with current one-off prompt
   - From stdin (no `--new`): Append content to existing prompt

3. **Saving One-Off Prompts**:
   - With `save`: Convert to reusable prompt
   - Add minimal frontmatter if not present
   - Prompt for confirmation when overwriting existing prompts

### Moving Cache Files to Config
When using `mv`:
1. Remove the help/comment text at the top
2. Add empty/default frontmatter if not present
3. Save to the specified location in the config directory

## Data Handling
### Fragment Resolution Algorithm
1. Find all fragment references in the current text
2. For each reference:
   - Resolve the path (handling $project, $language)
   - Load the fragment file
   - Parse arguments and validate required ones
   - Apply arguments to the fragment content
   - Recursively resolve any references in the fragment
   - Replace the reference with the resolved content

### Cycle Detection
- Maintain a stack of fragments being processed
- Before resolving a fragment, check if it's already in the stack
- If a cycle is detected, report the full chain

## Error Handling
- **Missing Fragments**:
  ```
  Error: Missing prompt fragment '@project/test-steps'
    in file: ~/.config/prompy/cache/my-project/CURRENT_FILE.md
    at line: 12
    searched paths:
      - ~/.config/prompy/prompts/projects/my-project/test-steps.md
      - ~/.config/prompy/prompts/test-steps.md
  ```

- **Cycle Detection**:
  ```
  Error: Cyclic reference detected '@a' -> '@b' -> '@c' -> '@a'
    in file: ~/.config/prompy/cache/my-project/CURRENT_FILE.md
    - ~/.config/prompy/prompts/a.md
    - ~/.config/prompy/prompts/b.md
    - ~/.config/prompy/prompts/c.md
    - ~/.config/prompy/prompts/a.md
    starting at line: 5
  ```

- **Argument Validation**:
  ```
  Error: Missing required argument 'tasks' for fragment '@finish-when'
    in file: ~/.config/prompy/cache/my-project/CURRENT_FILE.md
    at line: 8
  ```

## Testing Plan
### Unit Tests
- **Fragment Parsing**:
  - Test parsing of YAML frontmatter and Markdown content
  - Validate argument extraction
  - Test path resolution (project, language variables)

- **Fragment Resolution**:
  - Test resolution of nested fragments
  - Test argument passing and substitution
  - Ensure cycles are detected and reported
  - Verify required argument validation

- **Command-Line Interface**:
  - Test all CLI options and argument parsing
  - Test project and language detection

### Integration Tests
- **Editor Workflow**:
  - Simulate launching the editor and editing a file
  - Validate the output after fragment resolution

- **Project and Language Detection**:
  - Test detection logic with various directory structures and marker files

- **File Operations**:
  - Test cache file management
  - Test moving files with the `mv` option
  - Test appending to one-off prompts from stdin
  - Test saving one-off prompts to reusable prompts
  - Test output to clipboard, stdout, and files

### End-to-End Tests
- **Full Workflow**:
  - Test starting with a template, editing, and generating the final prompt
  - Validate clipboard functionality with the `--pbcopy` flag
  - Test output to files and stdout
  - Test one-off prompt workflows (create, edit, append, save)
  - Test reusable prompt workflows (edit, list, output, move, remove)
  - Test error cases and verify helpful error messages

### Mocking and Fixture
- Minimize use of patching and mocks: they make for brittle code and brittle tests.
- Mock file system for project directory structures
- Sample directories as fixtures of fragments for end to end tests.
- Use temporary directories for cache and config files
- Patch the open editor to write to the filesystem to simulate edits without actually opening an editor.

## Implementation Plan

### Phase 1: Core Functionality
1. Set up project structure and CLI command parsing
2. Implement fragment file loading and parsing
3. Build the editor launch and handling
4. Create basic fragment resolution (non-recursive)

### Phase 2: Advanced Features
1. Add recursive fragment resolution
2. Implement cycle detection
3. Add argument validation
4. Build project and language detection

### Phase 3: Polish and Extras
1. Add clipboard support and expanded output options (--pbcopy, --stdout, --file)
2. Implement the `mv` and `save` commands
3. Add one-off prompt handling (--new, stdin append, etc.)
4. Enhance prompt listing functionality
5. Create shell completions
6. Add error handling and reporting improvements

## Dependencies
- `pyyaml`: For YAML frontmatter parsing
- `jinja2`: For templating (with custom syntax)
- `click`: For command-line argument parsing
- `pyperclip`: For clipboard functionality

---

This specification provides a comprehensive guide for implementing Prompy. Developers can use this as a reference to build the tool step by step, with clear requirements, architecture decisions, and testing strategies.
