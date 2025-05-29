# Prompy: Implementation Prompt Plan

This document outlines a step-by-step approach to implementing the Prompy prompt building tool. Each section represents a discrete implementation prompt that builds incrementally upon previous work.

## Overview

Prompy is a command-line tool for building, managing, and sharing prompt templates for AI code assistance. The core features include:

1. Template management with fragment references
2. Editor integration
3. Project and language detection
4. Clipboard and stdout output options
5. Caching of in-progress prompts

The implementation is broken down into small, testable chunks that build upon each other, following a test-driven development approach.

## Implementation Plan

### PROMPT 1: Project Setup and Basic CLI Structure

```
You will be implementing a command-line tool called Prompy for managing prompts used with AI tools. In this first phase, set up the project structure and implement basic CLI functionality using Click.

1. Create the basic project structure:
   - Set up the main package directory structure
   - Create a setup.py file with metadata and dependencies
   - Set up a requirements.txt file with initial dependencies
   - Create a README.md with basic usage information

2. Implement a basic CLI interface using Click that:
   - Supports the `--version` and `--help` flags
   - Has placeholder subcommands (`new`, `edit`, `out`, etc.)
   - Parses command line arguments but doesn't yet perform any real actions

3. Include unit tests for the CLI interface that test:
   - Command parsing
   - Help text display
   - Version information

4. Follow best practices:
   - Use type hints throughout
   - Include docstrings
   - Follow PEP 8 style guidelines
   - Set up logging with different verbosity levels

Tasks:
- [x] Create project directory structure
- [x] Create setup.py with metadata and dependencies
- [x] Create requirements.txt
- [x] Create README.md
- [x] Implement basic CLI using Click
- [x] Add help and version flags
- [x] Add placeholder subcommands
- [x] Write unit tests
- [x] Add proper type hints and docstrings
- [x] PROMPT 1 COMPLETE
```

### PROMPT 2: File System Structure and Configuration

```
Now let's implement the file system structure and configuration handling for Prompy. We need to set up the configuration directory structure and implement functions to locate and manage prompt fragments.

1. Implement functions to determine the configuration directory:
   - Use the PROMPY_CONFIG_DIR environment variable if set
   - Otherwise, default to ~/.config/prompy
   - Create the directory structure if it doesn't exist

2. Implement project detection:
   - Walk up the directory tree to find a .git directory
   - Store the project directory path
   - Extract the project name from the directory

3. Implement language detection:
   - Create the basic structure for a language detection system
   - Use a simple default detection based on file extensions
   - Prepare for more complex detection rules later

4. Create functions to locate prompt fragments:
   - Support both global fragments in $PROMPY_CONFIG_DIR/prompts/
   - Support project-specific fragments in $PROJECT_DIR/.prompts/

5. Write comprehensive tests:
   - Test configuration directory resolution
   - Test project detection with various directory structures
   - Test language detection with various file types
   - Test locating prompt fragments in different locations

Tasks:
- [x] Implement config directory determination
- [x] Create necessary directory structure
- [x] Implement project detection function
- [x] Implement basic language detection
- [x] Create functions to locate prompt fragments
- [x] Write tests for configuration handling
- [x] Write tests for project detection
- [x] Write tests for language detection
- [x] Write tests for fragment location
- [x] PROMPT 2 COMPLETE
```

### PROMPT 3: Prompt File Parsing and Representation

```
In this prompt, we'll implement the core classes for representing and parsing prompt files. These classes will handle the YAML frontmatter and markdown content of prompt fragments.

1. Implement the PromptFile class:
   - Create methods to parse YAML frontmatter
   - Extract metadata like description, categories, and arguments
   - Store the markdown template content
   - Include methods to save and load from disk

2. Implement basic slug parsing:
   - Create methods to parse prompt slugs (e.g., 'project/fragment', 'language/fragment')
   - Resolve slugs to file paths based on the configuration

3. Write unit tests:
   - Test parsing of YAML frontmatter
   - Test extraction of metadata
   - Test loading and saving to disk
   - Test slug parsing and resolution

4. Update the relevant CLI commands to use these classes:
   - Modify the 'list' command to display available prompt fragments
   - Update the 'edit' command to load and save prompt files

Tasks:
- [x] Implement the PromptFile class
- [x] Add methods for parsing YAML frontmatter
- [x] Add methods for loading/saving from disk
- [x] Implement slug parsing and resolution
- [x] Write tests for the PromptFile class
- [x] Write tests for slug parsing
- [x] Update 'list' command to display available fragments
- [x] Update 'edit' command to load/save files
- [x] PROMPT 3 COMPLETE
```

