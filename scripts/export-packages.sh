#!/usr/bin/env bash
# Refresh packages/*.txt from what is currently installed on this machine.
#
# Usage: scripts/export-packages.sh

source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

pkg_dir="$DOTFILES_DIR/packages"
mkdir -p "$pkg_dir"

pacman -Qqen | sort > "$pkg_dir/pacman.txt"
pacman -Qqem | sort > "$pkg_dir/aur.txt"
if command -v flatpak >/dev/null 2>&1; then
  flatpak list --app --columns=application | sort > "$pkg_dir/flatpak.txt"
fi
ok "package lists refreshed:"
wc -l "$pkg_dir"/*.txt
