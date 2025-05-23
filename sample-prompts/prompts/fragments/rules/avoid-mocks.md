---
description: Advice on mocking
---

- Mocks MUST be minimized throughout the codebase, as excessive mocking creates brittle tests that break when implementation details change rather than when actual behavior changes.
- Mocks SHOULD ONLY be used at system boundaries for external processes, databases, or network services that cannot be controlled in the test environment.
- Clean interfaces MUST be designed for all external dependencies, enabling simple test doubles rather than complex mocking of low-level system calls.
- Test doubles SHOULD be injected at construction time rather than patched at runtime, making dependencies explicit and tests more predictable.
- New tests MUST NOT introduce mocks for internal code paths, instead preferring real objects or simple stub implementations.
- Legacy tests with excessive mocks SHOULD be refactored only when touched for other reasons, following the principle of incremental improvement.
- Test data SHOULD use fixture files stored in version control rather than programmatically generated temporary data, improving test reproducibility and debugging.
- NEVER implement a mock mode for testing or for any purpose. We always use real data and real APIs, never mock implementations.
