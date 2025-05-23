"""
Command-line interface for Prompy.
"""

import logging
import subprocess
import sys
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

import click
import yaml

from prompy import __version__
from prompy.cache import (
    append_to_cache,
    clear_cache,
    get_cache_file_path,
    load_from_cache,
    read_from_stdin,
    save_to_cache,
)
from prompy.cli_completions import (
    complete_prompt_slug,
)
from prompy.config import (
    detect_language,
    ensure_config_dirs,
    find_project_dir,
)
from prompy.context import create_prompt_context, from_click_context
from prompy.editor import (
    edit_file_with_comments,
    find_editor,
    launch_editor,
)
from prompy.output import (
    output_content,
    output_to_clipboard,
    output_to_file,
    output_to_stdout,
)
from prompy.prompt_context import PromptContext
from prompy.prompt_file import PromptFile
from prompy.prompt_files import PromptFiles
from prompy.references import update_references

# Set up logging
logger = logging.getLogger(__name__)


@click.group(invoke_without_command=True)
@click.option("--version", is_flag=True, help="Show the version and exit.")
@click.option("--debug", is_flag=True, help="Enable debug logging.")
@click.option("--language", help="Specify the language manually.")
@click.option("--project", help="Specify the project manually.")
@click.option(
    "--global",
    "-g",
    "global_only",
    help="Use prompts not saved in the project directory.",
)
@click.pass_context
def cli(
    ctx: click.Context,
    version: bool,
    debug: bool,
    language: Optional[str],
    project: Optional[str],
    global_only: bool,
) -> None:
    """
    Prompy: A command-line tool for building prompts with reusable fragments.

    If no command is specified, Prompy will behave as if 'edit' was called.
    """
    # Configure logging
    log_level = logging.DEBUG if debug else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    if version:
        click.echo(f"Prompy version {__version__}")
        sys.exit(0)

    # Ensure config directories exist
    config_dir, prompts_dir, cache_dir, detections_file = ensure_config_dirs()

    # Detect project if not provided
    project_dir = None
    project_name = project

    if project_name is None:
        project_dir = find_project_dir()
        if project_dir:
            project_name = project_dir.name

    # Detect language if not provided
    detected_language = language
    if detected_language is None:
        detected_language = detect_language(project_dir)

    # Store options in the context
    ctx.ensure_object(dict)
    ctx.obj["language"] = detected_language
    ctx.obj["project"] = project_name
    ctx.obj["project_dir"] = project_dir
    ctx.obj["config_dir"] = config_dir
    ctx.obj["prompts_dir"] = prompts_dir
    ctx.obj["cache_dir"] = cache_dir
    ctx.obj["debug"] = debug
    ctx.obj["global_only"] = global_only

    if ctx.invoked_subcommand is None:
        # Default behavior is to act like the 'edit' command
        ctx.invoke(edit)


@cli.command()
@click.argument("prompt_slug", required=False, shell_complete=complete_prompt_slug)
@click.option("--save", "save_as", required=False, shell_complete=complete_prompt_slug)
@click.pass_context
def new(ctx: click.Context, prompt_slug: Optional[str], save_as: Optional[str]) -> None:
    """
    Start a new prompt.

    If PROMPT_SLUG is provided, use it as a template.
    """
    # Use context values
    project_name = ctx.obj.get("project")
    cache_dir = ctx.obj.get("cache_dir")

    if not project_name:
        click.echo("No project detected. Please specify a project with --project.")
        return

    prompt_context = from_click_context(ctx)

    try:
        # Start with empty content
        template_content = ""

        # Check if we're using a template
        if prompt_slug:
            try:
                template_path = prompt_context.parse_prompt_slug(prompt_slug)
                if template_path:
                    prompt_file = PromptFile.load(template_path)
                    template_content = prompt_file.markdown_template
                    click.echo(f"Using template: {prompt_slug}")
                else:
                    click.echo(f"Template not found: {prompt_slug}")
                    return
            except FileNotFoundError:
                click.echo(f"Template not found: {prompt_slug}")
                return

        # Check if we need to append from stdin
        stdin_content = read_from_stdin()
        if stdin_content:
            template_content = stdin_content + "\n" + template_content
            click.echo("Appended content from stdin.")

        # Clear any existing cache and save the new content
        clear_cache(cache_dir, project_name)
        save_to_cache(cache_dir, project_name, template_content)

        if not stdin_content:
            # Get the cache file path
            cache_file_path = get_cache_file_path(cache_dir, project_name)

            # Load prompt files for help comments
            prompt_files = prompt_context.load_all()

            # Launch the editor
            success = edit_file_with_comments(str(cache_file_path), prompt_files)

            if success:
                click.echo(f"New prompt cached for {project_name}")
            else:
                click.echo(f"Error: Failed to save prompt.")

        if save_as is not None:
            ctx.invoke(save, prompt_slug=save_as)

    except Exception as e:
        logger.error(f"Error creating new prompt: {e}")
        if ctx.obj.get("debug"):
            logger.exception(e)
        click.echo(f"Error: {e}", err=True)
        return


