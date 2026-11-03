"""Skudsekunder — de ekstra sekunder, der holder urene i takt med Jorden.

Jordens rotation er ikke helt regelmaessig: tidevandet bremser den, og store
jordskaelv og massebevaegelser i kernen rykker en anelse paa doegnets laengde.
Atomurene er derimod ubevaegelige. For at UTC ikke skal loebe fra solen,
indsaetter IERS i Paris af og til et ekstra sekund — 23:59:60 — sidst paa en
juni- eller decemberdag.

Alle 27 skudsekunder siden 1972 har vaeret positive. Det seneste blev indsat
31. december 2016, og IERS Bulletin C 72 (6. juli 2026) bekraeftede, at der
heller ikke kommer et ved udgangen af 2026. Det er den laengste pause i hele
raekken.
"""

from __future__ import annotations

from datetime import date, datetime, timezone

# Datoer hvor et positivt skudsekund blev indsat som 23:59:60 UTC.
# Kilde: IERS Bulletin C / USNO. 27 i alt, alle positive.
LEAP_SECOND_DATES: tuple[date, ...] = (
    date(1972, 6, 30),
    date(1972, 12, 31),
    date(1973, 12, 31),
    date(1974, 12, 31),
    date(1975, 12, 31),
    date(1976, 12, 31),
    date(1977, 12, 31),
    date(1978, 12, 31),
    date(1979, 12, 31),
    date(1981, 6, 30),
    date(1982, 6, 30),
    date(1983, 6, 30),
    date(1985, 6, 30),
    date(1987, 12, 31),
    date(1989, 12, 31),
    date(1990, 12, 31),
    date(1992, 6, 30),
    date(1993, 6, 30),
    date(1994, 6, 30),
    date(1995, 12, 31),
    date(1997, 6, 30),
    date(1998, 12, 31),
    date(2005, 12, 31),
    date(2008, 12, 31),
    date(2012, 6, 30),
    date(2015, 6, 30),
    date(2016, 12, 31),
)

# UTC blev indfoert i sin nuvaerende form 1. januar 1972 med TAI-UTC = 10 s.
UTC_EPOCH = datetime(1972, 1, 1, tzinfo=timezone.utc)
TAI_UTC_AT_EPOCH = 10


def _insertion_instant(day: date) -> datetime:
    """Skudsekundet ligger i doegnets sidste sekund, altsaa lige foer midnat."""
    return datetime(day.year, day.month, day.day, 23, 59, 59, tzinfo=timezone.utc)


def leap_seconds_between(start: datetime, end: datetime) -> int:
    """Antal skudsekunder indsat i intervallet (start, end]."""
    if end <= start:
        return 0
    return sum(1 for day in LEAP_SECOND_DATES if start < _insertion_instant(day) <= end)


def leap_seconds_since_birth(birth_utc: datetime, now_utc: datetime) -> int:
    """Hvor mange ekstra sekunder verdens ure har faaet, siden du blev foedt."""
    return leap_seconds_between(birth_utc, now_utc)


def tai_minus_utc(moment: datetime) -> int | None:
    """Forskellen mellem atomtid og UTC paa et givet tidspunkt, i sekunder.

    Returnerer None for tidspunkter foer 1972, hvor UTC endnu ikke koerte med
    hele skudsekunder.
    """
    if moment < UTC_EPOCH:
        return None
    return TAI_UTC_AT_EPOCH + leap_seconds_between(UTC_EPOCH, moment)


def born_before_utc(birth_utc: datetime) -> bool:
    """Sandt hvis foedslen ligger foer UTC fik skudsekunder (1. januar 1972)."""
    return birth_utc < UTC_EPOCH


TOTAL_LEAP_SECONDS = len(LEAP_SECOND_DATES)
LAST_LEAP_SECOND = LEAP_SECOND_DATES[-1]
