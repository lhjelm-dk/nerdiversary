"""Selve udregningen: fra foedselsoejeblik til en liste af maerkedage.

Princippet er, at alt regnes paa absolut tid i UTC og foerst oversaettes til
lokal tid til sidst. Det er derfor en 10.000-dages maerkedag kan have et
klokkeslaet, der ligger en time fra foedselstidspunktet: sommertiden har
flyttet vaegurets visning, ikke selve oejeblikket.

Undtagelsen er kalenderenhederne (maaneder og aar), som netop skal regnes paa
vaeguret: 1000 maaneder betyder "samme dag i maaneden, samme klokkeslaet".
"""

from __future__ import annotations

from collections.abc import Iterable
from dataclasses import dataclass, field
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo

from dateutil.relativedelta import relativedelta

from . import formatting as fmt
from . import stardate as sd
from .catalog import GROUPS_BY_KEY, MILESTONES, Bundle, Group, Milestone
from .celebrations import SpecError, celebration_milestones, parse_spec, spec_in_year
from .legends import legend_milestones
from .units import (
    CALENDAR_DAY_UNITS,
    EARTH_AGE_MA,
    GREGORIAN_YEAR_DAYS,
    MAX_AGE_YEARS,
    ONE_OFF_UNITS,
    PAIR_UNITS,
    SECONDS_PER_UNIT,
    TROPICAL_YEAR_DAYS,
)

UNIX_EPOCH = datetime(1970, 1, 1, tzinfo=timezone.utc)

# Ordet for hver enhed, som det staar i etiketten.
_UNIT_WORDS: dict[str, tuple[str, str]] = {
    # nøgle: (dansk, engelsk)
    "sec": ("sekunder", "seconds"),
    "min": ("minutter", "minutes"),
    "hour": ("timer", "hours"),
    "day": ("dage", "days"),
    "week": ("uger", "weeks"),
    "cal_month": ("måneder", "months"),
    "cal_year": ("år", "years"),
    "trop_year": ("år", "years"),
    "julian_year": ("lysår", "light-years"),
    "lunation": ("månemåneder", "lunar months"),
    "cs133": ("cæsiumperioder", "caesium periods"),
    "jiffy": ("jiffies", "jiffies"),
    "orbit_km": ("km rundt om Solen", "km around the Sun"),
    "heartbeat": ("hjerteslag", "heartbeats"),
    "breath": ("åndedrag", "breaths"),
    "sleep_hour": ("timers søvn", "hours asleep"),
    "meal": ("måltider", "meals"),
    "step": ("skridt", "steps"),
}

_SUPERSCRIPT = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")


@dataclass(frozen=True)
class Rates:
    """Satserne bag de skoennede maerkedage. Alle kan aendres i sidepanelet."""

    bpm: float = 70.0                    # Hjerteslag i minuttet.
    breaths_per_min: float = 16.0        # Aandedrag i minuttet.
    sleep_hours_per_day: float = 8.0     # Timers soevn i doegnet.
    meals_per_day: float = 3.0           # Maaltider i doegnet.
    steps_per_day: float = 7000.0        # Skridt i doegnet.


@dataclass(frozen=True)
class Profile:
    """Alt appen skal vide om personen."""

    birth_local: datetime                # Tidszonebevidst.
    name: str = ""
    lifespan_years: float = 100.0
    rates: Rates = field(default_factory=Rates)
    time_is_approximate: bool = False
    partner_birth: datetime | None = None   # Den anden person, hvis der er en.
    partner_name: str = ""

    @property
    def tz(self) -> ZoneInfo:
        tzinfo = self.birth_local.tzinfo
        assert tzinfo is not None, "birth_local skal være tidszonebevidst"
        return tzinfo  # type: ignore[return-value]

    @property
    def birth_utc(self) -> datetime:
        return self.birth_local.astimezone(timezone.utc)

    @property
    def unix_birth(self) -> float:
        return self.birth_utc.timestamp()

    @property
    def partner_utc(self) -> datetime | None:
        if self.partner_birth is None:
            return None
        return self.partner_birth.astimezone(timezone.utc)

    @property
    def has_partner(self) -> bool:
        return self.partner_birth is not None

    def age_gap(self) -> relativedelta | None:
        """Aldersforskellen, altid som et positivt tidsrum."""
        partner = self.partner_birth
        if partner is None:
            return None
        # Begge oversaettes til samme zone foerst. relativedelta regner paa
        # vaegurets felter, saa to forskellige zoner ville give et forkert svar.
        first, second = sorted((self.birth_local, partner))
        return relativedelta(second.astimezone(self.tz), first.astimezone(self.tz))

    def partner_is_younger(self) -> bool:
        """Sandt naar den anden er den yngste af de to (lighed taeller med)."""
        partner = self.partner_utc
        return partner is None or partner >= self.birth_utc


