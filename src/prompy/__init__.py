"""
Prompy: A command-line tool for building prompts with reusable fragments.
"""

__version__ = "0.1.0"

from .frontmatter import generate_frontmatter
from .prompt_context import PromptContext
from .prompt_file import PromptFile
from .prompt_files import PromptFiles

# Import core classes for easier access
from .prompt_render import PromptRender
