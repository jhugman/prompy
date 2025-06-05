"""
Configuration and file system structure for Prompy.
"""

import logging
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import yaml

logger = logging.getLogger(__name__)

DEFAULT_CONFIG_DIR = "~/.config/prompy"


def get_config_dir() -> Path:
    """
    Get the configuration directory path.

    Returns:
        Path: The configuration directory path.
    """
    prompy_config_dir = os.environ.get("PROMPY_CONFIG_DIR")
    if prompy_config_dir:
        config_dir = Path(prompy_config_dir).expanduser()
    else:
        config_dir = Path(DEFAULT_CONFIG_DIR).expanduser()

    return config_dir


def ensure_config_dirs() -> Tuple[Path, Path, Path, Path]:
    """
    Ensure that all necessary config directories exist.

    Returns:
        Tuple[Path, Path, Path, Path]: Tuple containing config_dir, prompts_dir,
            cache_dir, detections_file
    """
    config_dir = get_config_dir()

    # Create main directories
    prompts_dir = config_dir / "prompts"
    cache_dir = config_dir / "cache"

    # Create directory structure
    for directory in [
        config_dir,
        prompts_dir,
        prompts_dir / "projects",
        prompts_dir / "languages",
        prompts_dir / "fragments",
        cache_dir,
    ]:
        directory.mkdir(exist_ok=True, parents=True)

    # Create detections file if it doesn't exist
    detections_file = config_dir / "detections.yaml"
    if not detections_file.exists():
        with open(detections_file, "w") as f:
            yaml.dump(get_default_detections(), f)

    return config_dir, prompts_dir, cache_dir, detections_file


def get_project_markers() -> List[str]:
    """
    Get the list of directories or files that indicate a project root.

    Returns:
        List[str]: List of project marker files or directories
    """
    return [
        ".git",  # Git projects
        ".hg",  # Mercurial projects
        ".svn",  # Subversion projects
        ".bzr",  # Bazaar projects
        "pyproject.toml",  # Python projects with modern config
        "setup.py",  # Python projects
        "package.json",  # Node.js projects
        "Cargo.toml",  # Rust projects
        "go.mod",  # Go projects
        "pom.xml",  # Maven projects
        "build.gradle",  # Gradle projects
        "Gemfile",  # Ruby projects
        "composer.json",  # PHP projects
        "CMakeLists.txt",  # C/C++ projects with CMake
    ]


def find_project_dir() -> Optional[Path]:
    """
    Find the project directory by walking up from the current directory
    looking for common project markers.

    Returns:
        Optional[Path]: The project directory path or None if not found
    """
    current_dir = Path.cwd()
    project_markers = get_project_markers()

    # Walk up the directory tree
    while current_dir != current_dir.parent:
        # Check all project markers
        for marker in project_markers:
            marker_path = current_dir / marker
            if marker_path.exists():
                # Found project directory
                logger.debug(
                    f"Found project directory at {current_dir} with marker {marker}"
                )
                return current_dir

        current_dir = current_dir.parent

    return None