@dataclass(frozen=True)
class Occasion:
    """En udregnet maerkedag paa et konkret tidspunkt."""

    milestone: Milestone
    when_utc: datetime
    when_local: datetime
    label: str
    group: Group

    @property
    def is_estimate(self) -> bool:
        return self.milestone.estimate

    @property
    def is_absolute(self) -> bool:
        """Sandt for maerkedage, der gaelder hele planeten (Unix-tid)."""
        return self.milestone.unit == "unix_abs"

    def is_past(self, now: datetime) -> bool:
        return self.when_utc < now

    def age_at(self, profile: Profile) -> relativedelta:
        return relativedelta(self.when_local, profile.birth_local)

    def age_text(self, profile: Profile, lang: str) -> str:
        return fmt.fmt_relativedelta(self.age_at(profile), lang)

    def age_years(self, profile: Profile) -> float:
        seconds = (self.when_utc - profile.birth_utc).total_seconds()
        return seconds / (TROPICAL_YEAR_DAYS * 86_400)

    def stardate(self) -> str:
        return sd.format_tng(self.when_local)

    def countdown(self, now_local: datetime, lang: str) -> str:
        return fmt.fmt_countdown(self.when_local, now_local, lang)

    def seconds_from(self, moment: datetime) -> float:
        return (self.when_utc - moment).total_seconds()

    def progress(self, profile: Profile, now: datetime) -> float:
        """Hvor langt man er naaet mod maalet, som tal mellem 0 og 1."""
        start = profile.birth_utc if not self.is_absolute else UNIX_EPOCH
        total = (self.when_utc - start).total_seconds()
        if total <= 0:
            return 1.0
        return max(0.0, min(1.0, (now - start).total_seconds() / total))


# -------------------------------------------------------------------------
# Etiketter
# -------------------------------------------------------------------------


def fmt_big(amount: float, lang: str) -> str:
    """Store tal som 10¹⁸ eller 9,19 × 10¹⁸ i stedet for en mur af nuller."""
    if amount < 1e13:
        if amount == int(amount):
            return fmt.fmt_int(amount, lang)
        return fmt.fmt_num(amount, lang, 2)

    exponent = 0
    mantissa = float(amount)
    while mantissa >= 10:
        mantissa /= 10
        exponent += 1
    power = f"10{str(exponent).translate(_SUPERSCRIPT)}"
    if abs(mantissa - 1.0) < 1e-9:
        return power
    # Tre decimaler, men uden overfloedige nuller: 1,337 og 4 — ikke 1,34 og 4,00.
    text = fmt.fmt_num(mantissa, lang, 3)
    separator = "," if lang == "da" else "."
    if separator in text:
        text = text.rstrip("0").rstrip(separator)
    return f"{text} × {power}"


def _unit_word(unit: str, lang: str) -> str:
    words = _UNIT_WORDS.get(unit)
    if words is None:
        return unit
    return words[0] if lang == "da" else words[1]


_REPDIGIT = {"da": "Alle cifre er ens.", "en": "Every digit is the same."}
_PALINDROME = {
    "da": "En palindrom — læses ens begge veje.",
    "en": "A palindrome — it reads the same both ways.",
}


def _digit_pattern(amount: float, lang: str) -> str:
    """"Alle cifre er ens" eller "en palindrom", hvis tallet er en af delene."""
    if amount != int(amount) or amount < 100:
        return ""
    digits = str(int(amount))
    if len(set(digits)) == 1:
        return _REPDIGIT[lang]
    if digits == digits[::-1]:
        return _PALINDROME[lang]
    return ""


