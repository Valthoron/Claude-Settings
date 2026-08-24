#!/usr/bin/env bash
set -uo pipefail

payload="$(cat)"

command="$(printf '%s' "$payload" | jq -r '.tool_input.command // empty' 2>/dev/null)" || exit 0
[ -n "$command" ] || exit 0

publishes='(^|[^[:alnum:]_-])git[^;&|]*[[:space:]]push([^[:alnum:]_-]|$)'
publishes="$publishes"'|(^|[^[:alnum:]_-])gh[[:space:]]+pr[[:space:]]+(create|merge)([^[:alnum:]_-]|$)'
publishes="$publishes"'|(^|[^[:alnum:]_-])gh[[:space:]]+release[[:space:]]+create([^[:alnum:]_-]|$)'

if printf '%s' "$command" | grep -Eq "$publishes"; then
    cat <<'JSON'
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"This command publishes to a remote."}}
JSON
fi

exit 0
