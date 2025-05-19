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
    uv pip --python 3.9 build .

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
