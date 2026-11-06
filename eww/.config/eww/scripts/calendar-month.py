#!/usr/bin/env python3
"""Print a month as JSON for the eww calendar window (eww/eww.yuck).

Usage: calendar-month.py [offset]   offset = months away from the current one

The grid is always 42 days, like macOS, so the window keeps its height when
moving between months.
"""

import json
import sys
from datetime import date, timedelta

# 0 = Monday, 6 = Sunday
WEEK_START = 0
WEEKDAY_LETTERS = "MTWTFSS"


def day_classes(day, month, today):
    if day.month != month:
        return "other-month"
    if day == today:
        return "today"
    return "weekend" if day.weekday() >= 5 else ""


def build_month(offset, today):
    year, month_index = divmod(today.year * 12 + today.month - 1 + offset, 12)
    first = date(year, month_index + 1, 1)
    grid_start = first - timedelta(days=(first.weekday() - WEEK_START) % 7)
    days = [
        {
            "n": day.day,
            "cls": day_classes(day, first.month, today),
            "iso": day.isoformat(),
            # The offset to pass back to show this day's own month.
            "offset": offset + (day.year - first.year) * 12 + day.month - first.month,
        }
        for day in (grid_start + timedelta(days=i) for i in range(42))
    ]
    return {
        "offset": offset,
        "month": first.strftime("%B"),
        "year": str(first.year),
        "weekdays": [WEEKDAY_LETTERS[(WEEK_START + i) % 7] for i in range(7)],
        "weeks": [days[i : i + 7] for i in range(0, 42, 7)],
    }


if __name__ == "__main__":
    month_offset = int(sys.argv[1]) if len(sys.argv) > 1 else 0
    print(json.dumps(build_month(month_offset, date.today())))
