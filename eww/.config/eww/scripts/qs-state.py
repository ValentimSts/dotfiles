#!/usr/bin/python3
"""Print the quick settings panel's state as JSON.

qs-state.py          one line now, then one on every change; eww runs this
                     only while the panel is open. SIGUSR1 asks for a refresh
                     right away, which qs-action.sh sends after each action.
qs-state.py --once   one line, then exit.

SSIDs and Bluetooth names are other people's text. They are only ever displayed:
the commands the panel runs carry UUIDs, MAC addresses and numeric ids instead.
"""

import glob
import json
import os
import re
import select
import signal
import subprocess
import sys

POLL_SECONDS = 1
MAX_NETWORKS = 6
WIFI_TYPE = "802-11-wireless"
# Hyprland keeps a layout per keyboard, and its "main" one can be a mouse's
# keyboard interface, so the panel follows the keyboard actually typed on.
TYPING_KEYBOARD = "at-translated-set-2-keyboard"

ICONS = {
    "battery": "\U000f0079",
    "bluetooth": "\U000f00af",
    "bluetooth_connected": "\U000f00b1",
    "bluetooth_off": "\U000f00b2",
    "brightness": "\U000f00e0",
    "charging": "\U000f0084",
    "check": "\U000f012c",
    "chevron_down": "\U000f0140",
    "chevron_up": "\U000f0143",
    "dnd": "\U000f009b",
    "keyboard": "\U000f030c",
    "lock": "\U000f033e",
    "mic": "\U000f036c",
    "mic_off": "\U000f036d",
    "night": "\U000f0594",
    "power": "\U000f0425",
    "speaker": "\U000f04c3",
    "volume_high": "\U000f057e",
    "volume_low": "\U000f057f",
    "volume_medium": "\U000f0580",
    "volume_muted": "\U000f075f",
    "wifi": "\U000f05a9",
    "wifi_off": "\U000f05aa",
}

BATTERY_LEVELS = [
    "\U000f007a", "\U000f007b", "\U000f007c", "\U000f007d", "\U000f007e",
    "\U000f007f", "\U000f0080", "\U000f0081", "\U000f0082", "\U000f0079",
]
SIGNAL_LEVELS = ["\U000f091f", "\U000f0922", "\U000f0925", "\U000f0928"]
SIGNAL_LEVELS_LOCKED = ["\U000f0920", "\U000f0923", "\U000f0926", "\U000f0929"]


def run(*command):
    """Stdout of a command, or "" if it failed: a missing reading is not fatal."""
    try:
        result = subprocess.run(command, capture_output=True, text=True, timeout=3)
    except (OSError, subprocess.TimeoutExpired):
        return ""
    return result.stdout if result.returncode == 0 else ""


def nmcli_fields(line):
    """Split a line of `nmcli -t`, which escapes ':' and '\\' inside a value."""
    fields = re.split(r"(?<!\\):", line)
    return [re.sub(r"\\(.)", r"\1", field) for field in fields]


def read_volume(target):
    # "Volume: 0.84" or "Volume: 0.84 [MUTED]"
    output = run("wpctl", "get-volume", target)
    match = re.search(r"Volume: ([0-9.]+)", output)
    percent = round(float(match.group(1)) * 100) if match else 0
    return percent, "[MUTED]" in output


def audio_state():
    percent, muted = read_volume("@DEFAULT_AUDIO_SINK@")
    if muted or percent == 0:
        icon = ICONS["volume_muted"]
    elif percent < 34:
        icon = ICONS["volume_low"]
    elif percent < 67:
        icon = ICONS["volume_medium"]
    else:
        icon = ICONS["volume_high"]

    default = run("pactl", "get-default-sink").strip()
    try:
        sinks = json.loads(run("pactl", "-f", "json", "list", "sinks") or "[]")
    except json.JSONDecodeError:
        sinks = []

    return {
        "percent": percent,
        "muted": muted,
        "icon": icon,
        "sinks": [
            {
                "id": sink["index"],
                "name": sink["description"],
                "active": sink["name"] == default,
                "icon": ICONS["speaker"],
                "mark": ICONS["check"] if sink["name"] == default else "",
            }
            for sink in sinks
        ],
    }


def mic_state():
    _, muted = read_volume("@DEFAULT_AUDIO_SOURCE@")
    return {
        "muted": muted,
        "icon": ICONS["mic_off"] if muted else ICONS["mic"],
        "subtitle": "Muted" if muted else "On",
    }


def brightness_state():
    # device,class,current,percent%,max
    fields = run("brightnessctl", "-m").strip().split(",")
    percent = int(fields[3].rstrip("%")) if len(fields) > 3 else 0
    return {"percent": percent}


def saved_wifi():
    """Saved Wi-Fi profiles by name, which NetworkManager defaults to the SSID."""
    saved = {}
    for line in run("nmcli", "-t", "-f", "NAME,UUID,TYPE", "connection", "show").splitlines():
        fields = nmcli_fields(line)
        if len(fields) == 3 and fields[2] == WIFI_TYPE:
            saved[fields[0]] = fields[1]
    return saved


