#!/usr/bin/env bash
# Restore GNOME settings from gnome/ and install missing shell extensions.
#
# Usage: scripts/gnome-import.sh [--dry-run] [--skip-extensions]
#   Extensions from extensions.gnome.org are installed with gnome-extensions-cli
#   (pipx) when it is available; otherwise the missing UUIDs are listed.

source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

skip_ext=0
while [ $# -gt 0 ]; do
  case "$1" in
    --dry-run) DRY_RUN=1 ;;
    --skip-extensions) skip_ext=1 ;;
    -h|--help) sed -n '2,6p' "$0"; exit 0 ;;
    *) die "unknown argument: $1" ;;
  esac
  shift
done

need_cmd dconf
src="$DOTFILES_DIR/gnome"

# Path mapping must match gnome-export.sh.
declare -A PATHS=(
  [shell]=/org/gnome/shell/
  [interface]=/org/gnome/desktop/interface/
  [wm]=/org/gnome/desktop/wm/
  [peripherals]=/org/gnome/desktop/peripherals/
  [background]=/org/gnome/desktop/background/
  [media-keys]=/org/gnome/settings-daemon/plugins/media-keys/
  [power]=/org/gnome/settings-daemon/plugins/power/
  [mutter]=/org/gnome/mutter/
  [nautilus]=/org/gnome/nautilus/
  [tweaks]=/org/gnome/tweaks/
)

for f in "$src"/dconf/*.ini; do
  name="$(basename "$f" .ini)"
  path="${PATHS[$name]:-}"
  [ -n "$path" ] || { warn "no dconf path known for $name.ini; skipping"; continue; }
  [ -s "$f" ] || continue
  log "loading $f -> $path"
  if [ "$DRY_RUN" = "1" ]; then
    printf '%s[dry]%s dconf load %s < %s\n' "$C_WARN" "$C_RESET" "$path" "$f"
  else
    dconf load "$path" < "$f"
  fi
done

if [ "$skip_ext" = "0" ] && [ -f "$src/extensions.txt" ]; then
  mapfile -t wanted < <(read_list "$src/extensions.txt")
  missing=()
  for uuid in "${wanted[@]}"; do
    gnome-extensions info "$uuid" >/dev/null 2>&1 || missing+=("$uuid")
  done
  if [ ${#missing[@]} -gt 0 ]; then
    if command -v gext >/dev/null 2>&1; then
      log "installing ${#missing[@]} extensions with gnome-extensions-cli"
      run gext install "${missing[@]}"
    else
      warn "missing extensions (install via Extension Manager or 'pipx install gnome-extensions-cli'):"
      printf '  %s\n' "${missing[@]}"
    fi
  fi
  for uuid in "${wanted[@]}"; do
    gnome-extensions info "$uuid" >/dev/null 2>&1 && run gnome-extensions enable "$uuid"
  done
fi

ok "GNOME import complete (log out and back in for shell changes to apply)"