@cli.command()
@click.argument("prompt_slug", required=False, shell_complete=complete_prompt_slug)
@click.pass_context
def edit(ctx: click.Context, prompt_slug: Optional[str]) -> None:
    """
    Edit an existing prompt.

    If PROMPT_SLUG is provided, edit that prompt.
    Otherwise, edit the current one-off prompt.
    """
    # Use context values
    project_name = ctx.obj.get("project")
    cache_dir = ctx.obj.get("cache_dir")
    global_only = ctx.obj.get("global_only")

    prompt_context = from_click_context(ctx)

    try:
        file_path = None
        prompt_files = None

        # Check if we need to append from stdin
        stdin_content = read_from_stdin()

        # Determine which file to edit
        if prompt_slug:
            # Try to resolve the slug to edit an existing prompt
            try:
                file_path = prompt_context.parse_prompt_slug(
                    prompt_slug, global_only=global_only
                )
                if not file_path or not file_path.exists():
                    click.echo(f"Prompt not found: {prompt_slug}")
                    return

                # If stdin content exists, append it directly to the file
                if stdin_content:
                    with open(file_path, "r", encoding="utf-8") as f:
                        existing_content = f.read()

                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(existing_content.rstrip() + "\n\n" + stdin_content)

                    click.echo("Appended content from stdin.")

                click.echo(f"Editing prompt: {prompt_slug}")
            except FileNotFoundError:
                click.echo(f"Prompt not found: {prompt_slug}")
                return
        else:
            # Edit the current one-off prompt in cache
            if not project_name:
                click.echo(
                    "No project detected. Please specify a project with --project."
                )
                return

            # Get the cache file path
            file_path = get_cache_file_path(cache_dir, project_name)

            # If stdin content exists, append it to the cache
            if stdin_content:
                append_to_cache(cache_dir, project_name, stdin_content)
                click.echo("Appended content from stdin.")

            # If the cache file doesn't exist yet, create an empty one
            if not file_path.exists():
                save_to_cache(cache_dir, project_name, "")

            click.echo(f"Editing current one-off prompt for project: {project_name}")

        # Load prompt files for help comments
        prompt_files = prompt_context.load_all()

        # Launch the editor
        success = edit_file_with_comments(str(file_path), prompt_files)

        if success:
            click.echo(f"Prompt saved successfully.")
        else:
            click.echo(f"Error: Failed to save prompt.")

    except Exception as e:
        logger.error(f"Error editing prompt: {e}")
        if ctx.obj.get("debug"):
            logger.exception(e)
        click.echo(f"Error: {e}", err=True)
        return


