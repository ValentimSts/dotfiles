#!/usr/bin/env bash
# Export GNOME settings (dconf) and the enabled extension list into gnome/.
#
# Usage: scripts/gnome-export.sh
#   Run this after changing GNOME settings you want to keep, then commit.

source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"
need_cmd dconf

out="$DOTFILES_DIR/gnome"
mkdir -p "$out/dconf"

# name=dconf path. Add a line to track another schema.
DCONF_PATHS=(
  "shell=/org/gnome/shell/"
  "interface=/org/gnome/desktop/interface/"
  "wm=/org/gnome/desktop/wm/"
  "peripherals=/org/gnome/desktop/peripherals/"
  "background=/org/gnome/desktop/background/"
  "media-keys=/org/gnome/settings-daemon/plugins/media-keys/"
  "power=/org/gnome/settings-daemon/plugins/power/"
  "mutter=/org/gnome/mutter/"
  "nautilus=/org/gnome/nautilus/"
  "tweaks=/org/gnome/tweaks/"
)

for entry in "${DCONF_PATHS[@]}"; do
  name="${entry%%=*}"; path="${entry#*=}"
  dconf dump "$path" > "$out/dconf/$name.ini"
  log "dumped $path -> gnome/dconf/$name.ini ($(wc -l < "$out/dconf/$name.ini") lines)"
done

if command -v gnome-extensions >/dev/null 2>&1; then
  gnome-extensions list --enabled | sort > "$out/extensions.txt"
  log "wrote $(wc -l < "$out/extensions.txt") extension UUIDs"
fi

# Keep the export reproducible: strip the noisy app-picker layout, which
# GNOME rewrites constantly and which is not worth tracking.
sed -i '/^app-picker-layout=/d' "$out/dconf/shell.ini"

ok "GNOME export complete"
