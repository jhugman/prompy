---
description: Look for the next prompt and perform it
---
1. {{@steps/init-shell}}
2. Open **docs/spec.md** for background on the project.
3. Open **docs/prompt-plan.md** and identify any prompts not marked as completed.
4. For the next incomplete prompt:
    - Double-check if it's truly unfinished (if uncertain, ask for clarification).
    - If you confirm it's already done, skip it.
    - Otherwise, implement it as described.
    - The prompts build upon each other, so look for opportunities for code-reuse, and refactor when necessary.
5. As you work through each **part** of the prompt, you SHOULD be in a loop of:
    - Write focused tests for new functionality
    - Implement new functionality
    - Fix the code until it passes the tests.
    - Refactor until it's the smallest and simplest version that still passes all the tests.
6. After finishing each **part** of the prompt,
    - Run the tests with `{{ @project/run-all-tests }}`.
    - Fix any breakages, until the tests pass. This might mean changing the tests, or fixing the code to account for new assumptions.
    - Update **docs/prompt-plan.md** to mark this part of the prompt as done.
7. After you finish the whole **prompt**:
    - Format the code with `{{ @project/format-code }}`.
    - Update **docs/prompt-plan.md** to mark this prompt as completed.
    - Commit the changes to your repository with a clear commit message.

{{@rules/all}}
