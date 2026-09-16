#!/bin/bash

# Control Panel Popup for Waybar
# Requires: yad, pamixer (or pactl), brightnessctl, nmcli, bluetoothctl

# Check if already running, if so close it
if pgrep -f "yad.*--title=Control Panel" > /dev/null; then
    pkill -f "yad.*--title=Control Panel"
    exit 0
fi

# Get current values
VOLUME=$(pamixer --get-volume 2>/dev/null || echo "50")
BRIGHTNESS=$(brightnessctl -m | cut -d',' -f4 | tr -d '%' 2>/dev/null || echo "50")

# Check wifi and bluetooth status
WIFI_STATUS=$(nmcli radio wifi 2>/dev/null || echo "disabled")
BT_STATUS=$(bluetoothctl show 2>/dev/null | grep "Powered:" | awk '{print $2}')

if [ "$WIFI_STATUS" = "enabled" ]; then
    WIFI_ICON="network-wireless-symbolic"
    WIFI_TEXT="WiFi On"
else
    WIFI_ICON="network-wireless-disabled-symbolic"
    WIFI_TEXT="WiFi Off"
fi

if [ "$BT_STATUS" = "yes" ]; then
    BT_ICON="bluetooth-active-symbolic"
    BT_TEXT="Bluetooth On"
else
    BT_ICON="bluetooth-disabled-symbolic"
    BT_TEXT="Bluetooth Off"
fi

# Create the popup
result=$(yad --form \
    --title="Control Panel" \
    --width=300 \
    --no-buttons \
    --undecorated \
    --close-on-unfocus \
    --on-top \
    --skip-taskbar \
    --posx=-50 \
    --posy=50 \
    --field="<b>Volume</b>":LBL "" \
    --field="🔊":SCL "$VOLUME" \
    --field="<b>Brightness</b>":LBL "" \
    --field="☀️":SCL "$BRIGHTNESS" \
    --field="":LBL "" \
    --field="$WIFI_TEXT!$WIFI_ICON!Toggle WiFi":FBTN "@bash -c 'if nmcli radio wifi | grep -q enabled; then nmcli radio wifi off; else nmcli radio wifi on; fi'" \
    --field="$BT_TEXT!$BT_ICON!Toggle Bluetooth":FBTN "@bash -c 'if bluetoothctl show | grep -q \"Powered: yes\"; then bluetoothctl power off; else bluetoothctl power on; fi'" \
    2>/dev/null)

# Parse results and apply changes
if [ -n "$result" ]; then
    NEW_VOL=$(echo "$result" | cut -d'|' -f2 | cut -d'.' -f1)
    NEW_BRIGHT=$(echo "$result" | cut -d'|' -f4 | cut -d'.' -f1)
    
    # Apply volume if changed
    if [ "$NEW_VOL" != "$VOLUME" ] 2>/dev/null; then
        pamixer --set-volume "$NEW_VOL" 2>/dev/null || pactl set-sink-volume @DEFAULT_SINK@ "${NEW_VOL}%" 2>/dev/null
    fi
    
    # Apply brightness if changed
    if [ "$NEW_BRIGHT" != "$BRIGHTNESS" ] 2>/dev/null; then
        brightnessctl set "${NEW_BRIGHT}%" 2>/dev/null
    fi
fi
