#!/bin/bash

# Toggles the quick settings panel: an eww window, plus the transparent one
# behind it that closes it on a click elsewhere. The state is read first, so the
# panel opens filled in rather than waiting for its listener's first line.

state=$(~/.config/eww/scripts/qs-state.py --once)
eww update qs="$state" qs-open=""
exec eww open-many --toggle popup-closer quick-settings
