#!/usr/bin/env bash
# Installation script for Prompy

set -e

# Check Python version
PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 9 ]); then
    echo "Error: Prompy requires Python 3.9 or later. Your Python version: $PYTHON_VERSION"
    exit 1
fi

# Check if pip is installed
if ! command -v pip &> /dev/null; then
    echo "Error: pip is not installed. Please install pip before continuing."
    exit 1
fi

# Create config directory
CONFIG_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/prompy"
mkdir -p "$CONFIG_DIR/prompts/fragments"
mkdir -p "$CONFIG_DIR/prompts/languages"
mkdir -p "$CONFIG_DIR/prompts/projects"
mkdir -p "$CONFIG_DIR/prompts/tasks"
mkdir -p "$CONFIG_DIR/cache"

# Install Prompy
echo "Installing Prompy..."
pip install --user prompy

# Create basic detections.yaml if it doesn't exist
if [ ! -f "$CONFIG_DIR/detections.yaml" ]; then
    echo "Creating default detections.yaml..."
    cat > "$CONFIG_DIR/detections.yaml" << EOF
rules:
  python:
    extensions: [".py", ".pyx", ".pyi"]
    filenames: ["Pipfile", "setup.py", "requirements.txt", "pyproject.toml"]
    content_patterns: ["import", "from .* import", "def"]

  javascript:
    extensions: [".js", ".jsx", ".mjs"]
    filenames: ["package.json", "webpack.config.js"]
    content_patterns: ["import .* from", "export", "const", "let"]

  typescript:
    extensions: [".ts", ".tsx"]
    filenames: ["tsconfig.json"]
    content_patterns: ["interface", "type ", "namespace"]

  rust:
    extensions: [".rs"]
    filenames: ["Cargo.toml"]
    content_patterns: ["fn ", "struct ", "enum ", "impl"]
EOF
fi

# Setup shell completion based on the current shell
SHELL_TYPE=$(basename "$SHELL")
INSTALL_COMPLETIONS=false

case "$SHELL_TYPE" in
    bash)
        echo "Bash shell detected. Setting up bash completions..."
        COMPLETION_DIR="$HOME/.bash_completion.d"
        mkdir -p "$COMPLETION_DIR"
        prompy completions bash > "$COMPLETION_DIR/prompy"
        echo -e "\nAdding the following lines to your .bashrc:"
        echo "source $COMPLETION_DIR/prompy"
        echo -e "\nsource $COMPLETION_DIR/prompy" >> "$HOME/.bashrc"
        INSTALL_COMPLETIONS=true
        ;;
    zsh)
        echo "Zsh shell detected. Setting up zsh completions..."
        COMPLETION_DIR="$HOME/.zsh"
        mkdir -p "$COMPLETION_DIR"
        prompy completions zsh > "$COMPLETION_DIR/_prompy"
        echo -e "\nAdding the following lines to your .zshrc:"
        echo "fpath=($COMPLETION_DIR \$fpath)"
        echo "autoload -U compinit && compinit"
        echo -e "\nfpath=($COMPLETION_DIR \$fpath)" >> "$HOME/.zshrc"
        echo "autoload -U compinit && compinit" >> "$HOME/.zshrc"
        INSTALL_COMPLETIONS=true
        ;;
    fish)
        echo "Fish shell detected. Setting up fish completions..."
        COMPLETION_DIR="$HOME/.config/fish/completions"
        mkdir -p "$COMPLETION_DIR"
        prompy completions fish > "$COMPLETION_DIR/prompy.fish"
        INSTALL_COMPLETIONS=true
        ;;
    *)
        echo "Unknown shell: $SHELL_TYPE"
        echo "Shell completions not automatically installed."
        echo "You can manually install completions with:"
        echo "  prompy completions bash|zsh|fish > [completion-file]"
        ;;
esac

echo -e "\nPrompy has been successfully installed!"
echo "Configuration directory: $CONFIG_DIR"

if [ "$INSTALL_COMPLETIONS" = true ]; then
    echo -e "\nShell completions have been installed. You may need to restart your shell or run:"
    echo "  source ~/.${SHELL_TYPE}rc"
fi

echo -e "\nTo get started, run:"
echo "  prompy --help"
