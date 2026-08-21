Set-Location $HOME\.claude

$branch = git symbolic-ref --quiet --short HEAD
if ($branch -ne 'main') {
    if ($branch) {
        $at = "on branch '$branch'"
    } else {
        $at = "in detached HEAD"
    }
    '{{"systemMessage":"Claude-Config: \u2755 Not on main branch ({0})"}}' -f $at
    exit 0
}

git fetch --quiet origin 2>$null
$n = git rev-list --count 'HEAD..@{u}' 2>$null
if ($n -and [int]$n -gt 0) {
    $plural = ''
    if ([int]$n -gt 1) { $plural = 's' }
    '{{"systemMessage":"Claude-Config: \ud83d\udd3c {0} new commit{1} upstream"}}' -f $n, $plural
}
exit 0
