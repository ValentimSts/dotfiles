#!/bin/bash

# Runs what the quick settings panel asks for, then has qs-state.py refresh the
# panel. Everything after the action name comes through a shell command line
# built by eww, so each value is checked against the form it must have.

action=${1:-}
arg=${2:-}

is_number() { [[ $1 =~ ^[0-9]+(\.[0-9]+)?$ ]]; }
is_mac() { [[ $1 =~ ^([0-9A-F]{2}:){5}[0-9A-F]{2}$ ]]; }
is_uuid() { [[ $1 =~ ^[0-9a-f]{8}(-[0-9a-f]{4}){3}-[0-9a-f]{12}$ ]]; }

# Started apart from this script, because eww kills a button's command when its
# timeout runs out, and that must not take a lock screen or a terminal with it.
launch() {
  eww close quick-settings popup-closer
  setsid -f "$@" >/dev/null 2>&1
}

refresh() { pkill -USR1 -x qs-state.py; }
trap refresh EXIT

case "$action" in
  volume)
    is_number "$arg" || exit 1
    wpctl set-volume -l 1 @DEFAULT_AUDIO_SINK@ "${arg%.*}%"
    wpctl set-mute @DEFAULT_AUDIO_SINK@ 0
    ;;
  volume-mute)
    wpctl set-mute @DEFAULT_AUDIO_SINK@ toggle
    ;;
  sink)
    [[ $arg =~ ^[0-9]+$ ]] || exit 1
    pactl set-default-sink "$arg"
    ;;
  brightness)
    is_number "$arg" || exit 1
    brightnessctl --quiet set "${arg%.*}%"
    ;;
  keyboard-backlight)
    # One of the backlight's own levels (0 is off), not a percentage.
    is_number "$arg" || exit 1
    brightnessctl --quiet --device='*kbd_backlight' set "${arg%.*}"
    ;;
  expand)
    # expand <section> <section open now>; opening it again closes it.
    if [ "$arg" = "${3:-}" ]; then
      eww update qs-open=""
    else
      eww update qs-open="$arg"
      if [ "$arg" = wifi ]; then
        nmcli device wifi rescan >/dev/null 2>&1
      fi
    fi
    ;;
  wifi-toggle)
    if [ "$(nmcli radio wifi)" = enabled ]; then
      nmcli radio wifi off
    else
      nmcli radio wifi on
    fi
    ;;
  wifi-connect)
    if [ "$arg" = active ]; then
      exit 0
    elif [ -z "$arg" ]; then
      launch kitty -e nmtui-connect
    else
      is_uuid "$arg" || exit 1
      nmcli connection up uuid "$arg" >/dev/null 2>&1
    fi
    ;;
  wifi-settings)
    launch kitty -e nmtui
    ;;
  vpn)
    # vpn up|down <uuid>...: the tile passes every active VPN, or the first one.
    case "$arg" in up | down) ;; *) exit 1 ;; esac
    shift 2
    for uuid in "$@"; do
      is_uuid "$uuid" || exit 1
    done
    # Detached: bringing a VPN up can wait on a password prompt from nm-applet
    # for longer than the click's timeout.
    for uuid in "$@"; do
      setsid -f nmcli connection "$arg" uuid "$uuid" >/dev/null 2>&1
    done
    ;;
  bluetooth-toggle)
    if bluetoothctl show | grep -q 'Powered: yes'; then
      bluetoothctl power off >/dev/null
    else
      bluetoothctl power on >/dev/null
    fi
    ;;
  bluetooth-device)
    is_mac "$arg" || exit 1
    case "${3:-}" in
      connect | disconnect) bluetoothctl "$3" "$arg" >/dev/null ;;
      *) exit 1 ;;
    esac
    ;;
  bluetooth-settings)
    launch blueman-manager
    ;;
  keyboard-next | keyboard-layout)
    # keyboard-next <device>, keyboard-layout <device> <index>. This keyboard
    # alone, like Ctrl+Space: with "all", a mouse's keyboard interface would
    # leave its first layout and misreport itself on reconnect.
    [[ $arg =~ ^[a-z0-9-]+$ ]] || exit 1
    layout=next
    if [ "$action" = keyboard-layout ]; then
      layout=${3:-}
      [[ $layout =~ ^[0-9]+$ ]] || exit 1
    fi
    hyprctl switchxkblayout "$arg" "$layout" >/dev/null
    ;;
  airplane)
    # GNOME's Airplane Mode: every radio off, or every radio back.
    if [ "$(cat /sys/class/rfkill/rfkill*/soft 2>/dev/null | sort -u)" = 1 ]; then
      rfkill unblock all
    else
      rfkill block all
    fi
    ;;
  dark-style)
    # color-scheme reloads eww, which would kill this script mid-way.
    if [[ $(readlink ~/.local/state/color-schemes/active) == */dark ]]; then
      mode=light
    else
      mode=dark
    fi
    setsid -f ~/.local/bin/color-scheme mode "$mode" >/dev/null 2>&1
    ;;
  dnd)
    swaync-client -d >/dev/null
    ;;
  night)
    if systemctl --user is-active --quiet hyprsunset; then
      systemctl --user stop hyprsunset
    else
      systemctl --user start hyprsunset
      # Forced on, since the profile in hyprsunset.conf is neutral by day. The
      # socket takes a moment to appear. 5500 K is that profile's night value.
      for _ in {1..20}; do
        [ "$(hyprctl hyprsunset temperature 5500)" = ok ] && break
        sleep 0.1
      done
    fi
    ;;
  lock)
    launch hyprlock
    ;;
  screenshot)
    # A moment for the panel to leave the screen before hyprshot freezes it.
    launch sh -c 'sleep 0.2; exec hyprshot -m region'
    ;;
  power)
    case "$arg" in
      suspend) launch systemctl suspend ;;
      reboot) launch systemctl reboot ;;
      poweroff) launch systemctl poweroff ;;
      logout) launch hyprctl dispatch 'hl.dsp.exit()' ;;
      *) exit 1 ;;
    esac
    ;;
  *)
    exit 1
    ;;
esac
