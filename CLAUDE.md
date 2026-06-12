# bluesky_raindrops

Periodically posts Raindrop.io items tagged `toskeet` to Bluesky, then removes the tag. Runs in Docker via cron (default every 10 minutes).

## Environment & Prerequisites

- **Runtime:** Python 3.7+ (Docker image is the recommended target)
- **Package manager:** pip (`requirements.txt`); no lockfile
- **External services:** Raindrop.io API, Bluesky (atproto), SMTP for failure alerts
- **First-time setup:** `cp .env.example .env` and fill in `RAINDROP_TOKEN`, `BLUESKY_IDENTIFIER`, `BLUESKY_PASSWORD`, SMTP creds

## Build & Run

```bash
# Docker (preferred)
make deploy            # env-check + build + up
make logs-live         # follow container logs
make test              # run the script once inside the container
make down              # stop the container

# Manual Python
python -m venv venv && source venv/bin/activate
pip install -r requirements.txt
python raindrop_to_bluesky.py
```

Regression tests under `scripts/` (no test runner — exit non-zero on failure):

```bash
.venv/bin/python scripts/test_formatter.py            # post_formatter behavior
.venv/bin/python scripts/test_warnings_setup.py       # pydantic warning filter
.venv/bin/python scripts/test_posted_tracker.py       # double-post safety net
.venv/bin/python scripts/test_bluesky_retry.py        # transient-error retry logic
bash scripts/test_env_loader.sh                       # entrypoint .env-loader behavior
bash scripts/test_entrypoint_resilience.sh            # container survives failed initial run
```

End-to-end verification is still "run it once in the container and watch the log."

## Architecture

```
raindrop_to_bluesky.py    # Entry point — orchestrates one fetch/post/untag cycle
src/raindrop_handler.py   # Raindrop.io API: fetch latest `toskeet` item, remove tag
src/bluesky_handler.py    # atproto client: login + post (text, facets, embed)
src/post_formatter.py     # Builds Bluesky post text + facets + embed from a Raindrop
src/utils/config.py       # Loads .env via python-dotenv
src/utils/logging_config.py
src/utils/error_handler.py    # send_error_alert() — wraps email_handler, never raises
src/utils/email_handler.py    # SMTP send: builds alert email with last 50 log lines
src/utils/posted_tracker.py   # Persists posted raindrop IDs to prevent double-posts
src/utils/file_lock.py        # script_lock() context manager — prevents overlapping runs
src/utils/warnings_setup.py   # Filters pydantic deprecation warnings from atproto
scripts/test_*.py, *.sh   # Regression tests (run directly, no pytest)
Dockerfile, docker-compose.yml, entrypoint.sh   # Cron-driven container
```

Flow: `script_lock` → `load_config` → `cleanup_old_entries` → `get_latest_raindrop_to_skeet` → `format_bluesky_post_from_raindrop` → `post_content_to_bluesky` → `mark_as_posted` → `remove_toskeet_tag`. Failures at any step trigger `send_error_alert`.

The Raindrop note field uses `[skeet_content: ...]` to carry post commentary — anything outside the brackets stays private.

## Patterns & Conventions

- **Naming:** snake_case
- **Error handling:** exceptions bubble to `main()`, logged via `logger.exception`, then SMTP alert
- **Idempotency:** `mark_as_posted` runs *before* `remove_toskeet_tag` so a tag-removal failure doesn't cause a double-post on the next run
- **Concurrency:** `file_lock.script_lock()` ensures only one instance runs at a time
- **Commits:** repo uses short imperative-mood messages (e.g. "Fix tag removal"); not strict conventional commits

## Gotchas

- **Bluesky facet indices are byte offsets, not character offsets** — see commit `ba0ecfb`. Anything that touches link/mention positioning must encode the text first.
- **Cover images need conversion before posting** — see commits `09d2439`, `bf1659f`, `c003431`. The Pillow path handles odd source formats and user-agent quirks.
- **Grapheme limit is not the same as character limit** — `5ef0a47` reduced the cap; Bluesky counts graphemes for the 300-char post limit.
- **`.env` is volume-mounted in the container** — `cb4f54d` fixed handling so changes don't require a rebuild.
- **`.env` loader avoids `set -a; source <(...)`** — bash glob-expands unquoted values like `CRON_SCHEDULE=*/5 * * * *` and silently drops them. `entrypoint.sh` reads line-by-line and `export "$line"` instead. See `scripts/test_env_loader.sh` and commit `48718d0`.
- **Pydantic warnings can't be filtered via `PYTHONWARNINGS`** — Python parses `-W` filters before user packages are importable, so any non-builtin warning class fails with `Invalid -W option ignored`. Filter via `src/utils/warnings_setup.py` (imported at the top of `raindrop_to_bluesky.py`) instead.
- The container runs cron as a non-root user; logs land in `./logs` on the host.

## Working Agreements

- **Red-green-refactor TDD.** New behavior gets a failing test before the implementation. Bug fixes get a regression test that reproduces the bug before the fix lands. Keep tests under `scripts/` (`test_*.py` for Python, `test_*.sh` for shell) — no pytest yet, plain scripts that exit non-zero on failure.
- Update WORKLOG.md each session with what was done and what's next
- Keep this file under 200 lines — move details to code comments or `docs/`
