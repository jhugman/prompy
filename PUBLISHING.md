# Publishing Guide

This document outlines the process for publishing Prompy to PyPI and Homebrew using our separated publishing system.

## Overview

The publishing process has been separated into dedicated workflows for better control and testing:

1. **PyPI Publishing** (`.github/workflows/pypi-publishing.yml`) - Handles package building and PyPI/TestPyPI publication
2. **Homebrew Publishing** (`.github/workflows/homebrew-publishing.yml`) - Handles Homebrew formula updates
3. **Release (Legacy)** (`.github/workflows/release.yml`) - Backward-compatible trigger for existing tag-based releases
4. **CI Workflow** (`.github/workflows/ci.yml`) - Runs on every PR and push to main

## Key Benefits

✅ **Separation of Concerns**: Each workflow has a single responsibility
✅ **Comprehensive Dry-Run Testing**: Test everything before actual publication
✅ **Granular Control**: Run just PyPI or just Homebrew updates as needed
✅ **Better Error Handling**: Easier to debug issues in specific publishing steps
✅ **Flexible Testing**: Use TestPyPI for safe testing before production

## Quick Start

### Test Everything First (Recommended)

```bash
# Test PyPI publishing
gh workflow run pypi-publishing.yml \
  -f version=1.0.0 \
  -f dry_run=true

# Test Homebrew update
gh workflow run homebrew-publishing.yml \
  -f version=1.0.0 \
  -f dry_run=true
```

### Production Publishing

```bash
# 1. Publish to PyPI
gh workflow run pypi-publishing.yml -f version=1.0.0

# 2. Wait 10-15 minutes for PyPI propagation

# 3. Update Homebrew
gh workflow run homebrew-publishing.yml -f version=1.0.0
```

## Publishing Methods

### Method 1: New Separated Workflows (Recommended)

Complete control with comprehensive testing:

```bash
# 1. Test everything first
gh workflow run pypi-publishing.yml -f version=1.2.0 -f dry_run=true
gh workflow run homebrew-publishing.yml -f version=1.2.0 -f dry_run=true

# 2. Publish to PyPI
gh workflow run pypi-publishing.yml -f version=1.2.0

# 3. Update Homebrew (after PyPI propagation)
gh workflow run homebrew-publishing.yml -f version=1.2.0
```

### Method 2: Tag-Based Release (Legacy Compatible)

Still works with the new system:

1. **Update version** in `pyproject.toml`
2. **Create and push a git tag**:
   ```bash
   just release 1.0.0  # Updates version and runs tests
   just tag 1.0.0      # Creates and pushes tag
   ```
3. **GitHub Actions will automatically**:
   - Trigger PyPI publishing workflow
   - Run tests and linting
   - Build the package
   - Publish to PyPI
   - Create a GitHub release
4. **Manually run Homebrew update**:
   ```bash
   gh workflow run homebrew-publishing.yml -f version=1.0.0
   ```

### Method 3: Manual Release Trigger (Legacy)

```bash
# Using justfile (requires GitHub CLI)
just release-manual 1.0.0

# Or directly via GitHub CLI
gh workflow run release.yml --field version=1.0.0

# Or via GitHub web interface
# Go to Actions → Release → Run workflow
```

## Required Secrets

Configure these in your GitHub repository settings:

- `PYPI_API_TOKEN`: Your PyPI API token (required for production)
- `TEST_PYPI_API_TOKEN`: Your TestPyPI API token (optional, for testing)
- `GITHUB_TOKEN`: Automatically provided by GitHub

## Workflow Details

### PyPI Publishing Workflow

**File:** `.github/workflows/pypi-publishing.yml`

**Features:**
- Runs full test suite on multiple Python versions
- Code quality checks and linting
- Version updating in `pyproject.toml`
- Package building and validation
- Dry-run mode for safe testing
- TestPyPI support for testing publications
- Automatic GitHub release creation

**Options:**
- `version` (required): Version to publish
- `dry_run` (default: false): Test without publishing
- `test_pypi` (default: false): Use TestPyPI instead of PyPI

### Homebrew Publishing Workflow

**File:** `.github/workflows/homebrew-publishing.yml`

**Features:**
- Waits for PyPI package availability
- Downloads and calculates SHA256 automatically
- Updates local Homebrew formula
- Tests formula with `brew audit`
- Commits changes to repository
- Prepares homebrew-core PR files
- Full dry-run testing support

**Options:**
- `version` (required): Version to update to
- `dry_run` (default: false): Test without making changes
- `create_pr` (default: false): Prepare homebrew-core PR
- `commit_changes` (default: true): Commit formula changes

