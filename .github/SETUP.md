# GitHub Actions Setup for Publishing

## Workflow Architecture

We use a two-workflow system:

### CI Workflow (`.github/workflows/ci.yml`)
- **Triggers:** Every push to main, every PR
- **Purpose:** Continuous integration testing
- **Runs:** Tests, linting, coverage reporting
- **Platforms:** Ubuntu + macOS, Python 3.9-3.13

### Release Workflow (`.github/workflows/release.yml`)
- **Triggers:** Version tags (`v*.*.*`) OR manual dispatch
- **Purpose:** Publishing and releases
- **Runs:** Tests, builds, PyPI publishing, GitHub releases

## Required Repository Secrets

To enable automated publishing, you need to set up the following secrets in your GitHub repository:

### For PyPI Publishing

1. **Go to your repository on GitHub**
2. **Navigate to Settings → Secrets and variables → Actions**
3. **Add the following secret:**

#### `PYPI_API_TOKEN`
- **Name:** `PYPI_API_TOKEN`
- **Value:** Your PyPI API token

**To get a PyPI API token:**
1. Go to [pypi.org](https://pypi.org) and log in
2. Go to Account settings → API tokens
3. Click "Add API token"
4. Give it a name (e.g., "GitHub Actions - prompy")
5. Set scope to "Entire account" or specific to your project
6. Copy the token (starts with `pypi-`)

## Release Methods

### Method 1: Tag-Based Release (Recommended)
```bash
just release 1.0.0  # Updates version, runs tests
just tag 1.0.0      # Creates tag, triggers workflow
```

### Method 2: Manual Release
```bash
# Via justfile (requires GitHub CLI)
just release-manual 1.0.0

# Via GitHub CLI directly
gh workflow run release.yml --field version=1.0.0

# Via GitHub web interface
# Actions → Release → Run workflow → Enter version
```

## Testing the Setup

### Test PyPI (Recommended)

Before publishing to the real PyPI, test with TestPyPI:

1. **Create a TestPyPI account** at [test.pypi.org](https://test.pypi.org)
2. **Get a TestPyPI API token** following the same process as above
3. **Add as repository secret:** `TEST_PYPI_API_TOKEN`
4. **Modify release workflow** temporarily to use TestPyPI

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

## Workflow Features

### CI Workflow Benefits:
- ✅ **Multi-platform testing** (Ubuntu + macOS)
- ✅ **Multiple Python versions** (3.9, 3.10, 3.11, 3.13)
- ✅ **Coverage reporting** via Codecov
- ✅ **Uses your existing scripts** (`./run.sh`)
- ✅ **Fast feedback** on every PR

### Release Workflow Benefits:
- ✅ **Flexible triggering** (tags or manual)
- ✅ **Automated PyPI publishing**
- ✅ **GitHub releases** with binaries
- ✅ **Homebrew instructions**
- ✅ **Version validation**

## Troubleshooting

### Common Issues:

1. **PyPI token issues:**
   - Make sure the token is correctly copied (including `pypi-` prefix)
   - Ensure the token has the right scope (entire account or project-specific)

2. **Version conflicts:**
   - PyPI doesn't allow re-uploading the same version
   - Increment version number if you need to republish

3. **Workflow failures:**
   - Check that CI workflow passes before releasing
   - Ensure `./run.sh` scripts work correctly
   - Verify all dependencies are properly specified

4. **Manual release issues:**
   - Install GitHub CLI: `brew install gh` (macOS) or see [installation guide](https://github.com/cli/cli#installation)
   - Authenticate: `gh auth login`

## Security Notes

- **Never commit API tokens** to your repository
- **Use GitHub secrets** for all sensitive information
- **Limit token scope** when possible (project-specific rather than account-wide)
- **Rotate tokens** periodically for security
- **Review workflow permissions** regularly
