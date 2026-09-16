#!/usr/bin/env bash
# Create ~/.config/shell/secrets.sh from the tracked example if it is missing.
#
# Usage: scripts/secrets-init.sh

source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

target="$HOME/.config/shell/secrets.sh"
example="$DOTFILES_DIR/bash/.config/shell/secrets.sh.example"

if [ -f "$target" ]; then
  ok "secrets file already exists: $target"
  exit 0
fi

run mkdir -p "$(dirname "$target")"
run cp "$example" "$target"
run chmod 600 "$target"
ok "created $target; edit it to add real values (it is never committed)"
