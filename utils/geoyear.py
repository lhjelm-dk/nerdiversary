"""Jordens historie lagt ned i ét kalenderaar.

Den anden maade at gribe dyb tid an paa. ``utils.geology`` klemmer de 4,54
milliarder aar ned i *dit* liv, saa svaret afhaenger af, hvornaar du er foedt,
og hvor laenge du regner med at vaere her. Her klemmes de ned i et aar, som
alle har det samme af: 1. januar er Jordens dannelse, og 31. december er nu.

Det er den version, der kan siges til et middagsbord uden forbehold.
Dinosaurerne doer anden juledag. Hele den menneskelige civilisation ligger i
de sidste halvfems sekunder foer nytaar.

Regnestykket er det samme som i ``utils.geology`` — en lineaer skala — bare
med 365 dage i stedet for en levetid:

    forloebet andel = (4540 - alder_i_mio_aar) / 4540
    dag i aaret     = loft(andel * 365)

Der regnes paa 365 dage og ikke 365,2425. Et skudaar ville flytte
graenserne et doegn hid og did, og pointen er ikke at ramme sekundet — den er,
at Kridttiden slutter i julen.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, timedelta

from .catalog import Milestone
from .geology import GEO_EVENTS, GeoEvent
from .units import EARTH_AGE_MA

# Noeglerne faar samme forstavelse som de oevrige festdage.
PREFIX = "cel_"

# Aaret, der regnes i. Et almindeligt aar, saa den 29. februar aldrig kan
# dukke op som en geologisk graense.
DAYS_IN_YEAR = 365
_REFERENCE_YEAR = 2001          # Et ikke-skudaar. Bruges kun til at finde maaned og dag.


@dataclass(frozen=True)
class YearPoint:
    """Et punkt i Jordens historie, oversat til en dato i kalenderaaret."""

    event: GeoEvent
    day_of_year: int

    @property
    def month(self) -> int:
        return self.as_date().month

    @property
    def day(self) -> int:
        return self.as_date().day

    def as_date(self) -> date:
        return date(_REFERENCE_YEAR, 1, 1) + timedelta(days=self.day_of_year - 1)

    @property
    def when(self) -> str:
        """Datoangivelsen, ``utils.celebrations`` kan laese."""
        return f"{self.month:02d}-{self.day:02d}"

    @property
    def days_left(self) -> int:
        """Hvor mange dage af aaret der er tilbage, naar graensen falder."""
        return DAYS_IN_YEAR - self.day_of_year


def day_of_year(start_ma: float, days: int = DAYS_IN_YEAR) -> int:
    """Dagen i aaret, hvor ``start_ma`` millioner aar siden falder.

    1. januar er dannelsen, den sidste dag er nu. Der rundes op, saa et punkt,
    der ligger inde i et doegn, hoerer til det doegn — og saa selve dannelsen
    lander paa dag 1 og ikke paa dag 0.
    """
    elapsed = (EARTH_AGE_MA - start_ma) / EARTH_AGE_MA
    return min(days, max(1, math.ceil(elapsed * days)))


def year_points() -> tuple[YearPoint, ...]:
    """Alle graenser i ``utils.geology``, oversat til datoer i aaret."""
    return tuple(
        YearPoint(event, day_of_year(event.start_ma)) for event in GEO_EVENTS
    )


def _span(point: YearPoint, lang: str) -> str:
    """"med 5 dage af aaret tilbage" — eller "med 81 sekunder af aaret tilbage".

    Hele pointen i skalaen er, hvor lidt plads det kendte faar. Civilisationen
    fylder under to minutter af aaret, og det kan kun siges, hvis enheden
    foelger med ned. Derfor skifter den fra dage til timer til minutter til
    sekunder, naar tallet bliver for lille at sige i dage.
    """
    seconds = point.event.start_ma / EARTH_AGE_MA * DAYS_IN_YEAR * 86_400

    if seconds >= 2 * 86_400:
        value, words = round(seconds / 86_400), ("dage", "days")
    elif seconds >= 2 * 3_600:
        value, words = round(seconds / 3_600), ("timer", "hours")
    elif seconds >= 120:
        value, words = round(seconds / 60), ("minutter", "minutes")
    else:
        value, words = round(seconds), ("sekunder", "seconds")

    if lang == "da":
        return f"med {value} {words[0]} af året tilbage"
    return f"with {value} {words[1]} of the year left"


def geoyear_milestones() -> tuple[Milestone, ...]:
    """Jordens historie som aarligt tilbagevendende maerkedage.

    Hver geologisk graense bliver en dato, der kommer igen hvert aar — for i
    denne udgave er skalaen kalenderen, ikke et liv. Derfor er de ``annual``
    og ikke ``geo_ma``.
    """
    out: list[Milestone] = []
    for point in year_points():
        event = point.event
        out.append(
            Milestone(
                key=f"{PREFIX}geoyear_{event.key}",
                group="geoyear",
                unit="annual",
                amount=0.0,
                when=point.when,
                label_da=f"{event.emoji} {event.name('da')} — i Jordens år",
                label_en=f"{event.emoji} {event.name('en')} — in Earth's year",
                why_da=(
                    f"Hvis 1. januar var Jordens dannelse og 31. december var i dag, "
                    f"faldt dette på dag {point.day_of_year} af 365, "
                    f"{_span(point, 'da')}. "
                    f"{event.description('da')}"
                ),
                why_en=(
                    f"If 1 January were the formation of the Earth and 31 December "
                    f"were today, this would land on day {point.day_of_year} of 365, "
                    f"{_span(point, 'en')}. "
                    f"{event.description('en')}"
                ),
            )
        )
    return tuple(out)
