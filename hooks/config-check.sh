#!/bin/bash
esc='\ud83d\udd3c'

cd ~/.claude || exit 0
git fetch --quiet origin 2>/dev/null || exit 0
n=$(git rev-list --count 'HEAD..@{u}' 2>/dev/null) || exit 0

if [ "${n:-0}" -gt 0 ]; then
    plural=''
    if [ "$n" -gt 1 ]; then plural='s'; fi
    printf '{"systemMessage":"Claude-Config: %s %s new commit%s upstream"}\n' "$esc" "$n" "$plural"
fi
