#!/usr/bin/env bash
# Power menu for the waybar power button: a rofi list anchored under the
# button (rofi/power.rasi). Labels keep their icon glyph, so match on the word.

choices="Shutdown\n Reboot\n Suspend\n Logout"

chosen=$(printf '%b\n' "$choices" | rofi -dmenu -i -no-custom -p "Power" -theme ~/.config/rofi/power.rasi)

case "$chosen" in
    *Shutdown) systemctl poweroff ;;
    *Reboot)   systemctl reboot ;;
    *Suspend)  systemctl suspend ;;
    *Logout)   hyprctl dispatch exit ;;
esac
