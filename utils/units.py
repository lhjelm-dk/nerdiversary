"""Enheder, naturkonstanter og omregning til sekunder.

Alt det, der kan udtrykkes som "et fast antal sekunder efter foedselsoejeblikket",
samles her. Kalenderbaserede enheder (maaneder og aar) haandteres i engine.py,
fordi de skal regnes paa vaegurets tid og ikke paa SI-sekunder.
"""

from __future__ import annotations

# --- Tid -----------------------------------------------------------------

TROPICAL_YEAR_DAYS = 365.242190      # Aarstidernes aar. Bruges til "x aar gammel" i broekdele.
JULIAN_YEAR_DAYS = 365.25            # Definitionen bag lysaaret.
GREGORIAN_YEAR_DAYS = 365.2425       # Kalenderens middelaar.
SYNODIC_MONTH_DAYS = 29.530588853    # Nymaane til nymaane.

# --- Fysik ---------------------------------------------------------------

LIGHT_SPEED_KMS = 299_792.458                    # Lysets fart i vakuum, km/s.
LIGHT_SPEED_MS = 299_792_458                     # ... og i m/s (definitionen af metren).
CS133_PERIODS_PER_SECOND = 9_192_631_770         # SI-definitionen af ét sekund.
C14_HALF_LIFE_YEARS = 5730.0                     # Kulstof-14's halveringstid (Cambridge-vaerdien).
JIFFY_SECONDS = 0.01 / LIGHT_SPEED_MS            # Lysets tid over 1 cm = 33,356 ps.
EARTH_ORBITAL_SPEED_KMS = 29.7859                # Jordens middelfart om Solen.
LIGHT_HOUR_KM = LIGHT_SPEED_KMS * 3600           # 1.079.252.848,8 km
LIGHT_DAY_KM = LIGHT_SPEED_KMS * 86400           # 25.902.068.371,2 km

# --- Jordens alder -------------------------------------------------------

EARTH_AGE_MA = 4540.0                # Jordens alder i millioner aar (ICS/IUGS).

# --- Graenser ------------------------------------------------------------

MAX_AGE_YEARS = 150                  # Vi regner ikke paa noget hinsides dette.
DEFAULT_LIFESPAN_YEARS = 100         # Bruges til den geologiske skala.

# --- Sekunder pr. enhed --------------------------------------------------
#
# Enheder, hvor én enhed er et fast antal SI-sekunder. Alt andet (kalender-
# maaneder, kalenderaar, satsbaserede og absolutte enheder) haandteres saerskilt.

SECONDS_PER_UNIT: dict[str, float] = {
    "sec": 1.0,
    "min": 60.0,
    "hour": 3600.0,
    "day": 86_400.0,
    "week": 604_800.0,
    "trop_year": TROPICAL_YEAR_DAYS * 86_400.0,
    "julian_year": JULIAN_YEAR_DAYS * 86_400.0,
    "lunation": SYNODIC_MONTH_DAYS * 86_400.0,
    "cs133": 1.0 / CS133_PERIODS_PER_SECOND,
    "jiffy": JIFFY_SECONDS,
    "orbit_km": 1.0 / EARTH_ORBITAL_SPEED_KMS,
}

# Enheder regnet paa kalenderen, ikke paa sekunder.
CALENDAR_UNITS = frozenset({"cal_month", "cal_year"})

# Enheder, hvor brugeren selv saetter satsen (slag i minuttet osv.).
RATE_UNITS = frozenset({"heartbeat", "breath", "sleep_hour", "meal", "step"})

# Enheder, der ikke maales fra foedslen.
ABSOLUTE_UNITS = frozenset({"unix_abs"})

# Festdage, der ligger paa kalenderen i stedet for et antal enheder fra
# foedslen. ``annual`` falder igen hvert aar; ``date_abs`` er én bestemt dag i
# historien. Datoen staar i ``Milestone.when`` (se ``utils.celebrations``).
CALENDAR_DAY_UNITS = frozenset({"annual", "date_abs"})

# Enheder, der peger paa ét oejeblik i historien og derfor kun hoerer med,
# hvis det oejeblik faktisk falder inden for et menneskeliv.
ONE_OFF_UNITS = ABSOLUTE_UNITS | frozenset({"date_abs"})

# Enheder, der kraever to foedselsoejeblikke. De regnes i engine.py, fordi de
# afhaenger af forholdet mellem to tidspunkter og ikke af et antal sekunder.
PAIR_UNITS = frozenset(
    {"pair_ratio", "pair_sum_sec", "pair_sum_day", "pair_sum_year"}
)

# Enheder, der skaleres efter den forventede levetid.
LIFESPAN_UNITS = frozenset({"geo_ma", "pct_life"})

# Enheder hvis resultat er et skoen og derfor maerkes med en advarsel.
ESTIMATE_UNITS = frozenset({"lunation", "orbit_km", "geo_ma"}) | RATE_UNITS


def unit_seconds(unit: str) -> float:
    """Antal SI-sekunder i én enhed. Rejser KeyError for kalenderenheder."""
    return SECONDS_PER_UNIT[unit]
