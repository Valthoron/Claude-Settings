param([string]$Mode)

# Keeps settings.json, which Claude Code owns and rewrites at will, in step with the
# committed settings.<machine>.json.
#   save: settings.json -> settings.<machine>.json   (Claude Code session hooks)
#   load: settings.<machine>.json -> settings.json   (git post-merge and post-rewrite)
# .settings-baseline.json holds the content both files last agreed on. A side that
# still matches it is the one allowed to be overwritten, so neither direction can
# erase a change the other side has not picked up yet.
Set-Location $HOME\.claude

$live = 'settings.json'
$base = '.settings-baseline.json'

function Say([string]$Text) {
    if ($Mode -eq 'save') {
        '{{"systemMessage":"Claude-Config: ❕ {0}"}}' -f $Text
    } else {
        [Console]::Error.WriteLine("Claude-Config: $Text")
    }
}

function Same([string]$A, [string]$B) {
    (Test-Path $A) -and (Test-Path $B) -and ((Get-FileHash $A).Hash -eq (Get-FileHash $B).Hash)
}

function Valid([string]$File) {
    try {
        Get-Content -Raw $File | ConvertFrom-Json | Out-Null
        $true
    } catch {
        $false
    }
}

if ($Mode -ne 'save' -and $Mode -ne 'load') {
    [Console]::Error.WriteLine('usage: settings-sync.ps1 save|load')
    exit 2
}

$machine = Get-Content .machine -TotalCount 1 -ErrorAction SilentlyContinue
if (-not $machine) {
    Say 'No machine name; run hooks/install-sync.ps1'
    exit 0
}
$tracked = "settings.$machine.json"
if (-not (Test-Path $tracked)) {
    Say "$tracked does not exist"
    exit 0
}

if (Same $live $tracked) {
    if (-not (Same $tracked $base)) { Copy-Item $tracked $base -Force }
    exit 0
}

if ($Mode -eq 'save') {
    $from = $live; $to = $tracked
} else {
    $from = $tracked; $to = $live
}

if (Same $to $base) {
    if (-not (Valid $from)) {
        Say "$from is not valid JSON, not copied"
        exit 0
    }
    Copy-Item $from $to -Force
    Copy-Item $from $base -Force
} elseif (Same $from $base) {
    # Only the destination moved. In load mode that is a session's unsaved change,
    # which the session end will save; in save mode it is a pull or an edit that
    # never reached settings.json.
    if ($Mode -eq 'save') {
        if (Valid $tracked) {
            Say "$tracked changed but is not applied; run hooks/settings-sync.ps1 load"
        } else {
            Say "$tracked is not valid JSON; resolve it, then run hooks/settings-sync.ps1 load"
        }
    }
} else {
    Say "$live and $tracked both changed; merge them by hand until they are identical"
}
exit 0
