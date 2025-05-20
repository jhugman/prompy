---
description: Check that the project conforms to the spec
---
1. {{ @init-shell }}
2. Read the **docs/spec.md** thoroughly.
3. Write end-to-end tests to demonstrate that the system works as specified.
    - Use Mocks, patch and monkey-patching **only** for stubbing out launching and waiting for an editor and clipboard actions.
    - Use fixtures containing actual files, then writing those files, and looking at them is acceptable for end-to-end tests. Copying the fixtures to a temporary directory, then mutating and checking that directory would be ideal.
    - We want to make sure this all works before completions, optimization, packaging etc
4. {{ @all-tests-pass }}
5. {{ @git-commit }}
