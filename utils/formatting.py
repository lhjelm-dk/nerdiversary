"""Tal-, dato- og varighedsformatering paa dansk og engelsk.

Alle datoer vises baade med cifre og med maaneden skrevet med bogstaver
(12.04.1980 (12. apr 1980)), saa 12.04 aldrig kan forveksles med 4. december.
"""

from __future__ import annotations

from datetime import datetime

from dateutil.relativedelta import relativedelta

WEEKDAYS: dict[str, list[str]] = {
    "da": ["mandag", "tirsdag", "onsdag", "torsdag", "fredag", "lørdag", "søndag"],
    "en": [
        "Monday",
        "Tuesday",
        "Wednesday",
        "Thursday",
        "Friday",
        "Saturday",
        "Sunday",
    ],
}

MONTHS_ABBR: dict[str, list[str]] = {
    "da": ["jan", "feb", "mar", "apr", "maj", "jun", "jul", "aug", "sep", "okt", "nov", "dec"],
    "en": ["Jan", "Feb", "Mar", "Apr", "May", "Jun", "Jul", "Aug", "Sep", "Oct", "Nov", "Dec"],
}

MONTHS_FULL: dict[str, list[str]] = {
    "da": [
        "januar",
        "februar",
        "marts",
        "april",
        "maj",
        "juni",
        "juli",
        "august",
        "september",
        "oktober",
        "november",
        "december",
    ],
    "en": [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ],
}

# (ental, flertal) for hver tidsenhed.
_UNIT_WORDS: dict[str, dict[str, tuple[str, str]]] = {
    "da": {
        "year": ("år", "år"),
        "month": ("måned", "måneder"),
        "week": ("uge", "uger"),
        "day": ("dag", "dage"),
        "hour": ("time", "timer"),
        "minute": ("minut", "minutter"),
        "second": ("sekund", "sekunder"),
    },
    "en": {
        "year": ("year", "years"),
        "month": ("month", "months"),
        "week": ("week", "weeks"),
        "day": ("day", "days"),
        "hour": ("hour", "hours"),
        "minute": ("minute", "minutes"),
        "second": ("second", "seconds"),
    },
}

_AND = {"da": "og", "en": "and"}


def fmt_int(value: float, lang: str = "da") -> str:
    """1234567 -> "1.234.567" (da) / "1,234,567" (en)."""
    grouped = f"{round(value):,}"
    return grouped.replace(",", ".") if lang == "da" else grouped


def fmt_num(value: float, lang: str = "da", decimals: int = 2) -> str:
    """Decimaltal med dansk komma eller engelsk punktum."""
    grouped = f"{value:,.{decimals}f}"
    if lang == "da":
        return grouped.replace(",", "\x00").replace(".", ",").replace("\x00", ".")
    return grouped


def fmt_date_numeric(moment: datetime) -> str:
    """12.04.1980 - altid med fire-cifret aarstal."""
    return moment.strftime("%d.%m.%Y")


def fmt_date_text(moment: datetime, lang: str = "da") -> str:
    """12. apr 1980 (da) / 12 Apr 1980 (en)."""
    month = MONTHS_ABBR[lang][moment.month - 1]
    if lang == "da":
        return f"{moment.day}. {month} {moment.year}"
    return f"{moment.day} {month} {moment.year}"


def fmt_date_both(moment: datetime, lang: str = "da") -> str:
    """12.04.1980 (12. apr 1980) - cifre og bogstaver, saa intet er tvetydigt."""
    return f"{fmt_date_numeric(moment)} ({fmt_date_text(moment, lang)})"


def fmt_weekday(moment: datetime, lang: str = "da") -> str:
    return WEEKDAYS[lang][moment.weekday()]


def fmt_clock(moment: datetime, lang: str = "da", seconds: bool = True) -> str:
    """09.41.33 (da) / 09:41:33 (en)."""
    pattern = "%H:%M:%S" if seconds else "%H:%M"
    text = moment.strftime(pattern)
    return text.replace(":", ".") if lang == "da" else text


def fmt_datetime_full(moment: datetime, lang: str = "da", seconds: bool = True) -> str:
    """lørdag 12.04.1980 (12. apr 1980) kl. 09.41.33."""
    weekday = fmt_weekday(moment, lang)
    date_part = fmt_date_both(moment, lang)
    clock = fmt_clock(moment, lang, seconds)
    if lang == "da":
        return f"{weekday} {date_part} kl. {clock}"
    return f"{weekday} {date_part} at {clock}"


def _unit_phrase(count: int, unit: str, lang: str) -> str:
    singular, plural = _UNIT_WORDS[lang][unit]
    word = singular if abs(count) == 1 else plural
    return f"{fmt_int(count, lang)} {word}"


def unit_phrase(count: int, unit: str, lang: str = "da") -> str:
    """"3 måneder" / "3 months" - tallet og enheden i rigtigt tal.

    Enhederne er noeglerne i ``_UNIT_WORDS``: year, month, week, day, hour,
    minute, second.
    """
    return _unit_phrase(count, unit, lang)


def _join(parts: list[str], lang: str) -> str:
    if not parts:
        return ""
    if len(parts) == 1:
        return parts[0]
    return f"{', '.join(parts[:-1])} {_AND[lang]} {parts[-1]}"


def fmt_relativedelta(delta: relativedelta, lang: str = "da", max_parts: int = 3) -> str:
    """"34 år, 7 måneder og 12 dage" - de groveste enheder foerst."""
    candidates = [
        ("year", int(delta.years)),
        ("month", int(delta.months)),
        ("day", int(delta.days)),
        ("hour", int(delta.hours)),
        ("minute", int(delta.minutes)),
        ("second", int(delta.seconds)),
    ]
    parts = [_unit_phrase(count, unit, lang) for unit, count in candidates if count]
    if not parts:
        return _unit_phrase(0, "second", lang)
    return _join(parts[:max_parts], lang)


def fmt_age(birth: datetime, moment: datetime, lang: str = "da") -> str:
    """Alderen paa et givet tidspunkt, fx "34 år, 7 måneder og 12 dage"."""
    return fmt_relativedelta(relativedelta(moment, birth), lang)


def fmt_countdown(target: datetime, now: datetime, lang: str = "da") -> str:
    """"om 2 år, 4 måneder og 11 dage" / "3 år siden"."""
    if target >= now:
        span = fmt_relativedelta(relativedelta(target, now), lang)
        return f"om {span}" if lang == "da" else f"in {span}"
    span = fmt_relativedelta(relativedelta(now, target), lang)
    return f"{span} siden" if lang == "da" else f"{span} ago"


def fmt_hms_countdown(seconds_left: float, lang: str = "da") -> str:
    """Nedtaelling som 12d 04t 33m 07s - til det levende ur."""
    total = max(0, int(seconds_left))
    days, rest = divmod(total, 86400)
    hours, rest = divmod(rest, 3600)
    minutes, secs = divmod(rest, 60)
    day_tag = "d" if lang == "da" else "d"
    hour_tag = "t" if lang == "da" else "h"
    return f"{days}{day_tag} {hours:02d}{hour_tag} {minutes:02d}m {secs:02d}s"
