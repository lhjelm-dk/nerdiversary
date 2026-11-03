"""Stjernedatoer / stardates.

Der findes ingen officiel omregning. Paramount har aldrig udgivet en formel,
og i The Original Series var stjernedatoerne aabenlyst tilfaeldige. To
konventioner har dog vundet haevd blandt fans, og begge er med her:

TNG-stil
    1000 stjernedato-enheder = ét aar, og stardate 41000.0 svarer til aar 2364
    (starten paa The Next Generation, saeson 1). Formlen er
    ``(aar - 2323) * 1000 + aarets broekdel * 1000``.
    For at nutidige datoer ikke skal give negative tal, laegger de fleste
    beregnere 340 aar til: 2026 behandles som 2366, saa du lander i 43xxx —
    midt i TNG-aeraen. Det er en konvention, ikke kanon.

Film-stil
    J.J. Abrams' film fra 2009 brugte ``AAAA.DDD``: aarstallet, punktum, og
    dagen i aaret. 2233.04 er altsaa 4. januar 2233. Den er utvetydig og
    kraever ingen forskydning.
"""

from __future__ import annotations

from datetime import datetime

TNG_EPOCH_YEAR = 2323          # Stardate 0.0 i TNG-formlen.
TNG_REFERENCE_STARDATE = 41000.0
TNG_REFERENCE_YEAR = 2364      # ... svarer til dette aar.
TREK_YEAR_OFFSET = 340         # Konventionen, der flytter nutiden ind i TNG-aeraen.


def _year_fraction(moment: datetime) -> float:
    """Hvor langt inde i aaret vi er, som tal mellem 0 og 1."""
    year_start = moment.replace(
        month=1, day=1, hour=0, minute=0, second=0, microsecond=0
    )
    next_year_start = year_start.replace(year=moment.year + 1)
    return (moment - year_start).total_seconds() / (
        next_year_start - year_start
    ).total_seconds()


def to_tng_stardate(moment: datetime, offset_years: int = TREK_YEAR_OFFSET) -> float:
    """TNG-stil stjernedato, fx 43837.2.

    ``offset_years`` flytter den virkelige dato ind i Star Trek-aeraen. Saet
    den til 0 for at regne raat paa det virkelige aarstal (som giver et
    negativt tal for nutiden).
    """
    trek_year = moment.year + offset_years
    return (trek_year - TNG_EPOCH_YEAR) * 1000 + _year_fraction(moment) * 1000


def to_film_stardate(moment: datetime) -> str:
    """Film-stil stjernedato, fx "2026.306" — aar punktum dag i aaret."""
    return f"{moment.year}.{moment.timetuple().tm_yday:03d}"


def format_tng(moment: datetime, offset_years: int = TREK_YEAR_OFFSET) -> str:
    """TNG-stjernedato med én decimal, som den skrives i loggen."""
    return f"{to_tng_stardate(moment, offset_years):.1f}"


def format_both(moment: datetime, offset_years: int = TREK_YEAR_OFFSET) -> str:
    """Begge konventioner paa én linje."""
    return f"{format_tng(moment, offset_years)} (TNG) · {to_film_stardate(moment)} (film)"
