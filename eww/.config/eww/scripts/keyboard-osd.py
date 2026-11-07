#!/usr/bin/python3
"""Show the keyboard layouts on screen for a moment when the active one changes.

Lists every configured layout with the active one highlighted, like GNOME's
input source switcher. Follows Hyprland's event socket and drives the keyboard-osd eww window. Runs as
the keyboard-osd user service.
"""

import json
import os
import select
import socket
import subprocess
import sys
import time
import xml.etree.ElementTree as ElementTree

WINDOW = "keyboard-osd"
SHOW_SECONDS = 1.2
EVENT_PREFIX = "activelayout>>"
XKB_REGISTRY = "/usr/share/X11/xkb/rules/evdev.xml"


def eww(*args):
    subprocess.run(["eww", *args], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def read_keyboards():
    output = subprocess.run(
        ["hyprctl", "devices", "-j"], capture_output=True, text=True
    ).stdout
    return json.loads(output)["keyboards"]


def read_layout_labels():
    """Map xkb layout ids to (language code, name): us -> (EN, English (US))."""
    labels = {}
    for item in ElementTree.parse(XKB_REGISTRY).findall("./layoutList/layout/configItem"):
        labels[item.findtext("name")] = (
            item.findtext("shortDescription", item.findtext("name")).upper(),
            item.findtext("description"),
        )
    return labels


def layout_options(keyboard, labels):
    options = []
    for index, layout in enumerate(keyboard["layout"].split(",")):
        layout = layout.strip()
        code, name = labels.get(layout, (layout.upper(), layout))
        options.append(
            {"code": code, "name": name, "active": index == keyboard["active_layout_index"]}
        )
    return options


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
    layouts = {k["name"]: k["active_keymap"] for k in read_keyboards()}
    labels = read_layout_labels()
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
            keyboard = next((k for k in read_keyboards() if k["name"] == device), None)
            if keyboard is None:
                continue  # it detached again before we could read it
            options = json.dumps(layout_options(keyboard, labels))
            if options != shown:
                eww("update", f"osd-options={options}")
                shown = options
            # Opening a window that is already open would make it flash.
            if hide_at is None:
                eww("open", WINDOW)
            hide_at = time.monotonic() + SHOW_SECONDS


if __name__ == "__main__":
    sys.exit(main())
