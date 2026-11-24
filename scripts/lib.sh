#!/usr/bin/env bash
# Shared helpers for the dotfiles scripts. Source this file; do not run it.

set -o errexit -o nounset -o pipefail

DOTFILES_DIR="${DOTFILES_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
DRY_RUN="${DRY_RUN:-0}"
BACKUP_DIR="${BACKUP_DIR:-$HOME/.dotfiles-backup/$(date +%Y%m%d-%H%M%S)}"

# Stow package sets. "common" applies to every profile.
PKGS_COMMON=(bash starship git gh kitty nvim neofetch vscode xdg color-schemes wallpapers claude)
PKGS_GNOME=()
PKGS_HYPRLAND=(hypr waybar rofi eww icons systemd)

# Packages Stow must link file by file, never as one directory symlink, because
# other programs write into the same tree and what they write would otherwise
# land in the repo: icons lives in ~/.local/share/icons/hicolor, where apps
# install their own icons, and claude lives in ~/.claude, where Claude Code
# keeps its settings, session history and credentials.
# shellcheck disable=SC2034  # read by stow.sh
PKGS_NO_FOLDING=(icons claude)

# dconf schemas tracked under gnome/dconf/, as name=path: gnome-export.sh dumps
# each path to <name>.ini and gnome-import.sh loads it back. Add a line to
# track another schema.
# shellcheck disable=SC2034  # read by the scripts that source this file
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

if [ -t 1 ]; then
  C_RESET=$'\033[0m'; C_INFO=$'\033[1;34m'; C_OK=$'\033[1;32m'
  C_WARN=$'\033[1;33m'; C_ERR=$'\033[1;31m'
else
  C_RESET=""; C_INFO=""; C_OK=""; C_WARN=""; C_ERR=""
fi

log()  { printf '%s[..]%s %s\n' "$C_INFO" "$C_RESET" "$*"; }
ok()   { printf '%s[ok]%s %s\n' "$C_OK" "$C_RESET" "$*"; }
warn() { printf '%s[!!]%s %s\n' "$C_WARN" "$C_RESET" "$*" >&2; }
die()  { printf '%s[xx]%s %s\n' "$C_ERR" "$C_RESET" "$*" >&2; exit 1; }

# run <cmd...>: execute, or print when DRY_RUN=1.
run() {
  if [ "$DRY_RUN" = "1" ]; then
    printf '%s[dry]%s %s\n' "$C_WARN" "$C_RESET" "$*"
  else
    "$@"
  fi
}

need_cmd() { command -v "$1" >/dev/null 2>&1 || die "missing required command: $1"; }

confirm() { # confirm <prompt>; returns 0 on yes. Auto-yes when ASSUME_YES=1.
  if [ "${ASSUME_YES:-0}" = "1" ]; then return 0; fi
  local reply
  read -r -p "$1 [y/N] " reply
  [[ "$reply" =~ ^[Yy]$ ]]
}

# packages_for_profile <profile>: prints package names, one per line.
packages_for_profile() {
  case "$1" in
    common)   printf '%s\n' "${PKGS_COMMON[@]}" ;;
    gnome)    printf '%s\n' "${PKGS_COMMON[@]}" "${PKGS_GNOME[@]}" ;;
    hyprland) printf '%s\n' "${PKGS_COMMON[@]}" "${PKGS_HYPRLAND[@]}" ;;
    all)      printf '%s\n' "${PKGS_COMMON[@]}" "${PKGS_GNOME[@]}" "${PKGS_HYPRLAND[@]}" ;;
    *) die "unknown profile: $1 (expected common, gnome, hyprland, all)" ;;
  esac
}

# read_list <file>...: prints non-empty, non-comment lines; a missing file is skipped.
read_list() {
  local f
  for f in "$@"; do
    [ -f "$f" ] || continue
    grep -vE '^\s*(#|$)' "$f" || true
  done
}

# package_lists <kind> <profile>: the list files for a kind (pacman, aur,
# flatpak): packages/<kind>.txt for every profile, plus
# packages/<kind>-<profile>.txt. "all" takes every profile's file.
package_lists() {
  local kind="$1" profile="$2" dir="$DOTFILES_DIR/packages"
  printf '%s\n' "$dir/$kind.txt"
  case "$profile" in
    common) ;;
    all) printf '%s\n' "$dir/$kind-gnome.txt" "$dir/$kind-hyprland.txt" ;;
    gnome|hyprland) printf '%s\n' "$dir/$kind-$profile.txt" ;;
    *) die "unknown profile: $profile (expected common, gnome, hyprland, all)" ;;
  esac
}
