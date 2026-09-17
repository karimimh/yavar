"""Jalali display, Saturday-first weeks, timezone-aware resolution. Spec 13.2."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, date, datetime, time, timedelta
from zoneinfo import ZoneInfo

import jdatetime

from apps.core.persian import fold_persian, to_latin_digits, to_persian_digits

DEFAULT_TIMEZONE = "Asia/Tehran"
WEEKDAY_FA = {
    5: "شنبه",  # Saturday
    6: "یکشنبه",
    0: "دوشنبه",
    1: "سه‌شنبه",
    2: "چهارشنبه",
    3: "پنجشنبه",
    4: "جمعه",
}
WEEKDAY_NAME_TO_PYTHON = {
    "پنجشنبه": 3,
    "پنج شنبه": 3,
    "چهارشنبه": 2,
    "سه‌شنبه": 1,
    "سه شنبه": 1,
    "یکشنبه": 6,
    "دوشنبه": 0,
    "جمعه": 4,
    "شنبه": 5,
}


@dataclass(frozen=True)
class ResolvedDateTime:
    instant: datetime
    timezone: str
    jalali_date: str
    gregorian_date: str
    time_display: str | None
    weekday_fa: str
    ambiguous: bool = False
    clarification: str | None = None


def tzinfo_of(name: str) -> ZoneInfo:
    try:
        return ZoneInfo(name)
    except Exception:
        return ZoneInfo(DEFAULT_TIMEZONE)


def now_in(tz_name: str) -> datetime:
    return datetime.now(tzinfo_of(tz_name))


def to_jalali_date(d: date | datetime) -> str:
    if isinstance(d, datetime):
        d = d.date()
    j = jdatetime.date.fromgregorian(date=d)
    return f"{j.year:04d}-{j.month:02d}-{j.day:02d}"


def format_jalali_fa(dt: datetime, *, include_time: bool) -> str:
    local = dt
    j = jdatetime.datetime.fromgregorian(datetime=local)
    date_part = to_persian_digits(f"{j.year:04d}/{j.month:02d}/{j.day:02d}")
    weekday = WEEKDAY_FA[local.weekday()]
    if include_time:
        t = to_persian_digits(local.strftime("%H:%M"))
        return f"{weekday} {date_part} ساعت {t}"
    return f"{weekday} {date_part}"


def saturday_start_of_week(d: date) -> date:
    # Python weekday: Monday=0 ... Sunday=6. Saturday=5.
    delta = (d.weekday() - 5) % 7
    return d - timedelta(days=delta)


def next_weekday(from_date: date, python_weekday: int, *, allow_today: bool) -> date:
    days_ahead = (python_weekday - from_date.weekday()) % 7
    if days_ahead == 0 and not allow_today:
        days_ahead = 7
    return from_date + timedelta(days=days_ahead)


def parse_clock(text: str) -> time | None:
    folded = to_latin_digits(fold_persian(text))
    match = None
    import re

    match = re.search(r"ساعت\s*(\d{1,2})(?:[:.](\d{2}))?", folded)
    if not match:
        match = re.search(r"\b(\d{1,2})[:.](\d{2})\b", folded)
    if not match:
        return None
    hour = int(match.group(1))
    minute = int(match.group(2) or 0)
    if hour == 24:
        hour = 0
    if not (0 <= hour <= 23 and 0 <= minute <= 59):
        return None
    return time(hour, minute)


def resolve_relative_date(
    text: str,
    *,
    timezone: str,
    now: datetime | None = None,
) -> ResolvedDateTime | None:
    """Resolve ordinary Persian relative dates. Returns None if no date found.

    Ambiguous weekday (e.g. «پنجشنبه» when today is Thursday) sets ambiguous=True
    and does not pick today vs next week.
    """
    tz = tzinfo_of(timezone)
    current = now.astimezone(tz) if now else datetime.now(tz)
    folded = fold_persian(to_latin_digits(text))
    clock = parse_clock(folded)
    target: date | None = None
    ambiguous = False
    clarification = None

    if "پس‌فردا" in folded or "پسفردا" in folded.replace(" ", ""):
        target = current.date() + timedelta(days=2)
    elif "فردا" in folded:
        target = current.date() + timedelta(days=1)
    elif "امروز" in folded:
        target = current.date()
    else:
        for name, wd in WEEKDAY_NAME_TO_PYTHON.items():
            if name in folded:
                if current.weekday() == wd:
                    ambiguous = True
                    clarification = (
                        f"منظورتان {WEEKDAY_FA[wd]} امروز است یا {WEEKDAY_FA[wd]} آینده؟"
                    )
                    target = current.date()
                else:
                    target = next_weekday(current.date(), wd, allow_today=False)
                break

    if target is None:
        return None

    if clock is None:
        instant = datetime.combine(target, time(0, 0), tzinfo=tz)
        return ResolvedDateTime(
            instant=instant,
            timezone=timezone,
            jalali_date=to_jalali_date(target),
            gregorian_date=target.isoformat(),
            time_display=None,
            weekday_fa=WEEKDAY_FA[target.weekday()],
            ambiguous=ambiguous,
            clarification=clarification,
        )

    instant = datetime.combine(target, clock, tzinfo=tz)
    return ResolvedDateTime(
        instant=instant,
        timezone=timezone,
        jalali_date=to_jalali_date(target),
        gregorian_date=target.isoformat(),
        time_display=clock.strftime("%H:%M"),
        weekday_fa=WEEKDAY_FA[target.weekday()],
        ambiguous=ambiguous,
        clarification=clarification,
    )


def shift_keep_local_clock(dt: datetime, old_tz: str, new_tz: str) -> datetime:
    """Keep wall-clock time, change zone."""
    naive = dt.astimezone(tzinfo_of(old_tz)).replace(tzinfo=None)
    return naive.replace(tzinfo=tzinfo_of(new_tz))


def shift_keep_instant(dt: datetime, new_tz: str) -> datetime:
    return dt.astimezone(tzinfo_of(new_tz))


def as_utc(dt: datetime) -> datetime:
    if dt.tzinfo is None:
        return dt.replace(tzinfo=UTC)
    return dt.astimezone(UTC)
