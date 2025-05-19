"""
Tests for shell completions functionality.
"""

import os
from pathlib import Path

import pytest
from click.testing import CliRunner

from prompy.cli import cli
from prompy.completions import get_completion_script, get_installation_instructions


def test_get_completion_script():
    """Test getting completion scripts for different shells."""
    # Test bash completion script
    bash_script = get_completion_script("bash")
    assert "_prompy_completion" in bash_script
    assert "complete -o nosort -F _prompy_completion prompy" in bash_script

    # Test zsh completion script
    zsh_script = get_completion_script("zsh")
    assert "#compdef prompy" in zsh_script
    assert "_prompy_completion" in zsh_script

    # Test fish completion script
    fish_script = get_completion_script("fish")
    assert "__fish_prompy_complete" in fish_script
    assert "complete -c prompy -f -a" in fish_script

    # Test invalid shell
    with pytest.raises(ValueError, match=r"Unsupported shell: .*"):
        get_completion_script("invalid")


def test_get_installation_instructions():
    """Test getting installation instructions for different shells."""
    # Test bash instructions
    bash_instructions = get_installation_instructions("bash")
    assert "~/.bashrc" in bash_instructions
    assert "_PROMPY_COMPLETE=bash_source" in bash_instructions

    # Test zsh instructions
    zsh_instructions = get_installation_instructions("zsh")
    assert "~/.zshrc" in zsh_instructions
    assert "_PROMPY_COMPLETE=zsh_source" in zsh_instructions

    # Test fish instructions
    fish_instructions = get_installation_instructions("fish")
    assert "~/.config/fish/config.fish" in fish_instructions
    assert "_PROMPY_COMPLETE=fish_source" in fish_instructions

    # Test invalid shell
    with pytest.raises(ValueError, match=r"Unsupported shell: .*"):
        get_installation_instructions("invalid")


def test_completions_command(tmp_path):
    """Test the completions command."""
    runner = CliRunner()

    # Test generating bash completion to stdout
    result = runner.invoke(cli, ["completions", "bash"])
    assert result.exit_code == 0
    assert "_prompy_completion" in result.output
    assert "To enable bash completion" in result.output

    # Test generating zsh completion to stdout
    result = runner.invoke(cli, ["completions", "zsh"])
    assert result.exit_code == 0
    assert "#compdef prompy" in result.output
    assert "To enable zsh completion" in result.output

    # Test generating fish completion to stdout
    result = runner.invoke(cli, ["completions", "fish"])
    assert result.exit_code == 0
    assert "__fish_prompy_complete" in result.output
    assert "To enable fish completion" in result.output

    # Test generating completion script to file
    output_file = tmp_path / "prompy-complete.bash"
    result = runner.invoke(cli, ["completions", "bash", "-o", str(output_file)])
    assert result.exit_code == 0
    assert "Completion script for bash written to" in result.output
    assert output_file.exists()

    # Check content of written file
    content = output_file.read_text()
    assert "_prompy_completion" in content

    # Test invalid shell
    result = runner.invoke(cli, ["completions", "invalid"])
    assert result.exit_code != 0
    assert "Error: Invalid value for '{bash|zsh|fish}'" in result.output
