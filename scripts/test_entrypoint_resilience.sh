#!/usr/bin/env bash
# Regression test: entrypoint.sh must survive a failing initial run.
#
# entrypoint.sh runs the script once at startup under `set -e`. If that run
# exits non-zero (e.g. a missing env var makes load_config() raise before
# main()'s try/except), the container used to die — and with
# `restart: unless-stopped` it restart-looped, hammering the APIs.
# Cron is the supervisor; a failed initial run must not kill the container.
#
# Runs the REAL entrypoint.sh (paths rewritten into a temp dir, system
# commands stubbed) with a python that always fails, and asserts the
# script still reaches `exec cron -f`.
#
# Run from the repo root:
#   bash scripts/test_entrypoint_resilience.sh

set -u

REPO_ROOT="$(cd "$(dirname "$0")/.." && pwd)"
TMP="$(mktemp -d)"
trap 'rm -rf "$TMP"' EXIT

mkdir -p "$TMP/app/logs" "$TMP/bin"

# Minimal valid .env so the loader section passes
cat > "$TMP/app/.env" <<'EOF'
RAINDROP_TOKEN=dummy
EOF

# --- Command stubs ---

# python that always fails — simulates load_config() crashing at startup
cat > "$TMP/bin/python" <<'EOF'
#!/bin/bash
echo "stub python: simulated startup crash" >&2
exit 1
EOF

# su: ignore args, execute the heredoc piped on stdin, propagate exit code
cat > "$TMP/bin/su" <<'EOF'
#!/bin/bash
exec bash
EOF

# crontab: accept install (-u user file) and list (-l) invocations
cat > "$TMP/bin/crontab" <<'EOF'
#!/bin/bash
exit 0
EOF

# cron: entrypoint ends with `exec cron -f`; reaching this is the success marker
cat > "$TMP/bin/cron" <<'EOF'
#!/bin/bash
echo "CRON_STARTED"
exit 0
EOF

cat > "$TMP/bin/chown" <<'EOF'
#!/bin/bash
exit 0
EOF

chmod +x "$TMP/bin/"*

# --- Rewrite the real entrypoint's absolute paths into the sandbox ---
sed -e "s|/usr/local/bin/python|$TMP/bin/python|g" \
    -e "s|/app|$TMP/app|g" \
    "$REPO_ROOT/entrypoint.sh" > "$TMP/entrypoint_under_test.sh"
chmod +x "$TMP/entrypoint_under_test.sh"

output=$(PATH="$TMP/bin:$PATH" bash "$TMP/entrypoint_under_test.sh" 2>&1)
status=$?

echo "--- entrypoint output ---"
echo "$output"
echo "-------------------------"

FAIL=0
if ! grep -q "CRON_STARTED" <<< "$output"; then
    echo "FAIL: entrypoint died before starting cron — failing initial run killed the container"
    FAIL=1
else
    echo "OK:   entrypoint reached cron despite failing initial run"
fi

if [[ $status -ne 0 ]]; then
    echo "FAIL: entrypoint exited non-zero ($status)"
    FAIL=1
else
    echo "OK:   entrypoint exited 0"
fi

if [[ $FAIL -eq 0 ]]; then
    echo
    echo "All entrypoint-resilience tests passed."
    exit 0
else
    echo
    echo "Entrypoint-resilience tests FAILED."
    exit 1
fi
