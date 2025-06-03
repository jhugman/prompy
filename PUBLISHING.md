# Publishing Guide

This document outlines the process for publishing Prompy to PyPI and Homebrew.

## Two-Workflow System

We use separate workflows for different purposes:

- **CI Workflow** (`.github/workflows/ci.yml`) - Runs on every PR and push to main
  - Tests across multiple OS (Ubuntu, macOS) and Python versions
  - Linting and code quality checks
  - Coverage reporting

- **Release Workflow** (`.github/workflows/release.yml`) - Runs for publishing
  - Triggered by version tags OR manually
  - Publishes to PyPI
  - Creates GitHub releases
  - Provides Homebrew update instructions

## Publishing Methods

### Method 1: Tag-Based Release (Recommended)

1. **Update version** in `pyproject.toml`
2. **Create and push a git tag**:
   ```bash
   just release 1.0.0  # Updates version and runs tests
   just tag 1.0.0      # Creates and pushes tag
   ```
3. **GitHub Actions will automatically**:
   - Run tests and linting
   - Build the package
   - Publish to PyPI
   - Create a GitHub release

### Method 2: Manual Release Trigger

You can trigger a release manually without creating a tag:

```bash
# Using justfile (requires GitHub CLI)
just release-manual 1.0.0

# Or directly via GitHub CLI
gh workflow run release.yml --field version=1.0.0

# Or via GitHub web interface
# Go to Actions → Release → Run workflow
```

### Required Secrets:

Make sure you have set up the following GitHub repository secret:
- `PYPI_API_TOKEN`: Your PyPI API token

## Semi-Automated Publishing (Homebrew)

Homebrew publishing is semi-automated. The release workflow will provide instructions:

### Process:

1. **After PyPI publishing** (wait 10-15 minutes for propagation)
2. **Update the local Homebrew formula**:
   ```bash
   just update-homebrew 1.0.0
   ```
3. **Commit the updated formula**:
   ```bash
   git add packaging/homebrew/prompy.rb
   git commit -m "Update Homebrew formula to v1.0.0"
   git push
   ```

### Submit to homebrew-core:

1. **Fork** [homebrew-core](https://github.com/Homebrew/homebrew-core)
2. **Copy** your updated `packaging/homebrew/prompy.rb` to `Formula/p/prompy.rb` in your fork
3. **Create a PR** with title: `prompy: update 1.0.0`

## Manual Publishing

If you need to publish manually:

### PyPI:
```bash
# Build
./run.sh build

# Check
uv pip install twine
twine check dist/*

# Upload
twine upload dist/*
```

### Homebrew Formula Update:
```bash
# Use the helper script
python scripts/update_homebrew.py 1.0.0
```

## Troubleshooting

### CI Workflow Issues:
- Check that tests pass on both Ubuntu and macOS
- Ensure linting passes (run `./run.sh lint` locally)
- Check Python version compatibility

### Release Workflow Issues:
- Ensure your PyPI API token has the correct permissions
- Check that the version number is higher than the current published version
- Verify all tests pass before releasing

### Homebrew Issues:
- Wait for PyPI propagation before updating Homebrew formula
- Test the formula locally: `brew install --build-from-source ./packaging/homebrew/prompy.rb`
- Follow Homebrew's contribution guidelines for homebrew-core PRs

## Release Checklist

- [ ] Update version in `pyproject.toml`
- [ ] Update CHANGELOG.md
- [ ] Run tests locally: `just test`
- [ ] Choose release method:
  - [ ] Tag-based: `just release 1.0.0 && just tag 1.0.0`
  - [ ] Manual: `just release-manual 1.0.0`
- [ ] Verify PyPI publication
- [ ] Update Homebrew formula: `just update-homebrew 1.0.0`
- [ ] Submit homebrew-core PR
- [ ] Update documentation if needed
