# Development Guide

This project uses modern Python tooling:

- `uv` for dependency management and virtual environments
- `just` for running common tasks
- `pyproject.toml` for project configuration

### Prerequisites

- Install [uv](https://github.com/astral-sh/uv): `curl -sSf https://astral.sh/uv/install.sh | bash`
- Install [just](https://github.com/casey/just): `brew install just` (on macOS)

## Quick Start

Get started with a single command:

```bash
just setup
```

This will:
1. Create a virtual environment using `uv venv` if one doesn't exist
2. Install the project in development mode with all dependencies

### Without Just

If you don't have `just` installed, you can use the provided shell script:

```bash
./run.sh setup
```

## Common Tasks

All common development tasks are available as `just` recipes:

```bash
# Run tests
just test [args]         # e.g., just test tests/test_cache.py -v

# Run tests with coverage
just coverage

# Lint code
just lint

# Build package
just build

# Run the application
just run [args]          # e.g., just run --help

# Update dependency lock files
just update

# Create/recreate virtual environment
just venv

# Clean up build artifacts
just clean
```

You can see all available commands with `just --list`.

## Project Structure

- `src/prompy/` - Main source code
- `tests/` - Test suite
- `scripts/` - Helper scripts for development tasks
- `sample-prompts/` - Example prompts and templates

## Dependency Management

Dependencies are managed in `pyproject.toml`. The project uses `uv` for fast and reliable dependency resolution.

To update dependencies:

```bash
just update
```

This will regenerate the lock files:
- `requirements.lock` - Production dependencies
- `dev-requirements.lock` - Development dependencies

## Virtual Environment

The project uses `uv` for virtual environment management. To create or recreate a virtual environment:

```bash
just venv
```

## Clean Up

To remove build artifacts and other generated files:

```bash
just clean
```
