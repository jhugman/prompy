# GitHub Setup and Workflows

This document covers GitHub Actions setup, repository configuration, and workflow details for the prompy project.

## Repository Setup

### Required Secrets

To enable automated publishing, configure these secrets in your GitHub repository (Settings → Secrets and variables → Actions):

#### `PYPI_API_TOKEN` (Required)
Your PyPI API token for production publishing.

**To get a PyPI API token:**
1. Go to [pypi.org](https://pypi.org) and log in
2. Go to Account settings → API tokens
3. Click "Add API token"
4. Give it a name (e.g., "GitHub Actions - prompy")
5. Set scope to "Entire account" or specific to your project
6. Copy the token (starts with `pypi-`)

#### `TEST_PYPI_API_TOKEN` (Optional)
Your TestPyPI API token for testing publications.

Follow the same process at [test.pypi.org](https://test.pypi.org) for safe testing before production releases.

#### `GITHUB_TOKEN`
Automatically provided by GitHub Actions (no setup required).

## Available Workflows

### 1. CI Workflow (`.github/workflows/ci.yml`)
**Trigger:** Automatically on every push to `main` and on pull requests

**Purpose:** Continuous integration testing
- Runs tests on multiple OS (Ubuntu, macOS) and Python versions (3.9, 3.10, 3.11, 3.13)
- Performs code quality checks and linting
- Uploads coverage reports

### 2. PyPI Publishing Workflow (`.github/workflows/pypi-publishing.yml`)
**Trigger:** Manual dispatch only

**Purpose:** Publishes the package to PyPI or TestPyPI with comprehensive options

**Options:**
- `version` (required): Version to publish (e.g., 1.0.0)
- `dry_run` (default: false): Test without publishing
- `test_pypi` (default: false): Use TestPyPI instead of PyPI

**Usage:**
```bash
# Dry run to test everything
gh workflow run pypi-publishing.yml -f version=1.0.0 -f dry_run=true

# Publish to TestPyPI for testing
gh workflow run pypi-publishing.yml -f version=1.0.0 -f test_pypi=true

# Publish to PyPI (production)
gh workflow run pypi-publishing.yml -f version=1.0.0
```

### 3. Homebrew Publishing Workflow (`.github/workflows/homebrew-publishing.yml`)
**Trigger:** Manual dispatch only

**Purpose:** Updates the Homebrew formula with a new version

**Options:**
- `version` (required): Version to update to (e.g., 1.0.0)
- `dry_run` (default: false): Test without making changes
- `create_pr` (default: false): Prepare homebrew-core PR
- `commit_changes` (default: true): Commit formula changes

**Usage:**
```bash
# Dry run to test everything
gh workflow run homebrew-publishing.yml -f version=1.0.0 -f dry_run=true

# Update formula and commit
gh workflow run homebrew-publishing.yml -f version=1.0.0

# Update formula, commit, and prepare homebrew-core PR
gh workflow run homebrew-publishing.yml -f version=1.0.0 -f create_pr=true
```

### 4. Release Workflow (`.github/workflows/release.yml`) - Legacy
**Trigger:** Git tags (`v*.*.*`) or manual dispatch

**Purpose:** Legacy workflow that triggers the PyPI publishing workflow
- Maintained for backward compatibility with existing tag-based releases
- Automatically triggers the PyPI publishing workflow
- Provides instructions for Homebrew updates

## Quick Publishing Guide

For detailed publishing instructions, examples, and best practices, see [PUBLISHING.md](../PUBLISHING.md).

### Basic Release Process

1. **Test Everything First:**
   ```bash
   gh workflow run pypi-publishing.yml -f version=1.0.0 -f dry_run=true
   gh workflow run homebrew-publishing.yml -f version=1.0.0 -f dry_run=true
   ```

2. **Publish to PyPI:**
   ```bash
   gh workflow run pypi-publishing.yml -f version=1.0.0
   ```

3. **Wait for PyPI Propagation** (10-15 minutes)

4. **Update Homebrew:**
   ```bash
   gh workflow run homebrew-publishing.yml -f version=1.0.0
   ```

### Legacy Method (Still Supported)

```bash
# Tag-based release (triggers PyPI publishing automatically)
git tag v1.0.0
git push origin v1.0.0

# Then manually update Homebrew
gh workflow run homebrew-publishing.yml -f version=1.0.0
```

## Testing Setup

### Test with TestPyPI (Recommended)

Before publishing to production PyPI, test with TestPyPI:

```bash
# Publish to TestPyPI
gh workflow run pypi-publishing.yml -f version=1.0.0-test -f test_pypi=true

# Test installation
pip install -i https://test.pypi.org/simple/ prompy==1.0.0-test

# Test Homebrew update (dry run)
gh workflow run homebrew-publishing.yml -f version=1.0.0-test -f dry_run=true
```

### Manual Test Build

Test your package builds correctly:

```bash
# Clean any previous builds
just clean

# Build the package
./run.sh build

# Check the build
uv pip install twine
twine check dist/*

# Test install locally
pip install dist/prompy-*.whl
```

## Troubleshooting

### PyPI Token Issues
- Ensure the token is correctly copied (including `pypi-` prefix)
- Verify the token has the right scope (entire account or project-specific)
- Check token hasn't expired

### Version Conflicts
- PyPI doesn't allow re-uploading the same version
- Increment version number if you need to republish
- Use TestPyPI for testing before production

### Workflow Failures
- Check that CI workflow passes before releasing
- Ensure `./run.sh` scripts work correctly
- Verify all dependencies are properly specified
- Check workflow logs in GitHub Actions tab

### GitHub CLI Issues
- Install: `brew install gh` (macOS) or see [installation guide](https://github.com/cli/cli#installation)
- Authenticate: `gh auth login`
- Verify permissions: `gh auth status`

## Security Best Practices

- **Never commit API tokens** to your repository
- **Use GitHub secrets** for all sensitive information
- **Limit token scope** when possible (project-specific rather than account-wide)
- **Rotate tokens** periodically for security
- **Review workflow permissions** regularly

## Migration from Legacy Workflow

The old monolithic release workflow has been split into separate workflows for better control and testing. The legacy workflow still exists for backward compatibility but now delegates to the new PyPI publishing workflow.

**Benefits of the new system:**
- Better separation of concerns
- Comprehensive dry-run testing
- More granular control over each publishing step
- Easier debugging when issues occur
- Support for TestPyPI testing

For comprehensive usage examples and detailed publishing guidance, see [PUBLISHING.md](../PUBLISHING.md).
