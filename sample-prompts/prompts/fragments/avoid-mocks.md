My general preference about mocking and patching.

- Adding more mocks to a system makes the system more brittle and the tests less resilient to change.
- Avoid mocks or patching for anything except on the edges of the system, like starting a new process.
- Prefer fixtures directories to writing test fixtures in test code.