@cli.command()
@click.argument("prompt_slug", required=False, shell_complete=complete_prompt_slug)
@click.option("--file", "-f", help="Save to a file.")
@click.option("--pbcopy", is_flag=True, help="Copy output to clipboard.")
@click.pass_context
def out(
    ctx: click.Context, prompt_slug: Optional[str], file: Optional[str], pbcopy: bool
) -> None:
    """
    Output the current prompt.

    If OUTPUT_FILE is provided, write to that file.
    Otherwise, write to standard output.
    Use --pbcopy to copy to the clipboard instead.
    """
    # Use context values
    project_name = ctx.obj.get("project")
    cache_dir = ctx.obj.get("cache_dir")
    global_only = ctx.obj.get("global_only")

    if not project_name:
        click.echo("No project detected. Please specify a project with --project.")
        return
    prompt_context = from_click_context(ctx)

    try:
        if prompt_slug is None:
            stdin_content = read_from_stdin()
            if stdin_content:
                prompt_file = PromptFile(slug="stdin", markdown_template=stdin_content)
            else:
                # Load the current cache content
                success, content = load_from_cache(cache_dir, project_name)
                if not success or not content:
                    click.echo(f"No current prompt found for project: {project_name}")
                    return
                prompt_file = PromptFile(slug="cache", markdown_template=content)
        else:
            prompt_file = prompt_context.load_slug(prompt_slug, global_only=global_only)
    except Exception as e:
        logger.error(f"Error outputting prompt: {e}")
        if ctx.obj.get("debug"):
            logger.exception(e)
        click.echo(f"Error: {e}", err=True)
        return

    # Resolve fragment references in the content
    from prompy.prompt_render import PromptRender

    try:
        # Create a PromptFile object from the content
        renderer = PromptRender(prompt_file)
        resolved_content = renderer.render(prompt_context)
    except Exception as e:
        logger.error(f"Error resolving prompt fragments: {e}")
        if ctx.obj.get("debug"):
            logger.exception(e)
        click.echo(f"Error resolving prompt fragments: {e}", err=True)
        return

    # Output the content using the appropriate method
    if output_to := file:
        from prompy.output import output_to_file

        if output_to_file(resolved_content, file):
            click.echo(f"Prompt output to file: {output_to}")
        else:
            click.echo(f"Failed to write to file: {output_to}", err=True)
    if pbcopy:
        from prompy.output import output_to_clipboard

        if output_to_clipboard(resolved_content):
            click.echo("Prompt copied to clipboard.")
        else:
            click.echo("Failed to copy to clipboard.", err=True)
    if not pbcopy and file is None:
        # Output to stdout with a header
        from prompy.output import output_to_stdout

        output_to_stdout(resolved_content)


@cli.command()
@click.argument("prompt_slug", shell_complete=complete_prompt_slug)
@click.option("--description", "-d", help="Description of the prompt.")
@click.option(
    "--category",
    "-c",
    "categories",
    multiple=True,
    help="Categories for the prompt. Can be specified multiple times.",
)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Overwrite existing prompts without confirmation.",
)
@click.pass_context
def save(
    ctx: click.Context,
    prompt_slug: str,
    description: Optional[str] = None,
    categories: Tuple[str, ...] = (),
    force: bool = False,
) -> None:
    """
    Save the current one-off prompt as a reusable prompt.

    PROMPT_SLUG specifies where to save the prompt.
    """
    # Use context values
    project_name = ctx.obj.get("project")
    cache_dir = ctx.obj.get("cache_dir")
    global_only = ctx.obj.get("global_only")

    if not project_name:
        click.echo("No project detected. Please specify a project with --project.")
        return

    prompt_context = from_click_context(ctx)

    try:
        # Load the current cache content
        success, content = load_from_cache(cache_dir, project_name)
        if not success or not content:
            click.echo(f"No current prompt found for project: {project_name}")
            ctx.exit(1)
            return

        # Get the destination path
        dest_path = prompt_context.parse_prompt_slug(
            prompt_slug, should_exist=False, global_only=global_only
        )
        if not dest_path:
            click.echo(f"Could not resolve destination path for slug: {prompt_slug}")
            ctx.exit(1)
            return

        # Check if the file already exists
        if dest_path.exists() and not force:
            if not click.confirm(f"File already exists at {dest_path}. Overwrite?"):
                click.echo("Save operation aborted.")
                return

        # Generate frontmatter
        from prompy.frontmatter import generate_frontmatter

        category_list = list(categories) if categories else None
        frontmatter_dict = generate_frontmatter(content, description, category_list)

        # Create the prompt file
        prompt_file = PromptFile(
            slug=prompt_slug,
            markdown_template=content,
            # Set metadata from frontmatter dict
            description=frontmatter_dict.get("description", ""),
            categories=frontmatter_dict.get("categories", []),
            arguments=frontmatter_dict.get("args", {}),
        )

        # Generate YAML frontmatter string
        prompt_file.frontmatter = prompt_file.generate_frontmatter()
        # Ensure parent directory exists and save
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        prompt_file.save(dest_path)

        click.echo(f"Prompt saved successfully to: {dest_path}")

    except Exception as e:
        logger.error(f"Error saving prompt: {e}")
        if ctx.obj.get("debug"):
            logger.exception(e)
        click.echo(f"Error: {e}", err=True)
        ctx.exit(1)
        return


