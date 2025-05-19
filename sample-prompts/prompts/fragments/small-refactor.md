---
description: small-refactor
---

Read the **docs/spec.md**.

Refactor the CLI such that:

- the `--mv` functionality is now a `mv` subcommand, to move re-usable prompts from one slug to another.
- the `--edit` functionality is now an `edit` subcommand. If the template for the slug doesn't exist, a new one should be made.
- the `--save` functionality is now an `save` subcommand. If the template for the slug exists, a it should overwrite the old one.
- the `--list` functionality is now a `list` command.
- the `--detections` functionality is now a `detections` command.
- the remaining options are applied in this order:
  - `--new`: if present, then the `CURRENT_FILE.md` is overwritten.
  - If a PROMPT_SLUG is present, then the reusable prompt is added to the `CURRENT_FILE.md`.
  - If `-o`, `-f` or `-c` are present, the we're outputting.
  - If `--new` is present, we're not outputting, then open an editor with the current
  - If `--new` is not present, and we outputting then we output the expanded re-usable prompt.
  - If the editor is open and we're outputting then wait for the editor to close, then output the expanded re-usable prompt.

Each new subcommand should have `--help` and `--debug` flags.

Steps:

1. @init-shell
2. For each refactor:
    - Update the code
    - Update the tests
    - @all-tests-pass
3. Update the documentation.
4. Update the prompt plan if needed.
5. @git-commit

@avoid-mocks
