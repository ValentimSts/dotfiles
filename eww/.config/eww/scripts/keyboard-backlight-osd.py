#!/usr/bin/python3
"""Show the keyboard backlight's level in the middle of the screen for a moment
when the laptop's own key changes it (Fn+Space on a ThinkPad).

Usage: keyboard-backlight-osd.py         watch the backlight (the user service)
       keyboard-backlight-osd.py --show  show the level once, to look at it

The firmware handles that key by itself and Hyprland never sees it, so there is
nothing to bind. The kernel reports the change instead, through the backlight's
brightness_hw_changed file, which this waits on. A level set by software, such
as the quick settings slider, is not reported there and shows nothing. Runs as
the keyboard-backlight-osd user service and drives the level-osd eww window.
"""

import os
import select
import sys
import time

from osd import LEVEL_SECONDS, hide_level, show_level
from readings import KEYBOARD_BACKLIGHT_ICON, keyboard_backlight_path, read_keyboard_backlight


def show():
    """Show the level now and return the window's token, or None unreadable."""
    backlight = read_keyboard_backlight()
    if backlight is None or backlight[1] < 1:
        return None
    level, highest = backlight
    return show_level({"icon": KEYBOARD_BACKLIGHT_ICON, "value": round(level * 100 / highest), "bar": True})


def acknowledge(changed):
    """Read the file, which is what makes the next change wake poll again."""
    changed.seek(0)
    try:
        changed.read()
    except OSError:
        pass  # "No data available" until the key is first pressed


def watch(path):
    token = None
    hide_at = None
    with open(os.path.join(path, "brightness_hw_changed")) as changed:
        acknowledge(changed)
        # sysfs announces a change as POLLPRI, alongside POLLERR.
        poller = select.poll()
        poller.register(changed, select.POLLPRI | select.POLLERR)
        while True:
            timeout = None if hide_at is None else max(0, hide_at - time.monotonic()) * 1000
            if poller.poll(timeout):
                acknowledge(changed)
                token = show() or token
                hide_at = time.monotonic() + LEVEL_SECONDS
            elif token is not None:
                hide_level(token)
                token = None
                hide_at = None
            else:
                hide_at = None


def main(args):
    path = keyboard_backlight_path()
    if path is None:
        # Not a failure, so the service does not keep restarting.
        print("no keyboard backlight on this machine", file=sys.stderr)
        return 0
    if not args:
        try:
            watch(path)
        except FileNotFoundError:
            print("this keyboard backlight does not report its own changes", file=sys.stderr)
            return 0
    if args == ["--show"]:
        token = show()
        if token is not None:
            time.sleep(LEVEL_SECONDS)
            hide_level(token)
        return 0
    print(__doc__.split("\n\n")[1], file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
