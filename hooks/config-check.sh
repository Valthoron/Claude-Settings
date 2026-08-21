#!/bin/bash
cd ~/.claude || exit 0
branch=$(git symbolic-ref --quiet --short HEAD)
if [ "$branch" != "main" ]; then
    if [ -n "$branch" ]; then
        at="on branch '$branch'"
    else
        at="in detached HEAD"
    fi
    esc='\u2755'
    printf '{"systemMessage":"Claude-Config: %s Not on main branch (%s)"}\n' "$esc" "$at"
    exit 0
fi

git fetch --quiet origin 2>/dev/null || exit 0
n=$(git rev-list --count 'HEAD..@{u}' 2>/dev/null) || exit 0
if [ "${n:-0}" -gt 0 ]; then
    plural=''
    if [ "$n" -gt 1 ]; then plural='s'; fi
    esc='\ud83d\udd3c'
    printf '{"systemMessage":"Claude-Config: %s %s new commit%s upstream"}\n' "$esc" "$n" "$plural"
fi