def _conversion(milestone: Milestone, lang: str) -> str:
    """Samme maengde udtrykt i en enhed, et menneske kan forholde sig til.

    1.000.000 minutter siger ingenting; 694 doegn siger noget.
    """
    unit, amount = milestone.unit, milestone.amount
    subject = f"{fmt_big(amount, lang)} {_unit_word(unit, lang)}"

    if unit == "cal_month":
        years, months = divmod(int(amount), 12)
        if lang == "da":
            tail = f" og {months} måneder" if months else ""
            return f"{subject} er {fmt.fmt_int(years, lang)} år{tail} på dagen."
        tail = f" and {months} months" if months else ""
        return f"{subject} is {fmt.fmt_int(years, lang)} years{tail} to the day."

    if unit == "cal_year":
        days = amount * GREGORIAN_YEAR_DAYS
        if lang == "da":
            return f"{subject} svarer til {fmt.fmt_int(days, lang)} døgn."
        return f"{subject} comes to {fmt.fmt_int(days, lang)} days."

    seconds = amount * SECONDS_PER_UNIT.get(unit, 0.0)
    if not seconds:
        return ""

    days = seconds / 86_400
    years = seconds / (TROPICAL_YEAR_DAYS * 86_400)

    def tidy(value: float) -> str:
        """Smaa tal med én decimal, store uden — 11,6 doegn, men 714 uger."""
        return fmt.fmt_num(value, lang, 1) if value < 100 else fmt.fmt_int(value, lang)

    if unit == "day":
        other = f"{tidy(amount / 7)} {'uger' if lang == 'da' else 'weeks'}"
    else:
        other = f"{tidy(days)} {'døgn' if lang == 'da' else 'days'}"

    # "eller 0,0 aar" hjaelper ingen — og for en maerkedag, der allerede er
    # maalt i aar, ville aarstallet bare gentage overskriften.
    if years < 0.095 or unit in {"trop_year", "julian_year"}:
        if lang == "da":
            return f"{subject} svarer til {other}."
        return f"{subject} comes to {other}."

    if lang == "da":
        return f"{subject} svarer til {other} eller {fmt.fmt_num(years, lang, 1)} år."
    return f"{subject} comes to {other}, or {fmt.fmt_num(years, lang, 1)} years."


def generated_note(milestone: Milestone, lang: str) -> str:
    """Den automatiske forklaring til de maerkedage, der ikke har en skrevet."""
    parts = [_digit_pattern(milestone.amount, lang), _conversion(milestone, lang)]
    return " ".join(part for part in parts if part)


def explanation(milestone: Milestone, lang: str) -> str:
    """Forklaringen, som appen viser: den skrevne, ellers den beregnede.

    De faa maerkedage, der med vilje skal staa uforklarede (5318008), er
    undtaget, saa de heller ikke faar en automatisk.
    """
    if milestone.silent:
        return ""
    written = milestone.why(lang)
    return written if written else generated_note(milestone, lang)


# Forholdet mellem to aldre, sat paa ord. Nøglen er multiplummet.
_RATIO_PHRASE: dict[float, tuple[str, str]] = {
    10.0: ("ti gange så gammel", "ten times as old"),
    5.0: ("fem gange så gammel", "five times as old"),
    4.0: ("fire gange så gammel", "four times as old"),
    3.0: ("tre gange så gammel", "three times as old"),
    2.0: ("dobbelt så gammel", "twice as old"),
    1.5: ("halvanden gang så gammel", "one and a half times as old"),
}

_SOMEONE = {"da": "den anden", "en": "the other"}


def _pair_label(milestone: Milestone, profile: Profile, lang: str) -> str:
    """Etiketten for en maerkedag, der kraever to foedselsdatoer.

    Forholdsmaerkedagene skal vendes om, naar det er den anden, der er
    aeldst: ellers ville der staa "dobbelt saa gammel som Emma" paa det
    oejeblik, hvor det er Emma, der er dobbelt saa gammel.
    """
    unit, amount = milestone.unit, milestone.amount
    other = profile.partner_name.strip() or _SOMEONE[lang]

    if unit == "pair_ratio":
        words = _RATIO_PHRASE.get(float(amount))
        if words is None:
            times = fmt.fmt_num(amount, lang, 1)
            words = (f"{times} gange så gammel", f"{times} times as old")
        phrase = words[0] if lang == "da" else words[1]
        if profile.partner_is_younger():
            return f"{phrase.capitalize()} som {other}" if lang == "da" else (
                f"{phrase.capitalize()} as {other}"
            )
        you = "dig" if lang == "da" else "you"
        return f"{other} {phrase} som {you}" if lang == "da" else (
            f"{other} {phrase} as {you}"
        )

    if unit == "pair_sum_day":
        total = f"{fmt.fmt_int(amount, lang)} døgn" if lang == "da" else (
            f"{fmt.fmt_int(amount, lang)} days"
        )
    elif unit == "pair_sum_year":
        total = f"{fmt.fmt_int(amount, lang)} år" if lang == "da" else (
            f"{fmt.fmt_int(amount, lang)} years"
        )
    else:
        total = f"{fmt_big(amount, lang)} sekunder" if lang == "da" else (
            f"{fmt_big(amount, lang)} seconds"
        )

    return f"Tilsammen {total}" if lang == "da" else f"{total} between you"


