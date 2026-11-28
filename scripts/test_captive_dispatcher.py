"""Tests for system/etc/NetworkManager/dispatcher.d/90-captive-no-autoconnect.

The script only talks to nmcli and logger, so both are replaced by stand-ins on
PATH that answer from the scenario and record what they were asked to do.
"""

import os
import pathlib
import subprocess

import pytest

SCRIPT = pathlib.Path(__file__).resolve().parent.parent / "system/etc/NetworkManager/dispatcher.d/90-captive-no-autoconnect"
WIFI = "11111111-1111-1111-1111-111111111111"

NMCLI = """#!/bin/sh
printf '%s\\n' "$*" >> "$CALLS"
case "$*" in
    "-t -f TYPE,IP4-CONNECTIVITY,IP6-CONNECTIVITY,CON-UUID device status") cat "$DEVICES" ;;
    "-g 802-11-wireless-security.key-mgmt connection show uuid "*) printf '%s\\n' "$SECURITY" ;;
    "-g connection.autoconnect connection show uuid "*) printf '%s\\n' "$AUTOCONNECT" ;;
    "-g connection.id connection show uuid "*) echo "Cafe Wi-Fi" ;;
esac
"""
LOGGER = """#!/bin/sh
printf 'logger %s\\n' "$*" >> "$CALLS"
"""


def run(tmp_path, devices, action="connectivity-change", security="", autoconnect="yes"):
    """Run the script against a made-up NetworkManager; return what it asked for."""
    bin_dir = tmp_path / "bin"
    bin_dir.mkdir()
    for name, body in (("nmcli", NMCLI), ("logger", LOGGER)):
        path = bin_dir / name
        path.write_text(body)
        path.chmod(0o755)
    calls = tmp_path / "calls"
    calls.write_text("")
    (tmp_path / "devices").write_text("".join(line + "\n" for line in devices))
    env = {
        "PATH": "%s:/usr/bin:/bin" % bin_dir,
        "CALLS": str(calls),
        "DEVICES": str(tmp_path / "devices"),
        "SECURITY": security,
        "AUTOCONNECT": autoconnect,
    }
    result = subprocess.run(["sh", str(SCRIPT), "wlan0", action], env=env, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr
    return calls.read_text().splitlines()


def turned_off(calls):
    return "connection modify uuid %s connection.autoconnect no" % WIFI in calls


PORTAL = ["wifi:portal:none:" + WIFI]


@pytest.mark.parametrize("security", ["", "owe"])
def test_an_open_network_behind_a_login_page_stops_auto_connecting(tmp_path, security):
    calls = run(tmp_path, PORTAL, security=security)
    assert turned_off(calls)
    assert any(call.startswith("logger ") and "Cafe Wi-Fi" in call for call in calls)


def test_a_login_page_seen_over_ipv6_only_counts_too(tmp_path):
    assert turned_off(run(tmp_path, ["wifi:none:portal:" + WIFI]))


def test_it_also_acts_when_the_connection_comes_up(tmp_path):
    assert turned_off(run(tmp_path, PORTAL, action="up"))


@pytest.mark.parametrize("security", ["wpa-psk", "sae", "wpa-eap"])
def test_a_network_with_a_password_is_left_alone(tmp_path, security):
    assert not turned_off(run(tmp_path, PORTAL, security=security))


@pytest.mark.parametrize("state", ["full", "limited", "none", "unknown"])
def test_no_login_page_means_no_change(tmp_path, state):
    assert not turned_off(run(tmp_path, ["wifi:%s:%s:%s" % (state, state, WIFI)]))


def test_only_wifi_devices_count(tmp_path):
    devices = ["ethernet:portal:portal:" + WIFI, "wifi-p2p:none:none:", "wifi:portal:portal:"]
    assert not turned_off(run(tmp_path, devices))


def test_a_network_that_already_does_not_auto_connect_is_not_touched(tmp_path):
    assert not turned_off(run(tmp_path, PORTAL, autoconnect="no"))


@pytest.mark.parametrize("action", ["down", "pre-up", "dhcp4-change", "hostname"])
def test_other_events_do_not_even_ask_networkmanager(tmp_path, action):
    assert run(tmp_path, PORTAL, action=action) == []


def test_the_script_is_executable():
    assert os.access(SCRIPT, os.X_OK)
