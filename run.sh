#!/bin/bash
# Script to run common commands for CI environments or users without just installed
# Usage: ./run.sh <command> [arguments]
# Example: ./run.sh test --verbose

set -e

# Define common variables
VENV_DIR=".venv"
PYTHON="$VENV_DIR/bin/python"

# Function to show usage
show_usage() {
    echo "Usage: $0 <command> [arguments]"
    echo "Available commands:"
    echo "  setup         - Install development dependencies"
    echo "  test          - Run tests"
    echo "  coverage      - Run tests with coverage"
    echo "  update        - Update lock files"
    echo "  venv          - Create virtual environment"
    echo "  install       - Install production dependencies"
    echo "  lint          - Run linting"
    echo "  build         - Build the package"
    echo "  clean         - Clean build artifacts"
    echo "  run           - Run the application"
    echo
    echo "For the same functionality with a better interface, install 'just':"
    echo "  https://github.com/casey/just"
}

# Check if command is provided
if [ -z "$1" ]; then
    show_usage
    exit 1
fi

# Parse command
command=$1
shift

# Execute commands
case $command in
    setup)
        # Create venv if it doesn't exist
        if [ ! -d $VENV_DIR ]; then
            echo "Creating virtual environment..."
            uv venv
        fi

        echo "Installing dependencies..."
        uv pip install -e ".[dev]"

        echo "Development setup complete!"
        ;;

    test)
        uv run python -m pytest "$@"
        ;;

    coverage)
        uv run python -m pytest --cov=src/prompy "$@"
        ;;

    update)
        # Generate requirements.lock file
        uv pip compile pyproject.toml --upgrade -o requirements.lock

        # Generate dev-requirements.lock file (including dev dependencies)
        uv pip compile pyproject.toml --extra dev --upgrade -o dev-requirements.lock

        echo "Lock files updated!"
        ;;

    venv)
        # Remove existing venv if it exists
        if [ -d $VENV_DIR ]; then
            echo "Removing existing virtual environment..."
            rm -rf $VENV_DIR
        fi

        # Create a new venv
        echo "Creating virtual environment..."
        uv venv

        echo "Virtual environment created at $VENV_DIR/"
        ;;

    install)
        echo "Installing production dependencies..."
        uv pip install .
        echo "Installation complete!"
        ;;

    lint)
        uv run ruff check src tests || echo "Ruff not installed, skipping"
        ;;

    build)
        uv pip --python 3.9 build .
        ;;

    clean)
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
        ;;

    run)
        uv run python -m prompy.cli "$@"
        ;;

    *)
        echo "Unknown command: $command"
        show_usage
        exit 1
        ;;
esac
