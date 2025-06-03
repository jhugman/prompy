# justfile for prompy
# To use: just <command>

# Define common variables
venv_dir := ".venv"
python := venv_dir + "/bin/python"
uv_run := "uv run"

# List all recipes
@default:
    just --list

# Install dependencies with uv
setup:
    #!/usr/bin/env bash
    set -e
    # Create venv if it doesn't exist
    if [ ! -d {{venv_dir}} ]; then
        echo "Creating virtual environment..."
        uv venv
    fi

    # Install project in development mode with all dev dependencies
    echo "Installing dependencies..."
    uv pip install -e ".[dev]"

    echo "Development setup complete!"

# Run tests
test *args='':
    #!/usr/bin/env bash
    set -e
    {{uv_run}} python -m pytest {{args}}

# Run tests with coverage
coverage:
    #!/usr/bin/env bash
    set -e
    {{uv_run}} python -m pytest --cov=src/prompy

# Update the lock file
update:
    #!/usr/bin/env bash
    set -e
    # Generate requirements.lock file
    uv pip compile pyproject.toml --upgrade -o requirements.lock

    # Generate dev-requirements.lock file (including dev dependencies)
    uv pip compile pyproject.toml --extra dev --upgrade -o dev-requirements.lock

    echo "Lock files updated!"

# Create or recreate virtual environment
venv:
    #!/usr/bin/env bash
    set -e
    # Remove existing venv if it exists
    if [ -d {{venv_dir}} ]; then
        echo "Removing existing virtual environment..."
        rm -rf {{venv_dir}}
    fi

    # Create a new venv
    echo "Creating virtual environment..."
    uv venv

    echo "Virtual environment created at {{venv_dir}}/"

# Install production dependencies
install:
    #!/usr/bin/env bash
    set -e
    echo "Installing production dependencies..."
    uv pip install .
    echo "Installation complete!"

# Run linting
lint:
    uv run ruff check src tests || echo "Ruff not installed, skipping"

# Format code
fmt:
    #!/usr/bin/env bash
    set -e
    echo "Formatting Python code..."
    {{uv_run}} isort src tests
    {{uv_run}} black src tests
    {{uv_run}} ruff format src tests
    echo "Code formatting complete!"

# Build the package
build:
    python -m build .

# Remove build artifacts
clean:
    rm -rf build/
    rm -rf dist/
    rm -rf src/*.egg-info
    find . -type d -name __pycache__ -exec rm -rf {} +
    find . -type f -name "*.pyc" -delete
    find . -type f -name "*.pyo" -delete
    find . -type f -name "*.pyd" -delete
    rm -rf .pytest_cache/
    rm -rf .coverage
    rm -rf htmlcov/

# Run the application
run *args='':
    #!/usr/bin/env bash
    set -e
    {{uv_run}} python -m prompy.cli {{args}}

# Release commands
# Prepare a release by updating version and creating tag
release version:
    #!/usr/bin/env bash
    set -e

    echo "Preparing release {{version}}..."

    # Update version in pyproject.toml
    sed -i.bak "s/version = \"[^\"]*\"/version = \"{{version}}\"/" pyproject.toml
    rm pyproject.toml.bak

    # Run tests to make sure everything works
    just test

    echo "Version updated to {{version}}"
    echo "Ready to create tag. Run: just tag {{version}}"

# Create and push a git tag for release
tag version:
    #!/usr/bin/env bash
    set -e

    # Check if we're on main branch
    if [ "$(git branch --show-current)" != "main" ]; then
        echo "Error: Must be on main branch to tag"
        exit 1
    fi

    # Check if working directory is clean
    if [ -n "$(git status --porcelain)" ]; then
        echo "Error: Working directory is not clean"
        exit 1
    fi

    # Create and push tag
    git tag v{{version}}
    git push origin v{{version}}

    echo "Tag v{{version}} created and pushed!"
    echo "GitHub Actions will now publish to PyPI"

# Publish to PyPI (with dry-run option)
publish-pypi version *args='':
    #!/usr/bin/env bash
    set -e
    python scripts/publish_pypi.py {{version}} {{args}}

# Publish to PyPI dry-run
publish-pypi-dry-run version *args='':
    #!/usr/bin/env bash
    set -e
    python scripts/publish_pypi.py {{version}} --dry-run {{args}}

# Publish to TestPyPI for testing
publish-test-pypi version *args='':
    #!/usr/bin/env bash
    set -e
    python scripts/publish_pypi.py {{version}} --test-pypi {{args}}

# Update Homebrew formula after PyPI publication (with dry-run option)
publish-homebrew version *args='':
    #!/usr/bin/env bash
    set -e
    python scripts/publish_homebrew.py {{version}} {{args}}

# Update Homebrew formula dry-run
publish-homebrew-dry-run version *args='':
    #!/usr/bin/env bash
    set -e
    python scripts/publish_homebrew.py {{version}} --dry-run {{args}}

# Update Homebrew formula and commit changes
publish-homebrew-commit version *args='':
    #!/usr/bin/env bash
    set -e
    python scripts/publish_homebrew.py {{version}} --commit {{args}}

# Legacy command (deprecated, use publish-homebrew instead)
update-homebrew version:
    #!/usr/bin/env bash
    set -e

    echo "⚠️  Warning: 'update-homebrew' is deprecated. Use 'publish-homebrew' instead."
    echo "Updating Homebrew formula for version {{version}}..."
    python scripts/update_homebrew.py {{version}}

    echo "Homebrew formula updated!"
    echo "To commit: git add packaging/homebrew/prompy.rb && git commit -m 'Update Homebrew formula to v{{version}}'"

# Trigger manual release via GitHub Actions (alternative to tagging)
release-manual version:
    #!/usr/bin/env bash
    set -e

    echo "Triggering manual release for version {{version}}..."

    # Check if gh CLI is installed
    if ! command -v gh &> /dev/null; then
        echo "Error: GitHub CLI (gh) is not installed"
        echo "Install it from: https://github.com/cli/cli#installation"
        exit 1
    fi

    # Trigger the workflow
    gh workflow run release.yml --field version={{version}}

    echo "Manual release workflow triggered for version {{version}}"
    echo "Check progress at: https://github.com/$(gh repo view --json owner,name -q '.owner.login + "/" + .name')/actions"
