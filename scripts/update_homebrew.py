#!/usr/bin/env python3
"""
Script to update Homebrew formula and optionally create PR to homebrew-core
"""

import hashlib
import re
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path


def get_pypi_tarball_sha256(package_name: str, version: str) -> str:
    """Download tarball from PyPI and calculate SHA256."""
    url = f"https://files.pythonhosted.org/packages/source/{package_name[0]}/{package_name}/{package_name}-{version}.tar.gz"

    print(f"Downloading {url}")
    with urllib.request.urlopen(url) as response:
        data = response.read()

    return hashlib.sha256(data).hexdigest()


def update_local_formula(formula_path: Path, version: str, sha256: str):
    """Update the local Homebrew formula with new version and SHA256."""
    content = formula_path.read_text()

    # Update URL
    content = re.sub(
        r'url "https://files\.pythonhosted\.org/packages/source/p/prompy/prompy-[^"]+\.tar\.gz"',
        f'url "https://files.pythonhosted.org/packages/source/p/prompy/prompy-{version}.tar.gz"',
        content
    )

    # Update SHA256
    content = re.sub(
        r'sha256 "[a-f0-9]{64}"',
        f'sha256 "{sha256}"',
        content
    )

    formula_path.write_text(content)
    print(f"Updated local formula at {formula_path}")


def create_homebrew_core_pr(version: str, sha256: str):
    """Create a PR to homebrew-core with the updated formula."""

    # Clone homebrew-core
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir = Path(tmpdir)
        homebrew_core = tmpdir / "homebrew-core"

        print("Cloning homebrew-core...")
        subprocess.run([
            "git", "clone", "--depth=1",
            "https://github.com/Homebrew/homebrew-core.git",
            str(homebrew_core)
        ], check=True)

        # Create new branch
        branch_name = f"prompy-{version}"
        subprocess.run([
            "git", "checkout", "-b", branch_name
        ], cwd=homebrew_core, check=True)

        # Copy our formula
        formula_src = Path(__file__).parent.parent / "packaging" / "homebrew" / "prompy.rb"
        formula_dst = homebrew_core / "Formula" / "p" / "prompy.rb"

        # Update the formula content
        content = formula_src.read_text()

        # Update URL
        content = re.sub(
            r'url "https://files\.pythonhosted\.org/packages/source/p/prompy/prompy-[^"]+\.tar\.gz"',
            f'url "https://files.pythonhosted.org/packages/source/p/prompy/prompy-{version}.tar.gz"',
            content
        )

        # Update SHA256
        content = re.sub(
            r'sha256 "[a-f0-9]{64}"',
            f'sha256 "{sha256}"',
            content
        )

        formula_dst.write_text(content)

        # Commit changes
        subprocess.run([
            "git", "add", "Formula/p/prompy.rb"
        ], cwd=homebrew_core, check=True)

        subprocess.run([
            "git", "commit", "-m", f"prompy: update {version}"
        ], cwd=homebrew_core, check=True)

        print(f"Created commit for prompy {version}")
        print("To push and create PR, run:")
        print(f"cd {homebrew_core}")
        print(f"git push origin {branch_name}")
        print("Then create a PR on GitHub to homebrew/homebrew-core")


def main():
    if len(sys.argv) != 2:
        print("Usage: python update_homebrew.py <version>")
        print("Example: python update_homebrew.py 1.0.0")
        sys.exit(1)

    version = sys.argv[1]

    # Calculate SHA256 of PyPI tarball
    print(f"Getting SHA256 for prompy {version}...")
    sha256 = get_pypi_tarball_sha256("prompy", version)
    print(f"SHA256: {sha256}")

    # Update local formula
    formula_path = Path(__file__).parent.parent / "packaging" / "homebrew" / "prompy.rb"
    update_local_formula(formula_path, version, sha256)

    # Ask if user wants to create homebrew-core PR
    response = input("Create homebrew-core PR? (y/N): ")
    if response.lower() == 'y':
        create_homebrew_core_pr(version, sha256)


if __name__ == "__main__":
    main()
