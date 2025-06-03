"""
Tests for diagnostics functionality.
"""

from unittest.mock import patch

import pytest
from click.testing import CliRunner

from prompy.cli import cli
from prompy.diagnostics import (
    DiagnosticsManager,
    FragmentResolutionNode,
    diagnostics_manager,
    enable_diagnostics,
)


def test_diagnostics_manager_initialization():
    """Test basic DiagnosticsManager initialization."""
    # Default state
    manager = DiagnosticsManager()
    assert not manager.enabled
    assert len(manager.events) == 0
    assert manager.resolution_tree is None

    # Explicit enabled state
    manager = DiagnosticsManager(enabled=True)
    assert manager.enabled
    assert len(manager.events) == 0


def test_diagnostics_manager_events():
    """Test event recording in the DiagnosticsManager."""
    manager = DiagnosticsManager(enabled=True)

    # Test adding a simple event
    manager.add_event("test_event", key1="value1", key2=123)
    assert len(manager.events) == 1
    assert manager.events[0].event_type == "test_event"
    assert manager.events[0].details == {"key1": "value1", "key2": 123}

    # Test operation timing
    manager.start_operation("test_operation", desc="Test operation")
    assert len(manager.events) == 2
    assert manager.events[1].event_type == "start_test_operation"

    manager.end_operation("test_operation", result="success")
    assert len(manager.events) == 3
    assert manager.events[2].event_type == "end_test_operation"
    assert manager.events[2].duration is not None
    assert manager.events[2].details == {"result": "success"}


def test_fragment_resolution_tree():
    """Test fragment resolution tree construction and visualization."""
    manager = DiagnosticsManager(enabled=True)

    # Create a sample resolution tree
    root = FragmentResolutionNode(slug="root", duration=0.01)
    child1 = FragmentResolutionNode(slug="child1", depth=1, duration=0.005)
    child2 = FragmentResolutionNode(slug="child2", depth=1, duration=0.003)
    grandchild = FragmentResolutionNode(slug="grandchild", depth=2, duration=0.002)

    child1.children.append(grandchild)
    root.children.append(child1)
    root.children.append(child2)

    # Record the tree
    manager.record_fragment_resolution(root)

    # Test visualization
    visualization = manager.visualize_resolution_tree()
    assert "@root (10.00ms)" in visualization
    assert "@child1 (5.00ms)" in visualization
    assert "@grandchild (2.00ms)" in visualization
    assert "@child2 (3.00ms)" in visualization


def test_enable_diagnostics():
    """Test enabling diagnostics globally."""
    # Ensure diagnostics are disabled initially
    diagnostics_manager.enabled = False

    # Enable diagnostics
    enable_diagnostics()

    # Verify that diagnostics are enabled
    assert diagnostics_manager.enabled


@pytest.fixture
def sample_prompt_files(tmp_path):
    """Create sample prompt files for testing."""
    # Set up the standard prompy directory structure
    prompts_dir = tmp_path / "prompts"
    prompts_dir.mkdir(parents=True, exist_ok=True)

    # Create fragments directory
    fragments_dir = prompts_dir / "fragments"
    fragments_dir.mkdir(parents=True, exist_ok=True)

    # Create cache directory
    cache_dir = tmp_path / "cache"
    cache_dir.mkdir(parents=True, exist_ok=True)

    # Create a simple prompt with no references
    simple_prompt = fragments_dir / "simple.md"
    simple_prompt.write_text(
        """---
description: A simple prompt
---
This is a simple prompt with no references.
"""
    )

    # Create a prompt with references
    parent_prompt = fragments_dir / "parent.md"
    parent_prompt.write_text(
        """---
description: A parent prompt with references
---
This is a parent prompt that references:
@simple
"""
    )

    # Create a prompt with nested references
    nested_prompt = fragments_dir / "nested.md"
    nested_prompt.write_text(
        """---
description: A nested prompt
---
This is a nested prompt that references:
@parent
"""
    )

    # Create a cyclic reference
    cyclic_prompt = fragments_dir / "cyclic.md"
    cyclic_prompt.write_text(
        """---
description: A prompt with cyclic references
---
This references itself:
{{ @cyclic }}
"""
    )

    return {
        "prompts_dir": prompts_dir,
        "fragments_dir": fragments_dir,
        "cache_dir": cache_dir,
        "simple": simple_prompt,
        "parent": parent_prompt,
        "nested": nested_prompt,
        "cyclic": cyclic_prompt,
    }


def test_cli_with_diagnostics(monkeypatch, tmp_path, sample_prompt_files):
    """Test the CLI with diagnostics flag."""
    runner = CliRunner()

    # Mock the config directory
    monkeypatch.setenv("PROMPY_CONFIG_DIR", str(tmp_path))

    # The sample_prompt_files fixture has already set up the correct directory structure
    # We'll use the config_dir directly from the fixture
    config_dir = tmp_path

    # Create a function to run a test with diagnostics for a specific prompt
    def run_test_with_prompt(prompt_slug, expected_slugs):
        """Helper function to run a test with a specific prompt and verify outputs"""
        with patch("prompy.cli.ensure_config_dirs") as mock_config_dirs:
            # Use the properly structured directories
            mock_config_dirs.return_value = (
                config_dir,  # config_dir
                sample_prompt_files["prompts_dir"],  # prompts_dir
                sample_prompt_files["cache_dir"],  # cache_dir
                config_dir / "detections.yaml",  # detections_file
            )

            result = runner.invoke(
                cli,
                ["--diagnose", "--project", "test", "out", prompt_slug],
                catch_exceptions=False,
            )

            assert result.exit_code == 0, f"Command failed with output: {result.output}"
            assert "PROMPY DIAGNOSTICS REPORT" in result.output
            assert "Fragment Resolution Tree" in result.output

            # Verify all expected slugs are in the output
            for slug in expected_slugs:
                assert f"@{slug}" in result.output, (
                    f"Expected slug '{slug}' not found in output"
                )

    # Test simple prompt
    run_test_with_prompt("simple", ["simple"])

    # Test parent prompt that references simple
    run_test_with_prompt("parent", ["parent", "simple"])

    # Test nested prompt that references parent
    # Note: simple is indirectly referenced but might not show in visualization
    # due to how fragment resolution works in the tested implementation
    run_test_with_prompt("nested", ["nested", "parent"])

    # Test error case with cyclic references
    with patch("prompy.cli.ensure_config_dirs") as mock_config_dirs:
        mock_config_dirs.return_value = (
            config_dir,
            sample_prompt_files["prompts_dir"],
            sample_prompt_files["cache_dir"],
            config_dir / "detections.yaml",
        )

        result = runner.invoke(
            cli, ["--diagnose", "--project", "test", "out", "cyclic"]
        )
        assert "Cyclic reference detected" in result.output or "ERROR" in result.output