def build_label(milestone: Milestone, profile: Profile, lang: str) -> str:
    """Etiketten, maerkedagen vises under."""
    override = milestone.label_override(lang)
    if override:
        return override

    unit = milestone.unit
    amount = milestone.amount

    if unit in PAIR_UNITS:
        return _pair_label(milestone, profile, lang)

    if unit == "pct_life":
        pct = fmt.fmt_num(amount * 100, lang, 2).rstrip("0").rstrip(",").rstrip(".")
        years = fmt.fmt_int(profile.lifespan_years, lang)
        if lang == "da":
            return f"{pct} % af et liv på {years} år"
        return f"{pct}% of a {years}-year life"

    if unit in {"cs133", "jiffy"}:
        return f"{fmt_big(amount, lang)} {_unit_word(unit, lang)}"

    if unit in {"trop_year", "cal_year"}:
        number = (
            fmt.fmt_int(amount, lang)
            if float(amount).is_integer()
            else fmt.fmt_num(amount, lang, 2)
        )
        return f"{number} {_unit_word(unit, lang)}"

    return f"{fmt_big(amount, lang)} {_unit_word(unit, lang)}"


# -------------------------------------------------------------------------
# Tidspunktet for en enkelt maerkedag
# -------------------------------------------------------------------------


def _localise(naive: datetime, tz: ZoneInfo) -> datetime:
    """Saet tidszone paa en naiv vaegurstid.

    Ved sommertidsskift kan vaegurstiden enten mangle eller findes to gange.
    ``fold=0`` vaelger den foerste forekomst, hvilket svarer til den gaengse
    konvention.
    """
    return naive.replace(tzinfo=tz, fold=0)


def _pair_instant(milestone: Milestone, profile: Profile) -> datetime | None:
    """Tidspunktet for en maerkedag, der afhaenger af to foedselsoejeblikke.

    Begge slags har en lukket formel. Kalder vi den aeldstes foedsel ``a`` og
    den yngstes ``b``, saa gaelder:

    * forhold n:  (t - a) = n · (t - b)      =>  t = (n·b - a) / (n - 1)
    * sum s:      (t - a) + (t - b) = s      =>  t = (a + b + s) / 2

    Returnerer None, naar der ikke er indtastet en anden foedselsdato, eller
    naar svaret ligger foer den yngste er foedt — en sum, der er mindre end
    aldersforskellen, naas aldrig af to levende mennesker.
    """
    partner = profile.partner_utc
    if partner is None:
        return None

    older, younger = sorted((profile.birth_utc, partner))
    unit, amount = milestone.unit, milestone.amount

    if unit == "pair_ratio":
        # Forholdet starter uendeligt stort og falder mod 1. Ved tvillinger
        # er det 1 fra foerste sekund, og saa findes maerkedagen ikke.
        if amount <= 1 or older == younger:
            return None
        seconds = (amount * younger.timestamp() - older.timestamp()) / (amount - 1)
    else:
        if unit == "pair_sum_day":
            total = amount * 86_400.0
        elif unit == "pair_sum_year":
            total = amount * TROPICAL_YEAR_DAYS * 86_400.0
        else:
            total = float(amount)
        seconds = (older.timestamp() + younger.timestamp() + total) / 2

    when = datetime.fromtimestamp(seconds, tz=timezone.utc)
    return when if when >= younger else None


