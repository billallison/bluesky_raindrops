# Worklog

<!--
Session diary for this project. Claude reads this on return to pick up context.

TRIMMING RULE: When this file exceeds 150 lines, compress older entries:
- Delete anything recoverable from git history or current code
- Condense completed work into one-line summaries
- Keep: open questions, key decisions, active experiments, blockers
-->

## Active

Healthy — three reliability fixes deployed today on top of the previous
maintenance-mode baseline. Next likely work: README's "Future enhancements"
(genAI alt-text on cover images, genAI summary in place of Raindrop excerpt).

## Decisions

- Mark-as-posted runs *before* tag removal so a Raindrop API failure on the
  untag step can't cause a double-post on the next cron tick.
- Bluesky facet indices use byte positions (not character positions) — required
  by the atproto spec.
- Suppress pydantic deprecation warnings in Python (via
  `src/utils/warnings_setup.py`), not via `PYTHONWARNINGS`. Python parses `-W`
  filters before user packages are importable, so non-builtin warning classes
  fail with `Invalid -W option ignored`.
- Tests live as plain runnable scripts under `scripts/` (no pytest yet) — each
  exits non-zero on failure so CI can pick them up unchanged.

## Sessions

### 2026-05-06

- **Set up:** Added Claude Code scaffolding (CLAUDE.md, WORKLOG.md, `.gitignore` entry for `.claude-transcripts/`); deleted three redundant root-level docs (`DEPLOYMENT_CHECKLIST.md`, `DOCKER_IMPLEMENTATION.md`, `DOCKER_QUICKSTART.md` — 758 lines of overlap with README); de-duplicated repeated sections in README.
- **Bug fixed (`a93491c`):** `grapheme too big (got 318)` 400s on Bloomberg/newsletter URLs. Added `strip_tracking_params()` (utm_*, cmpid, gclid, fbclid, etc.) and a build-and-measure retry that re-truncates if atproto's `TextBuilder` inflates the URL during `build_text()` (e.g. percent-encoding). Regression test: `scripts/test_formatter.py`.
- **Bug fixed (`48718d0`):** `entrypoint.sh` was emitting `logs: command not found` on every container start because `set -a; source <(...)` glob-expanded `CRON_SCHEDULE=*/5 * * * *`. Replaced with line-by-line `export "$line"`. Regression test: `scripts/test_env_loader.sh`.
- **Bug fixed (`0ed029b`):** `Invalid -W option ignored: invalid module name: 'pydantic'`. Moved pydantic-deprecation suppression from `PYTHONWARNINGS` (parsed before user packages are importable) into `src/utils/warnings_setup.py`, imported at the top of `raindrop_to_bluesky.py`. Regression test: `scripts/test_warnings_setup.py`.
- **Docs:** Updated README's Features list to cover the reliability work added since v1.0; added a Development & Testing section pointing at the test scripts. Updated CLAUDE.md with the test commands and two new gotchas (`.env` glob expansion, `PYTHONWARNINGS` parse-order trap).
- **Stack:** Python 3.11 in container (Python 3.7+ supported), atproto, Docker + cron.
- **Working agreement adopted:** Red-green-refactor TDD as default — failing test before implementation; bug fixes get a regression test that fails on the bug before the fix lands.
