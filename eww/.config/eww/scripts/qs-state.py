#!/usr/bin/python3
"""Print the quick settings panel's state as JSON.

qs-state.py          one line now, then one on every change; eww runs this
                     only while the panel is open. SIGUSR1 asks for a refresh
                     right away, which qs-action.sh sends after each action.
                     Volume, screen and keyboard brightness and battery are
                     read every second; the rest (see slow_state) every few,
                     since each reading starts a process and those values
                     rarely change unasked.
qs-state.py --once   one line, then exit.

Icons are GNOME's symbolic icon names, for eww's image widget.

SSIDs, VPN and Bluetooth names are other people's text. They are only ever
displayed: the commands the panel runs carry UUIDs, MAC addresses and numeric
ids instead.
"""

import glob
import json
import os
import re
import select
import signal
import sys
import time

from readings import (
    battery_icon,
    brightness_icon,
    layout_options,
    read_battery,
    read_brightness,
    read_keyboard_backlight,
    read_keyboards,
    read_volume,
    run,
    typing_keyboard,
    volume_icon,
)

POLL_SECONDS = 1
SLOW_POLL_SECONDS = 5
# After an action the slow readings are also taken every second for this long:
# a Wi-Fi scan or a Bluetooth connection lands a few seconds after the click.
EAGER_SECONDS = 10
MAX_NETWORKS = 6
WIFI_TYPE = "802-11-wireless"
VPN_TYPES = ("vpn", "wireguard")
COLOR_SCHEME_ACTIVE = os.path.expanduser("~/.local/state/color-schemes/active")

SIGNAL_LEVELS = ["weak", "ok", "good", "excellent"]


def nmcli_fields(line):
    """Split a line of `nmcli -t`, which escapes ':' and '\\' inside a value."""
    fields = re.split(r"(?<!\\):", line)
    return [re.sub(r"\\(.)", r"\1", field) for field in fields]


