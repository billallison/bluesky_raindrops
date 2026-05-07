#!/usr/bin/env bash
# Regression test for entrypoint.sh's .env loader.
#
# Catches bash glob expansion on unquoted values like
#   CRON_SCHEDULE=*/5 * * * *
# which used to print "logs: command not found" on every container start
# and silently dropped the variable.
#
# Run from the repo root:
#   bash scripts/test_env_loader.sh

set -u

FAIL=0
fail() { echo "FAIL: $*"; FAIL=1; }
ok()   { echo "OK:   $*"; }

# --- Loader under test (must mirror entrypoint.sh) ---
load_env() {
    while IFS= read -r line || [[ -n "$line" ]]; do
        line="${line%$'\r'}"
        [[ -z "$line" || "$line" =~ ^[[:space:]]*# ]] && continue
        export "$line"
    done < "$1"
}

# --- Fixture: representative .env including the failing case ---
fixture=$(mktemp)
err_file=$(mktemp)
trap 'rm -f "$fixture" "$err_file"' EXIT
cat > "$fixture" <<'EOF'
# comment line

KEY1=simple
KEY2=with spaces and  multiple    spaces
CRON_SCHEDULE=*/5 * * * *
EMPTY=
EOF

# --- Run loader and capture stderr; loader runs in main shell so exports
#     are visible to the assertions below. ---
load_env "$fixture" 2>"$err_file"
loader_stderr=$(cat "$err_file")

# --- Assertions ---
if [[ -n "${loader_stderr//[[:space:]]/}" ]]; then
    fail "loader emitted stderr (likely a 'command not found' from glob expansion):"
    printf '      %s\n' "$loader_stderr"
else
    ok "loader emitted no stderr"
fi

[[ "${KEY1-}" == "simple" ]] \
    && ok "KEY1=simple" \
    || fail "KEY1: expected 'simple', got '${KEY1-UNSET}'"

[[ "${KEY2-}" == "with spaces and  multiple    spaces" ]] \
    && ok "KEY2 preserves runs of spaces" \
    || fail "KEY2: got '${KEY2-UNSET}'"

[[ "${CRON_SCHEDULE-}" == '*/5 * * * *' ]] \
    && ok "CRON_SCHEDULE preserved without glob expansion" \
    || fail "CRON_SCHEDULE: expected '*/5 * * * *', got '${CRON_SCHEDULE-UNSET}'"

[[ "${EMPTY-}" == "" ]] \
    && ok "EMPTY is empty string" \
    || fail "EMPTY: got '${EMPTY-UNSET}'"

if [[ $FAIL -eq 0 ]]; then
    echo
    echo "All env-loader tests passed."
    exit 0
else
    echo
    echo "Env-loader tests FAILED."
    exit 1
fi