@cli.command()
@click.argument("prompt_slug", required=False, shell_complete=complete_prompt_slug)
@click.pass_context
def pbcopy(ctx: click.Context, prompt_slug: Optional[str]) -> None:
    """
    Copy a prompt to the clipboard.

    If PROMPT_SLUG is provided, copy that prompt.
    Otherwise, copy the current one-off prompt.
    """
    # For prompt_slug, call regular out command with --pbcopy flag
    ctx.invoke(out, prompt_slug=prompt_slug, file=None, pbcopy=True)


@cli.command()
@click.option("--project", help="Filter by project.")
@click.option("--language", help="Filter by language.")
@click.option("--category", help="Filter by category.")
@click.option(
    "--format",
    "format_type",
    type=click.Choice(["simple", "detailed"]),
    default="detailed",
    help="Output format: simple (just slugs) or detailed (with descriptions).",
)
@click.pass_context
def list(
    ctx: click.Context,
    project: Optional[str],
    language: Optional[str],
    category: Optional[str],
    format_type: str,
) -> None:
    """
    List available prompts.

    Filter by project, language, and category if specified.
    Use --all to show prompts from all projects and languages.
    """
    # Use context values or override with options
    project_name = project or ctx.obj.get("project")
    detected_language = language or ctx.obj.get("language")
    global_only = ctx.obj.get("is_global")

    prompt_context = from_click_context(ctx)

    try:
        # Load all available prompt files
        prompt_files = prompt_context.load_all(global_only=global_only)

        # Count total prompts before filtering
        total_count = len(prompt_files.available_slugs())

        # Filter by category if specified
        if category:
            # We'll need to apply the filter inside the help_text method
            category_filter = category
            click.echo(f"Filtering prompts by category: {category}")
        else:
            category_filter = None

        # Get the formatted help text using the enhanced help_text method with inline descriptions
        help_text = prompt_files.help_text(
            slug_prefix="",  # No @ prefix for CLI output
            include_syntax=False,  # Skip syntax help in CLI output
            include_header=False,  # We'll add our own header
            use_dashes=False,
            inline_description=(
                format_type == "detailed"
            ),  # Only include descriptions for detailed format
            category_filter=category_filter,  # Apply category filter if specified
        )

        # Print header with filtering info
        filters_applied = []
        if project_name:
            filters_applied.append(f"project: {project_name}")
        if detected_language:
            filters_applied.append(f"language: {detected_language}")
        if category:
            filters_applied.append(f"category: {category}")

        filter_text = f" ({', '.join(filters_applied)})" if filters_applied else ""
        click.echo(f"Available prompt fragments{filter_text}:")

        # Print the formatted output
        if help_text.strip():
            click.echo(help_text)
        else:
            click.echo("No prompts found matching the specified criteria.")

        # Show filtered count if filtering was applied
        displayed_count = len(help_text.strip().split("\n")) - sum(
            1 for line in help_text.split("\n") if line.endswith(":")
        )
        if category or global_only:
            click.echo(f"Showing {displayed_count} of {total_count} total prompts.")

        # Add tips for filters if no prompts are found
        if not prompt_files.available_slugs():
            if not project_name and global_only:
                click.echo("Tip: Use --project to filter by a specific project.")
            if not detected_language and global_only:
                click.echo("Tip: Use --language to filter by a specific language.")
            if global_only:
                click.echo(
                    "Tip: Use --all to show prompts from all projects and languages."
                )

    except Exception as e:
        logger.error(f"Error listing prompts: {e}")
        if ctx.obj.get("debug"):
            logger.exception(e)
        click.echo(f"Error: {e}", err=True)
        return


