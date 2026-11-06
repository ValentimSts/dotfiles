#!/usr/bin/python3
"""Show the keyboard layout on screen for a moment whenever it changes.

Follows Hyprland's event socket and drives the keyboard-osd eww window. Runs as
the keyboard-osd user service.
"""

import json
import os
import select
import socket
import subprocess
import sys
import time

WINDOW = "keyboard-osd"
SHOW_SECONDS = 1.2
EVENT_PREFIX = "activelayout>>"
KEYBOARD_ICON = "\U000f030c"


def eww(*args):
    subprocess.run(["eww", *args], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def device_layouts():
    output = subprocess.run(
        ["hyprctl", "devices", "-j"], capture_output=True, text=True
    ).stdout
    return {k["name"]: k["active_keymap"] for k in json.loads(output)["keyboards"]}


def layout_events(lines):
    # activelayout>>keyboard-name,Layout Name
    for line in lines:
        if line.startswith(EVENT_PREFIX) and "," in line:
            yield line[len(EVENT_PREFIX):].split(",", 1)


def main():
    path = os.path.join(
        os.environ["XDG_RUNTIME_DIR"],
        "hypr",
        os.environ["HYPRLAND_INSTANCE_SIGNATURE"],
        ".socket2.sock",
    )
    events = socket.socket(socket.AF_UNIX)
    events.connect(path)

    # Each keyboard has its own layout, and a keyboard (or a Bluetooth mouse's
    # keyboard interface) announces its layout when it attaches. So a switch is
    # a device we already know changing layout, not any event that names a
    # layout different from the last one.
    layouts = device_layouts()
    shown = None
    hide_at = None
    pending = ""

    while True:
        timeout = None if hide_at is None else max(0, hide_at - time.monotonic())
        ready, _, _ = select.select([events], [], [], timeout)

        if not ready:
            eww("close", WINDOW)
            shown = None
            hide_at = None
            continue

        data = events.recv(4096)
        if not data:
            return 1  # Hyprland went away; the service restarts this

        lines = (pending + data.decode(errors="replace")).split("\n")
        pending = lines.pop()

        for device, layout in layout_events(lines):
            previous = layouts.get(device)
            layouts[device] = layout
            if previous is None or previous == layout:
                continue
            if layout != shown:
                eww("update", f"osd-icon={KEYBOARD_ICON}", f"osd-layout={layout}")
                shown = layout
            # Opening a window that is already open would make it flash.
            if hide_at is None:
                eww("open", WINDOW)
            hide_at = time.monotonic() + SHOW_SECONDS


if __name__ == "__main__":
    sys.exit(main())
