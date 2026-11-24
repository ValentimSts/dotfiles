#!/usr/bin/env bash
# Compare packages/*.txt with what is installed on this machine.
#
# Usage: scripts/packages-diff.sh
#   Prints the packages that are installed by hand but in no list, and the
#   listed ones that are not installed. The lists are curated by hand, split by
#   profile, so nothing is written: add or remove the lines yourself.
#   Exits 1 when either set is non-empty.

source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

case "${1:-}" in
  -h|--help) sed -n '2,8p' "$0"; exit 0 ;;
  "") ;;
  *) die "unknown argument: $1" ;;
esac

# listed <kind>: every profile's packages of that kind, sorted.
listed() {
  local files
  mapfile -t files < <(package_lists "$1" all)
  read_list "${files[@]}" | sort -u
}

# report <title> <lines>: print a titled, indented block; returns 1 if it printed.
report() {
  [ -n "$2" ] || return 0
  warn "$1"
  printf '%s\n' "$2" | sed 's/^/  /'
  return 1
}

drift=0
need_cmd pacman

# Installed by hand (not as a dependency), from the repos and from the AUR.
report "installed but in no pacman list:" \
  "$(comm -23 <(pacman -Qqen | sort) <(listed pacman))" || drift=1
report "installed but in no AUR list:" \
  "$(comm -23 <(pacman -Qqem | sort) <(listed aur))" || drift=1
# A listed package counts as installed whatever pulled it in.
report "listed but not installed:" \
  "$(comm -23 <(cat <(listed pacman) <(listed aur) | sort -u) <(pacman -Qq | sort))" || drift=1

if command -v flatpak >/dev/null 2>&1; then
  installed="$(flatpak list --app --columns=application | sort)"
  report "flatpak installed but not listed:" "$(comm -23 <(printf '%s\n' "$installed") <(listed flatpak))" || drift=1
  report "flatpak listed but not installed:" "$(comm -13 <(printf '%s\n' "$installed") <(listed flatpak))" || drift=1
fi

[ "$drift" = "0" ] && ok "package lists match this machine"
exit "$drift"