@cli.command()
@click.argument("source_slug", shell_complete=complete_prompt_slug)
@click.argument("dest_slug", shell_complete=complete_prompt_slug)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Override destination without confirmation if it exists.",
)
@click.pass_context
def mv(ctx: click.Context, source_slug: str, dest_slug: str, force: bool) -> None:
    """
    Move/rename a prompt.

    SOURCE_SLUG is the current location of the prompt.
    DEST_SLUG is the new location for the prompt.
    """
    # Use context values
    global_only = ctx.obj.get("is_global")

    prompt_context = from_click_context(ctx)

    try:
        # Find source file
        source_path = prompt_context.parse_prompt_slug(source_slug)
        if not source_path or not source_path.exists():
            click.echo(f"Error: Source prompt not found: {source_slug}", err=True)
            return

        # Load the source prompt
        source_prompt = PromptFile.load(source_path)

        # Parse the destination slug and get its path
        dest_path = prompt_context.parse_prompt_slug(
            dest_slug, should_exist=False, global_only=global_only
        )
        if not dest_path:
            click.echo(
                f"Error: Invalid destination path for slug: {dest_slug}", err=True
            )
            return

        # Check if destination exists and confirm overwrite if needed
        if dest_path.exists() and not force:
            if not click.confirm(
                f"Destination '{dest_slug}' already exists. Overwrite?"
            ):
                click.echo("Move operation cancelled.")
                return

        # Ensure parent directories exist
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # Set the slug to the new destination slug
        source_prompt.slug = dest_slug

        # Save the prompt to the new location
        source_prompt.save(
            dest_path
        )  # Remove the original file if successfully saved to new location
        if dest_path.exists():
            # Update references in all prompt files before removing the original
            try:
                click.echo("Updating references in other prompt files...")
                updates = update_references(prompt_context, source_slug, dest_slug)

                # Count updated files
                update_count = sum(1 for updated in updates.values() if updated)
                if update_count > 0:
                    click.echo(
                        f"Updated {update_count} file(s) with references to '{source_slug}'."
                    )
                else:
                    click.echo("No references to update.")
            except Exception as e:
                logger.warning(f"Error updating references: {e}")
                if ctx.obj.get("debug"):
                    logger.exception(e)
                click.echo(f"Warning: Some references may not have been updated: {e}")

            # Now remove the source file
            source_path.unlink()
            click.echo(f"Moved '{source_slug}' to '{dest_slug}'.")
        else:
            click.echo(
                f"Error: Failed to save to destination path: {dest_path}", err=True
            )

    except Exception as e:
        logger.error(f"Error moving prompt: {e}")
        if ctx.obj.get("debug"):
            logger.exception(e)
        click.echo(f"Error: {e}", err=True)
        return


