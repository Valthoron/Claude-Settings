#!/usr/bin/env bash
#
# PreToolUse/Bash: raise a permission prompt before any command that publishes to a
# remote -- git push, gh pr create, gh pr merge, gh release create.
#
# Written after a branch was pushed and a pull request opened without being asked for.
# An instruction against exactly that was already in place and was reasoned around, so
# this is a gate that runs before the tool call rather than another sentence to read.
#
# Local commits and every read-only git command are deliberately untouched.
#
# Matching is over-inclusive on purpose: it reads the raw command string, so it also
# sees compound commands, `git -C <dir> push`, and a push buried mid-pipeline. A false
# positive costs one extra prompt; a false negative is the failure this exists to
# prevent.

set -uo pipefail

payload="$(cat)"

# No jq, unreadable payload, or a non-Bash shape: say nothing rather than guess. The
# permissions.ask rules in settings.json remain as the second net.
command="$(printf '%s' "$payload" | jq -r '.tool_input.command // empty' 2>/dev/null)" || exit 0
[ -n "$command" ] || exit 0

# `git <anything that is not a command separator> push` catches `git push`,
# `git -C /path push`, `git --no-pager push`, and any of those after a && or a pipe.
publishes='(^|[^[:alnum:]_-])git[^;&|]*[[:space:]]push([^[:alnum:]_-]|$)'
publishes="$publishes"'|(^|[^[:alnum:]_-])gh[[:space:]]+pr[[:space:]]+(create|merge)([^[:alnum:]_-]|$)'
publishes="$publishes"'|(^|[^[:alnum:]_-])gh[[:space:]]+release[[:space:]]+create([^[:alnum:]_-]|$)'

if printf '%s' "$command" | grep -Eq "$publishes"; then
    cat <<'JSON'
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"This command publishes to a remote. Claude may not run it unless you asked for this specific action, in this session, in your own words."}}
JSON
fi

exit 0
