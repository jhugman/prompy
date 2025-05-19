# RELEASE.md

## Releasing a new version of Prompy

This document outlines the process for releasing a new version of Prompy.

### Prerequisites

- You have push access to the repository
- You have PyPI credentials for the project

### Steps for Release

1. Update version number:
   - Edit `pyproject.toml` to increase the version number
   - Follow [semantic versioning](https://semver.org/) guidelines

2. Update CHANGELOG.md:
   - Add a new section for the version being released
   - Include notable changes, improvements, and bug fixes
   - Credit contributors where appropriate

3. Verify tests pass and documentation is up to date:
   ```bash
   just test
   ./scripts/verify_dist.sh
   ```

4. Commit and tag the release:
   ```bash
   git add pyproject.toml CHANGELOG.md
   git commit -m "Release version X.Y.Z"
   git tag -a vX.Y.Z -m "Version X.Y.Z"
   git push origin main --tags
   ```

5. Build distribution packages:
   ```bash
   just clean
   just build
   ```

6. Upload to PyPI:
   ```bash
   twine upload dist/*
   ```

### Post-Release

1. Create a release on GitHub:
   - Navigate to the repository's "Releases" section
   - Click "Draft a new release"
   - Select the tag you just created
   - Fill in the release title and description (often copied from CHANGELOG.md)
   - Attach the distribution packages if desired

2. Announce the release:
   - Update project documentation with the new version
   - Notify users through appropriate channels

3. Start the next development cycle:
   - Update version in pyproject.toml to next development version (X.Y.Z+1-dev0)
   - Commit the change
