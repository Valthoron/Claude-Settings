#!/usr/bin/env pwsh
$ErrorActionPreference = 'Stop'

$payload = [Console]::In.ReadToEnd()

try {
    $command = ($payload | ConvertFrom-Json).tool_input.command
} catch {
    exit 0
}
if ([string]::IsNullOrWhiteSpace($command)) { exit 0 }

$publishes = '(^|[^a-zA-Z0-9_-])git[^;&|]*\spush([^a-zA-Z0-9_-]|$)'
$publishes += '|(^|[^a-zA-Z0-9_-])gh\s+pr\s+(create|merge)([^a-zA-Z0-9_-]|$)'
$publishes += '|(^|[^a-zA-Z0-9_-])gh\s+release\s+create([^a-zA-Z0-9_-]|$)'

if ($command -cmatch $publishes) {
    @'
{"hookSpecificOutput":{"hookEventName":"PreToolUse","permissionDecision":"ask","permissionDecisionReason":"This command publishes to a remote. Claude may not run it unless you asked for this specific action, in this session, in your own words."}}
'@
}

exit 0