@cli.command()
@click.argument("source_slug", shell_complete=complete_prompt_slug)
@click.argument("dest_slug", shell_complete=complete_prompt_slug)
@click.option(
    "--force",
    "-f",
    is_flag=True,
    help="Override destination without confirmation if it exists.",
)
@click.pass_context
def cp(ctx: click.Context, source_slug: str, dest_slug: str, force: bool) -> None:
    """
    Copy a prompt to a new location.

    SOURCE_SLUG is the source location of the prompt.
    DEST_SLUG is the destination location for the prompt copy.
    """
    # Use context values
    global_only = ctx.obj.get("is_global")

    prompt_context = from_click_context(ctx)
    try:
        # Find source file
        source_path = prompt_context.parse_prompt_slug(source_slug)
        if not source_path or not source_path.exists():
            click.echo(f"Error: Source prompt not found: {source_slug}", err=True)
            return

        # Load the source prompt
        source_prompt = PromptFile.load(source_path)

        # Parse the destination slug and get its path
        dest_path = prompt_context.parse_prompt_slug(
            dest_slug, should_exist=False, global_only=global_only
        )
        if not dest_path:
            click.echo(
                f"Error: Invalid destination path for slug: {dest_slug}", err=True
            )
            return

        # Check if destination exists and confirm overwrite if needed
        if dest_path.exists() and not force:
            if not click.confirm(
                f"Destination '{dest_slug}' already exists. Overwrite?"
            ):
                click.echo("Copy operation cancelled.")
                return

        # Ensure parent directories exist
        dest_path.parent.mkdir(parents=True, exist_ok=True)

        # Set the slug to the new destination slug
        source_prompt.slug = dest_slug

        # Save the prompt to the new location
        source_prompt.save(dest_path)

        # Confirm copy
        if dest_path.exists():
            click.echo(f"Copied '{source_slug}' to '{dest_slug}'.")
        else:
            click.echo(
                f"Error: Failed to save to destination path: {dest_path}", err=True
            )

    except Exception as e:
        logger.error(f"Error copying prompt: {e}")
        if ctx.obj.get("debug"):
            logger.exception(e)
        click.echo(f"Error: {e}", err=True)
        return


@cli.command()
@click.argument("prompt_slug", shell_complete=complete_prompt_slug)
@click.option("--force", "-f", is_flag=True, help="Remove without confirmation.")
@click.pass_context
def rm(ctx: click.Context, prompt_slug: str, force: bool) -> None:
    """
    Remove a prompt.

    PROMPT_SLUG specifies which prompt to remove.
    """
    global_only = ctx.obj.get("is_global")

    # Create a prompt context
    prompt_context = from_click_context(ctx)

    try:
        # Find the file
        file_path = prompt_context.parse_prompt_slug(
            prompt_slug, global_only=global_only
        )
        if not file_path or not file_path.exists():
            click.echo(f"Error: Prompt not found: {prompt_slug}", err=True)
            return

        # Confirm deletion unless force flag is used
        if not force:
            if not click.confirm(f"Are you sure you want to remove '{prompt_slug}'?"):
                click.echo("Remove operation cancelled.")
                return

        # Delete the file
        try:
            file_path.unlink()
            click.echo(f"Removed prompt: {prompt_slug}")

            # Check if parent directories are empty and remove them if they are
            parent_dir = file_path.parent
            while parent_dir.name and not any(parent_dir.iterdir()):
                # Don't delete the root prompts directory or anything above it
                if parent_dir.name in ("prompts", "fragments", "languages", "projects"):
                    break
                parent_dir.rmdir()
                click.echo(f"Removed empty directory: {parent_dir}")
                parent_dir = parent_dir.parent

        except OSError as e:
            click.echo(f"Error removing prompt: {e}", err=True)

    except Exception as e:
        logger.error(f"Error removing prompt: {e}")
        if ctx.obj.get("debug"):
            logger.exception(e)
        click.echo(f"Error: {e}", err=True)
        return


