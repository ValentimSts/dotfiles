#!/usr/bin/env bash
# Calendar for the waybar clock: toggles the eww calendar window (eww/eww.yuck)
# together with popup-closer, which dismisses it on a click outside. Always
# opens on the current month.

month=$(~/.config/eww/scripts/calendar-month.py)
eww update cal="$month" cal-page-0="$month" cal-page=0 cal-transition=none cal-selected=""
# --no-daemonize: never start a second eww daemon if the service is slow.
exec eww --no-daemonize open-many --toggle popup-closer calendar
