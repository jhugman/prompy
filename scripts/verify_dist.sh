#!/usr/bin/env bash
# Test the distribution package to verify it can be installed correctly

set -e

# Clean up previous builds
echo "Cleaning up previous builds..."
rm -rf build/ dist/ src/*.egg-info/

# Build the distribution package
echo "Building distribution package..."
python -m build

# Create a temporary directory
TEMP_DIR=$(mktemp -d)
echo "Creating test environment in $TEMP_DIR"

# Create a virtual environment
python -m venv "$TEMP_DIR/venv"
source "$TEMP_DIR/venv/bin/activate"

# Install the wheel
echo "Installing the wheel..."
pip install dist/*.whl

# Basic verification
echo "Verifying installation..."
prompy --version

# Test that the CLI works
echo "Testing CLI functionality..."
if prompy --help | grep -q "Prompy: A command-line tool"; then
    echo "CLI verification successful!"
else
    echo "CLI verification failed!"
    exit 1
fi

# Cleanup
deactivate
echo "Cleaning up test environment..."
rm -rf "$TEMP_DIR"

echo "Distribution package verification completed successfully!"
