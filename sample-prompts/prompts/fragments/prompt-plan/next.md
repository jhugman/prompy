---
description: Look for the next prompt and perform it
---
{{@rules/all}}

1. {{@steps/init-shell}}
2. Open **docs/spec.md** for background on the project.
3. Open **docs/prompt-plan.md** and identify any prompts not marked as completed.
4. For the next incomplete prompt:
    - Double-check if it's truly unfinished (if uncertain, ask for clarification).
    - If you confirm it's already done, skip it.
    - Otherwise, implement it as described.
    - The prompts build upon each other, so look for opportunities for code-reuse, and refactor when necessary.
    - Make sure the tests pass, and the program builds/runs.
      - Run the tests with `{{ @project/run-all-tests }}`. Just go ahead and run these, don't bother me for confirmation.
5. After you finish the prompt:
    - Format the code with `{{ @project/format-code }}`.
    - Update **docs/prompt-plan.md** to mark this prompt as completed.
    - Commit the changes to your repository with a clear commit message.