def signal_icon(strength):
    # Levels rather than raw strength, as in GNOME.
    return "network-wireless-signal-%s-symbolic" % SIGNAL_LEVELS[min(strength // 25, 3)]


def volume_state():
    percent, muted = read_volume("@DEFAULT_AUDIO_SINK@")
    return {"percent": percent, "muted": muted, "icon": volume_icon(percent, muted)}


def sinks_state():
    default = run("pactl", "get-default-sink").strip()
    try:
        sinks = json.loads(run("pactl", "-f", "json", "list", "sinks") or "[]")
    except json.JSONDecodeError:
        sinks = []
    return [
        {
            "id": sink["index"],
            "name": sink["description"],
            "active": sink["name"] == default,
            "icon": "audio-speakers-symbolic",
        }
        for sink in sinks
    ]


def read_connections():
    """NetworkManager's saved connections: [{name, uuid, type, active}]."""
    connections = []
    output = run("nmcli", "-t", "-f", "NAME,UUID,TYPE,ACTIVE", "connection", "show")
    for line in output.splitlines():
        fields = nmcli_fields(line)
        if len(fields) == 4:
            name, uuid, kind, active = fields
            connections.append({"name": name, "uuid": uuid, "type": kind, "active": active == "yes"})
    return connections


def wifi_state(connections):
    on = run("nmcli", "radio", "wifi").strip() == "enabled"
    if not on:
        return {
            "on": False,
            "icon": "network-wireless-disabled-symbolic",
            "subtitle": "Off",
            "networks": [],
            "notice": "Wi-Fi is off",
        }

    # Saved Wi-Fi profiles by name, which NetworkManager defaults to the SSID.
    saved = {c["name"]: c["uuid"] for c in connections if c["type"] == WIFI_TYPE}
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

    # Sorted by level rather than raw strength, so the list does not reorder
    # itself on every small change in signal.
    networks = sorted(
        strongest.values(),
        key=lambda n: (not n["active"], n["ssid"] not in saved, -min(n["strength"] // 25, 3), n["ssid"]),
    )[:MAX_NETWORKS]

    current = next((n for n in networks if n["active"]), None)
    return {
        "on": True,
        "icon": signal_icon(current["strength"]) if current else "network-wireless-offline-symbolic",
        "subtitle": current["ssid"] if current else "Not connected",
        "networks": [
            {
                "name": n["ssid"],
                "active": n["active"],
                # The connected network is ticked; a secured one shows a lock.
                "mark": "object-select-symbolic" if n["active"]
                else "channel-secure-symbolic" if n["secure"] else "",
                # "active" does nothing, a UUID connects, and empty sends you
                # to nmtui, because a new network may need a password.
                "connect": "active" if n["active"] else saved.get(n["ssid"], ""),
                "icon": signal_icon(n["strength"]),
            }
            for n in networks
        ],
        "notice": "" if networks else "No networks found",
    }


def vpn_state(connections):
    vpns = [c for c in connections if c["type"] in VPN_TYPES]
    active = [c for c in vpns if c["active"]]
    if active:
        subtitle = active[0]["name"] if len(active) == 1 else f"{len(active)} connected"
    else:
        subtitle = vpns[0]["name"] if vpns else "None set up"
    return {
        "on": bool(active),
        "icon": "network-vpn-symbolic" if active else "network-vpn-disabled-symbolic",
        "subtitle": subtitle,
        # What the tile's toggle acts on: the active ones, or else the first.
        "target": " ".join(c["uuid"] for c in active) if active else (vpns[0]["uuid"] if vpns else ""),
        "connections": [
            {
                "uuid": c["uuid"],
                "name": c["name"],
                "active": c["active"],
                "icon": "network-vpn-symbolic",
                "mark": "object-select-symbolic" if c["active"] else "",
            }
            for c in vpns
        ],
        "notice": "" if vpns else "No VPN connections",
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
            "icon": "bluetooth-disabled-symbolic",
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
        "icon": "bluetooth-active-symbolic",
        "subtitle": subtitle,
        "devices": [
            {
                "mac": mac,
                "name": name,
                "connected": mac in connected,
                "icon": "bluetooth-active-symbolic",
                "mark": "object-select-symbolic" if mac in connected else "",
            }
            for mac, name in sorted(paired.items(), key=lambda item: item[0] not in connected)
        ],
        "notice": "" if paired else "No paired devices",
    }


def keyboard_state():
    keyboard = typing_keyboard(read_keyboards())
    if keyboard is None:
        return {"device": "", "layout": "Unknown", "layouts": []}
    return {
        "device": keyboard["name"],
        "layout": keyboard["active_keymap"],
        "layouts": [
            dict(option, mark="object-select-symbolic" if option["active"] else "")
            for option in layout_options(keyboard)
        ],
    }


def airplane_state():
    """On when every radio is soft-blocked, as GNOME's Airplane Mode does it."""
    blocked = []
    for path in glob.glob("/sys/class/rfkill/rfkill*/soft"):
        try:
            with open(path) as handle:
                blocked.append(handle.read().strip() == "1")
        except OSError:
            pass
    return {"on": bool(blocked) and all(blocked)}


def dark_state():
    # The colour-scheme switcher's "active" link ends in /dark or /light.
    try:
        on = os.readlink(COLOR_SCHEME_ACTIVE).rstrip("/").endswith("/dark")
    except OSError:
        on = False
    return {"on": on}


def brightness_state():
    percent = read_brightness()
    return {"percent": percent, "icon": brightness_icon(percent)}


def keyboard_backlight_state():
    backlight = read_keyboard_backlight()
    if backlight is None or backlight[1] < 1:
        return {"present": False, "level": 0, "max": 1}
    return {"present": True, "level": backlight[0], "max": backlight[1]}


def battery_state():
    battery = read_battery()
    if battery is None:
        return {"present": False, "percent": 0, "icon": "battery-missing-symbolic"}
    percent, status = battery
    return {"present": True, "percent": percent, "icon": battery_icon(percent, status)}


def slow_state():
    """Readings that cost several processes and rarely change on their own."""
    connections = read_connections()
    dnd = run("swaync-client", "-D").strip() == "true"
    night = run("systemctl", "--user", "is-active", "hyprsunset").strip() == "active"
    return {
        "sinks": sinks_state(),
        "wifi": wifi_state(connections),
        "vpn": vpn_state(connections),
        "bluetooth": bluetooth_state(),
        "keyboard": keyboard_state(),
        "dnd": {"on": dnd},
        "night": {"on": night},
    }


def state(slow):
    return json.dumps(
        {
            "audio": {**volume_state(), "sinks": slow["sinks"]},
            "brightness": brightness_state(),
            "keyboard_backlight": keyboard_backlight_state(),
            "wifi": slow["wifi"],
            "vpn": slow["vpn"],
            "bluetooth": slow["bluetooth"],
            "keyboard": slow["keyboard"],
            "battery": battery_state(),
            "airplane": airplane_state(),
            "dark": dark_state(),
            "dnd": slow["dnd"],
            "night": slow["night"],
        },
        separators=(",", ":"),
    )


def main():
    if "--once" in sys.argv[1:]:
        print(state(slow_state()))
        return

    # Turns SIGUSR1 into something select can wait on alongside the poll timer.
    wake_read, wake_write = os.pipe()
    os.set_blocking(wake_write, False)
    signal.set_wakeup_fd(wake_write)
    signal.signal(signal.SIGUSR1, lambda *_: None)

    last = None
    slow = None
    slow_due = 0.0
    eager_until = 0.0
    while True:
        now = time.monotonic()
        if slow is None or now >= slow_due or now < eager_until:
            slow = slow_state()
            slow_due = now + SLOW_POLL_SECONDS
        current = state(slow)
        if current != last:
            print(current, flush=True)
            last = current
        ready, _, _ = select.select([wake_read], [], [], POLL_SECONDS)
        if ready:
            os.read(wake_read, 1024)
            eager_until = time.monotonic() + EAGER_SECONDS


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        pass
