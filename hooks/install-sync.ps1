param([Parameter(Mandatory)][string]$Machine)

# One-time setup of settings sync on this machine: install-sync.ps1 <machine>
# <machine> is the middle of settings.<machine>.json.
$ErrorActionPreference = 'Stop'
Set-Location $HOME\.claude

if (-not (Test-Path "settings.$Machine.json")) {
    [Console]::Error.WriteLine("settings.$Machine.json does not exist")
    exit 1
}

Set-Content .machine $Machine

git config core.hooksPath hooks/git
git config merge.autoStash true
git config rebase.autoStash true

# Claude Code saves settings.json by replacing the file, which turns a symlink into a
# stale copy. The two files are kept in step by copying instead.
if ((Test-Path settings.json) -and (Get-Item settings.json).LinkType) {
    Remove-Item settings.json
}
if (-not (Test-Path settings.json)) {
    Copy-Item "settings.$Machine.json" settings.json
}

& "$PSScriptRoot\settings-sync.ps1" load
"Settings sync installed for $Machine."
