"""
Command-line interface for Prompy.
"""

import logging
import re
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
from prompy.diagnostics import diagnostics_manager, enable_diagnostics
from prompy.editor import (
    edit_file_with_comments,
    find_editor,
    launch_editor,
)
from prompy.error_handling import PrompyError, handle_error
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
@click.option(
    "--diagnose", is_flag=True, help="Enable diagnostic mode for fragment resolution."
)
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
    diagnose: bool,
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

    # Enable diagnostics if requested
    if diagnose:
        enable_diagnostics()
        logging.info("Diagnostic mode enabled")

    # Store diagnostic mode in the context
    ctx.ensure_object(dict)
    ctx.obj["diagnose"] = diagnose

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
    Create a new prompt and open it in an editor.

    If PROMPT_SLUG is provided, use it as a template. Otherwise, start with an empty prompt.
    """
    try:
        # Get project info
        project_name = ctx.obj.get("project")
        if not project_name:
            click.echo(
                "No project detected. Please specify a project with --project.",
                err=True,
            )
            return

        # Get config dirs
        cache_dir = ctx.obj.get("cache_dir")
        prompt_context = from_click_context(ctx)

        # Clear existing cache
        clear_cache(cache_dir, project_name)

        # Get the cache file path and ensure parent directory exists
        cache_file_path = get_cache_file_path(cache_dir, project_name)
        cache_file_path.parent.mkdir(parents=True, exist_ok=True)

        # Check for stdin content
        stdin_content = get_stdin_content()
        if stdin_content:
            # Save stdin content to cache
            save_to_cache(cache_dir, project_name, stdin_content)
            click.echo("Appended content from stdin.")
        else:
            # If a template prompt is specified, use it
            if prompt_slug:
                prompt_file = prompt_context.load_slug(prompt_slug)
                save_to_cache(cache_dir, project_name, prompt_file.markdown_template)
            else:
                # Start with empty file
                save_to_cache(cache_dir, project_name, "")

        # Load prompt files for help comments
        prompt_files = prompt_context.load_all()

        # Launch the editor
        success = edit_file_with_comments(str(cache_file_path), prompt_files)

        if success:
            click.echo(f"New prompt cached for {project_name}")
        else:
            click.echo("Failed to save prompt.", err=True)
            return

        if save_as is not None:
            ctx.invoke(save, prompt_slug=save_as)

    except Exception as e:
        handle_error(e, ctx)
        return


@cli.command()
@click.argument("prompt_slug", required=False, shell_complete=complete_prompt_slug)
@click.pass_context
def edit(ctx: click.Context, prompt_slug: Optional[str]) -> None:
    """
    Edit a prompt in the default editor.

    If PROMPT_SLUG is provided, edit that prompt.
    Otherwise, edit the current one-off prompt.
    """
    try:
        prompt_context = from_click_context(ctx)
        project_name = ctx.obj.get("project")
        cache_dir = ctx.obj.get("cache_dir")

        # Get stdin content if available
        stdin_content = get_stdin_content()

        # If a slug is provided, edit that prompt
        file_path = None
        if prompt_slug:
            file_path = prompt_context.parse_prompt_slug(prompt_slug)
            assert file_path is not None

            # If stdin content exists, append it directly to the file
            if stdin_content:
                with open(file_path, "r", encoding="utf-8") as f:
                    existing_content = f.read()

                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(existing_content.rstrip() + "\n\n" + stdin_content)

                click.echo("Appended content from stdin.")

            click.echo(f"Editing prompt: {prompt_slug}")
        else:
            # Edit the current one-off prompt in cache
            if not project_name:
                raise PrompyError(
                    "No project detected",
                    suggestion="Specify a project with --project or run prompy in a project directory",
                )

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
            raise PrompyError(
                "Failed to save prompt",
                suggestion="Check file permissions and make sure you have write access",
            )

    except Exception as e:
        handle_error(e, ctx)
        return


def get_stdin_content():
    """Get content from stdin if available."""
    if not sys.stdin.isatty():
        return sys.stdin.read()
    return None


@cli.command()
@click.argument("prompt_slug", required=False, shell_complete=complete_prompt_slug)
@click.option("--file", "-f", help="Save to a file.")
@click.option("--pbcopy", is_flag=True, help="Copy output to clipboard.")
@click.pass_context
def out(
    ctx: click.Context, prompt_slug: Optional[str], file: Optional[str], pbcopy: bool
) -> None:
    """Output the current prompt or a specified prompt.

    If no prompt_slug is provided, outputs the current cached prompt for the project.
    """
    from prompy.context import from_click_context
    from prompy.prompt_file import PromptFile

    project_name = ctx.obj.get("project")
    cache_dir = ctx.obj.get("cache_dir")
    global_only = ctx.obj.get("global_only", False)
    prompt_context = from_click_context(ctx)

    try:
        # Load either the specified prompt or the current cache
        if not prompt_slug:
            if not project_name:
                raise PrompyError(
                    "No project detected",
                    suggestion="Specify a project with --project or run prompy in a project directory",
                )

            # Load the current cache content
            success, content = load_from_cache(cache_dir, project_name)
            if not success or not content:
                raise PrompyError(
                    "No current prompt found",
                    suggestion="Try specifying a prompt slug or providing content via stdin",
                )
            prompt_file = PromptFile(slug="cache", markdown_template=content)
        else:
            prompt_file = prompt_context.load_slug(prompt_slug, global_only=global_only)

        # Resolve fragment references in the content
        from prompy.diagnostics import diagnostics_manager
        from prompy.prompt_render import PromptRender

        # Create a PromptFile object from the content
        renderer = PromptRender(prompt_file)
        resolved_content = renderer.render(prompt_context)

        # Print diagnostics report if diagnostic mode is enabled
        if ctx.obj.get("diagnose", False):
            diagnostics_manager.print_report()

        # Output the content using the appropriate method
        if output_to := file:
            from prompy.output import output_to_file

            if output_to_file(resolved_content, file):
                click.echo(f"Prompt output to file: {output_to}")
            else:
                raise PrompyError(
                    "Failed to write to file",
                    file_path=output_to,
                    suggestion="Check file permissions and try again",
                )
        if pbcopy:
            from prompy.output import output_to_clipboard

            if output_to_clipboard(resolved_content):
                click.echo("Prompt copied to clipboard.")
            else:
                raise PrompyError(
                    "Failed to copy to clipboard",
                    suggestion="Make sure your system clipboard is accessible",
                )
        if not pbcopy and file is None:
            # Output to stdout with a header
            from prompy.output import output_to_stdout

            output_to_stdout(resolved_content)

    except Exception as e:
        handle_error(e, ctx)


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
    """Save the current cached prompt to a reusable fragment."""
    project_name = ctx.obj.get("project")
    cache_dir = ctx.obj.get("cache_dir")
    global_only = ctx.obj.get("global_only", False)
    prompt_context = from_click_context(ctx)

    try:
        # Load the current cache content
        success, content = load_from_cache(cache_dir, project_name)
        if not success or not content:
            raise PrompyError(
                "No current prompt found",
                suggestion="Create a new prompt with 'prompy new' or edit an existing one with 'prompy edit'",
            )

        # Get the destination path
        dest_path = prompt_context.parse_prompt_slug(
            prompt_slug, should_exist=False, global_only=global_only
        )
        if not dest_path:
            raise PrompyError(
                "Could not resolve destination path",
                suggestion=f"Check that the slug '{prompt_slug}' is valid",
            )

        # Check if the file already exists
        if dest_path.exists() and not force:
            if not click.confirm(f"File already exists at {dest_path}. Overwrite?"):
                raise PrompyError(
                    "Save operation aborted",
                    suggestion="Use --force to overwrite without confirmation",
                )

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

        # Generate YAML frontmatter string and save
        prompt_file.frontmatter = prompt_file.generate_frontmatter()
        # Ensure parent directory exists and save
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        prompt_file.save(dest_path)

        click.echo(f"Prompt saved successfully to: {dest_path}")

    except Exception as e:
        handle_error(e, ctx)


@cli.command()
@click.argument("prompt_slug", required=False, shell_complete=complete_prompt_slug)
@click.pass_context
def pbcopy(ctx: click.Context, prompt_slug: Optional[str]) -> None:
    """
    Copy a prompt to the clipboard.

    If PROMPT_SLUG is provided, copy that prompt.
    Otherwise, copy the current one-off prompt.
    """
    try:
        # For prompt_slug, call regular out command with --pbcopy flag
        ctx.invoke(out, prompt_slug=prompt_slug, file=None, pbcopy=True)
    except Exception as e:
        handle_error(e, ctx)


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
def cp(ctx: click.Context, source_slug: str, dest_slug: str, force: bool) -> None:
    """Copy a prompt to a new location."""
    from prompy.context import from_click_context

    prompt_context = from_click_context(ctx)
    global_only = ctx.obj.get("global_only", False)

    try:
        # Check if source exists
        source_path = prompt_context.parse_prompt_slug(
            source_slug, global_only=global_only
        )
        assert source_path is not None

        # Get destination path
        dest_path = prompt_context.parse_prompt_slug(
            dest_slug, should_exist=False, global_only=global_only
        )
        if not dest_path:
            raise PrompyError(
                f"Invalid destination slug: {dest_slug}",
                suggestion="Ensure the destination slug follows the correct format",
            )

        # Check if destination exists
        if dest_path.exists() and not force:
            if not click.confirm(
                f"Destination already exists: {dest_path}. Overwrite?"
            ):
                raise PrompyError(
                    "Copy operation aborted",
                    suggestion="Use --force to overwrite without confirmation",
                )

        # Load source prompt to preserve metadata
        source_prompt = prompt_context.load_slug(source_slug, global_only=global_only)

        # Save to new location
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        source_prompt.save(dest_path)

        # Confirm copy worked
        if dest_path.exists():
            click.echo(f"Copied '{source_slug}' to '{dest_slug}'")
        else:
            raise PrompyError(
                "Failed to save to destination",
                suggestion="Check file permissions and try again",
            )

    except Exception as e:
        handle_error(e, ctx)


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
    """Move/rename a prompt from one location to another."""
    try:
        from prompy.context import from_click_context

        prompt_context = from_click_context(ctx)
        global_only = ctx.obj.get("global_only", False)

        # Check if source exists
        source_path = prompt_context.parse_prompt_slug(
            source_slug, global_only=global_only
        )
        assert source_path is not None

        # Get destination path
        dest_path = prompt_context.parse_prompt_slug(
            dest_slug, should_exist=False, global_only=global_only
        )
        if not dest_path:
            raise PrompyError(
                f"Invalid destination slug: {dest_slug}",
                suggestion="Ensure the destination slug follows the correct format",
            )

        # Check if destination exists and handle confirmation
        if dest_path.exists() and not force:
            if not click.confirm(
                f"Destination already exists: {dest_path}. Overwrite?"
            ):
                raise PrompyError(
                    "Move operation aborted",
                    suggestion="Use --force to overwrite without confirmation",
                )

        # Load source prompt to preserve metadata
        source_prompt = prompt_context.load_slug(source_slug, global_only=global_only)

        # Save to new location
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        source_prompt.save(dest_path)

        # Delete source once we've successfully copied to destination
        source_path.unlink()
        click.echo(f"Moved '{source_slug}' to '{dest_slug}'")

        # Update references
        updated_files = update_references(
            prompt_context,
            source_slug,
            dest_slug,
        )

        if updated_files:
            num_files = len(updated_files)
            click.echo(f"✨ Updated references in {num_files} file(s)")
        else:
            click.echo("✨ No references to update")

    except Exception as e:
        # All errors are handled here, including user cancellations
        handle_error(e, ctx)


@cli.command()
@click.argument("prompt_slug", shell_complete=complete_prompt_slug)
@click.option("--force", "-f", is_flag=True, help="Remove without confirmation.")
@click.pass_context
def rm(ctx: click.Context, prompt_slug: str, force: bool) -> None:
    """Remove a prompt."""
    from prompy.context import from_click_context

    prompt_context = from_click_context(ctx)
    global_only = ctx.obj.get("global_only", False)

    try:
        # Check if prompt exists
        file_path = prompt_context.parse_prompt_slug(
            prompt_slug, global_only=global_only
        )
        assert file_path is not None

        # Confirm deletion if not forced
        if not force:
            if not click.confirm(f"Remove prompt '{prompt_slug}'?"):
                raise PrompyError(
                    "Remove operation aborted",
                    suggestion="Use --force to remove without confirmation",
                )

        # Remove the file
        try:
            file_path.unlink()
            click.echo(f"Removed '{prompt_slug}'")
        except Exception as e:
            raise PrompyError(
                f"Failed to remove {prompt_slug}",
                str(e),
                suggestion="Check file permissions and try again",
            )

    except Exception as e:
        handle_error(e, ctx)
        return


@cli.command()
@click.option(
    "--validate",
    is_flag=True,
    help="Validate the detections file format without opening the editor.",
)
@click.pass_context
def detections(ctx: click.Context, validate: bool) -> None:
    """Edit or validate language detection rules."""
    detections_file = ctx.obj.get("detections_file")

    try:
        # Load current detections
        try:
            with open(detections_file, "r", encoding="utf-8") as f:
                content = f.read()
                current_detections = yaml.safe_load(content)
        except FileNotFoundError:
            raise PrompyError(
                "Detections file not found",
                details=f"Could not find file at: {detections_file}",
                suggestion="💡 Run 'prompy detections' to create and edit the detections file, or check file permissions",
            )
        except yaml.YAMLError as e:
            # Get file content and extract error info
            try:
                with open(detections_file, "r", encoding="utf-8") as f:
                    content = f.read()
            except:
                content = None

            # Extract line/column info from the error message
            error_msg = str(e)
            line_match = re.search(r"line (\d+)", error_msg)
            col_match = re.search(r"column (\d+)", error_msg)
            line_num = int(line_match.group(1)) if line_match else None
            col_num = int(col_match.group(1)) if col_match else None

            raise PrompyError(
                "Invalid YAML in detections file",
                details=error_msg,
                suggestion="💡 Fix the YAML syntax error and try again:\n"
                + "  - Check indentation levels\n"
                + "  - Ensure all quotes are properly closed\n"
                + "  - Verify list items use consistent formatting",
                file_path=str(detections_file),
                snippet=content,
                snippet_line=line_num,
                snippet_column=col_num,
            )

        if validate:
            # Just validate the file and exit
            click.echo("✅ Detections file is valid.")
            return

        # Launch editor with an empty PromptFiles since we don't need fragment help text
        empty_prompt_files = PromptFiles(
            project_name=None,
            language_name=None,
            languages={},
            projects={},
            fragments={},
        )
        success = edit_file_with_comments(str(detections_file), empty_prompt_files)
        if not success:
            raise PrompyError(
                "Failed to edit detections file",
                details=f"Could not save changes to: {detections_file}",
                suggestion="💡 Make sure you have write permissions and try again",
            )

        # Validate after editing
        try:
            with open(detections_file, "r", encoding="utf-8") as f:
                yaml.safe_load(f)
                click.echo("✅ Detections configuration updated and validated.")
        except yaml.YAMLError as e:
            raise PrompyError(
                "Invalid YAML in edited detections file",
                details=str(e),
                suggestion="💡 Fix the YAML syntax and try again:\n"
                + "  - Check indentation levels\n"
                + "  - Ensure all quotes are properly closed\n"
                + "  - Verify list items use consistent formatting",
                file_path=str(detections_file),
            )

    except Exception as e:
        handle_error(e, ctx)


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
