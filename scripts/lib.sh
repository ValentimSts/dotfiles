#!/usr/bin/env bash
# Shared helpers for the dotfiles scripts. Source this file; do not run it.

set -o errexit -o nounset -o pipefail

DOTFILES_DIR="${DOTFILES_DIR:-$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)}"
DRY_RUN="${DRY_RUN:-0}"
BACKUP_DIR="${BACKUP_DIR:-$HOME/.dotfiles-backup/$(date +%Y%m%d-%H%M%S)}"

# Stow package sets. "common" applies to every profile.
PKGS_COMMON=(bash starship git gh kitty nvim neofetch vscode xdg color-schemes wallpapers)
PKGS_GNOME=()
PKGS_HYPRLAND=(hypr waybar rofi eww waypaper libinput-gestures systemd)

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

# read_list <file>: prints non-empty, non-comment lines.
read_list() { grep -vE '^\s*(#|$)' "$1" || true; }
