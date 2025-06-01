#!/bin/bash
set -euo pipefail

# Build script for Prompy package distribution
# This script builds PyPI packages and verifies they install correctly

echo "🏗️  Building Prompy package..."

# Clean previous builds
echo "Cleaning previous build artifacts..."
rm -rf dist/ build/ src/*.egg-info/

# Ensure we have build dependencies
echo "Installing build dependencies..."
uv add --group dev build twine

# Build source distribution and wheel
echo "Building source distribution and wheel..."
uv build

# Verify the build
echo "Verifying package integrity..."
uv run twine check dist/*

# List the built packages
echo "Built packages:"
ls -la dist/

echo "✅ Package build complete!"
echo ""
echo "To test the package locally:"
echo "  pip install dist/prompy-*.whl"
echo ""
echo "To upload to PyPI test:"
echo "  uv run twine upload --repository testpypi dist/*"
echo ""
echo "To upload to PyPI production:"
echo "  uv run twine upload dist/*"