@cli.command()
@click.option(
    "--validate",
    is_flag=True,
    help="Validate the detections file format without opening the editor.",
)
@click.pass_context
def detections(ctx: click.Context, validate: bool) -> None:
    """
    Edit language detection rules.

    Opens the detections.yaml file in your default editor, allowing you to customize language detection rules.
    If the --validate flag is set, it will only validate the file format without opening the editor.
    """
    config_dir = ctx.obj.get("config_dir")
    detections_file = config_dir / "detections.yaml"

    # Check if the file exists, if not create it with default rules
    if not detections_file.exists():
        from prompy.config import get_default_detections

        with open(detections_file, "w") as f:
            yaml.dump(get_default_detections(), f, sort_keys=False)
        click.echo(f"Created detections file at {detections_file}")

    # Validate the file format
    try:
        with open(detections_file, "r") as f:
            detections = yaml.safe_load(f)

        # Check the structure of the detections file
        if not isinstance(detections, dict):
            click.echo("Error: Invalid detections file format. Expected a dictionary.")
            return

        # Validate each language section
        valid = True
        for lang, rules in detections.items():
            if not isinstance(rules, dict):
                click.echo(
                    f"Error: Invalid rules for language '{lang}'. Expected a dictionary."
                )
                valid = False
                continue  # Check required keys
            for key in ["file_patterns", "dir_patterns"]:
                if key not in rules:
                    click.echo(f"Warning: Missing '{key}' for language '{lang}'.")
                elif not isinstance(rules[key], List):
                    click.echo(
                        f"Error: Invalid '{key}' for language '{lang}'. Expected a list."
                    )
                    valid = False

        if validate:
            if valid:
                click.echo("Detections file is valid.")
            else:
                click.echo("Detections file has validation errors.")
                sys.exit(1)
            return
    except yaml.YAMLError as e:
        click.echo(f"Error: Invalid YAML format in detections file: {e}")
        if validate:
            sys.exit(1)
        return
    except IOError as e:
        click.echo(f"Error: Could not read detections file: {e}")
        if validate:
            sys.exit(1)
        return

    # If we're not just validating, open the editor
    from prompy.editor import edit_file_with_comments, find_editor

    # Create a description/help text for the detections file
    help_text = """
# Prompy Language Detection Configuration
#
# This file configures how Prompy detects programming languages in your projects.
# For each language, you can define:
#
# file_patterns: List of file patterns (glob) that indicate this language
# dir_patterns: List of directory patterns (glob) that indicate this language
# content_patterns: List of strings to look for in file contents
# weight: Optional weight multiplier for this language (default: 1.0)
#
# Example:
# python:
#   file_patterns:
#     - "*.py"
#     - "requirements.txt"
#   dir_patterns:
#     - ".venv"
#     - "__pycache__"
#   content_patterns:
#     - "import "
#     - "def "
#   weight: 1.0
"""

    # Add the help text to the detections file if it doesn't already have it
    with open(detections_file, "r") as f:
        content = f.read()

    if "# Prompy Language Detection Configuration" not in content:
        with open(detections_file, "w") as f:
            f.write(
                help_text + content
            )  # Open the editor directly without using edit_file_with_comments since we don't need
    # all the prompt handling functionality for the detections file
    try:
        # Launch the editor with the file
        return_code = launch_editor(str(detections_file))

        if return_code == 0:
            click.echo("Detections configuration updated.")

            # Validate the updated file
            with open(detections_file, "r") as f:
                try:
                    yaml.safe_load(f)
                except yaml.YAMLError as e:
                    click.echo(
                        f"Warning: The updated detections file contains YAML errors: {e}"
                    )
            return True
        else:
            click.echo("Error: Failed to update detections configuration.")
            return False

    except Exception as e:
        logger.error(f"Error editing detections file: {e}")
        if ctx.obj.get("debug"):
            logger.exception(e)
        click.echo(f"Error: {e}", err=True)
        return


@cli.command()
@click.argument("shell", type=click.Choice(["bash", "zsh", "fish"]))
@click.option("--output", "-o", help="Output file to write the completion script to.")
@click.pass_context
def completions(ctx: click.Context, shell: str, output: Optional[str] = None) -> None:
    """
    Generate shell completion script.

    SHELL must be one of: bash, zsh, or fish.
    """
    from prompy.completions import get_completion_script, get_installation_instructions
    from prompy.error_handling import PrompyError, handle_error

    try:
        completion_script = get_completion_script(shell)

        if output:
            try:
                # Write completion script to the specified file
                with open(output, "w") as f:
                    f.write(completion_script)
                click.echo(f"Completion script for {shell} written to {output}")
                click.echo(get_installation_instructions(shell))
            except IOError as e:
                error_msg = f"Could not write to file {output}: {str(e)}"
                handle_error(PrompyError(error_msg), ctx)
                return
        else:
            # Output completion script to stdout
            click.echo(completion_script)
            click.echo("\n" + get_installation_instructions(shell))

    except ValueError as e:
        handle_error(PrompyError(f"Error generating completion script: {str(e)}"), ctx)
        return


def main() -> None:
    """
    Entry point for the Prompy command-line tool.
    """
    cli()  # pylint: disable=no-value-for-parameter


if __name__ == "__main__":
    main()
