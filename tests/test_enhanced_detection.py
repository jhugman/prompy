"""
Tests for enhanced language detection with content patterns.
"""

import tempfile
from pathlib import Path
from unittest.mock import patch

import yaml

from prompy.config import detect_language


def test_language_detection_with_content_patterns():
    """Test that language detection works with content patterns."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create a detection rule with content patterns
        detection_rules = {
            "python": {
                "file_patterns": ["*.py"],
                "dir_patterns": [],
                "content_patterns": ["import ", "def "],
            },
            "javascript": {
                "file_patterns": ["*.js"],
                "dir_patterns": [],
                "content_patterns": ["function ", "const "],
            },
        }

        # Create a project with Python content
        python_file = tmpdir_path / "test.py"
        with open(python_file, "w") as f:
            f.write("import os\nimport sys\n\ndef main():\n    print('Hello')\n")

        # Create detections.yaml
        detections_file = tmpdir_path / "detections.yaml"
        with open(detections_file, "w") as f:
            yaml.dump(detection_rules, f)

        with patch("prompy.config.get_config_dir", return_value=tmpdir_path):
            # Test detection
            detected = detect_language(tmpdir_path)
            assert detected == "python"

        # Create a project with JavaScript content that has a .txt extension
        js_file = tmpdir_path / "script.txt"  # Misleading extension
        with open(js_file, "w") as f:
            f.write(
                "function hello() {\n    const name = 'World';\n    "
                "console.log('Hello ' + name);\n}\n"
            )

        # Remove the Python file to avoid it affecting the detection
        python_file.unlink()

        with patch("prompy.config.get_config_dir", return_value=tmpdir_path):
            # This should still detect JavaScript based on content patterns
            detected = detect_language(tmpdir_path)
            assert detected == "javascript"


def test_multifile_language_detection():
    """Test language detection across multiple files."""
    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create detection rules with weights
        detection_rules = {
            "python": {
                "file_patterns": ["*.py"],
                "dir_patterns": [".venv"],
                "content_patterns": ["import ", "def "],
                "weight": 1.0,
            },
            "javascript": {
                "file_patterns": ["*.js"],
                "dir_patterns": ["node_modules"],
                "content_patterns": ["function ", "const "],
                "weight": 1.0,
            },
            "typescript": {
                "file_patterns": ["*.ts"],
                "dir_patterns": [],
                "content_patterns": ["interface ", "type "],
                "weight": 1.5,  # Higher weight for TypeScript
            },
        }

        # Create a mixed project with Python and JavaScript,
        # but more JavaScript files
        (tmpdir_path / "script1.js").touch()
        (tmpdir_path / "script2.js").touch()
        (tmpdir_path / "script3.js").touch()
        (tmpdir_path / "main.py").touch()
        (tmpdir_path / "util.py").touch()

        # Create detections.yaml
        detections_file = tmpdir_path / "detections.yaml"
        with open(detections_file, "w") as f:
            yaml.dump(detection_rules, f)

        with patch("prompy.config.get_config_dir", return_value=tmpdir_path):
            # Test detection - should be JavaScript due to more files
            detected = detect_language(tmpdir_path)
            assert detected == "javascript"

        # Add a TypeScript file which has a higher weight
        ts_file = tmpdir_path / "app.ts"
        with open(ts_file, "w") as f:
            f.write(
                "interface User {\n  name: string;\n}\n\ntype ID = string | number;\n"
            )

        with patch("prompy.config.get_config_dir", return_value=tmpdir_path):
            # This should now detect TypeScript due to the higher weight
            detected = detect_language(tmpdir_path)
            assert detected == "typescript"


def test_project_markers():
    """Test project detection with various project markers."""
    from prompy.config import find_project_dir, get_project_markers

    # Check that we have multiple markers defined
    markers = get_project_markers()
    assert len(markers) > 1
    assert ".git" in markers

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create a project with a non-git marker
        project_dir = tmpdir_path / "my-project"
        project_dir.mkdir()

        # Use a marker that's not .git
        non_git_marker = next(marker for marker in markers if marker != ".git")
        marker_path = project_dir / non_git_marker

        if "." in non_git_marker:  # It's a file
            marker_path.touch()
        else:  # It's a directory
            marker_path.mkdir()

        # Check that project detection works
        with patch("pathlib.Path.cwd", return_value=project_dir):
            detected_dir = find_project_dir()
            assert detected_dir is not None
            assert detected_dir == project_dir
