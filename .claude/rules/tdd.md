---
name: tdd
description: Test-driven development — write the failing test first
---

This project uses red/green/refactor TDD. Apply it to new behavior and bug fixes:

- **Red:** write a failing test that specifies the desired behavior *before*
  writing the implementation. Run it; confirm it fails for the expected reason.
- **Green:** write the minimum code needed to make the test pass.
- **Refactor:** clean up with the test as a safety net; keep it green.

Conventions:
- One behavior per test; name the test after the behavior it asserts.
- For a bug fix, first write a test that reproduces the bug (red), then fix it.
- This is a deliberately project-level rule (not global) — it lives in this
  project's `.claude/rules/` because TDD was chosen for *this* project.
