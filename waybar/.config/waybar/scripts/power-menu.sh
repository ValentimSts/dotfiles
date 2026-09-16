#!/bin/bash
# filepath: ~/.config/waybar/scripts/power-menu.sh

choices="Shutdown\n Reboot\n Suspend\n Logout"

chosen=$(echo -e "$choices" | wofi --dmenu --prompt "Power Menu" --width 200 --height 200)

case "$chosen" in
    "Shutdown") systemctl poweroff ;;
    "Reboot") systemctl reboot ;;
    "Suspend") systemctl suspend ;;
    "Logout") hyprctl dispatch exit ;;
esac