def _calendar_instant(
    milestone: Milestone, profile: Profile, now: datetime
) -> datetime | None:
    """Tidspunktet for en festdag, der ligger paa kalenderen.

    En engangsdato er den dag, den er. En tilbagevendende dag er den *naeste*
    gang, den falder — ellers ville den samme 4. maj staa hundrede gange i et
    menneskeliv, og kalenderen var ubrugelig.

    Der ledes fremad aar for aar, fordi ikke alle aar har dagen: den 29.
    februar findes kun i skudaar, og "den femte mandag i maaneden" findes
    slet ikke hvert aar.
    """
    try:
        spec = parse_spec(milestone.when)
    except SpecError:
        return None

    def moment(day: date) -> datetime:
        naive = datetime.combine(day, time(spec.hour, spec.minute))
        return _localise(naive, profile.tz)

    if spec.kind == "once":
        return moment(date(spec.year, spec.month, spec.day)).astimezone(timezone.utc)

    reference = now.astimezone(profile.tz)
    for year in range(reference.year, reference.year + 9):
        day = spec_in_year(spec, year)
        if day is None:
            continue
        when = moment(day)
        if when >= reference:
            return when.astimezone(timezone.utc)
    return None


def milestone_instant(
    milestone: Milestone, profile: Profile, now: datetime | None = None
) -> datetime | None:
    """Tidspunktet i UTC, eller None hvis maerkedagen ikke kan regnes ud.

    ``now`` bruges kun af de tilbagevendende festdage, som skal vide, hvad
    "naeste gang" betyder. Alt andet i kataloget regnes af foedselsoejeblikket
    alene og er det samme, uanset hvornaar man spoerger.
    """
    unit = milestone.unit
    amount = milestone.amount

    if unit in PAIR_UNITS:
        return _pair_instant(milestone, profile)

    if unit in CALENDAR_DAY_UNITS:
        return _calendar_instant(
            milestone, profile, now or datetime.now(timezone.utc)
        )

    if unit == "unix_abs":
        return UNIX_EPOCH + timedelta(seconds=amount)

    if unit in SECONDS_PER_UNIT:
        return profile.birth_utc + timedelta(seconds=amount * SECONDS_PER_UNIT[unit])

    if unit in {"cal_month", "cal_year"}:
        naive = profile.birth_local.replace(tzinfo=None)
        delta = (
            relativedelta(months=int(amount))
            if unit == "cal_month"
            else relativedelta(years=int(amount))
        )
        return _localise(naive + delta, profile.tz).astimezone(timezone.utc)

    rates = profile.rates
    seconds: float | None = None

    if unit == "heartbeat":
        seconds = amount * 60.0 / rates.bpm
    elif unit == "breath":
        seconds = amount * 60.0 / rates.breaths_per_min
    elif unit == "sleep_hour":
        seconds = amount / rates.sleep_hours_per_day * 24.0 * 3600.0
    elif unit == "meal":
        seconds = amount / rates.meals_per_day * 86_400.0
    elif unit == "step":
        seconds = amount / rates.steps_per_day * 86_400.0
    elif unit == "geo_ma":
        age_years = profile.lifespan_years * (EARTH_AGE_MA - amount) / EARTH_AGE_MA
        seconds = age_years * TROPICAL_YEAR_DAYS * 86_400.0
    elif unit == "pct_life":
        age_years = amount * profile.lifespan_years
        seconds = age_years * TROPICAL_YEAR_DAYS * 86_400.0

    if seconds is None:
        return None
    return profile.birth_utc + timedelta(seconds=seconds)


# -------------------------------------------------------------------------
# Hele listen
# -------------------------------------------------------------------------


def all_milestones() -> tuple[Milestone, ...]:
    """Kataloget plus legenderne plus festdagene."""
    return MILESTONES + tuple(legend_milestones()) + celebration_milestones()


