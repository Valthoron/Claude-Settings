#!/bin/bash
# Keeps settings.json, which Claude Code owns and rewrites at will, in step with the
# committed settings.<machine>.json.
#   save: settings.json -> settings.<machine>.json   (Claude Code session hooks)
#   load: settings.<machine>.json -> settings.json   (git post-merge and post-rewrite)
# .settings-baseline.json holds the content both files last agreed on. A side that
# still matches it is the one allowed to be overwritten, so neither direction can
# erase a change the other side has not picked up yet.
set -u
cd ~/.claude || exit 0

mode=${1:-}
live=settings.json
base=.settings-baseline.json

say() {
    if [ "$mode" = save ]; then
        esc='❕'
        printf '{"systemMessage":"Claude-Config: %s %s"}\n' "$esc" "$1"
    else
        printf 'Claude-Config: %s\n' "$1" >&2
    fi
}

same() { cmp -s "$1" "$2"; }
valid() { jq empty "$1" >/dev/null 2>&1; }

case $mode in
    save|load) ;;
    *) echo "usage: settings-sync.sh save|load" >&2; exit 2 ;;
esac

machine=$(head -n 1 .machine 2>/dev/null)
if [ -z "$machine" ]; then
    say "No machine name; run hooks/install-sync.sh"
    exit 0
fi
tracked="settings.$machine.json"
if [ ! -f "$tracked" ]; then
    say "$tracked does not exist"
    exit 0
fi

if same "$live" "$tracked"; then
    same "$tracked" "$base" || cp "$tracked" "$base"
    exit 0
fi

if [ "$mode" = save ]; then
    from=$live; to=$tracked
else
    from=$tracked; to=$live
fi

if same "$to" "$base"; then
    if ! valid "$from"; then
        say "$from is not valid JSON, not copied"
        exit 0
    fi
    cp "$from" "$to" && cp "$from" "$base"
elif same "$from" "$base"; then
    # Only the destination moved. In load mode that is a session's unsaved change,
    # which the session end will save; in save mode it is a pull or an edit that
    # never reached settings.json.
    if [ "$mode" = save ]; then
        if valid "$tracked"; then
            say "$tracked changed but is not applied; run hooks/settings-sync.sh load"
        else
            say "$tracked is not valid JSON; resolve it, then run hooks/settings-sync.sh load"
        fi
    fi
else
    say "$live and $tracked both changed; merge them by hand until they are identical"
fi
exit 0
