#!/usr/bin/env bash
# Enable system and user services for the chosen profile.
#
# Usage: scripts/enable-services.sh [--profile gnome|hyprland] [--dry-run]

source "$(dirname "${BASH_SOURCE[0]}")/lib.sh"

profile="gnome"
while [ $# -gt 0 ]; do
  case "$1" in
    --profile) profile="$2"; shift ;;
    --dry-run) DRY_RUN=1 ;;
    -h|--help) sed -n '2,4p' "$0"; exit 0 ;;
    *) die "unknown argument: $1" ;;
  esac
  shift
done

SYSTEM_COMMON=(NetworkManager bluetooth tlp)
SYSTEM_GNOME=(gdm)
USER_COMMON=(pipewire pipewire-pulse wireplumber)

enable_system() { for s in "$@"; do run sudo systemctl enable --now "$s"; done; }
enable_user()   { for s in "$@"; do run systemctl --user enable --now "$s"; done; }

enable_system "${SYSTEM_COMMON[@]}"
enable_user "${USER_COMMON[@]}"

case "$profile" in
  gnome)
    enable_system "${SYSTEM_GNOME[@]}"
    ;;
  hyprland)
    # Hyprland starts waybar and hyprland-session.target itself (see hyprland.conf).
    run systemctl --user daemon-reload
    if command -v libinput-gestures-setup >/dev/null 2>&1; then
      run libinput-gestures-setup autostart
    fi
    ;;
  *) die "unknown profile: $profile" ;;
esac

ok "services enabled for profile: $profile"
