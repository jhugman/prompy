"""
Tests for basic diagnostics functionality.

These tests verify the core diagnostic functionality without the CLI integration.
"""

import re
from unittest.mock import patch

import pytest

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


def test_diagnostics_report_format():
    """Test the format of the diagnostic report."""
    manager = DiagnosticsManager(enabled=True)

    # Add some test events
    manager.add_event("test_event", key="value")
    manager.start_operation("render")
    manager.end_operation("render", result="success")

    # Create a simple resolution tree
    root = FragmentResolutionNode(slug="test-root", duration=0.123)
    manager.record_fragment_resolution(root)

    # Generate the report
    report = manager.get_report()

    # Check the report sections
    assert "=== Diagnostic Summary ===" in report
    assert "Total execution time:" in report
    assert "=== Fragment Resolution Tree ===" in report
    assert "@test-root (123.00ms)" in report
    assert "=== Event Timeline ===" in report
    assert "test_event" in report
    assert "start_render" in report
    assert "end_render" in report
