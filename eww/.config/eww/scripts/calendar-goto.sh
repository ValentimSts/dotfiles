#!/usr/bin/env bash
# Move the eww calendar to another month. The grid is a two-page stack: the new
# month loads into the hidden page, then the stack slides over to it, in the
# direction of travel. Going to the month already shown only closes the day view.
# Usage: calendar-goto.sh month-offset current-month-offset

dir=$(dirname "$(readlink -f "$0")")
target=$1
current=$2

if [ "$target" = "$current" ]; then
  exec eww update cal-selected=""
fi

if [ "$target" -gt "$current" ]; then
  transition=slideleft
else
  transition=slideright
fi

month=$("$dir/calendar-month.py" "$target")
next_page=$((1 - $(eww get cal-page)))

eww update "cal-page-$next_page=$month" cal="$month" \
  cal-transition="$transition" cal-selected=""
exec eww update cal-page="$next_page"
