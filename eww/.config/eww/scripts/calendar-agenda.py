#!/usr/bin/python3
"""Print one day's events as JSON for the eww calendar window (eww/eww.yuck).

Usage: calendar-agenda.py YYYY-MM-DD
       calendar-agenda.py --hold

Events come from Evolution Data Server, the store behind GNOME Calendar, so
this sees the same calendars (online accounts included) and gets recurring
events expanded. The system python is named above because gi only exists there.
"""

import json
import signal
import sys
from datetime import date, datetime, time, timedelta

# Past this the panel would outgrow the screen; the rest are only counted.
MAX_EVENTS = 6

# Connecting waits up to this long for EDS to report a calendar as connected,
# and a local calendar only reports that while another client holds it open,
# hence --hold. 0 is not a shortcut: it means wait forever.
CONNECT_WAIT_SECONDS = 1


def to_date(itime):
    return date(itime.get_year(), itime.get_month(), itime.get_day())


def to_local(itime):
    """Convert an ICalGLib time to a naive local datetime."""
    zone = itime.get_timezone()
    if zone is None and not itime.is_utc():
        # Floating time: the fields already are wall-clock time.
        return datetime(
            itime.get_year(),
            itime.get_month(),
            itime.get_day(),
            itime.get_hour(),
            itime.get_minute(),
            itime.get_second(),
        )
    return datetime.fromtimestamp(itime.as_timet_with_zone(zone))


def all_day_covers(start, end, day):
    # An all-day DTEND is exclusive; one without a length lasts its start date.
    return start <= day and (day < end or day == start)


def timed_covers(start, end, day_start, day_end):
    # An event with no length still occurs at its start time.
    return start < day_end and (end > day_start or start == end >= day_start)


def time_label(start, end, day_start, day_end):
    starts_today = start >= day_start
    ends_today = end <= day_end
    if starts_today and ends_today:
        if start == end:
            return f"{start:%H:%M}"
        return f"{start:%H:%M} - {end:%H:%M}"
    if starts_today:
        return f"From {start:%H:%M}"
    if ends_today:
        return f"Until {end:%H:%M}"
    return "All day"


def build_event(icomp, start, end, day, day_start, day_end):
    """Return (sort key, event) for an instance, or None if not on this day."""
    if start.is_date():
        if not all_day_covers(to_date(start), to_date(end), day):
            return None
        sort_key = day_start
        when = "All day"
    else:
        local_start, local_end = to_local(start), to_local(end)
        if not timed_covers(local_start, local_end, day_start, day_end):
            return None
        sort_key = max(local_start, day_start)
        when = time_label(local_start, local_end, day_start, day_end)
    location = icomp.get_location()
    return sort_key, {
        "title": icomp.get_summary() or "(No title)",
        "detail": f"{when}, {location}" if location else when,
    }


def connect_calendars():
    """Return (connected clients, number of calendars that could not be read)."""
    import gi

    gi.require_version("ECal", "2.0")
    gi.require_version("EDataServer", "1.2")
    from gi.repository import ECal, EDataServer, GLib

    clients = []
    failed = 0
    registry = EDataServer.SourceRegistry.new_sync(None)
    for source in registry.list_enabled(EDataServer.SOURCE_EXTENSION_CALENDAR):
        try:
            clients.append(
                ECal.Client.connect_sync(
                    source, ECal.ClientSourceType.EVENTS, CONNECT_WAIT_SECONDS, None
                )
            )
        except GLib.Error:
            failed += 1
    return clients, failed


def hold_connections():
    """Stay connected until killed, so that queries connect instantly."""
    clients, _ = connect_calendars()
    signal.pause()
    return clients


def read_events(day):
    """Return (sorted events, number of calendars that could not be read)."""
    day_start = datetime.combine(day, time.min)
    day_end = day_start + timedelta(days=1)
    found = []

    def on_instance(icomp, start, end, *_):
        event = build_event(icomp, start, end, day, day_start, day_end)
        if event:
            found.append(event)
        return True

    clients, failed = connect_calendars()
    for client in clients:
        client.generate_instances_sync(
            int(day_start.timestamp()), int(day_end.timestamp()), None, on_instance
        )

    found.sort(key=lambda item: item[0])
    return [event for _, event in found], failed


def notice_for(hidden, shown, failed):
    if failed:
        return f"{failed} calendar(s) could not be read"
    if hidden:
        return f"and {hidden} more"
    return "" if shown else "Nothing planned"


def build_agenda(day):
    title = f"{day:%A}, {day.day} {day:%B}"
    try:
        events, failed = read_events(day)
    except Exception as error:  # gi may be missing, so GLib.Error can't be named
        print(f"calendar-agenda: {error}", file=sys.stderr)
        return {"title": title, "events": [], "notice": "Calendar unavailable"}
    shown = events[:MAX_EVENTS]
    return {
        "title": title,
        "events": shown,
        "notice": notice_for(len(events) - len(shown), len(shown), failed),
    }


if __name__ == "__main__":
    if sys.argv[1] == "--hold":
        hold_connections()
    else:
        print(json.dumps(build_agenda(date.fromisoformat(sys.argv[1]))))
