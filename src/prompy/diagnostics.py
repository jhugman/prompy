"""
Diagnostic utilities for Prompy.

This module provides diagnostic tools for analyzing and visualizing fragment resolution.
"""

import logging
import time
from dataclasses import dataclass, field
from io import StringIO
from typing import Any, Dict, List, Optional

import click
from rich.box import SIMPLE
from rich.console import Console
from rich.table import Table
from rich.tree import Tree

logger = logging.getLogger(__name__)


@dataclass
class DiagnosticEvent:
    """An event captured during diagnostic mode."""

    event_type: str
    timestamp: float
    details: Dict[str, Any] = field(default_factory=dict)
    duration: Optional[float] = None

    @property
    def formatted_time(self) -> str:
        """Format the timestamp as milliseconds."""
        return f"{self.timestamp * 1000:.2f}ms"

    @property
    def formatted_duration(self) -> str:
        """Format the duration as milliseconds if available."""
        if self.duration is not None:
            return f"{self.duration * 1000:.2f}ms"
        return "N/A"


@dataclass
class FragmentResolutionNode:
    """A node in the fragment resolution tree."""

    slug: str
    children: List["FragmentResolutionNode"] = field(default_factory=list)
    depth: int = 0
    duration: Optional[float] = None
    error: Optional[str] = None
    arguments: Dict[str, Any] = field(default_factory=dict)


class DiagnosticsManager:
    """Manager for diagnostic information collection and reporting."""

    def __init__(self, enabled: bool = False):
        """
        Initialize the diagnostics manager.

        Args:
            enabled: Whether diagnostics are enabled
        """
        self.enabled = enabled
        self.events: List[DiagnosticEvent] = []
        self._current_operations: Dict[str, float] = {}
        self.resolution_tree: Optional[FragmentResolutionNode] = None
        self._start_time = time.time()

    def start_operation(self, operation_name: str, **details) -> None:
        """
        Start timing an operation.

        Args:
            operation_name: Name of the operation
            **details: Additional details about the operation
        """
        if not self.enabled:
            return

        timestamp = time.time() - self._start_time
        self._current_operations[operation_name] = timestamp
        self.events.append(
            DiagnosticEvent(
                event_type=f"start_{operation_name}",
                timestamp=timestamp,
                details=details,
            )
        )

    def end_operation(self, operation_name: str, **details) -> None:
        """
        End timing an operation and record its duration.

        Args:
            operation_name: Name of the operation
            **details: Additional details about the operation
        """
        if not self.enabled:
            return

        if operation_name not in self._current_operations:
            logger.warning(
                f"Attempting to end operation {operation_name} that was never started"
            )
            return

        start_time = self._current_operations.pop(operation_name)
        timestamp = time.time() - self._start_time
        duration = timestamp - start_time

        self.events.append(
            DiagnosticEvent(
                event_type=f"end_{operation_name}",
                timestamp=timestamp,
                details=details,
                duration=duration,
            )
        )

    def add_event(self, event_type: str, **details) -> None:
        """
        Record a diagnostic event.

        Args:
            event_type: Type of event
            **details: Additional details about the event
        """
        if not self.enabled:
            return

        self.events.append(
            DiagnosticEvent(
                event_type=event_type,
                timestamp=time.time() - self._start_time,
                details=details,
            )
        )

    def record_fragment_resolution(self, root: FragmentResolutionNode) -> None:
        """
        Record the fragment resolution tree.

        Args:
            root: Root node of the resolution tree
        """
        if not self.enabled:
            return

        self.resolution_tree = root

    def visualize_resolution_tree(self) -> str:
        """
        Create a visual representation of the fragment resolution tree using Rich.

        Returns:
            String representation of the tree
        """
        if not self.resolution_tree:
            return "No resolution tree available"

        # Create a string buffer to capture the tree output
        buffer = StringIO()
        console = Console(file=buffer, highlight=False)

        # Create a rich tree starting from the root
        tree = Tree(
            (
                f"@{self.resolution_tree.slug} "
                f"({self.resolution_tree.duration * 1000:.2f}ms)"
            )
            if self.resolution_tree.duration
            else f"@{self.resolution_tree.slug}"
        )

        def add_nodes(parent_tree: Tree, node: FragmentResolutionNode) -> None:
            for child in node.children:
                # Format the child's label with timing information
                label = (
                    f"@{child.slug} ({child.duration * 1000:.2f}ms)"
                    if child.duration
                    else f"@{child.slug}"
                )

                # Add error information if present
                if child.error:
                    label += f" ERROR: {child.error}"

                # Add arguments if present
                if child.arguments:
                    args = [f"{k}={v}" for k, v in child.arguments.items()]
                    label += f" ({', '.join(args)})"

                # Create the child branch
                child_branch = parent_tree.add(label)

                # Recursively add this child's children
                add_nodes(child_branch, child)

        # Add all child nodes recursively
        add_nodes(tree, self.resolution_tree)

        # Render the tree
        console.print(tree)
        return buffer.getvalue().strip()

    def get_report(self) -> str:
        """
        Generate a comprehensive diagnostic report.

        Returns:
            Formatted diagnostic report
        """
        if not self.enabled:
            return "Diagnostics disabled"

        sections = []

        # Summary information
        total_duration = time.time() - self._start_time
        sections.append("=== Diagnostic Summary ===")
        sections.append(f"Total execution time: {total_duration * 1000:.2f}ms")
        sections.append(f"Total events: {len(self.events)}")
        sections.append("")

        # Fragment resolution tree
        sections.append("=== Fragment Resolution Tree ===")
        sections.append(self.visualize_resolution_tree())
        sections.append("")

        # Timeline of events
        sections.append("=== Event Timeline ===")

        # Create a simple table for all events
        table = Table(box=SIMPLE, show_header=True, pad_edge=False)
        table.add_column("Time (ms)", style="dim")
        table.add_column("Event")
        table.add_column("Duration", style="green")
        table.add_column("Details", style="blue")

        # Add all events chronologically
        for event in self.events:
            # Keep original event type for backward compatibility
            event_type = event.event_type

            # Format duration if available
            duration = event.formatted_duration if event.duration else ""

            # Format details as a concise string
            details_items = []
            for k, v in event.details.items():
                if isinstance(v, (dict, list, set)) and len(str(v)) > 40:
                    details_items.append(f"{k}=[...]")
                else:
                    details_items.append(f"{k}={v}")
            details_str = ", ".join(details_items)

            table.add_row(event.formatted_time, event_type, duration, details_str)

        # Render the table to the buffer
        buffer = StringIO()
        console = Console(file=buffer, highlight=False)
        console.print(table)
        sections.append(buffer.getvalue())

        return "\n".join(sections)

    def print_report(self) -> None:
        """Print the diagnostic report to the console."""
        if not self.enabled:
            return

        click.echo("\n" + "=" * 80)
        click.echo(click.style("PROMPY DIAGNOSTICS REPORT", fg="green", bold=True))
        click.echo("=" * 80)
        click.echo(self.get_report())
        click.echo("=" * 80 + "\n")


# Create a global diagnostics manager instance
diagnostics_manager = DiagnosticsManager()
"""Global diagnostics manager instance that can be used throughout the application."""


def enable_diagnostics() -> None:
    """Enable diagnostics mode."""
    diagnostics_manager.enabled = True
    logger.info("Diagnostics mode enabled")


def is_diagnostics_enabled() -> bool:
    """Check if diagnostics mode is enabled."""
    return diagnostics_manager.enabled
