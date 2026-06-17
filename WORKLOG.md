# Worklog

<!--
Session diary for this project. Claude reads this on return to pick up context.

TRIMMING RULE: When this file exceeds 150 lines, compress older entries:
- Delete anything recoverable from git history or current code
- Condense completed work into one-line summaries
- Keep: open questions, key decisions, active experiments, blockers

PUBLIC REPO: this repository is public. Keep server names, hostnames, IPs,
Tailscale/VPN details, deploy paths, and personal info out of committed files
and commit messages — refer to infrastructure generically (e.g. "the
production server").
-->

## Active

Healthy — full code review done 2026-06-12; four reliability bugs fixed and
deployed to the production server same day (submodule bumped, container
rebuilt, clean first run). Minor review findings deferred, candidates for a
future session: file_lock TOCTOU race,
full-raindrop dump at INFO (logs private note text), deprecated
`datetime.utcnow()`, unpinned requirements + unused `unidecode`, dead embed
fields (`alt_text`/`mime_type`/`size`), unencoded `rdl.ink` fallback URL,
`count_graphemes` over-counting ZWJ emoji (safe direction). Also still open:
README's "Future enhancements" (genAI alt-text, genAI summary).

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

### 2026-06-12

- **Code review:** Full review of the app (all ~1,065 lines + Docker/cron infra).
  Confirmed local main in sync with origin and starter-kit scaffolding healthy
  (all `project-health` checks pass). Review report lives in this session's plan
  file; deferred minor findings listed under Active above.
- **Scaffolding aligned (`c480297`):** Added `.claude/rules/tdd.md` from the
  starter-kit template; fixed CLAUDE.md drift (missing `email_handler.py`,
  missing test entries).
- **Bug fixed (`3c6bac1`):** Double-post window — tracker entries expired after
  7 days, and a permanently failed tag removal was never retried (with
  `perpage: 5`, five stuck items would hide new ones). Skip path now re-attempts
  tag removal (self-healing), retention raised to 90 days, and tracker writes
  are atomic (temp file + `os.replace`; a crash mid-write used to truncate the
  file and erase posted history). Regression test: `scripts/test_posted_tracker.py`.
- **Bug fixed (`225386b`):** Container restart loop — a failing initial run
  under `set -e` killed the container, and `restart: unless-stopped` looped it.
  Initial run is now failure-tolerant; cron is the supervisor. Regression test:
  `scripts/test_entrypoint_resilience.sh` (runs the real entrypoint.sh with
  stubbed su/cron/crontab and a failing python).
- **Bug fixed (`5994c11`):** Bluesky retry detection matched `'429' in str(e)`,
  which false-positives on codes appearing in error bodies (e.g. a 400 with
  "size 4290" retried 3 times). Now checks `e.response.status_code` against
  (429, 502, 503, 504), text match only as fallback when no response is
  attached. Regression test: `scripts/test_bluesky_retry.py`.

### 2026-05-06

- **Set up:** Added Claude Code scaffolding (CLAUDE.md, WORKLOG.md, `.gitignore` entry for `.claude-transcripts/`); deleted three redundant root-level docs (`DEPLOYMENT_CHECKLIST.md`, `DOCKER_IMPLEMENTATION.md`, `DOCKER_QUICKSTART.md` — 758 lines of overlap with README); de-duplicated repeated sections in README.
- **Bug fixed (`a93491c`):** `grapheme too big (got 318)` 400s on Bloomberg/newsletter URLs. Added `strip_tracking_params()` (utm_*, cmpid, gclid, fbclid, etc.) and a build-and-measure retry that re-truncates if atproto's `TextBuilder` inflates the URL during `build_text()` (e.g. percent-encoding). Regression test: `scripts/test_formatter.py`.
- **Bug fixed (`48718d0`):** `entrypoint.sh` was emitting `logs: command not found` on every container start because `set -a; source <(...)` glob-expanded `CRON_SCHEDULE=*/5 * * * *`. Replaced with line-by-line `export "$line"`. Regression test: `scripts/test_env_loader.sh`.
- **Bug fixed (`0ed029b`):** `Invalid -W option ignored: invalid module name: 'pydantic'`. Moved pydantic-deprecation suppression from `PYTHONWARNINGS` (parsed before user packages are importable) into `src/utils/warnings_setup.py`, imported at the top of `raindrop_to_bluesky.py`. Regression test: `scripts/test_warnings_setup.py`.
- **Docs:** Updated README's Features list to cover the reliability work added since v1.0; added a Development & Testing section pointing at the test scripts. Updated CLAUDE.md with the test commands and two new gotchas (`.env` glob expansion, `PYTHONWARNINGS` parse-order trap).
- **Stack:** Python 3.11 in container (Python 3.7+ supported), atproto, Docker + cron.
- **Working agreement adopted:** Red-green-refactor TDD as default — failing test before implementation; bug fixes get a regression test that fails on the bug before the fix lands.
