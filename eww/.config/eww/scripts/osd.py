"""The eww side of the windows shown in the middle of the screen, shared by the
scripts that drive them: level-osd.py, keyboard-backlight-osd.py,
keyboard-osd.py and battery-warning.py.
"""

import fcntl
import json
import os
import subprocess
import tempfile
import time

LEVEL_WINDOW = "level-osd"
LEVEL_SECONDS = 1.5
# Holds the token of the caller that owns the level window, empty while it is
# closed.
LEVEL_STATE = os.path.join(os.environ.get("XDG_RUNTIME_DIR") or tempfile.gettempdir(), "eww-level-osd")


def eww(*args):
    # --no-daemonize: when the daemon takes over 100 ms to answer an open, the
    # client takes it for dead and starts a second one, which steals the socket
    # and leaves the first one's window stuck on screen.
    subprocess.run(["eww", "--no-daemonize", *args], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)


def show_level(level):
    """Show {icon, value, bar} in the level window; return a token for hide_level.

    The caller closes the window LEVEL_SECONDS later with hide_level. Each call
    takes the window over, so a key held down keeps it up and only the last
    caller's hide_level closes it. The window is opened once and only updated
    while it is up, since reopening an open eww window makes it flash.
    """
    token = f"{os.getpid()}-{time.monotonic_ns()}"
    with open(LEVEL_STATE, "a+") as state:
        fcntl.flock(state, fcntl.LOCK_EX)
        state.seek(0)
        showing = state.read() != ""
        eww("update", f"{LEVEL_WINDOW}={json.dumps(level)}")
        if not showing:
            eww("open", LEVEL_WINDOW)
        state.seek(0)
        state.truncate()
        state.write(token)
    return token


def hide_level(token):
    """Close the level window, unless a later show_level took it over."""
    with open(LEVEL_STATE, "a+") as state:
        fcntl.flock(state, fcntl.LOCK_EX)
        state.seek(0)
        if state.read() == token:
            eww("close", LEVEL_WINDOW)
            state.truncate(0)
