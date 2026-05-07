# Worklog

<!--
Session diary for this project. Claude reads this on return to pick up context.

TRIMMING RULE: When this file exceeds 150 lines, compress older entries:
- Delete anything recoverable from git history or current code
- Condense completed work into one-line summaries
- Keep: open questions, key decisions, active experiments, blockers
-->

## Active

Maintenance mode — bot is deployed via Docker and running on cron. Recent work
(commits `f7d5a86`, `35dcf83`, `777178c`, `cb4f54d`) focused on bug fixes:
double-posting prevention, tag removal, pydantic warnings, `.env` handling.

## Decisions

- Mark-as-posted runs *before* tag removal so a Raindrop API failure on the
  untag step can't cause a double-post on the next cron tick.
- Bluesky facet indices use byte positions (not character positions) — required
  by the atproto spec.

## Sessions

### 2026-05-06

- **Set up:** Added Claude Code scaffolding (CLAUDE.md, WORKLOG.md, `.claude/settings.local.json`, `.gitignore` entry for transcripts).
- **Stack:** Python 3.7+, atproto, Docker + cron
- **Next:** TBD — possibly the README's "Future enhancements" (genAI alt-text, genAI summary in place of excerpt).
