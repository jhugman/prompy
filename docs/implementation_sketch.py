"""
PromptContext is created once the language and project has been determined,
and uses the PROMPY_CONFIG_DIR environment variable and optionally the
`$PROJECT_DIR/.prompts` directories.
"""


class PromptContext:
    """
    A collection of directories used resolving prompts.
    """

    project_prompts_dir: Path
    fragment_prompts_dir: Path
    language_prompts_dir: Path

    def parse_prompt_ref(self,
        fragment_reference: str
    ) -> PromptRender:
        """
        Accepts a string which is a prompt slug. Here is the approximate EBNF.

        PROMPT_REF    := '@' SLUG ARG_LIST?
        SLUG          := (SLUG_PREFIX '/')? SLUG_PART ('/' SLUG_PART)+
        SLUG_PREFIX   := '$project' | '$language'
        SLUG_PART     := IDENTIFIER
        ARG_LIST      := '(' ARGS ')'
        ARGS          := ARG (',' ARG)+ ','+
        ARG           := ARG_VALUE | NAMED_ARG
        NAMED_ARG     := IDENTIFIER '=' ARG_VALUE
        ARG_VALUE     := STRING | PROMPT_REF | ARG_REF
        ARG_REF       := '$' IDENITFIER
        IDENTIFIER    := \w[\w-0-9]*
        STRING        := ... single or double quoted sting ... |
                         ... triple quoted multi-line string

        Returns a `PromptRender` instance or throws an error.

        The following errors may happen:
            - If the slug doesn't resolve to a valid file
            - a parse error
        """

    def parse_prompt_slug(self, slug: str) -> Optional[Path]:
        """
        SLUG          := (SLUG_PREFIX '/')? SLUG_PART ('/' SLUG_PART)+
        SLUG_PREFIX   := '$project' | '$language'
        SLUG_PART     := IDENTIFIER
        IDENTIFIER    := \w[\w-0-9]*

        '$language' refers to the language of the project as detected by looking at the project.

        '$project' refers to the project name, as detected by looking at the cwd.

        Detection does not happen in this class.
        """
        ...

    def load_slug(self, slug: str) -> PromptFile:
        """
        Parses the slug, then loads it into a PromptFile.

        Errors if the slug doesn't parse, or the file doesn't load.
        """
        ...

    def load_all(self) -> PromptFiles:
        """
        Finds all PromptFiles and loads them, construction a useful prompt slug
        from the filepath, relative to the different directories in the context.
        """
        ...

class PromptFiles:
    """Collection of prompt files"""

    def help_text(self) -> str:
        """
        Help text that is inserted into each file while editing.
        """
        ...

    def help_text_in_color(self, click) -> None:
        """
        Render the help text of the files with click, suitable for command line
        help.

        Should largely follow the same order as the help text.
        """
        ...

    def available_slugs(self) -> List[str]:
        """
        The slugs which can be used the prompt files.
        """
        ...



class PromptFile:
    """
    A class representing a file on disk, as edited by users.

    Prompt files have front matter, which is in YAML.

    The markdown content can contain fragment references within `{{` `}}` delimiters.
    """

    """
    If this is a one-off pronpt, can be referred to as "CURRENT_FILE".
    """
    slug: str

    description: Optional[str]
    categories: Optional[List[str]]
    """
    Argument names and their default values.

    Default values may be fragment references.
    """
    arguments: Optional[dict[str, str]]

    """
    Multi line fron matter used for description, categories, arguments etc.

    Kept here to keep comments and unused values intact.
    """
    frontmatter: str

    """
    The markdown text content.
    """
    markdown_template: str

    def is_fragment(self) -> bool:
        """
        Returns False if arguments are None or not fully satisified, i.e. not all defaulted.
        """
        ...

    def load(path: Path) -> PromptFile:
        """
        Load and deserialize from disk.
        """
        ...

    def save(self, path: Path) -> None:
        """
        Serialize to disk.
        """
        ...


class PromptRender:
    """
    A fully expanded prompt file, with all containing prompts expanded.
    """
    prompt_file: PromptFile
    arguments: dict[str, str]

    def render(self, context: PromptContext) -> str:
        """
        Renders the markdown_template with the prompt refs fully expanded,
        and fully expanded arguments.

        Markdown content may contain things that need to be expanded:

        TEMPLATE_DIRECTIVE := '{{' SUBSTITUTION '}}'
        SUBSTITUTION       := PROMPT_REF | ARG_REF | STRING

        These should be expanded recursively and replaced into the content.

        Once everythiing expanded with errors, the expanded content is returned.

        Errors which can be thrown:

        - A substitition not being parsed.
        - A prompt file not being resolved
        - An argument not being valid.
        """
        ...