### PROMPT 4: Fragment Reference Parsing

```
For this prompt, implement the parser for fragment references within prompt templates. This is the syntax that allows one prompt to include another using the @fragment-name notation.

1. Implement a parser for fragment references:
   - Parse the syntax @fragment-name(arg1, key=value)
   - Extract the fragment slug and any arguments
   - Handle nested fragment references
   - Support string arguments with quotes

2. Create a function to identify all fragment references in a template:
   - Scan the template for fragment reference patterns
   - Return the position and content of each reference

3. Implement error handling for the parser:
   - Handle invalid syntax
   - Provide clear error messages with line numbers
   - Return appropriate error objects

4. Write comprehensive tests:
   - Test parsing of simple fragment references
   - Test parsing of fragment references with arguments
   - Test parsing of nested fragment references
   - Test error handling for invalid syntax

Tasks:
- [x] Implement fragment reference parser
- [x] Create function to identify references in templates
- [x] Add error handling for invalid syntax
- [x] Write tests for simple fragment references
- [x] Write tests for references with arguments
- [x] Write tests for nested references
- [x] Write tests for error handling
- [x] PROMPT 4 COMPLETE
```

### PROMPT 5: Fragment Resolution and Template Rendering

```
Now implement the core functionality for resolving fragment references and rendering the final template. This builds directly on the parser you created `fragment_parser.py` and `prompt_file.py`.

1. Implement the PromptRender class:
   - Create a constructor that takes a PromptFile and arguments
   - Implement the render method to expand all fragment references

2. Create a function to recursively resolve fragment references:
   - Support nested references
   - Handle argument passing and substitution
   - Implement cycle detection to prevent infinite recursion

3. Implement argument validation:
   - Check that all required arguments are provided
   - Apply default values when arguments are not provided
   - Validate argument types

4. Write unit tests:
   - Test simple fragment resolution
   - Test nested fragment resolution
   - Test argument passing and substitution
   - Test cycle detection
   - Test argument validation

Tasks:
- [x] Implement the PromptRender class
- [x] Create recursive fragment resolution function
- [x] Implement cycle detection
- [x] Add argument validation
- [x] Write tests for simple fragment resolution
- [x] Write tests for nested fragment resolution
- [x] Write tests for argument handling
- [x] Write tests for cycle detection
- [x] Write tests for argument validation
- [x] PROMPT 5 COMPLETE
```

### PROMPT 6: Editor Integration

```
For this prompt, implement the functionality for launching the user's editor and handling the editing session. This will allow users to edit and create prompt templates.

1. Implement functions to determine the user's preferred editor:
   - Use the EDITOR environment variable
   - Fall back to common editors like nano, vim, etc.

2. Create functions to handle the editor session:
   - Launch the editor with a temporary file
   - Wait for the user to save and exit
   - Read the content after editing

3. Implement the pre_edit_load and post_edit_save methods:
   - Add helpful comments before editing
   - Remove comment section after editing

4. Add support for the 'edit' and 'new' commands:
   - Update the CLI to launch the editor
   - Handle saving edited content
   - Support creating new prompt fragments

5. Write comprehensive tests:
   - Test editor detection
   - Test adding and removing comments
   - Test handling of edited content
   - Mock the editor process for testing

Tasks:
- [x] Implement editor detection functions
- [x] Create functions to handle editor sessions
- [x] Implement pre_edit_load method
- [x] Implement post_edit_save method
- [x] Update CLI commands for editing
- [x] Write tests for editor detection
- [x] Write tests for comment handling
- [x] Write tests for content editing
- [x] PROMPT 6 COMPLETE
```

### PROMPT 7: Cache Management

