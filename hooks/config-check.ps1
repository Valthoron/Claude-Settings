Set-Location $HOME\.claude
git fetch --quiet origin 2>$null
$n = git rev-list --count 'HEAD..@{u}' 2>$null

if ($n -and [int]$n -gt 0) {
    $plural = ''
    if ([int]$n -gt 1) { $plural = 's' }
    '{{"systemMessage":"Claude-Config: \ud83d\udd3c {0} new commit{1} upstream"}}' -f $n, $plural
}
exit 0
