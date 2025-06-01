#!/usr/bin/env bash
# Installation script for Prompy

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

echo_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

echo_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

echo_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

echo_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check Python version
check_python() {
    echo_info "Checking Python version..."

    if ! command -v python3 &> /dev/null; then
        echo_error "Python 3 is not installed. Please install Python 3.9 or later."
        exit 1
    fi

    PYTHON_VERSION=$(python3 -c 'import sys; print(f"{sys.version_info.major}.{sys.version_info.minor}")')
    PYTHON_MAJOR=$(echo $PYTHON_VERSION | cut -d'.' -f1)
    PYTHON_MINOR=$(echo $PYTHON_VERSION | cut -d'.' -f2)

    if [ "$PYTHON_MAJOR" -lt 3 ] || ([ "$PYTHON_MAJOR" -eq 3 ] && [ "$PYTHON_MINOR" -lt 9 ]); then
        echo_error "Prompy requires Python 3.9 or later. Your Python version: $PYTHON_VERSION"
        echo_info "Please upgrade Python and try again."
        exit 1
    fi

    echo_success "Python $PYTHON_VERSION detected"
}

# Check if pip is installed
check_pip() {
    echo_info "Checking pip installation..."

    if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
        echo_error "pip is not installed. Please install pip before continuing."
        echo_info "You can install pip by running: python3 -m ensurepip --upgrade"
        exit 1
    fi

    # Use pip3 if available, otherwise pip
    PIP_CMD="pip3"
    if ! command -v pip3 &> /dev/null; then
        PIP_CMD="pip"
    fi

    echo_success "pip is available as $PIP_CMD"
}

# Create config directory structure
create_config_dirs() {
    echo_info "Creating configuration directory structure..."

    CONFIG_DIR="${PROMPY_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/prompy}"

    mkdir -p "$CONFIG_DIR/prompts/fragments"
    mkdir -p "$CONFIG_DIR/prompts/languages"
    mkdir -p "$CONFIG_DIR/prompts/projects"
    mkdir -p "$CONFIG_DIR/prompts/tasks"
    mkdir -p "$CONFIG_DIR/cache"

    echo_success "Configuration directory created at: $CONFIG_DIR"
}

# Install Prompy
install_prompy() {
    echo_info "Installing Prompy..."

    # Try installing with --user flag first, fall back to global install
    if $PIP_CMD install --user prompy; then
        echo_success "Prompy installed successfully for current user"
        INSTALL_TYPE="user"
    elif $PIP_CMD install prompy; then
        echo_success "Prompy installed successfully globally"
        INSTALL_TYPE="global"
    else
        echo_error "Failed to install Prompy"
        exit 1
    fi

    # Verify installation
    if command -v prompy &> /dev/null; then
        echo_success "Prompy command is available in PATH"
    elif python3 -m prompy.cli --version &> /dev/null; then
        echo_warning "Prompy installed but not in PATH. You can run it with: python3 -m prompy.cli"
        if [ "$INSTALL_TYPE" = "user" ]; then
            echo_info "Consider adding ~/.local/bin to your PATH"
        fi
    else
        echo_error "Prompy installation verification failed"
        exit 1
    fi
}

# Create basic detections.yaml if it doesn't exist
create_default_config() {
    CONFIG_DIR="${PROMPY_CONFIG_DIR:-${XDG_CONFIG_HOME:-$HOME/.config}/prompy}"

    if [ ! -f "$CONFIG_DIR/detections.yaml" ]; then
        echo_info "Creating default detections.yaml..."
        cat > "$CONFIG_DIR/detections.yaml" << 'EOF'
# Language detection rules for Prompy
# Add or modify rules to customize how Prompy detects your project's language

rules:
  python:
    extensions: [".py", ".pyx", ".pyi"]
    filenames: ["Pipfile", "setup.py", "requirements.txt", "pyproject.toml", "pipfile"]
    content_patterns: ["import", "from .* import", "def ", "class ", "if __name__"]
    directory_patterns: ["venv", "env", "__pycache__"]

  javascript:
    extensions: [".js", ".jsx", ".mjs"]
    filenames: ["package.json", "webpack.config.js", "babel.config.js"]
    content_patterns: ["import .* from", "export", "const ", "let ", "var ", "function"]
    directory_patterns: ["node_modules", "dist", "build"]

  typescript:
    extensions: [".ts", ".tsx", ".d.ts"]
    filenames: ["tsconfig.json", "tslint.json"]
    content_patterns: ["interface", "type ", "namespace", "export type", "import type"]
    directory_patterns: ["node_modules", "dist", "build"]

  rust:
    extensions: [".rs"]
    filenames: ["Cargo.toml", "Cargo.lock"]
    content_patterns: ["fn ", "struct ", "enum ", "impl ", "use ", "mod "]
    directory_patterns: ["target", "src"]

  go:
    extensions: [".go"]
    filenames: ["go.mod", "go.sum"]
    content_patterns: ["package ", "import ", "func ", "type ", "var ", "const "]
    directory_patterns: ["vendor"]

  java:
    extensions: [".java", ".class"]
    filenames: ["pom.xml", "build.gradle", "gradlew"]
    content_patterns: ["public class", "import ", "package ", "public static void main"]
    directory_patterns: ["src/main/java", "target", "build"]

  cpp:
    extensions: [".cpp", ".hpp", ".cc", ".h", ".cxx"]
    filenames: ["CMakeLists.txt", "Makefile"]
    content_patterns: ["#include", "namespace", "class ", "int main"]
    directory_patterns: ["build", "cmake"]
EOF
        echo_success "Default detections.yaml created"
    else
        echo_info "detections.yaml already exists, skipping creation"
    fi
}
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
