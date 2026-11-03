"""Eksport til kalender: .ics-fil, Google Calendar-CSV og direkte links.

ICS-filen skrives i haanden efter RFC 5545. Det er med vilje: pakken ``ics``
foelger ikke altid foldningsreglerne, og en kalenderfil er trods alt bare
tekst. De tre ting, der i praksis gaar galt, er haandteret:

* linjerne foldes ved 75 oktetter (ikke 75 tegn — æ, ø og å fylder to)
* komma, semikolon, backslash og linjeskift escapes i alle tekstfelter
* UID'et er stabilt, saa en ny import opdaterer begivenheden i stedet for at
  lave en kopi
"""

from __future__ import annotations

import csv
import hashlib
import io
from datetime import datetime, timedelta, timezone
from urllib.parse import urlencode

from . import formatting as fmt
from . import stardate as sd
from .engine import Occasion, Profile, explanation

PRODID = "-//Noerdilaeum//Your Next Special Celebrations//DA"
UID_DOMAIN = "nerdiversary.local"
GOOGLE_RENDER_URL = "https://calendar.google.com/calendar/render"


# -------------------------------------------------------------------------
# iCalendar
# -------------------------------------------------------------------------


def _escape(text: str) -> str:
    """Escape efter RFC 5545 — raekkefoelgen er vigtig, backslash foerst."""
    return (
        text.replace("\\", "\\\\")
        .replace(";", "\\;")
        .replace(",", "\\,")
        .replace("\r\n", "\\n")
        .replace("\n", "\\n")
    )


def _fold(line: str) -> str:
    """Fold en linje ved 75 oktetter med et mellemrum som fortsaettelsestegn."""
    raw = line.encode("utf-8")
    if len(raw) <= 75:
        return line

    chunks: list[bytes] = []
    start = 0
    limit = 75
    while start < len(raw):
        end = min(start + limit, len(raw))
        # Ryk tilbage, saa vi ikke deler midt i et UTF-8-tegn.
        while end > start and end < len(raw) and (raw[end] & 0xC0) == 0x80:
            end -= 1
        chunks.append(raw[start:end])
        start = end
        limit = 74  # Fortsaettelseslinjer starter med et mellemrum.
    return "\r\n ".join(chunk.decode("utf-8") for chunk in chunks)


def _stamp(moment: datetime) -> str:
    return moment.astimezone(timezone.utc).strftime("%Y%m%dT%H%M%SZ")


def _uid(profile: Profile, occasion: Occasion) -> str:
    seed = f"{profile.birth_utc.isoformat()}|{occasion.milestone.key}"
    digest = hashlib.sha1(seed.encode("utf-8")).hexdigest()[:20]
    return f"{digest}@{UID_DOMAIN}"


def event_title(occasion: Occasion, profile: Profile, lang: str) -> str:
    """Titlen paa kalenderbegivenheden."""
    emoji = occasion.group.emoji
    who = profile.name.strip()
    label = occasion.label
    if occasion.is_absolute:
        return f"{emoji} {label}"
    if who:
        if lang == "da":
            return f"{emoji} {who}: {label}"
        return f"{emoji} {who}: {label}"
    return f"{emoji} {label}"


def event_description(occasion: Occasion, profile: Profile, lang: str) -> str:
    """Beskrivelsen — med forklaring, alder, stjernedato og et forbehold."""
    lines: list[str] = []
    why = explanation(occasion.milestone, lang)
    if why:
        lines.append(why)
        lines.append("")

    when = fmt.fmt_datetime_full(occasion.when_local, lang)
    if lang == "da":
        lines.append(f"Præcist tidspunkt: {when}")
        if not occasion.is_absolute:
            lines.append(f"Din alder: {occasion.age_text(profile, lang)}")
        lines.append(f"Stjernedato: {sd.format_both(occasion.when_local)}")
        if occasion.is_estimate:
            lines.append("")
            lines.append("⚠ Skøn — bygger på en gennemsnitssats, ikke en måling.")
        if profile.time_is_approximate:
            lines.append("")
            lines.append("⚠ Fødselstidspunktet er omtrentligt, så klokkeslættet er det også.")
    else:
        lines.append(f"Exact moment: {when}")
        if not occasion.is_absolute:
            lines.append(f"Your age: {occasion.age_text(profile, lang)}")
        lines.append(f"Stardate: {sd.format_both(occasion.when_local)}")
        if occasion.is_estimate:
            lines.append("")
            lines.append("⚠ Estimate — based on an average rate, not a measurement.")
        if profile.time_is_approximate:
            lines.append("")
            lines.append("⚠ The birth time is approximate, so the clock time is too.")

    return "\n".join(lines)


