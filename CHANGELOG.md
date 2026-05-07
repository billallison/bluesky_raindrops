# Changelog

Notable changes to this project. See `git log` for the full history.

## [Unreleased]

- Strip tracking query params (`utm_*`, `cmpid`, `gclid`, `fbclid`, etc.) from posted URLs.
- Re-truncate post text after build if rendered length still exceeds 300 graphemes (safety net for URL percent-encoding by atproto).
- entrypoint: load `.env` line-by-line instead of `set -a; source <(...)` to avoid bash glob expansion on values like `CRON_SCHEDULE=*/5 * * * *` (was emitting `logs: command not found` on every container start).
- entrypoint: fix `PYTHONWARNINGS` filter — `pydantic.warnings.PydanticDeprecatedSince20` → `pydantic.PydanticDeprecatedSince20` (the warnings submodule moved in pydantic v2).

## [1.1.0] — 2026-01-26

- Prevent double-posts when Raindrop API fails during tag removal: track posted IDs locally before tag removal, with retry/backoff for transient errors.
- Use Bluesky's correct 300-grapheme limit with proper Unicode cluster counting (was 280/290).
- Add file lock to prevent overlapping cron runs.
- Migrate post formatting to atproto's `TextBuilder` for facet handling.
- Retry transient errors (502/503/504/429, timeouts) with exponential backoff.
- Centralize logging in a single `setup_logging()` call.

## [1.0.0]

- Initial release: Dockerized Bluesky poster driven by Raindrop.io `toskeet` tag, with image embeds, rich-text facets, and SMTP error alerts.