def compute(
    profile: Profile,
    keys: set[str] | None = None,
    lang: str = "da",
    max_age_years: float = MAX_AGE_YEARS,
    now: datetime | None = None,
) -> list[Occasion]:
    """Regn alle valgte maerkedage ud og sortér dem kronologisk."""
    horizon = profile.birth_utc + timedelta(days=max_age_years * TROPICAL_YEAR_DAYS)
    moment = now or datetime.now(timezone.utc)
    occasions: list[Occasion] = []

    for milestone in all_milestones():
        if keys is not None and milestone.key not in keys:
            continue
        when_utc = milestone_instant(milestone, profile, moment)
        if when_utc is None:
            continue
        if milestone.unit in ONE_OFF_UNITS:
            # Ét bestemt oejeblik i historien hoerer kun med, hvis du var her:
            # DOOM's udgivelse i 1993 er ikke din maerkedag, hvis du er foedt
            # i 1998.
            if when_utc < profile.birth_utc or when_utc > horizon:
                continue
        elif when_utc > horizon:
            continue

        occasions.append(
            Occasion(
                milestone=milestone,
                when_utc=when_utc,
                when_local=when_utc.astimezone(profile.tz),
                label=build_label(milestone, profile, lang),
                group=GROUPS_BY_KEY[milestone.group],
            )
        )

    occasions.sort(key=lambda occasion: occasion.when_utc)
    return occasions


def bundle_keys(bundle: Bundle, profile: Profile, now: datetime) -> set[str]:
    """Hvilke maerkedage en faerdigpakket udvaelgelse daekker.

    Regnes altid mod hele kataloget, ikke mod det nuvaerende valg — ellers
    kunne en pakke kun nogensinde blive mindre.
    """
    catalogue = all_milestones()

    if bundle.stars_only:
        return {m.key for m in catalogue if m.star}

    if bundle.groups:
        wanted = set(bundle.groups)
        return {m.key for m in catalogue if m.group in wanted}

    if bundle.within_years is not None:
        horizon = now + timedelta(days=bundle.within_years * TROPICAL_YEAR_DAYS)
        found: set[str] = set()
        for milestone in catalogue:
            when = milestone_instant(milestone, profile, now)
            if when is not None and now <= when <= horizon:
                found.add(milestone.key)
        return found

    return set()


# Hvad en pakke bygger paa.
BIRTH_SCOPE = "birth"          # Haenger paa foedselsoejeblikket.
CALENDAR_SCOPE = "calendar"    # Falder paa samme dato for alle.
BOTH_SCOPES = "both"           # Begge dele.

SCOPES: tuple[str, ...] = (BIRTH_SCOPE, CALENDAR_SCOPE, BOTH_SCOPES)


def _scope_of(milestones: Iterable[Milestone]) -> str:
    kinds = {
        CALENDAR_SCOPE if m.unit in CALENDAR_DAY_UNITS else BIRTH_SCOPE
        for m in milestones
    }
    if not kinds:
        return BIRTH_SCOPE
    return kinds.pop() if len(kinds) == 1 else BOTH_SCOPES


def bundle_scope(bundle: Bundle) -> str:
    """Om pakken haenger paa din foedselsdag, paa kalenderen, eller paa begge.

    Et gigasekund findes kun, fordi netop du blev foedt. Den 4. maj falder
    samme dag for alle, og det personlige er kun, hvor gammel du er den dag.
    Det er to forskellige slags maerkedage, og de hoerer ikke hjemme i den
    samme raekke knapper.

    Svaret regnes ud af enhederne i kataloget i stedet for at staa paa en
    liste et sted. En ny gruppe havner derfor det rigtige sted af sig selv,
    uden at nogen skal huske at foeje den til.
    """
    catalogue = all_milestones()

    if bundle.groups:
        wanted = set(bundle.groups)
        return _scope_of(m for m in catalogue if m.group in wanted)

    if bundle.stars_only:
        return _scope_of(m for m in catalogue if m.star)

    # En pakke, der skaerer efter tid ("alt inden for ti aar"), tager fra hele
    # kataloget og hoerer derfor til begge steder.
    return BOTH_SCOPES


def milestones_by_group() -> dict[str, list[Milestone]]:
    """Hele kataloget sorteret i grupper — ogsaa legenderne og festdagene.

    Opslaget hoerer til her og ikke i ``catalog``, fordi kun motoren kender
    hele kataloget. ``catalog.MILESTONES`` er de haandskrevne maerkedage;
    legenderne og festdagene bliver bygget, og et opslag, der kun kigger i
    ``MILESTONES``, svarer derfor tomt for en gruppe som Palindromdage uden
    at sige fra.
    """
    out: dict[str, list[Milestone]] = {}
    for milestone in all_milestones():
        out.setdefault(milestone.group, []).append(milestone)
    return out