def get_default_detections() -> Dict[str, Dict[str, List[str]]]:
    """
    Get default language detection rules.

    Returns:
        Dict: Default language detection rules
    """
    return {
        "python": {
            "file_patterns": [
                "*.py",
                "requirements.txt",
                "setup.py",
                "pyproject.toml",
                "Pipfile",
                "Pipfile.lock",
                "*.ipynb",
            ],
            "dir_patterns": [
                ".venv",
                "venv",
                "__pycache__",
                ".pytest_cache",
            ],
            "content_patterns": [
                "import ",
                "from ",
                "def ",
                "class ",
            ],
            "weight": 1.0,
        },
        "javascript": {
            "file_patterns": [
                "*.js",
                "*.jsx",
                "package.json",
                "package-lock.json",
                ".eslintrc*",
                ".babelrc*",
                "webpack.config.js",
            ],
            "dir_patterns": [
                "node_modules",
            ],
            "content_patterns": [
                "import ",
                "export ",
                "const ",
                "function ",
                "require(",
            ],
            "weight": 1.0,
        },
        "typescript": {
            "file_patterns": [
                "*.ts",
                "*.tsx",
                "tsconfig.json",
                "tslint.json",
            ],
            "dir_patterns": [
                "node_modules/@types",
            ],
            "content_patterns": [
                "interface ",
                "type ",
                "namespace ",
                "import ",
                "export ",
            ],
            "weight": 1.2,  # TypeScript gets a slight priority boost
        },
        "java": {
            "file_patterns": [
                "*.java",
                "pom.xml",
                "build.gradle",
                ".gradle",
                "gradlew",
                "settings.gradle",
            ],
            "dir_patterns": [
                "src/main/java",
                "src/test/java",
            ],
            "content_patterns": [
                "public class ",
                "private ",
                "protected ",
                "import java.",
                "package ",
            ],
            "weight": 1.0,
        },
        "rust": {
            "file_patterns": [
                "*.rs",
                "Cargo.toml",
                "Cargo.lock",
            ],
            "dir_patterns": [
                "target/debug",
                "target/release",
            ],
            "content_patterns": [
                "fn ",
                "struct ",
                "enum ",
                "impl ",
                "use ",
            ],
            "weight": 1.0,
        },
        "go": {
            "file_patterns": [
                "*.go",
                "go.mod",
                "go.sum",
            ],
            "dir_patterns": [
                "vendor",
            ],
            "content_patterns": [
                "package ",
                "import ",
                "func ",
                "type ",
                "struct ",
            ],
            "weight": 1.0,
        },
        "ruby": {
            "file_patterns": [
                "*.rb",
                "Gemfile",
                "Rakefile",
                "*.gemspec",
            ],
            "dir_patterns": [
                "gems",
                "vendor/bundle",
            ],
            "content_patterns": [
                "require ",
                "class ",
                "def ",
                "module ",
                "gem ",
            ],
            "weight": 1.0,
        },
        "c": {
            "file_patterns": [
                "*.c",
                "*.h",
                "Makefile",
                "CMakeLists.txt",
            ],
            "dir_patterns": [
                "obj",
                "bin",
            ],
            "content_patterns": [
                "#include ",
                "int ",
                "void ",
                "struct ",
                "typedef ",
            ],
            "weight": 1.0,
        },
        "cpp": {
            "file_patterns": [
                "*.cpp",
                "*.hpp",
                "*.cc",
                "*.h",
                "CMakeLists.txt",
            ],
            "dir_patterns": [
                "obj",
                "bin",
            ],
            "content_patterns": [
                "#include ",
                "class ",
                "namespace ",
                "std::",
                "template",
            ],
            "weight": 1.0,
        },
        "php": {
            "file_patterns": [
                "*.php",
                "composer.json",
                ".htaccess",
            ],
            "dir_patterns": [
                "vendor",
            ],
            "content_patterns": [
                "<?php",
                "namespace ",
                "use ",
                "function ",
                "class ",
            ],
            "weight": 1.0,
        },
        "csharp": {
            "file_patterns": [
                "*.cs",
                "*.csproj",
                "*.sln",
            ],
            "dir_patterns": [
                "bin",
                "obj",
            ],
            "content_patterns": [
                "namespace ",
                "using ",
                "class ",
                "public ",
                "private ",
            ],
            "weight": 1.0,
        },
    }


