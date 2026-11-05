"""Hvor laenge lever man? Regnet paa doedelighedstavler i stedet for gaet.

Resten af appen regner paa en *antaget* levetid, man selv skyder paa. Her er
et kvalificeret bud at skyde med.

Tavlerne ligger i ``data/lifetables.json`` og hentes med
``tools/fetch_lifetables.py``: Danmark fra Danmarks Statistik, de oevrige fra
Eurostat. Af hver tavle bruges ``lx`` — hvor mange af 100.000 nyfoedte der
stadig lever ved hver alder. Middellevetiden er bare gennemsnittet af den
kurve, men kurven selv kan svare paa mere: hvad er medianen, hvor ligger
kvartilerne, og hvad er chancen for at naa de halvfems.

Tre ting kan skrues paa:

**Perioden eller kohorten.** En periodetavle antager, at doedeligheden bliver
staaende, som den er i dag. Det goer den ikke. En fyrreaarig moeder foerst
doedeligheden ved halvfjerds om tredive aar, og til den tid er den lavere.
Kohortetallet regner en aarlig bedring ind (se ``IMPROVEMENT``). Forskellen
er flere aar for en ung og naesten ingenting for en gammel, og begge tal
vises, saa forskellen kan ses.

**Livsstilen.** Fire faktorer, hver med et risikoforhold fra et navngivet
studie (se ``FACTORS``). De ganges paa doedeligheden i alle aldre.

**Haleenden.** Tavlen stopper ved 95 eller 99. Den forlaenges med en konstant
doedelighed, valgt saa restlevetiden i sidste alderstrin bliver praecis den,
tavlen selv angiver — saa halen er tavlens eget tal og ikke et skoen.

Hvad det IKKE er: en forudsigelse om et menneske. Det er, hvad der i
gennemsnit skete for folk med de traek i de aar, tavlen daekker. Faktorerne
haenger desuden sammen indbyrdes, saa at gange dem sammen overdriver, naar
flere er slaaet til. Derfor vises svaret som et spaend og ikke som ét tal.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

DATA_FILE = Path(__file__).resolve().parent.parent / "data" / "lifetables.json"

# Saa langt regnes der. Ingen tavle naar hertil, men halen skal have et sted
# at slutte, og et menneske har ikke levet laengere.
MAX_AGE = 120

# Antaget aarlig bedring i doedeligheden, brugt til kohortetallet. Et rundt
# tal i den lave ende af, hvad de seneste aartier faktisk har vist i
# Vesteuropa. Det er en antagelse, ikke en maaling, og den staar her alene,
# saa den er til at finde og til at skrue paa.
IMPROVEMENT = 0.010

SEXES = ("M", "F")


# -------------------------------------------------------------------------
# Livsstilens faktorer
# -------------------------------------------------------------------------


@dataclass(frozen=True)
class Level:
    """Ét svar paa ét spoergsmaal, med det risikoforhold det baerer."""

    key: str
    da: str
    en: str
    hazard: float

    def name(self, lang: str) -> str:
        return self.da if lang == "da" else self.en


@dataclass(frozen=True)
class Factor:
    """Ét spoergsmaal om livsstil, med kilden til tallene."""

    key: str
    da: str
    en: str
    source: str
    levels: tuple[Level, ...]

    @property
    def default(self) -> str:
        """Det svar, der ikke flytter noget. Altid det foerste."""
        return self.levels[0].key

    def level(self, key: str) -> Level:
        for level in self.levels:
            if level.key == key:
                return level
        return self.levels[0]

    def name(self, lang: str) -> str:
        return self.da if lang == "da" else self.en


# Risikoforholdene er for doedelighed af alle aarsager, taget fra de
# offentliggjorte studier og rundet. Referenceniveauet staar foerst og er
# altid 1,0, saa "ikke oplyst" og "som referencen" er det samme tal.
FACTORS: tuple[Factor, ...] = (
    Factor(
        "smoking", "Rygning", "Smoking",
        "Jha m.fl., New England Journal of Medicine 2013;368:341–350",
        (
            Level("unknown", "Ikke oplyst", "Not given", 1.00),
            Level("never", "Har aldrig røget", "Never smoked", 1.00),
            Level("quit_early", "Stoppet før 40", "Quit before 40", 1.10),
            Level("quit_late", "Stoppet efter 40", "Quit after 40", 1.60),
            Level("current", "Ryger", "Current smoker", 2.80),
        ),
    ),
    Factor(
        "activity", "Motion", "Physical activity",
        "Arem m.fl., JAMA Internal Medicine 2015;175:959–967",
        (
            Level("unknown", "Ikke oplyst", "Not given", 1.00),
            Level("none", "Stillesiddende", "Sedentary", 1.00),
            Level("some", "Lidt, under det anbefalede", "Some, below the guideline", 0.82),
            Level("guideline", "Omkring 150 min. om ugen", "Around 150 min a week", 0.72),
            Level("high", "Det dobbelte eller mere", "Twice that or more", 0.69),
        ),
    ),
    Factor(
        "bmi", "Body mass index", "Body mass index",
        "Global BMI Mortality Collaboration, The Lancet 2016;388:776–786",
        (
            Level("unknown", "Ikke oplyst", "Not given", 1.00),
            Level("under", "Under 18,5", "Under 18.5", 1.51),
            Level("low_normal", "18,5–22,5", "18.5–22.5", 1.05),
            Level("normal", "22,5–25", "22.5–25", 1.00),
            Level("over", "25–27,5", "25–27.5", 1.07),
            Level("over2", "27,5–30", "27.5–30", 1.20),
            Level("obese", "30–35", "30–35", 1.45),
            Level("obese2", "35–40", "35–40", 1.94),
            Level("obese3", "Over 40", "Over 40", 2.76),
        ),
    ),
    Factor(
        "alcohol", "Alkohol", "Alcohol",
        "Wood m.fl., The Lancet 2018;391:1513–1523",
        (
            Level("unknown", "Ikke oplyst", "Not given", 1.00),
            Level("low", "Under 10 genstande om ugen", "Under 100 g a week", 1.00),
            Level("medium", "10–20 genstande", "100–200 g a week", 1.14),
            Level("high", "20–35 genstande", "200–350 g a week", 1.27),
            Level("very_high", "Over 35 genstande", "Over 350 g a week", 1.53),
        ),
    ),
)

FACTORS_BY_KEY: dict[str, Factor] = {f.key: f for f in FACTORS}


def combined_hazard(choices: dict[str, str]) -> float:
    """Risikoforholdene ganget sammen.

    At gange dem er den gaengse maade, men den antager, at faktorerne er
    uafhaengige. Det er de ikke — rygere motionerer mindre — saa produktet
    overdriver, naar flere er slaaet til. Derfor viser brugerfladen et spaend.
    """
    hazard = 1.0
    for factor in FACTORS:
        hazard *= factor.level(choices.get(factor.key, factor.default)).hazard
    return hazard


def damped(hazard: float) -> float:
    """Det samme risikoforhold, men med halv kraft.

    Kvadratroden er den simple modvaegt mod, at faktorerne overlapper: den
    svarer til, at halvdelen af virkningen allerede er talt med af en anden
    faktor. Sammen med det uddaempede tal spaender den svaret ud, saa det
    bliver et interval i stedet for en praecision, der ikke er daekning for.
    """
    return hazard**0.5


# -------------------------------------------------------------------------
# Tavlerne
# -------------------------------------------------------------------------


@dataclass(frozen=True)
class LifeTable:
    """Én doedelighedstavle: ét land, ét koen, én periode."""

    country: str
    name_da: str
    name_en: str
    sex: str
    source: str
    source_url: str
    period: str
    ages: tuple[int, ...]
    lx: tuple[float, ...]
    ex: tuple[float, ...]

    def name(self, lang: str) -> str:
        return self.name_da if lang == "da" else self.name_en

    @property
    def last_age(self) -> int:
        return self.ages[-1]

    def table_expectancy(self, age: int) -> float:
        """Restlevetiden, som tavlen selv angiver den."""
        age = max(self.ages[0], min(self.last_age, int(age)))
        return self.ex[self.ages.index(age)]


@dataclass(frozen=True)
class Catalogue:
    """Alle tavler, som de ligger i datafilen."""

    fetched: str
    default: str
    tables: dict[tuple[str, str], LifeTable]

    @property
    def countries(self) -> list[str]:
        return sorted({country for country, _ in self.tables})

    def get(self, country: str, sex: str) -> LifeTable | None:
        return self.tables.get((country, sex))

    def name(self, country: str, lang: str) -> str:
        for sex in SEXES:
            table = self.get(country, sex)
            if table:
                return table.name(lang)
        return country


@lru_cache(maxsize=1)
def load(path: str | None = None) -> Catalogue:
    """Laes datafilen. Husket, fordi brugerfladen spoerger ved hver koersel."""
    target = Path(path) if path else DATA_FILE
    if not target.is_file():
        return Catalogue(fetched="", default="", tables={})

    payload = json.loads(target.read_text(encoding="utf-8"))
    tables: dict[tuple[str, str], LifeTable] = {}
    for country, entry in payload.get("countries", {}).items():
        for sex, columns in entry.get("sexes", {}).items():
            tables[(country, sex)] = LifeTable(
                country=country,
                name_da=entry.get("name_da", country),
                name_en=entry.get("name_en", country),
                sex=sex,
                source=entry.get("source", ""),
                source_url=entry.get("source_url", ""),
                period=str(entry.get("period", "")),
                ages=tuple(entry["ages"]),
                lx=tuple(float(v) for v in columns["lx"]),
                ex=tuple(float(v) for v in columns["ex"]),
            )
    return Catalogue(
        fetched=payload.get("fetched", ""),
        default=payload.get("default", "DK"),
        tables=tables,
    )


# -------------------------------------------------------------------------
# Fra tavle til kurve
# -------------------------------------------------------------------------


def _tail_survival(table: LifeTable) -> float:
    """Den aarlige overlevelse efter tavlens sidste alder.

    Med en konstant doedelighed er restlevetiden ``p/(1-p) + 0,5``. Vi kender
    restlevetiden — den staar i tavlen — saa vi vender ligningen om og faar
    den ``p``, der goer halen enig med tavlen.
    """
    # Halen tager tavlens eget tal. Det er princippet: vi gaetter ikke, hvor
    # tavlen selv siger noget.
    #
    # Prisen staar i et par af de smaa lande. Eurostats slovakiske maend har
    # restlevetiden stige fra 5,3 aar ved 90 til 6,6 ved 95, hvilket ingen
    # befolkning goer — den aabne 95+-gruppe stoejer. Et forsoeg paa at
    # klippe den slags ned gik ud over de tavler, der var i orden, saa den
    # staar som den er. Det rammer kun de allerhoejeste aldre i de mindste
    # lande, og kilden staar i brugerfladen.
    remaining = table.ex[-1]
    if remaining <= 0.5:
        return 0.0
    return min(0.99, (remaining - 0.5) / (remaining + 0.5))


@lru_cache(maxsize=256)
def mortality(country: str, sex: str) -> tuple[float, ...]:
    """Doedssandsynligheden for hvert alderstrin 0..MAX_AGE-1.

    ``qx[a]`` er chancen for at doe mellem ``a`` og ``a+1``. Den regnes af
    ``lx``, og efter tavlens sidste alder holdes den konstant.
    """
    table = load().get(country, sex)
    if table is None:
        return ()

    by_age = dict(zip(table.ages, table.lx))
    out: list[float] = []
    for age in range(MAX_AGE):
        here, nxt = by_age.get(age), by_age.get(age + 1)
        if here and nxt and here > 0:
            out.append(max(0.0, min(1.0, 1.0 - nxt / here)))
        else:
            out.append(1.0 - _tail_survival(table))
    return tuple(out)


def survival_curve(
    country: str,
    sex: str,
    from_age: float,
    *,
    improvement: float = 0.0,
    hazard: float = 1.0,
) -> tuple[float, ...]:
    """Chancen for stadig at leve om 0, 1, 2 ... aar, naar man er der nu.

    ``improvement`` er den aarlige bedring i doedeligheden. Med 0 bliver det
    en periodekurve: verden staar stille. Med en positiv vaerdi bliver det en
    kohortekurve, hvor doedeligheden ved en given alder er lavere, jo
    senere man naar den.

    ``hazard`` ganges paa doedeligheden i alle aldre og er livsstilen.
    """
    qx = mortality(country, sex)
    if not qx:
        return ()

    start = max(0, int(from_age))
    curve = [1.0]
    alive = 1.0
    for step, age in enumerate(range(start, MAX_AGE)):
        q = qx[age] * hazard * (1.0 - improvement) ** step
        alive *= max(0.0, 1.0 - min(1.0, q))
        curve.append(alive)
        if alive <= 0.0:
            break
    return tuple(curve)


def expectancy(curve: tuple[float, ...]) -> float:
    """Den forventede restlevetid, regnet af kurven.

    Summen af overlevelsessandsynlighederne er antallet af hele aar, man
    forventes at faa. Den halve laegges til, fordi doedsfaldene i gennemsnit
    falder midt i aaret.
    """
    if len(curve) < 2:
        return 0.0
    return sum(curve[1:]) + 0.5


def chance_of_reaching(curve: tuple[float, ...], from_age: float, target: float) -> float:
    """Chancen for at naa en bestemt alder, naar man er ``from_age`` nu."""
    if not curve:
        return 0.0
    step = int(target) - int(from_age)
    if step <= 0:
        return 1.0
    if step >= len(curve):
        return 0.0
    return curve[step]


def age_at_quantile(curve: tuple[float, ...], from_age: float, share: float) -> float:
    """Den alder, hvor ``share`` af dem, der lever nu, er doede.

    Med 0,5 er det medianen: den alder, halvdelen naar. Der interpoleres
    inden for aaret, saa svaret ikke hopper i hele trin.
    """
    if not curve:
        return float(from_age)
    wanted = 1.0 - share
    start = int(from_age)
    for step in range(1, len(curve)):
        if curve[step] <= wanted:
            before, after = curve[step - 1], curve[step]
            spread = before - after
            part = (before - wanted) / spread if spread > 0 else 0.0
            return start + step - 1 + part
    return float(start + len(curve) - 1)


def exceedance_at(curve: tuple[float, ...], from_age: float, age: float) -> float:
    """Chancen for at leve *laengere* end en alder, der ikke er et helt tal.

    ``chance_of_reaching`` springer i hele aar, fordi tavlen goer det. Her
    interpoleres der lineaert inden for aaret. Det skal der, fordi
    gennemsnitsalderen naesten aldrig lander paa et helt aar, og den skal
    kunne saettes paa kurven dér, hvor den faktisk ligger, i stedet for at
    hoppe til naermeste trin.
    """
    if not curve:
        return 0.0
    offset = float(age) - int(from_age)
    if offset <= 0.0:
        return 1.0
    if offset >= len(curve) - 1:
        return curve[-1]
    step = int(offset)
    return curve[step] + (curve[step + 1] - curve[step]) * (offset - step)


def last_age_above(
    curve: tuple[float, ...], from_age: float, floor: float = 0.005
) -> int:
    """Den sidste alder, hvor chancen stadig er over ``floor``.

    Kurven har en lang, flad hale af naesten-nuller op mod ``MAX_AGE``.
    Tegnet med fylder den en tredjedel af x-aksen uden at sige noget, saa
    plottet stopper her i stedet.
    """
    start = int(from_age)
    last = start
    for step, alive in enumerate(curve):
        if alive >= floor:
            last = start + step
    return last