```
In this prompt, implement the caching system for one-off prompts and in-progress work. This will allow users to maintain state between sessions.

1. Implement the cache directory structure:
   - Create $PROMPY_CONFIG_DIR/cache/project/ directories
   - Handle the CURRENT_FILE.md for in-progress prompts

2. Create functions to manage cache files:
   - Load the current one-off prompt
   - Save edited content to the cache
   - Clear the cache when starting fresh

3. Update the CLI commands to use the cache:
   - 'new' command should create or clear cache files
   - Default behavior should load from cache
   - Allow appending from stdin to cache files

4. Write unit tests:
   - Test cache directory creation
   - Test loading from cache
   - Test saving to cache
   - Test clearing the cache
   - Test appending from stdin

Tasks:
- [x] Implement cache directory structure
- [x] Create functions to manage cache files
- [x] Update CLI commands to use cache
- [x] Implement appending from stdin
- [x] Write tests for cache directory handling
- [x] Write tests for loading/saving cache
- [x] Write tests for clearing cache
- [x] Write tests for stdin appending
- [x] PROMPT 7 COMPLETE
```

### PROMPT 8: Output Options

```
For this prompt, implement the output options for Prompy, including stdout, clipboard, and file output. This will allow users to use the generated prompts in various ways.

1. Implement the 'out' command:
   - Support outputting to stdout (default)
   - Add --pbcopy flag for clipboard output
   - Support outputting to a file

2. Add clipboard functionality:
   - Use pyperclip for cross-platform clipboard support
   - Handle errors gracefully when clipboard is unavailable

3. Update the CLI to support output options:
   - Add command-line options for output format
   - Support shorthand commands like 'pbcopy'

4. Write comprehensive tests:
   - Test stdout output
   - Test file output
   - Mock clipboard for testing clipboard output
   - Test error handling for unavailable clipboard

Tasks:
- [x] Implement 'out' command
- [x] Add stdout output support
- [x] Add clipboard functionality
- [x] Add file output support
- [x] Update CLI for output options
- [x] Write tests for stdout output
- [x] Write tests for file output
- [x] Write tests for clipboard output
- [x] Write tests for error handling
- [x] PROMPT 8 COMPLETE
```

### PROMPT 9: Language and Project Detection Configuration

```
In this prompt, implement the configuration system for language and project detection rules. This will allow users to customize how Prompy detects languages and projects.

1. Create the detections.yaml file structure:
   - Define the schema for language detection rules
   - Include default rules for common languages

2. Implement more sophisticated language detection:
   - Use file extensions, filenames, and content patterns
   - Support rules defined in detections.yaml
   - Allow overriding detection with command-line flags

3. Enhance project detection:
   - Support additional project markers beyond .git
   - Allow project name customization
   - Handle subprojects within larger repositories

4. Add the 'detections' command:
   - Allow editing the detections.yaml file
   - Provide validation for the file format
   - Include examples in the default file

5. Write comprehensive tests:
   - Test parsing of detection rules
   - Test language detection with various rules
   - Test project detection enhancements
   - Test the 'detections' command

Tasks:
- [x] Create detections.yaml schema
- [x] Include default language detection rules
- [x] Implement enhanced language detection
- [x] Enhance project detection
- [x] Add 'detections' command
- [x] Write tests for detection rule parsing
- [x] Write tests for enhanced language detection
- [x] Write tests for project detection
- [x] Write tests for 'detections' command
- [x] PROMPT 9 COMPLETE
```

### PROMPT 10: Prompt Management Commands

```
In this prompt, implement the commands for managing reusable prompts, including list, move, rename, and remove operations. These will allow users to organize and manage their prompt fragments.

1. Enhance the 'list' command:
   - Show prompts filtered by project and language
   - Format output nicely with descriptions
   - Group by categories

2. Implement the 'mv' command:
   - Support moving prompts between locations
   - Handle renaming of prompts
   - Update references in other prompts
   - Add confirmation to prevent accidental overwriting (testing optional)

3. Implement the 'rm' command:
   - Support removing prompt fragments
   - Handle errors gracefully
   - Add confirmation to prevent accidental deletion (testing optional)

4. Implement the 'cp' command (optional):
   - Support copying prompts to new locations
   - Add confirmation to prevent accidental overwriting (testing optional)

5. Write comprehensive tests:
   - Test 'list' command with filters
   - Test 'mv' command for moving and renaming
   - Test 'rm' command with confirmation
   - Test error handling for all commands

Tasks:
- [x] Enhance 'list' command with filtering and formatting
- [x] Implement 'mv' command
- [x] Implement 'rm' command
- [x] Implement 'cp' command (optional)
- [x] Write tests for 'list' command
- [x] Write tests for 'mv' command
- [x] Write tests for 'rm' command
- [x] Write tests for 'cp' command (optional)
- [x] PROMPT 10 COMPLETE
```

