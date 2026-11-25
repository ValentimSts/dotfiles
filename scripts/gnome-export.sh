#!/usr/bin/env bash
# Export GNOME settings (dconf) and the enabled extension list into gnome/.
#
# Usage: scripts/gnome-export.sh
#   Run this after changing GNOME settings you want to keep, then commit.

source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
need_cmd dconf

out="$DOTFILES_DIR/gnome"
mkdir -p "$out/dconf"

# DCONF_PATHS (name=dconf path) comes from lib.sh.
for entry in "${DCONF_PATHS[@]}"; do
  name="${entry%%=*}"; path="${entry#*=}"
  dconf dump "$path" > "$out/dconf/$name.ini"
  log "dumped $path -> gnome/dconf/$name.ini ($(wc -l < "$out/dconf/$name.ini") lines)"
done

if command -v gnome-extensions >/dev/null 2>&1; then
  gnome-extensions list --enabled | sort > "$out/extensions.txt"
  log "wrote $(wc -l < "$out/extensions.txt") extension UUIDs"
fi

# Keep the export reproducible: strip what is rewritten constantly and is not
# worth tracking: the app-picker layout, and the colour counts the Open Bar
# extension records each time it samples the wallpaper.
sed -i -E '/^(app-picker-layout|count[0-9]+)=/d' "$out/dconf/shell.ini"

ok "GNOME export complete"
