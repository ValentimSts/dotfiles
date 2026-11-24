#!/usr/bin/python3
"""Warn in the middle of the screen when the battery runs low.

Usage: battery-warning.py              watch the battery (the user service)
       battery-warning.py --show 20|5  show that warning once, to look at it

On battery power the battery-warning eww window opens when the charge falls to
20%, and again at 5%. Each level warns once per discharge: plugging in the
charger closes the window and arms both again. The 20% warning goes away by
itself after a while; the 5% one stays until it is clicked or the charger is
in. Runs as the battery-warning user service.
"""

import json
import sys
import time

from osd import eww
from readings import battery_icon, read_battery

WINDOW = "battery-warning"
# Charge levels to warn at, highest first, and how long each warning stays up
# (None: until dismissed).
LEVELS = {20: 15, 5: None}
POLL_SECONDS = 30
# While a warning is up the charger is checked this often, to close it promptly.
SHOWING_POLL_SECONDS = 2


def level_reached(percent):
    """The lowest warning level the charge is at or below, or None above all."""
    return min((level for level in LEVELS if percent <= level), default=None)


def show(level, percent):
    critical = level == min(LEVELS)
    state = {
        "icon": battery_icon(percent, "Discharging"),
        "title": "Battery Critically Low" if critical else "Battery Low",
        "text": f"{percent}% remaining. " + ("Plug in the charger now." if critical else "Plug in the charger soon."),
        "critical": critical,
    }
    eww("update", f"{WINDOW}={json.dumps(state)}")
    eww("open", WINDOW)


def watch():
    warned = None  # the lowest level already warned about during this discharge
    close_at = None  # when the warning on screen goes away; None: it stays
    showing = False
    while True:
        battery = read_battery()
        discharging = battery is not None and battery[1] == "Discharging"
        if not discharging:
            warned = None
            if showing:
                eww("close", WINDOW)
                showing = False
        else:
            level = level_reached(battery[0])
            if level is not None and (warned is None or level < warned):
                show(level, battery[0])
                warned, showing = level, True
                seconds = LEVELS[level]
                close_at = None if seconds is None else time.monotonic() + seconds
            elif showing and close_at is not None and time.monotonic() >= close_at:
                eww("close", WINDOW)
                showing = False
        time.sleep(SHOWING_POLL_SECONDS if showing else POLL_SECONDS)


def main(args):
    if not args:
        watch()
    if len(args) == 2 and args[0] == "--show" and args[1].isdigit() and int(args[1]) in LEVELS:
        show(int(args[1]), int(args[1]))
        return 0
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