### Legacy Release Workflow

**File:** `.github/workflows/release.yml`

**Features:**
- Maintains backward compatibility
- Triggers PyPI publishing workflow
- Provides instructions for Homebrew updates
- Still responds to version tags (`v*.*.*`)

## Advanced Usage Examples

### Testing with TestPyPI

```bash
# Publish to TestPyPI
gh workflow run pypi-publishing.yml \
  -f version=1.2.0-test \
  -f test_pypi=true

# Test installation
pip install -i https://test.pypi.org/simple/ prompy==1.2.0-test

# Test Homebrew update (dry-run only)
gh workflow run homebrew-publishing.yml \
  -f version=1.2.0-test \
  -f dry_run=true
```

### Emergency Homebrew-Only Update

```bash
# If you need to update just the Homebrew formula
gh workflow run homebrew-publishing.yml \
  -f version=1.2.0 \
  -f commit_changes=true
```

### Creating Homebrew Core PR

```bash
# Update formula and prepare homebrew-core PR
gh workflow run homebrew-publishing.yml \
  -f version=1.2.0 \
  -f create_pr=true
```

## Manual Publishing

If you need to publish manually without workflows:

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

# Or update manually with workflow commands
just update-homebrew 1.0.0
```

## Troubleshooting

### PyPI Publishing Issues
- Check test results in the workflow logs
- Verify `PYPI_API_TOKEN` is correctly set
- Ensure version number is higher than existing releases
- Use dry-run mode to test without publishing

### Homebrew Publishing Issues
- Ensure PyPI package is available (wait 10-15 minutes after PyPI publishing)
- Check that the version exists on PyPI: `https://pypi.org/project/prompy/VERSION/`
- Use dry-run mode to test formula updates
- Verify formula syntax with `brew audit --strict packaging/homebrew/prompy.rb`

### CI Workflow Issues:
- Check that tests pass on both Ubuntu and macOS
- Ensure linting passes (run `./run.sh lint` locally)
- Check Python version compatibility

### Legacy Release Workflow Issues:
- Ensure your PyPI API token has the correct permissions
- Check that the version number is higher than the current published version
- Verify all tests pass before releasing

### General Workflow Issues
- Check workflow logs in GitHub Actions tab
- Ensure all required secrets are configured
- Verify repository permissions for GitHub Actions

## Migration Guide

### From Old Monolithic Workflow

**Before:**
```bash
# All-in-one release
git tag v1.2.0
git push origin v1.2.0
# Then manually update Homebrew
```

**After (Method 1 - Legacy Compatible):**
```bash
# Still works! Uses new PyPI workflow internally
git tag v1.2.0
git push origin v1.2.0
# Then run Homebrew workflow
gh workflow run homebrew-publishing.yml -f version=1.2.0
```

**After (Method 2 - New Approach):**
```bash
# Separate workflows with full control
gh workflow run pypi-publishing.yml -f version=1.2.0
gh workflow run homebrew-publishing.yml -f version=1.2.0
```

## Best Practices

1. **Always test first**: Use dry-run mode before production publishing
2. **Use TestPyPI**: Test PyPI publishing with TestPyPI first
3. **Wait for propagation**: Allow 10-15 minutes between PyPI and Homebrew updates
4. **Monitor workflows**: Check GitHub Actions logs for any issues
5. **Keep versions consistent**: Use the same version number for both PyPI and Homebrew
6. **Test locally**: Run tests locally before triggering workflows

## Release Checklist

- [ ] Update version in `pyproject.toml`
- [ ] Update CHANGELOG.md
- [ ] Run tests locally: `just test`
- [ ] Choose release method:
  - [ ] **New Method (Recommended)**: Test with dry-run, then publish separately
    - [ ] `gh workflow run pypi-publishing.yml -f version=X.Y.Z -f dry_run=true`
    - [ ] `gh workflow run homebrew-publishing.yml -f version=X.Y.Z -f dry_run=true`
    - [ ] `gh workflow run pypi-publishing.yml -f version=X.Y.Z`
    - [ ] `gh workflow run homebrew-publishing.yml -f version=X.Y.Z`
  - [ ] **Legacy Method**: `just release X.Y.Z && just tag X.Y.Z`
  - [ ] **Manual Method**: `just release-manual X.Y.Z`
- [ ] Verify PyPI publication
- [ ] Verify Homebrew formula update
- [ ] Submit homebrew-core PR if needed
- [ ] Update documentation if needed
