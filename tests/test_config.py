"""
Tests for the config module.
"""

import os
import tempfile
from pathlib import Path
from unittest.mock import patch

import yaml

from prompy.config import (
    detect_language,
    ensure_config_dirs,
    find_project_dir,
    get_config_dir,
    get_default_detections,
)


def test_get_config_dir_from_env():
    """Test getting config dir from environment variable."""
    with patch.dict(os.environ, {"PROMPY_CONFIG_DIR": "/tmp/prompy-config"}):
        config_dir = get_config_dir()
        assert str(config_dir) == "/tmp/prompy-config"


def test_get_config_dir_default():
    """Test getting default config dir when env var is not set."""
    with patch.dict(os.environ, {"PROMPY_CONFIG_DIR": ""}):
        config_dir = get_config_dir()
        assert str(config_dir) == str(Path("~/.config/prompy").expanduser())


def test_ensure_config_dirs():
    """Test ensuring all config directories exist."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        with patch("prompy.config.get_config_dir", return_value=tmpdir_path):
            config_dir, prompts_dir, cache_dir, detections_file = ensure_config_dirs()

            assert config_dir.exists()
            assert prompts_dir.exists()
            assert cache_dir.exists()
            assert detections_file.exists()

            assert (prompts_dir / "projects").exists()
            assert (prompts_dir / "languages").exists()
            assert (prompts_dir / "fragments").exists()

            # Check if detections file contains default content
            with open(detections_file, "r") as f:
                detections = yaml.safe_load(f)
                assert "python" in detections
                assert "file_patterns" in detections["python"]


def test_find_project_dir():
    """Test finding project directory."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create a mock project structure
        project_dir = tmpdir_path / "my-project"
        project_dir.mkdir()
        git_dir = project_dir / ".git"
        git_dir.mkdir()

        # Mock the current working directory
        with patch("pathlib.Path.cwd", return_value=project_dir):
            result = find_project_dir()
            assert result is not None
            assert result == project_dir
            assert result.name == "my-project"

        # Test with a subdirectory
        subdir = project_dir / "src"
        subdir.mkdir()
        with patch("pathlib.Path.cwd", return_value=subdir):
            result = find_project_dir()
            assert result is not None
            assert result == project_dir
            assert result.name == "my-project"


def test_detect_language():
    """Test language detection based on file patterns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create a mock project with Python files
        (tmpdir_path / "file.py").touch()
        (tmpdir_path / "requirements.txt").touch()

        # Create mock detections file
        detections_file = tmpdir_path / "detections.yaml"
        with open(detections_file, "w") as f:
            yaml.dump(get_default_detections(), f)

        with patch("prompy.config.get_config_dir", return_value=tmpdir_path):
            language = detect_language(tmpdir_path)
            assert language == "python"

        # Test with JavaScript files
        (tmpdir_path / "file.js").touch()
        (tmpdir_path / "package.json").touch()

        with patch("prompy.config.get_config_dir", return_value=tmpdir_path):
            language = detect_language(tmpdir_path)
            # Python still has more files, should still be detected as Python
            assert language == "python"