def build_ics(
    occasions: list[Occasion],
    profile: Profile,
    lang: str = "da",
    all_day: bool = False,
    duration_minutes: int = 15,
    alarm_days_before: int | None = 1,
    alarm_hours_before: int | None = 1,
    calendar_name: str | None = None,
) -> str:
    """Hele kalenderen som én .ics-tekst."""
    now = datetime.now(timezone.utc)
    default_name = "Nørdilæum" if lang == "da" else "Nerdiversary"
    name = calendar_name or (
        f"{profile.name.strip()} — {default_name}" if profile.name.strip() else default_name
    )

    lines: list[str] = [
        "BEGIN:VCALENDAR",
        "VERSION:2.0",
        f"PRODID:{PRODID}",
        "CALSCALE:GREGORIAN",
        "METHOD:PUBLISH",
        f"X-WR-CALNAME:{_escape(name)}",
        f"X-WR-TIMEZONE:{profile.tz.key}",
    ]

    for occasion in occasions:
        lines.append("BEGIN:VEVENT")
        lines.append(f"UID:{_uid(profile, occasion)}")
        lines.append(f"DTSTAMP:{_stamp(now)}")

        if all_day:
            start_date = occasion.when_local.date()
            end_date = start_date + timedelta(days=1)
            lines.append(f"DTSTART;VALUE=DATE:{start_date.strftime('%Y%m%d')}")
            lines.append(f"DTEND;VALUE=DATE:{end_date.strftime('%Y%m%d')}")
        else:
            end = occasion.when_utc + timedelta(minutes=duration_minutes)
            lines.append(f"DTSTART:{_stamp(occasion.when_utc)}")
            lines.append(f"DTEND:{_stamp(end)}")

        lines.append(f"SUMMARY:{_escape(event_title(occasion, profile, lang))}")
        lines.append(f"DESCRIPTION:{_escape(event_description(occasion, profile, lang))}")
        lines.append(f"CATEGORIES:{_escape(occasion.group.name(lang))}")
        lines.append("TRANSP:TRANSPARENT")

        for trigger, enabled in (
            (f"-P{alarm_days_before}D", alarm_days_before),
            (f"-PT{alarm_hours_before}H", alarm_hours_before),
        ):
            if not enabled:
                continue
            lines.append("BEGIN:VALARM")
            lines.append("ACTION:DISPLAY")
            lines.append(f"TRIGGER:{trigger}")
            lines.append(f"DESCRIPTION:{_escape(event_title(occasion, profile, lang))}")
            lines.append("END:VALARM")

        lines.append("END:VEVENT")

    lines.append("END:VCALENDAR")
    return "\r\n".join(_fold(line) for line in lines) + "\r\n"


# -------------------------------------------------------------------------
# Google Calendar CSV
# -------------------------------------------------------------------------

GOOGLE_CSV_HEADER = [
    "Subject",
    "Start Date",
    "Start Time",
    "End Date",
    "End Time",
    "All Day Event",
    "Description",
    "Location",
    "Private",
]


def build_google_csv(
    occasions: list[Occasion],
    profile: Profile,
    lang: str = "da",
    all_day: bool = False,
    duration_minutes: int = 15,
) -> str:
    """CSV i det format, Google Calendars importfunktion forventer.

    Google kraever amerikansk datoformat (MM/DD/YYYY) og 12-timers klokkeslaet
    uanset brugerens egne indstillinger.
    """
    buffer = io.StringIO()
    writer = csv.writer(buffer, lineterminator="\r\n")
    writer.writerow(GOOGLE_CSV_HEADER)

    for occasion in occasions:
        start = occasion.when_local
        end = start + timedelta(minutes=duration_minutes)
        writer.writerow(
            [
                event_title(occasion, profile, lang),
                start.strftime("%m/%d/%Y"),
                "" if all_day else start.strftime("%I:%M %p").lstrip("0"),
                end.strftime("%m/%d/%Y"),
                "" if all_day else end.strftime("%I:%M %p").lstrip("0"),
                "True" if all_day else "False",
                event_description(occasion, profile, lang).replace("\n", " "),
                "",
                "False",
            ]
        )

    return buffer.getvalue()


# -------------------------------------------------------------------------
# Direkte link til Google Calendar
# -------------------------------------------------------------------------


def google_calendar_link(
    occasion: Occasion,
    profile: Profile,
    lang: str = "da",
    duration_minutes: int = 15,
) -> str:
    """Et "tilføj til Google Kalender"-link til én begivenhed."""
    start = occasion.when_utc
    end = start + timedelta(minutes=duration_minutes)
    params = {
        "action": "TEMPLATE",
        "text": event_title(occasion, profile, lang),
        "dates": f"{_stamp(start)}/{_stamp(end)}",
        "details": event_description(occasion, profile, lang),
        "ctz": profile.tz.key,
    }
    return f"{GOOGLE_RENDER_URL}?{urlencode(params)}"


def suggested_filename(profile: Profile, lang: str, extension: str) -> str:
    """Et filnavn, der ikke generer noget filsystem."""
    stem = "noerdilaeum" if lang == "da" else "nerdiversary"
    who = "".join(
        char for char in profile.name.strip().lower() if char.isalnum() or char in "-_"
    )
    if who:
        stem = f"{stem}-{who}"
    return f"{stem}.{extension}"