def wifi_state():
    on = run("nmcli", "radio", "wifi").strip() == "enabled"
    if not on:
        return {
            "on": False,
            "icon": ICONS["wifi_off"],
            "subtitle": "Off",
            "networks": [],
            "notice": "Wi-Fi is off",
        }

    saved = saved_wifi()
    strongest = {}
    output = run(
        "nmcli", "-t", "-f", "IN-USE,SSID,SIGNAL,SECURITY",
        "device", "wifi", "list", "--rescan", "no",
    )
    for line in output.splitlines():
        fields = nmcli_fields(line)
        if len(fields) != 4 or not fields[1]:
            continue  # hidden networks have no name to show
        in_use, ssid, signal_text, security = fields
        strength = int(signal_text or 0)
        known = strongest.get(ssid)
        if known is None or strength > known["strength"] or in_use == "*":
            active = in_use == "*" or (known is not None and known["active"])
            strongest[ssid] = {
                "ssid": ssid,
                "strength": strength,
                "active": active,
                "secure": bool(security),
            }

    # Levels rather than raw strength, so the list does not reorder itself on
    # every small change in signal.
    def level(network):
        return min(network["strength"] // 25, 3)

    networks = sorted(
        strongest.values(),
        key=lambda n: (not n["active"], n["ssid"] not in saved, -level(n), n["ssid"]),
    )[:MAX_NETWORKS]

    current = next((n["ssid"] for n in networks if n["active"]), None)
    return {
        "on": True,
        "icon": ICONS["wifi"],
        "subtitle": current or "Not connected",
        "networks": [
            {
                "name": n["ssid"],
                "active": n["active"],
                "mark": ICONS["check"] if n["active"] else "",
                # "active" does nothing, a UUID connects, and empty sends you
                # to nmtui, because a new network may need a password.
                "connect": "active" if n["active"] else saved.get(n["ssid"], ""),
                "icon": (SIGNAL_LEVELS_LOCKED if n["secure"] else SIGNAL_LEVELS)[level(n)],
            }
            for n in networks
        ],
        "notice": "" if networks else "No networks found",
    }


def bluetooth_devices(*kind):
    # "Device AA:BB:CC:DD:EE:FF Some Name"
    devices = {}
    for line in run("bluetoothctl", "devices", *kind).splitlines():
        parts = line.split(" ", 2)
        if len(parts) == 3 and parts[0] == "Device":
            devices[parts[1]] = parts[2]
    return devices


def bluetooth_state():
    on = "Powered: yes" in run("bluetoothctl", "show")
    if not on:
        return {
            "on": False,
            "icon": ICONS["bluetooth_off"],
            "subtitle": "Off",
            "devices": [],
            "notice": "Bluetooth is off",
        }

    paired = bluetooth_devices("Paired")
    connected = bluetooth_devices("Connected")
    names = list(connected.values())
    if len(names) == 1:
        subtitle = names[0]
    elif names:
        subtitle = f"{len(names)} connected"
    else:
        subtitle = "On"

    return {
        "on": True,
        "icon": ICONS["bluetooth_connected"] if names else ICONS["bluetooth"],
        "subtitle": subtitle,
        "devices": [
            {
                "mac": mac,
                "name": name,
                "connected": mac in connected,
                "icon": ICONS["bluetooth_connected" if mac in connected else "bluetooth"],
                "mark": ICONS["check"] if mac in connected else "",
            }
            for mac, name in sorted(paired.items(), key=lambda item: item[0] not in connected)
        ],
        "notice": "" if paired else "No paired devices",
    }


def keyboard_state():
    try:
        keyboards = json.loads(run("hyprctl", "devices", "-j"))["keyboards"]
    except (json.JSONDecodeError, KeyError):
        return {"device": "", "layout": "Unknown"}
    keyboard = next(
        (k for k in keyboards if k["name"] == TYPING_KEYBOARD),
        next((k for k in keyboards if k["main"]), None),
    )
    if keyboard is None:
        return {"device": "", "layout": "Unknown"}
    return {"device": keyboard["name"], "layout": keyboard["active_keymap"]}


def battery_state():
    paths = glob.glob("/sys/class/power_supply/BAT*")
    if not paths:
        return {"present": False, "percent": 0, "icon": ICONS["battery"]}
    try:
        with open(os.path.join(paths[0], "capacity")) as handle:
            percent = int(handle.read())
        with open(os.path.join(paths[0], "status")) as handle:
            status = handle.read().strip()
    except (OSError, ValueError):
        return {"present": False, "percent": 0, "icon": ICONS["battery"]}
    icon = ICONS["charging"] if status == "Charging" else BATTERY_LEVELS[min(percent // 10, 9)]
    return {"present": True, "percent": percent, "icon": icon}


def state():
    dnd = run("swaync-client", "-D").strip() == "true"
    night = run("systemctl", "--user", "is-active", "hyprsunset").strip() == "active"
    return json.dumps(
        {
            "icons": ICONS,
            "audio": audio_state(),
            "mic": mic_state(),
            "brightness": brightness_state(),
            "wifi": wifi_state(),
            "bluetooth": bluetooth_state(),
            "keyboard": keyboard_state(),
            "battery": battery_state(),
            "dnd": {"on": dnd, "subtitle": "On" if dnd else "Off"},
            "night": {"on": night, "subtitle": "On" if night else "Off"},
        },
        separators=(",", ":"),
    )


def main():
    if "--once" in sys.argv[1:]:
        print(state())
        return

    # Turns SIGUSR1 into something select can wait on alongside the poll timer.
    wake_read, wake_write = os.pipe()
    os.set_blocking(wake_write, False)
    signal.set_wakeup_fd(wake_write)
    signal.signal(signal.SIGUSR1, lambda *_: None)

    last = None
    while True:
        current = state()
        if current != last:
            print(current, flush=True)
            last = current
        ready, _, _ = select.select([wake_read], [], [], POLL_SECONDS)
        if ready:
            os.read(wake_read, 1024)


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        pass
