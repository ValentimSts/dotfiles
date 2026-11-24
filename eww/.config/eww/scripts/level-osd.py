#!/usr/bin/python3
"""Change the volume or brightness, then show the level in the middle of the
screen for a moment, like GNOME's OSD.

Usage: level-osd.py volume up|down|mute
       level-osd.py brightness up|down
       level-osd.py mic mute

Bound to the laptop's volume, brightness and mic-mute keys in hyprland.lua.
The change comes first and does not depend on eww, so the keys still work when
the window cannot be shown.

Each press restarts the timer: a key held down keeps the window up, and it
closes a moment after the last press (osd.py).
"""

import os
import subprocess
import sys
import time

from osd import LEVEL_SECONDS, hide_level, show_level
from readings import brightness_icon, read_brightness, read_volume, volume_icon

STEP = "5%"
SINK = "@DEFAULT_AUDIO_SINK@"
SOURCE = "@DEFAULT_AUDIO_SOURCE@"

USAGE = __doc__.split("\n\n")[1]


def call(*command):
    subprocess.run(command, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def change_volume(how):
    if how == "mute":
        call("wpctl", "set-mute", SINK, "toggle")
        return
    # Changing the volume unmutes, as GNOME does. -l 1 caps it at 100%.
    call("wpctl", "set-volume", "-l", "1", SINK, STEP + ("+" if how == "up" else "-"))
    call("wpctl", "set-mute", SINK, "0")


def change_brightness(how):
    # -n keeps the backlight from going fully dark on the way down.
    call("brightnessctl", "--quiet", "-n", "set", STEP + ("+" if how == "up" else "-"))


def change(kind, how):
    """Apply the change and return what the window should show."""
    if kind == "volume":
        change_volume(how)
        percent, muted = read_volume(SINK)
        return {"icon": volume_icon(percent, muted), "value": 0 if muted else percent, "bar": True}
    if kind == "brightness":
        change_brightness(how)
        percent = read_brightness()
        return {"icon": brightness_icon(percent), "value": percent, "bar": True}
    call("wpctl", "set-mute", SOURCE, "toggle")
    _, muted = read_volume(SOURCE)
    icon = "microphone-sensitivity-muted-symbolic" if muted else "microphone-sensitivity-high-symbolic"
    return {"icon": icon, "value": 0, "bar": False}


def show(level):
    token = show_level(level)
    # Close it later from a detached child, unless a later press took over.
    if os.fork() != 0:
        return
    os.setsid()
    time.sleep(LEVEL_SECONDS)
    hide_level(token)
    os._exit(0)


def main(args):
    allowed = {"volume": ("up", "down", "mute"), "brightness": ("up", "down"), "mic": ("mute",)}
    if len(args) != 2 or args[1] not in allowed.get(args[0], ()):
        print(USAGE, file=sys.stderr)
        return 2
    show(change(*args))
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