def detect_language(
    project_dir: Optional[Path] = None, sample_files_limit: int = 10
) -> Optional[str]:
    """
    Detect the language of the project based on file extensions, directory
    names, and content patterns.

    Args:
        project_dir: Optional path to the project directory. If None, uses
            current directory.
        sample_files_limit: Maximum number of files to sample for content
            pattern matching.

    Returns:
        Optional[str]: Detected language or None if no language could be determined
    """
    if project_dir is None:
        project_dir = Path.cwd()

    # Get detection rules
    config_dir = get_config_dir()
    detections_file = config_dir / "detections.yaml"

    if detections_file.exists():
        try:
            with open(detections_file, "r") as f:
                detections = yaml.safe_load(f)
        except (yaml.YAMLError, IOError) as e:
            logger.warning(f"Error loading detections file: {e}")
            detections = get_default_detections()
    else:
        detections = get_default_detections()

    # Count matches for each language
    language_scores = {lang: 0.0 for lang in detections.keys()}

    # Files to sample for content pattern matching
    sample_files = []

    # Check file patterns and collect sample files
    for lang, rules in detections.items():
        file_patterns = rules.get("file_patterns", [])
        dir_patterns = rules.get("dir_patterns", [])
        weight = rules.get("weight", 1.0)

        # Check file patterns
        for pattern in file_patterns:
            try:
                matches = list(project_dir.glob(f"**/{pattern}"))
                language_scores[lang] += len(matches) * weight
                # Collect sample files for content matching
                sample_files.extend(
                    matches[: sample_files_limit // len(file_patterns) + 1]
                )
            except Exception as e:
                logger.debug(f"Error matching pattern {pattern} for {lang}: {e}")

        # Check directory patterns
        for pattern in dir_patterns:
            try:
                matches = list(project_dir.glob(f"**/{pattern}/"))
                language_scores[lang] += (
                    len(matches) * 3 * weight
                )  # Weight directories more heavily
            except Exception as e:
                logger.debug(f"Error matching dir pattern {pattern} for {lang}: {e}")

        # Sample some files for content pattern matching - include all files
        # if no direct pattern matches
    if not sample_files and list(project_dir.glob("**/*")):
        for file_path in project_dir.glob("**/*"):
            if file_path.is_file() and file_path.suffix in [
                ".txt",
                ".md",
                ".html",
                ".css",
                ".js",
                ".py",
                ".java",
                ".c",
                ".cpp",
                ".h",
                ".rb",
                ".go",
                ".ts",
                ".rs",
            ]:
                sample_files.append(file_path)
                if len(sample_files) >= sample_files_limit:
                    break

    sample_files = sample_files[:sample_files_limit]

    # Check content patterns in the sampled files
    for file_path in sample_files:
        if not file_path.is_file():
            continue

        try:
            # Read the file content (first 5KB to avoid large files)
            with open(file_path, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read(5120)  # Read first 5KB

            # Check content patterns for each language
            for lang, rules in detections.items():
                content_patterns = rules.get("content_patterns", [])
                weight = rules.get("weight", 1.0)

                pattern_matches = 0
                for pattern in content_patterns:
                    # Count occurrences of the pattern
                    occurrences = content.count(pattern)
                    if occurrences > 0:
                        pattern_matches += occurrences

                if pattern_matches > 0:
                    logger.debug(
                        f"Found {pattern_matches} content matches for {lang} "
                        f"in {file_path}"
                    )
                    # Give more weight to content patterns if no file extension matches
                    content_weight = 1.0 if max(language_scores.values()) == 0 else 0.5
                    language_scores[lang] += pattern_matches * content_weight * weight
        except Exception as e:
            # Ignore errors reading files
            logger.debug(f"Error reading file {file_path}: {e}")

    # Find language with highest score
    if not language_scores:
        return None

    max_score = max(language_scores.values())
    if max_score == 0:
        return None

    # In case of a tie or close scores, use a predefined priority list
    priority_languages = [
        "typescript",
        "python",
        "javascript",
        "java",
        "rust",
        "go",
        "ruby",
        "c",
        "cpp",
        "csharp",
        "php",
    ]

    # Get languages within 10% of the max score to handle close calls
    threshold = max_score * 0.9
    top_langs = [lang for lang, score in language_scores.items() if score >= threshold]

    logger.debug(f"Language scores: {language_scores}")
    logger.debug(f"Top languages (threshold {threshold:.2f}): {top_langs}")

    # Sort by priority
    for priority_lang in priority_languages:
        if priority_lang in top_langs:
            return priority_lang

    # If no priority match, return the language with the highest score
    max_lang = max(language_scores.items(), key=lambda x: x[1])[0]
    return max_lang
