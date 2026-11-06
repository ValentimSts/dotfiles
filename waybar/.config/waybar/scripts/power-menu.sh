#!/usr/bin/env bash
# Power menu for the waybar power button: toggles the eww power-menu window
# (eww/eww.yuck) together with popup-closer, the transparent full-screen
# window that dismisses the menu on a click outside it. The eww daemon runs
# as the eww user service.

exec eww open-many --toggle popup-closer power-menu
