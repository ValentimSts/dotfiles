#!/usr/bin/env bash
# Click on a day in the eww calendar: slides that day's events open, or closed
# again when it is already the selected day. A day from a neighbouring month
# also moves the grid to that month.
# Usage: calendar-select.sh YYYY-MM-DD day-month-offset current-month-offset

dir=$(dirname "$(readlink -f "$0")")

if [ "$(eww get cal-selected)" = "$1" ]; then
  exec eww update cal-selected=""
fi

# The limit stays below the button's :timeout in eww.yuck.
if ! agenda=$(timeout 5 "$dir/calendar-agenda.py" "$1"); then
  agenda="{\"title\": \"$(date -d "$1" '+%A, %-d %B')\", \"events\": [], \"notice\": \"Calendar unavailable\"}"
fi

if [ "$2" != "$3" ]; then
  "$dir/calendar-goto.sh" "$2" "$3"
fi

exec eww update cal-agenda="$agenda" cal-selected="$1"
