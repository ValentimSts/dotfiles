"""Readings shared by the eww scripts: the quick settings panel (qs-state.py),
the volume and brightness OSD (level-osd.py), the keyboard backlight OSD
(keyboard-backlight-osd.py), the keyboard layout OSD (keyboard-osd.py) and the
low battery warning (battery-warning.py). Icons are GNOME's symbolic icon names.
"""

import functools
import glob
import json
import os
import re
import subprocess
import xml.etree.ElementTree as ElementTree

XKB_REGISTRY = "/usr/share/X11/xkb/rules/evdev.xml"
# Hyprland keeps a layout per keyboard, and its "main" one can be a mouse's
# keyboard interface, so the panel follows the keyboard actually typed on.
TYPING_KEYBOARD = "at-translated-set-2-keyboard"
# The kernel's name for a keyboard backlight ends this way whatever the laptop:
# tpacpi::kbd_backlight, dell::kbd_backlight, ...
KEYBOARD_BACKLIGHT = "/sys/class/leds/*kbd_backlight"
KEYBOARD_BACKLIGHT_ICON = "keyboard-brightness-symbolic"


def run(*command):
    """Stdout of a command, or "" if it failed: a missing reading is not fatal."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=3)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return result.stdout if result.returncode == 0 else ""


def read_volume(target):
    """(percent, muted) of a wpctl target such as @DEFAULT_AUDIO_SINK@."""
    # "Volume: 0.84" or "Volume: 0.84 [MUTED]"
    output = run("wpctl", "get-volume", target)
    match = re.search(r"Volume: ([0-9.]+)", output)
    percent = round(float(match.group(1)) * 100) if match else 0
    return percent, "[MUTED]" in output


def volume_icon(percent, muted):
    if muted or percent == 0:
        return "audio-volume-muted-symbolic"
    if percent < 34:
        return "audio-volume-low-symbolic"
    if percent < 67:
        return "audio-volume-medium-symbolic"
    return "audio-volume-high-symbolic"


def read_brightness():
    # device,class,current,percent%,max
    fields = run("brightnessctl", "-m").strip().split(",")
    return int(fields[3].rstrip("%")) if len(fields) > 3 else 0


def brightness_icon(percent):
    """A sun filled a quarter, half, three quarters or whole (icons package)."""
    level = next((step for step in (25, 50, 75) if percent <= step), 100)
    return f"display-brightness-{level}-symbolic"


def keyboard_backlight_path():
    """The keyboard backlight's sysfs directory, or None on a keyboard without one."""
    paths = glob.glob(KEYBOARD_BACKLIGHT)
    return paths[0] if paths else None


def read_keyboard_backlight():
    """(level, highest level) of the keyboard backlight, or None without one.

    Levels are the kernel's own steps, from 0 for off: a ThinkPad has 0 to 2.
    """
    path = keyboard_backlight_path()
    if path is None:
        return None
    try:
        with open(os.path.join(path, "brightness")) as handle:
            level = int(handle.read())
        with open(os.path.join(path, "max_brightness")) as handle:
            return level, int(handle.read())
    except (OSError, ValueError):
        return None


def read_battery():
    """(percent, status) of the first battery, or None without a readable one.

    Status is the kernel's: Charging, Discharging, Full or Not charging.
    """
    paths = glob.glob("/sys/class/power_supply/BAT*")
    if not paths:
        return None
    try:
        with open(os.path.join(paths[0], "capacity")) as handle:
            percent = int(handle.read())
        with open(os.path.join(paths[0], "status")) as handle:
            return percent, handle.read().strip()
    except (OSError, ValueError):
        return None


def battery_icon(percent, status):
    # The nearest tenth, as the bar's battery icon (waybar/modules/battery.jsonc).
    level = min((percent + 5) // 10 * 10, 100)
    if status == "Full":
        return "battery-level-100-charged-symbolic"
    if status == "Charging":
        return f"battery-level-{level}-charging-symbolic"
    if status == "Not charging":
        return f"battery-level-{level}-plugged-in-symbolic"
    return f"battery-level-{level}-symbolic"


def read_keyboards():
    """Hyprland's keyboards, or [] when Hyprland cannot be asked."""
    try:
        return json.loads(run("hyprctl", "devices", "-j"))["keyboards"]
    except (json.JSONDecodeError, KeyError):
        return []


def typing_keyboard(keyboards):
    return next(
        (k for k in keyboards if k["name"] == TYPING_KEYBOARD),
        next((k for k in keyboards if k["main"]), None),
    )


@functools.cache
def read_layout_labels():
    """Map xkb layout ids to (language code, name): us -> (EN, English (US))."""
    labels = {}
    for item in ElementTree.parse(XKB_REGISTRY).findall("./layoutList/layout/configItem"):
        labels[item.findtext("name")] = (
            item.findtext("shortDescription", item.findtext("name")).upper(),
            item.findtext("description"),
        )
    return labels


def layout_options(keyboard):
    """Every layout configured on a keyboard, in order, the active one marked."""
    options = []
    for index, layout in enumerate(keyboard["layout"].split(",")):
        layout = layout.strip()
        code, name = read_layout_labels().get(layout, (layout.upper(), layout))
        options.append(
            {
                "index": index,
                "code": code,
                "name": name,
                "active": index == keyboard["active_layout_index"],
            }
        )
    return options
