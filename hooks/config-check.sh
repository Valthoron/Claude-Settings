#!/bin/bash
cd ~/.claude || exit 0
git fetch --quiet origin 2>/dev/null || exit 0
n=$(git rev-list --count 'HEAD..@{u}' 2>/dev/null) || exit 0
[ "${n:-0}" -eq 0 ] && exit 0
printf '{"systemMessage":"claude config: %s new commit(s) upstream"}\n' "$n"