def group_scopes() -> dict[str, str]:
    """Hylden for hver gruppe i kataloget, regnet ud i ét gennemloeb.

    Samme skel som ``bundle_scope`` og udledt paa samme maade: af enhederne.
    Den samler alle grupper paa én gang, fordi brugerfladen skal bruge dem
    alle sammen samtidig og kataloget er langt.
    """
    kinds: dict[str, set[str]] = {}
    for milestone in all_milestones():
        kind = (
            CALENDAR_SCOPE
            if milestone.unit in CALENDAR_DAY_UNITS
            else BIRTH_SCOPE
        )
        kinds.setdefault(milestone.group, set()).add(kind)
    return {
        group: (next(iter(kind)) if len(kind) == 1 else BOTH_SCOPES)
        for group, kind in kinds.items()
    }


def group_scope(group_key: str) -> str:
    """Om gruppens maerkedage regnes fra foedslen eller ligger paa kalenderen."""
    return group_scopes().get(group_key, BIRTH_SCOPE)


def next_occasions(
    occasions: list[Occasion], now: datetime, count: int = 1
) -> list[Occasion]:
    """De foerste maerkedage, der endnu ikke er passeret."""
    return [o for o in occasions if o.when_utc >= now][:count]


def last_occasions(
    occasions: list[Occasion], now: datetime, count: int = 1
) -> list[Occasion]:
    """De sidst passerede maerkedage, nyeste foerst."""
    return [o for o in occasions if o.when_utc < now][-count:][::-1]


def age_seconds(profile: Profile, now: datetime) -> float:
    """Alder i sekunder — tallet bag det levende ur."""
    return (now - profile.birth_utc).total_seconds()


def age_hours(profile: Profile, now: datetime) -> float:
    """Alder i timer. Rene SI-timer a 3600 sekunder."""
    return age_seconds(profile, now) / 3600.0


def age_days(profile: Profile, now: datetime) -> float:
    """Alder i doegn. Rene SI-doegn a 86.400 sekunder.

    Bemaerk, at det ikke noedvendigvis er det samme som antallet af gange,
    kalenderen har skiftet dato: ved sommertidsskift forskydes vaeguret en
    time i forhold til den forloebne tid.
    """
    return age_seconds(profile, now) / 86_400.0


def _calendar_fraction(profile: Profile, now: datetime, unit: str) -> float:
    """Alder i hele kalenderenheder plus broekdelen af den igangvaerende.

    Regnes paa vaegurets tid, praecis som maanedsmaerkedagene, saa taelleren
    staar paa rundt 100,00 i netop det sekund, "100 maaneder" indtraeffer.
    Broekdelens naevner er den faktiske laengde af den igangvaerende maaned
    eller det igangvaerende aar — derfor tikker den ikke lige hurtigt hele
    tiden, og derfor er februar hurtigere end januar.
    """
    birth = profile.birth_local.replace(tzinfo=None)
    current = now.astimezone(profile.tz).replace(tzinfo=None)

    delta = relativedelta(current, birth)
    whole = delta.years * 12 + delta.months if unit == "month" else delta.years

    def anchor(count: int) -> datetime:
        step = relativedelta(months=count) if unit == "month" else relativedelta(years=count)
        return birth + step

    # Skudaarsfoedsler kan faa relativedelta og klampningen til at vaere uenige
    # med ét trin. Her retter vi op, saa broekdelen aldrig bliver negativ.
    while whole > 0 and anchor(whole) > current:
        whole -= 1

    start, end = anchor(whole), anchor(whole + 1)
    span = (end - start).total_seconds()
    if span <= 0:
        return float(whole)
    return whole + (current - start).total_seconds() / span


def age_months(profile: Profile, now: datetime) -> float:
    """Alder i kalendermaaneder, med broekdel."""
    return _calendar_fraction(profile, now, "month")


def age_years(profile: Profile, now: datetime) -> float:
    """Alder i kalenderaar, med broekdel. 8,00 betyder "fyldte 8 i dag"."""
    return _calendar_fraction(profile, now, "year")


def duration_breakdown(seconds: float, lang: str) -> str:
    """"31 år, 251 dage, 7 timer, 46 minutter og 40 sekunder"."""
    base = datetime(2000, 1, 1, tzinfo=timezone.utc)
    delta = relativedelta(base + timedelta(seconds=seconds), base)
    return fmt.fmt_relativedelta(delta, lang, max_parts=6)