### PROMPT 11: One-off to Reusable Prompt Conversion

```
For this prompt, implement the functionality to convert one-off prompts to reusable prompt fragments. This will allow users to save prompts they've crafted for reuse later.

1. Implement the 'save' command:
   - Convert one-off prompts to reusable fragments
   - Add minimal frontmatter if not present
   - Handle existing prompts with confirmation

2. Add frontmatter generation:
   - Create default description and categories
   - Identify potential arguments from the content
   - Format the frontmatter properly

3. Update the CLI to support saving:
   - Add command-line options for path
   - Support adding additional metadata during save

4. Write comprehensive tests:
   - Test conversion of one-off prompts
   - Test frontmatter generation
   - Test handling of existing prompts
   - Test CLI options for saving

Tasks:
- [x] Implement 'save' command
- [x] Add frontmatter generation
- [x] Handle existing prompts
- [x] Update CLI for save options
- [x] Write tests for prompt conversion
- [x] Write tests for frontmatter generation
- [x] Write tests for existing prompt handling
- [x] Write tests for CLI options
- [x] PROMPT 11 COMPLETE
```

### PROMPT 12: Shell Completion and Error Handling

```
In this final prompt, implement shell completion for convenience and enhance error handling throughout the application. This will improve the user experience and make the tool more robust.

1. Implement shell completion:
   - Add the 'completions' command
   - Support bash, zsh, and fish shells
   - Generate completion scripts

2. Enhance error handling:
   - Create a consistent error reporting system
   - Provide detailed error messages for common issues
   - Add debug mode for more verbose output

3. Audit and improve existing error messages:
   - Make fragment reference errors more helpful
   - Improve file not found errors
   - Enhance cycle detection error reporting

4. Write comprehensive tests:
   - Test shell completion generation
   - Test error reporting for various scenarios
   - Test debug mode output

5. Perform final integration testing:
   - Test end-to-end workflows
   - Verify all commands work together properly
   - Check edge cases and error conditions

Tasks:
- [x] Implement 'completions' command
- [x] Support different shells
- [x] Create consistent error reporting system
- [x] Improve error messages
- [x] Add debug mode
- [x] Write tests for shell completion
- [x] Write tests for error reporting
- [x] Perform end-to-end integration testing
- [x] Document known limitations and future improvements
- [x] PROMPT 12 COMPLETE
```

### PROMPT 13: Documentation and Distribution

```
For the final phase, focus on documentation and preparing the tool for distribution. This will ensure that users can easily install and use Prompy.

1. Complete the README.md:
   - Add comprehensive installation instructions
   - Include usage examples for all commands
   - Document configuration options
   - Add troubleshooting section

2. Create man pages or detailed help text:
   - Document each command in detail
   - Include examples for common scenarios
   - Explain the fragment reference syntax

3. Prepare for PyPI distribution:
   - Finalize setup.py
   - Create distribution packages
   - Test installation from PyPI

4. Add GitHub workflows (optional):
   - Set up CI/CD pipeline
   - Add automatic testing and linting
   - Create release automation

5. Final testing:
   - Test installation on different platforms
   - Verify documentation accuracy
   - Perform usability testing with sample workflows

Tasks:
- [x] Complete README.md with comprehensive documentation
- [x] Create man pages or detailed help text
- [x] Finalize setup.py for distribution
- [x] Create and test distribution packages
- [x] Set up GitHub workflows (optional)
- [x] Test installation on different platforms
- [x] Verify documentation accuracy
- [x] Perform usability testing
- [x] PROMPT 13 COMPLETE
```

### PROMPT 14: Performance Optimization and Code Quality

```
You will be implementing performance improvements for the Prompy tool's fragment resolution system. This builds on previous work in prompt_render.py and jinja_extension.py.

1. Refactor complex methods for improved readability:
   - Break down large methods into smaller, focused functions
   - Add clear documentation explaining the algorithm
   - Ensure consistent error handling throughout

2. Write comprehensive tests for:
   - Edge cases with complex nested references

Tasks:
- [x] Optimize regular expression patterns
- [x] Refactor complex methods for clarity
- [x] Update existing tests to cover optimizations
- [x] PROMPT 14 COMPLETE
```

