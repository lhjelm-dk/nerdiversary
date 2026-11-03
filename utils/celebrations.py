"""Festdage, der ligger paa kalenderen i stedet for i dit liv.

Resten af kataloget regner fremad fra foedselsoejeblikket: et gigasekund,
10.000 doegn, 1.000 maaneder. Her er det omvendt. Dagene ligger fast paa
kalenderen — den 4. maj, den 11.11., den foerste fredag i november — og det
personlige er, hvor gammel du er, naar de falder.

Dagene staar ikke i koden, men i ``data/celebrations/*.json``, én fil pr.
kategori. ``load_days()`` laeser mappen igennem, tjekker hver post og
sorterer den ind i sin gruppe. En post, der ikke kan laeses, bliver ikke
stiltiende tabt: den lander i ``Import.skipped`` med en grund, saa en
tastefejl i en datafil er til at finde. Det er ogsaa dér, en dato som
aar 802.701 ender — den slags kan en kalender ikke regne paa.

Fire slags datoangivelser:

====================== ==================================================
``"05-04"``            hvert aar den 4. maj
``"11-05 20:59"``      hvert aar, paa klokkeslaettet
``"nth:11:fri:1"``     den foerste fredag i november (``-1`` = den sidste)
``"1969-07-21"``       én gang, den dag
``"1955-11-12 22:04"`` én gang, paa minuttet
====================== ==================================================

De tilbagevendende dage vises som den naeste gang, de falder. Alt andet ville
drukne kalenderen: hver aarlig dag ville ellers optraede hundrede gange i et
menneskeliv.

Oven paa filerne ligger de dage, ingen har skrevet ned, fordi en regel finder
dem — palindromer, sekvenser, pythagoraeiske dage. De bor i
``utils.datepatterns``, og ``celebration_milestones()`` laegger de to kilder
sammen. Det er det skarpe snit i hele dette hjoerne af programmet: en dag er
enten *bestemt* af et menneske og staar i en fil, eller *fundet* af en regel
og staar i kode.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import date, timedelta
from functools import lru_cache
from pathlib import Path

from .catalog import GROUPS_BY_KEY, Milestone
from .datepatterns import PREFIX, pattern_milestones
from .geoyear import geoyear_milestones

DATA_DIR = Path(__file__).resolve().parent.parent / "data" / "celebrations"

_WEEKDAYS: dict[str, int] = {
    "mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6,
}

# Den korte forklaring, en post faar, naar den ikke har skrevet sin egen. Det
# er dét, der goer det overkommeligt at have hundredvis af udgivelsesdatoer:
# titlen og mediet er nok, resten siger datoen selv.
_MEDIUM_WHY: dict[str, tuple[str, str]] = {
    "film": ("Biografpremieren.", "The day it hit cinemas."),
    "tv": ("Den første udsendelse.", "The first broadcast."),
    "book": ("Udgivelsesdagen.", "The day it was published."),
    "comic": ("Den første optræden på tryk.", "The first appearance in print."),
    "game": ("Udgivelsesdagen.", "The day it was released."),
    "tech": ("Dagen den kom på markedet.", "The day it went on sale."),
    "event": ("Det skete den dag.", "It happened on this day."),
}


class SpecError(ValueError):
    """En datoangivelse, der ikke kan laeses."""


@dataclass(frozen=True)
class DaySpec:
    """En datoangivelse, oversat til noget, der kan regnes paa.

    ``kind`` er ``"annual"`` (samme dato hvert aar), ``"nth"`` (den n'te
    ugedag i en maaned) eller ``"once"`` (én bestemt dag i historien).
    """

    kind: str
    month: int
    day: int = 0
    year: int = 0
    weekday: int = -1
    nth: int = 0
    hour: int = 0
    minute: int = 0

    @property
    def recurring(self) -> bool:
        return self.kind != "once"

    @property
    def unit(self) -> str:
        """Enheden, maerkedagen skal regnes med i ``utils.engine``."""
        return "annual" if self.recurring else "date_abs"


@lru_cache(maxsize=None)
def parse_spec(text: str) -> DaySpec:
    """Laes en datoangivelse. Rejser ``SpecError``, hvis den ikke giver mening.

    Resultatet bliver husket, fordi motoren slaar den samme angivelse op igen
    for hver udregning.
    """
    if not isinstance(text, str) or not text.strip():
        raise SpecError("datoen mangler")

    body, _, clock = text.strip().partition(" ")
    hour = minute = 0
    if clock.strip():
        pieces = clock.strip().split(":")
        if len(pieces) != 2 or not all(piece.isdigit() for piece in pieces):
            raise SpecError(f"ulæseligt klokkeslæt i {text!r}")
        hour, minute = int(pieces[0]), int(pieces[1])
        if not (0 <= hour < 24 and 0 <= minute < 60):
            raise SpecError(f"klokkeslættet findes ikke i {text!r}")

    if body.startswith("nth:"):
        pieces = body.split(":")
        if len(pieces) != 4:
            raise SpecError(f"en nth-regel skal se ud som nth:11:fri:1, ikke {text!r}")
        _, month_text, weekday_text, nth_text = pieces
        weekday = _WEEKDAYS.get(weekday_text.lower(), -1)
        if weekday < 0:
            raise SpecError(f"ukendt ugedag {weekday_text!r} i {text!r}")
        month = _as_int(month_text, text)
        nth = _as_int(nth_text, text)
        if not 1 <= month <= 12:
            raise SpecError(f"måneden findes ikke i {text!r}")
        if not -5 <= nth <= 5 or nth == 0:
            raise SpecError(f"{nth} er ikke en brugbar ugedag i måneden ({text!r})")
        return DaySpec("nth", month, weekday=weekday, nth=nth, hour=hour, minute=minute)

    fields = body.split("-")
    if len(fields) == 2:
        month, day = (_as_int(field, text) for field in fields)
        # Skudddagen skal kunne staa i en datafil, selv om den ikke findes
        # hvert aar. Derfor proeves datoen af paa et skudaar.
        _valid_day(2000, month, day, text)
        return DaySpec("annual", month, day=day, hour=hour, minute=minute)

    if len(fields) == 3:
        year, month, day = (_as_int(field, text) for field in fields)
        if not date.min.year <= year <= date.max.year:
            raise SpecError(f"året {year} ligger uden for en kalender ({text!r})")
        _valid_day(year, month, day, text)
        return DaySpec("once", month, day=day, year=year, hour=hour, minute=minute)

    raise SpecError(f"{text!r} er hverken MM-DD, ÅÅÅÅ-MM-DD eller en nth-regel")


def _as_int(text: str, whole: str) -> int:
    stripped = text.strip()
    sign = -1 if stripped.startswith("-") else 1
    digits = stripped[1:] if stripped[0] in "+-" else stripped
    if not digits.isdigit():
        raise SpecError(f"{text!r} er ikke et tal ({whole!r})")
    return sign * int(digits)


def _valid_day(year: int, month: int, day: int, whole: str) -> None:
    try:
        date(year, month, day)
    except ValueError as exc:
        raise SpecError(f"{whole!r} er ikke en dato: {exc}") from exc


def spec_in_year(spec: DaySpec, year: int) -> date | None:
    """Den dag, angivelsen falder paa i ``year`` — eller None, hvis den ikke goer.

    Den 29. februar findes kun i skudaar, og "den femte mandag" findes ikke i
    alle maaneder. Begge svarer None, saa den, der spoerger, kan gaa videre
    til naeste aar i stedet for at falde over en undtagelse.
    """
    if spec.kind == "once":
        return date(spec.year, spec.month, spec.day) if year == spec.year else None

    if spec.kind == "annual":
        try:
            return date(year, spec.month, spec.day)
        except ValueError:
            return None

    first = date(year, spec.month, 1)
    if spec.nth > 0:
        shift = (spec.weekday - first.weekday()) % 7
        day = 1 + shift + (spec.nth - 1) * 7
    else:
        next_month = date(year + spec.month // 12, spec.month % 12 + 1, 1)
        last = next_month - timedelta(days=1)
        shift = (last.weekday() - spec.weekday) % 7
        day = last.day - shift + (spec.nth + 1) * 7
    try:
        return date(year, spec.month, day)
    except ValueError:
        return None


# -------------------------------------------------------------------------
# Indlaesningen
# -------------------------------------------------------------------------


@dataclass(frozen=True)
class Skipped:
    """En post, der blev sprunget over, og hvorfor."""

    source: str
    key: str
    reason: str


@dataclass(frozen=True)
class Import:
    """Resultatet af at laese datamappen igennem."""

    milestones: tuple[Milestone, ...]
    skipped: tuple[Skipped, ...]

    def by_group(self) -> dict[str, int]:
        counts: dict[str, int] = {}
        for milestone in self.milestones:
            counts[milestone.group] = counts.get(milestone.group, 0) + 1
        return counts


def _names(entry: dict) -> tuple[str, str]:
    """Navnet paa dansk og engelsk.

    De fleste poster er titler, der ikke bliver oversat — *DOOM* hedder DOOM
    paa begge sprog. Derfor kan en post slippe med ét ``name``.
    """
    shared = str(entry.get("name", "")).strip()
    da = str(entry.get("da", "")).strip() or shared
    en = str(entry.get("en", "")).strip() or shared
    if not da or not en:
        raise SpecError("posten mangler et navn")
    return da, en


def format_note(spec: DaySpec) -> tuple[str, str]:
    """Noten om datoformat: kan dagen forveksles med en amerikansk laesning?

    05.04 er den 4. maj i dansk raekkefoelge og den 5. april i amerikansk. Det
    er en reel faelde i en kalender, der er samlet fra engelske kilder, saa de
    datoer, der *kan* forveksles, siger det selv — og de faa, der staar ens i
    begge raekkefoelger, siger ogsaa det.

    En dato med en dag over den tolvte kan ikke laeses forkert, og saa staar
    der ingenting. Det er flertallet, og en note paa dem alle ville kun stoeje.
    """
    if spec.kind == "nth":
        return "", ""        # "foerste fredag i november" kan ikke vendes om.

    day, month = spec.day, spec.month
    written = f"{day:02d}.{month:02d}"

    if day == month:
        return (
            f" {written} står ens i dansk og amerikansk rækkefølge.",
            f" {written} reads the same in day-first and month-first order.",
        )
    if day > 12:
        return "", ""        # Der er ingen 13. maaned, saa den kan kun laeses én vej.
    return (
        f" Pas på formatet: {written} er den {day}. i {month}. måned her, men "
        f"den {month}. i {day}. måned i amerikansk rækkefølge — to forskellige dage.",
        f" Mind the format: {written} is day {day} of month {month} here, but "
        f"day {month} of month {day} in month-first order — two different days.",
    )


def _why(entry: dict) -> tuple[str, str]:
    """Forklaringen: den skrevne, ellers den mediet giver."""
    da = str(entry.get("why_da", "")).strip()
    en = str(entry.get("why_en", "")).strip()
    if da and en:
        return da, en
    medium = str(entry.get("medium", "")).strip().lower()
    fallback = _MEDIUM_WHY.get(medium, ("", ""))
    return da or fallback[0], en or fallback[1]


def _milestone(group: str, entry: dict, source: str) -> Milestone:
    """Lav én post om til en maerkedag. Rejser ``SpecError`` paa alt skaevt."""
    if not isinstance(entry, dict):
        raise SpecError("posten er ikke et objekt")

    key = str(entry.get("key", "")).strip()
    if not key:
        raise SpecError("posten mangler en nøgle")

    spec = parse_spec(str(entry.get("when", "")))
    da, en = _names(entry)
    why_da, why_en = _why(entry)
    note_da, note_en = format_note(spec)
    why_da, why_en = why_da + note_da, why_en + note_en

    # Vaerket staar i etiketten, naar der er et: "Towel Day (Hitchhiker's
    # Guide)". Det er den oplysning, man leder efter paa en fiktiv helligdag.
    work = str(entry.get("work", "")).strip()
    if work:
        da = f"{da} · {work}"
        en = f"{en} · {work}"

    return Milestone(
        key=f"{PREFIX}{key}",
        group=group,
        unit=spec.unit,
        amount=0.0,
        when=str(entry.get("when", "")).strip(),
        label_da=da,
        label_en=en,
        why_da=why_da,
        why_en=why_en,
    )


def load_dir(directory: Path | str = DATA_DIR) -> Import:
    """Laes alle datafiler i en mappe og sortér posterne i deres grupper.

    Filerne laeses i navneorden, saa to koersler giver samme resultat. En fil
    med en ukendt gruppe bliver sprunget over som helhed — det er bedre end at
    lade hundrede poster ende i en gruppe, appen ikke kender.
    """
    folder = Path(directory)
    found: dict[str, Milestone] = {}
    skipped: list[Skipped] = []

    if not folder.is_dir():
        return Import((), (Skipped(str(folder), "—", "mappen findes ikke"),))

    for path in sorted(folder.glob("*.json")):
        try:
            payload = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError) as exc:
            skipped.append(Skipped(path.name, "—", f"filen kunne ikke læses: {exc}"))
            continue

        group = str(payload.get("group", "")).strip()
        if group not in GROUPS_BY_KEY:
            skipped.append(Skipped(path.name, "—", f"ukendt gruppe {group!r}"))
            continue

        for entry in payload.get("days", []):
            key = str(entry.get("key", "")).strip() if isinstance(entry, dict) else "—"
            try:
                milestone = _milestone(group, entry, path.name)
            except SpecError as exc:
                skipped.append(Skipped(path.name, key or "—", str(exc)))
                continue
            if milestone.key in found:
                skipped.append(Skipped(path.name, key, "nøglen er brugt to gange"))
                continue
            found[milestone.key] = milestone

    return Import(tuple(found.values()), tuple(skipped))


@lru_cache(maxsize=1)
def load_days() -> Import:
    """Som ``load_dir``, men kun én gang pr. koersel."""
    return load_dir()


@lru_cache(maxsize=1)
def celebration_milestones() -> tuple[Milestone, ...]:
    """Alle festdage: de skrevne fra filerne og de udregnede fra reglerne.

    Det er dén, ``utils.engine`` kalder. Den bliver husket, fordi hele
    kataloget bliver slaaet op igen for hver eneste udregning.
    """
    return load_days().milestones + pattern_milestones() + geoyear_milestones()

