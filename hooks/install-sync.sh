#!/bin/bash
# One-time setup of settings sync on this machine: install-sync.sh <machine>
# <machine> is the middle of settings.<machine>.json.
set -eu
cd ~/.claude

machine=${1:?usage: install-sync.sh <machine>}
if [ ! -f "settings.$machine.json" ]; then
    echo "settings.$machine.json does not exist" >&2
    exit 1
fi

printf '%s\n' "$machine" > .machine

git config core.hooksPath hooks/git
git config merge.autoStash true
git config rebase.autoStash true
chmod +x hooks/settings-sync.sh hooks/git/post-merge hooks/git/post-rewrite

# Claude Code saves settings.json by replacing the file, which turns a symlink into a
# stale copy. The two files are kept in step by copying instead.
if [ -L settings.json ]; then
    rm settings.json
fi
if [ ! -e settings.json ]; then
    cp "settings.$machine.json" settings.json
fi

hooks/settings-sync.sh load
echo "Settings sync installed for $machine."