### PROMPT 15: Enhanced Error Reporting and Diagnostics

```
You will be implementing enhanced error reporting and diagnostics for the Prompy tool. This builds on previous work in error_handling.py and the various command implementations.

1. Improve error context information:
   - Add more detailed location information for syntax errors
   - Include snippet of the problematic template content in error messages
   - Provide suggested fixes for common errors

2. Create a diagnostic mode:
   - Implement a --diagnose flag for commands
   - Show detailed information about fragment resolution process
   - Display timing data for performance analysis

3. Enhance debugging capabilities:
   - Add structured logging throughout the codebase
   - Create visualization of fragment resolution tree
   - Implement step-by-step resolution tracing

4. Write comprehensive tests for:
   - Error reporting with various error types
   - Diagnostic mode output format
   - Debug logging content and structure

Tasks:
- [x] Enhance error messages with more context
- [x] Add template snippet to syntax error reports
- [x] Implement suggestion system for common errors
- [x] Create diagnostic mode flag and functionality
- [x] Add structured logging for debugging
- [x] Implement fragment resolution visualization
- [x] Write tests for enhanced error reporting
- [x] Write tests for diagnostic mode
- [x] PROMPT 15 COMPLETE
```

### PROMPT 16: Improvements to the output experience

```
You will be implementing advanced user experience improvements for the Prompy tool. This builds on previous work in cli.py, editor.py, and output.py.

1. Improve output formatting:
   - Add colorized output for the `out` command.
   - Detect when being `out` output is redirected, and just output text.
   - Create beautified clipboard output

2. Improve list formatting:
   - Create better formatting for `list` command: make it concise and pretty.
   - Create a `--json` option for `list`, so machines can read the list.

3. Write comprehensive tests for:
   - List formatting options
   - Output formatting options

Tasks:
- [x] Enhance editor comments for better usability
- [x] Implement colorized terminal output
- [x] Add multiple output format options
- [x] Write tests for formatting features
- [x] PROMPT 16 COMPLETE
```

### PROMPT 17: Improvements to the Editor experience

```
You will be implementing advanced user experience improvements for the Prompy tool. This builds on previous work in cli.py, editor.py, and output.py.

1. Enhance editor experience:
   - Add colorized editor help text in the console: make it concise and pretty.
   - The console help text should be cleared once the editor is closed.

2. Write comprehensive tests for:
   - Enhanced editor features

Tasks:
- [ ] Enhance editor comments for better usability
- [ ] Implement colorized terminal output
- [ ] Write tests for formatting features
- [ ] PROMPT 17 COMPLETE
```

### PROMPT 18: Distribution and Installation Enhancements

```
You will be implementing distribution and installation enhancements for the Prompy tool. This builds on previous work in setup.py and the installation scripts.

1. Finalize PyPI packaging:
   - Update package metadata for better discoverability
   - Create proper entry points for all commands
   - Ensure dependencies are correctly specified

2. Create platform-specific installers:
   - Add support for pip, brew, and other package managers
   - Create standalone executables for Windows
   - Test installation process on different platforms

3. Implement automatic updates:
   - Add version checking functionality
   - Create update notification system
   - Implement self-update capability

4. Write comprehensive tests for:
   - Package installation process
   - Entry point functionality
   - Update checking mechanism

Tasks:
- [ ] Update package metadata for PyPI
- [ ] Finalize entry points configuration
- [ ] Review and update dependencies
- [ ] Create Homebrew formula for macOS
- [ ] Build standalone executable for Windows
- [ ] Implement version checking functionality
- [ ] Add update notification system
- [ ] Write tests for package installation
- [ ] PROMPT 17 COMPLETE
```

## Conclusion

This prompt plan outlines a step-by-step approach to implementing Prompy, breaking the work into manageable chunks that build upon each other. Each prompt focuses on a specific aspect of functionality, with clear testing requirements and deliverables. Following this plan will result in a well-structured, tested, and robust implementation of the tool as specified in the requirements.

The implementation order prioritizes user value, starting with basic functionality and gradually adding more advanced features. Early prompts focus on the core functionality needed to create and edit prompts, while later prompts add polish and convenience features.
