#!/usr/bin/env bash
# Install packages from packages/*.txt.
#
# Usage: scripts/install-packages.sh [--profile P] [--pacman] [--aur] [--flatpak] [--dry-run]
#   With no selector flags, all three kinds are installed.
#   Each kind reads packages/<kind>.txt plus packages/<kind>-<profile>.txt.
#   yay is bootstrapped from the AUR if it is missing.

source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

profile="gnome"; do_pacman=0; do_aur=0; do_flatpak=0
while [ $# -gt 0 ]; do
  case "$1" in
    --profile) profile="$2"; shift ;;
    --pacman) do_pacman=1 ;;
    --aur) do_aur=1 ;;
    --flatpak) do_flatpak=1 ;;
    --dry-run) DRY_RUN=1 ;;
    -h|--help) sed -n '2,7p' "$0"; exit 0 ;;
    *) die "unknown argument: $1" ;;
  esac
  shift
done
if [ $((do_pacman + do_aur + do_flatpak)) -eq 0 ]; then
  do_pacman=1; do_aur=1; do_flatpak=1
fi

# list_for <kind>: the profile's packages of that kind, one per line.
list_for() {
  local files
  mapfile -t files < <(package_lists "$1" "$profile")
  read_list "${files[@]}"
}
package_lists pacman "$profile" >/dev/null # reject an unknown profile up front

bootstrap_yay() {
  command -v yay >/dev/null 2>&1 && return 0
  log "yay not found; building it from the AUR"
  need_cmd git
  run sudo pacman -S --needed --noconfirm base-devel git
  local tmp; tmp="$(mktemp -d)"
  run git clone https://aur.archlinux.org/yay-bin.git "$tmp/yay-bin"
  ( cd "$tmp/yay-bin" && run makepkg -si --noconfirm )
  rm -rf "$tmp"
}

if [ "$do_pacman" = "1" ]; then
  need_cmd pacman
  mapfile -t pkgs < <(list_for pacman)
  log "installing ${#pkgs[@]} packages from the official repos"
  run sudo pacman -Syu --needed --noconfirm "${pkgs[@]}"
  ok "pacman packages installed"
fi

if [ "$do_aur" = "1" ]; then
  bootstrap_yay
  mapfile -t pkgs < <(list_for aur)
  log "installing ${#pkgs[@]} packages from the AUR"
  run yay -S --needed --noconfirm "${pkgs[@]}"
  ok "AUR packages installed"
fi

if [ "$do_flatpak" = "1" ]; then
  need_cmd flatpak
  mapfile -t pkgs < <(list_for flatpak)
  if [ ${#pkgs[@]} -gt 0 ]; then
    log "installing ${#pkgs[@]} flatpaks"
    run flatpak remote-add --if-not-exists flathub https://dl.flathub.org/repo/flathub.flatpakrepo
    run flatpak install -y --noninteractive flathub "${pkgs[@]}"
  fi
  ok "flatpaks installed"
fi
