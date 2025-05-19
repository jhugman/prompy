"""
Prompy: A command-line tool for building prompts with reusable fragments.
"""

__version__ = "0.1.0"

from .frontmatter import generate_frontmatter

# Import core classes for easier access
from .prompt_render import PromptRender
