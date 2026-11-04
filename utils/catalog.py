"""Kataloget over skaeve maerkedage.

Hver post er et antal enheder regnet fra foedselsoejeblikket. ``unit`` afgoer,
hvordan den regnes ud (se ``utils.units`` og ``utils.engine``).

``why_da``/``why_en`` er valgfri. De er med paa konstanter og paa tal, hvis
pointe ikke er til at gaette — ikke paa de runde tal, der taler for sig selv.
"""

from __future__ import annotations

import math
from dataclasses import dataclass

from .geology import GEO_EVENTS
from .units import C14_HALF_LIFE_YEARS, ESTIMATE_UNITS


def c14_years(fraction_left: float) -> float:
    """Hvor mange aar der gaar, foer kun ``fraction_left`` af en kulstof-14-proeve er tilbage.

    Henfald foelger N(t) = N₀ · (1/2)^(t/T), saa t = T · ln(andel) / ln(1/2).
    """
    return C14_HALF_LIFE_YEARS * math.log(fraction_left) / math.log(0.5)


@dataclass(frozen=True)
class Group:
    """En kategori af maerkedage."""

    key: str
    da: str
    en: str
    emoji: str
    default_on: bool = True

    def name(self, lang: str) -> str:
        return self.da if lang == "da" else self.en

    def title(self, lang: str) -> str:
        return f"{self.emoji} {self.name(lang)}"


@dataclass(frozen=True)
class Milestone:
    """En enkelt skaev maerkedag."""

    key: str
    group: str
    unit: str
    amount: float
    # Kalenderdagene (``annual`` og ``date_abs``) har ingen maengde at regne
    # paa — de har en dato. Den staar her, som den stod i datafilen, og bliver
    # laest af ``utils.celebrations.parse_spec``.
    when: str = ""
    # Aaret, dagen taeller fra. Saettes paa de aarlige dage, der mindes noget
    # dateret, saa etiketten kan sige, hvilket aar i raekken det er: Maanedagen
    # i 2069 er 100-aaret. Nul betyder, at der ikke er noget at taelle fra.
    since: int = 0
    why_da: str = ""
    why_en: str = ""
    label_da: str | None = None
    label_en: str | None = None
    star: bool = False          # Fremhaevet klassiker.
    live: bool = False          # Faar et levende sekundur i appen.
    silent: bool = False        # Skal staa helt uden forklaring, ogsaa automatisk.
    # Hvor mange der holder dagen. Nul betyder "ikke sat" — se ``level``.
    tier: int = 0

    @property
    def level(self) -> int:
        """Niveau 1, 2 eller 3: hvor mange der holder dagen.

        Det er med vilje ikke en smagsdom om, hvor god dagen er, men en
        egenskab ved dagen selv — om der findes en fest, en by, en forening:

        1. **Den kender folk.** Du kan naevne den i en frokostpause, og
           nogen nikker. Star Wars-dagen, pi-dagen, gigasekundet.
        2. **Den har et rigtigt publikum, bare et lille et.** Nogen moeder
           faktisk op. Haandklaededagen, mol-dagen, mosesnorkling.
        3. **Den findes naesten kun paa en liste.** Ingen fejrer den, men
           den er sjov at vide. Repunitdage, de fleste figurfoedselsdage.

        Er niveauet ikke sat, afgoer stjernen det: en fremhaevet klassiker
        er niveau 1, og alt andet lander paa midten. Det er noejagtig den
        inddeling, appen havde i forvejen — niveauerne goer den bare
        finere, og ingen maerkedag skifter plads, fordi feltet blev til.
        """
        if self.tier:
            return self.tier
        return 1 if self.star else 2

    @property
    def estimate(self) -> bool:
        return self.unit in ESTIMATE_UNITS

    def why(self, lang: str) -> str:
        return self.why_da if lang == "da" else self.why_en

    def label_override(self, lang: str) -> str | None:
        return self.label_da if lang == "da" else self.label_en


GROUPS: tuple[Group, ...] = (
    Group("sec", "Sekunder", "Seconds", "⏱️"),
    Group("minhour", "Minutter og timer", "Minutes and hours", "🕐"),
    Group("dayweek", "Dage og uger", "Days and weeks", "📅"),
    Group("monthyear", "Måneder og år", "Months and years", "🗓️"),
    Group("constants", "Konstanter", "Constants", "🔬"),
    Group("nerd", "Nørdetal", "Nerd numbers", "🧮"),
    Group("s73", "73 — tallenes Chuck Norris", "73 — the Chuck Norris of numbers", "🧪"),
    Group("repeat", "Gentagne og spejlvendte tal", "Repdigits and palindromes", "🔢"),
    Group("exotic", "Eksotiske enheder", "Exotic units", "⚛️"),
    Group("moon", "Månen", "The Moon", "🌙"),
    Group("space", "Rumrejsen", "Space travel", "🚀"),
    Group("geo", "Jordens historie", "Earth's history", "🌋"),
    Group("body", "Kroppen", "The body", "❤️"),
    Group("century", "Procent af et liv", "Percent of a life", "📊"),
    # Par-gruppen giver kun noget, naar der er indtastet en anden foedselsdato.
    # Derfor er den slaaet til fra start: den fylder ingenting, saa laenge
    # feltet staar tomt, og virker med det samme, naar det bliver udfyldt.
    Group("pair", "Jer to", "The two of you", "👥"),
    Group("legend", "Legender", "Legends", "🎸", default_on=False),
    # Festdagene ligger paa kalenderen i stedet for i dit liv (se
    # ``utils.celebrations``). De er slaaet fra fra start: der er flere
    # hundrede af dem, og de ville drukne de maerkedage, appen handler om.
    Group("pop", "Popkulturens festdage", "Pop culture celebrations", "🍿",
          default_on=False),
    Group("dkday", "Danske skæve dage", "Danish odd days", "🇩🇰",
          default_on=False),
    # Kravet for at staa her er ikke, at dagen er stor, men at den er skaev:
    # en helligdag opstaaet af en hoerefejl, en by der kaster appelsiner, en
    # dag for at mislykkes.
    Group("wacky", "Verdens skæve dage", "The world's odd days", "🤪",
          default_on=False),
    # Kilden har en helligdag for hver eneste dag i aaret. Her staar de
    # kanoniske og et udvalg af resten.
    Group("fsm", "Pastafarianske helligdage", "Pastafarian holy days", "🍝",
          default_on=False),
    Group("fiction", "Fiktive helligdage", "Fictional holidays", "🎬",
          default_on=False),
    Group("chars", "Figurernes fødselsdage", "Characters' birthdays", "🦸",
          default_on=False),
    Group("scifi", "Science fiction-kanon", "Science fiction canon", "🛸",
          default_on=False),
    Group("sciday", "Videnskabens festdage", "Days of science", "🔭",
          default_on=False),
    Group("nerdhist", "Nørdehistorie", "Nerd history", "🕹️", default_on=False),
    Group("scihist", "Videnskabens gennembrud", "Scientific breakthroughs", "💡",
          default_on=False),
    # Talmoensterdagene. De staar ikke skrevet ned noget sted, men bliver
    # regnet ud af ``utils.datepatterns`` — én gruppe pr. moenster, saa man kan
    # slaa palindromerne til uden ogsaa at faa flere hundrede sumdage.
    Group("palindrome", "Palindromdage", "Palindrome days", "🔁",
          default_on=False),
    Group("sequence", "Sekvensdage", "Sequence days", "🪜", default_on=False),
    Group("repunit", "Repunitdage", "Repdigit days", "🎰", default_on=False),
    Group("binday", "Binære dage", "Binary days", "💾", default_on=False),
    Group("pyth", "Pythagoræiske dage", "Pythagorean days", "📐",
          default_on=False),
    Group("sqrtday", "Kvadratrodsdage", "Square root days", "√",
          default_on=False),
    Group("fibday", "Fibonacci-datoer", "Fibonacci dates", "🌀",
          default_on=False),
    Group("product", "Produktdage", "Product days", "✖️", default_on=False),
    Group("sumday", "Sumdage", "Sum days", "➕", default_on=False),
    Group("techday", "Teknologiens mærkedage", "Technology's red-letter days",
          "💻", default_on=False),
    Group("birthdays", "Nørdernes fødselsdage", "Nerd birthdays", "🎂",
          default_on=False),
    # Den anden maade at gribe Jordens historie an paa. ``geo`` klemmer de 4,54
    # milliarder aar ned i *dit* liv; her klemmes de ned i et kalenderaar, som
    # alle har det samme af (se ``utils.geoyear``).
    Group("geoyear", "Jordens år", "Earth's year", "🌍", default_on=False),
    # Runde aarsdage for alt det daterede. De udledes i
    # ``utils.celebrations.round_anniversaries`` og staar ikke skrevet
    # nogen steder.
    Group("anniversary", "Runde årsdage", "Round anniversaries", "🎊",
          default_on=False),
)

GROUPS_BY_KEY: dict[str, Group] = {g.key: g for g in GROUPS}


@dataclass(frozen=True)
class Bundle:
    """En faerdigpakket udvaelgelse, man kan slaa til med ét klik.

    En pakke er enten et udvalg af grupper, alle de fremhaevede klassikere,
    eller alt hvad der ligger inden for et bestemt antal aar. Den erstatter
    det nuvaerende valg i stedet for at laegge til.
    """

    key: str
    da: str
    en: str
    emoji: str
    desc_da: str
    desc_en: str
    groups: tuple[str, ...] = ()
    stars_only: bool = False
    within_years: float | None = None

    def name(self, lang: str) -> str:
        return self.da if lang == "da" else self.en

    def title(self, lang: str) -> str:
        return f"{self.emoji} {self.name(lang)}"

    def description(self, lang: str) -> str:
        return self.desc_da if lang == "da" else self.desc_en


BUNDLES: tuple[Bundle, ...] = (
    Bundle(
        "classics", "Klassikere", "Classics", "⭐",
        "De store, alle kender: gigasekundet, 10.000 dage, 1.000 måneder, "
        "1234567890 og resten af de fremhævede.",
        "The big ones everybody knows: the gigasecond, 10,000 days, 1,000 "
        "months, 1234567890 and the rest of the highlights.",
        stars_only=True,
    ),
    Bundle(
        "round", "Runde tal", "Round numbers", "🔟",
        "Kun de pæne multipla i sekunder, minutter, timer, dage, uger, "
        "måneder og år. Ingen krumspring.",
        "Just the tidy multiples in seconds, minutes, hours, days, weeks, "
        "months and years. No funny business.",
        groups=("sec", "minhour", "dayweek", "monthyear"),
    ),
    Bundle(
        "nerdpack", "Nørd-pakken", "Nerd pack", "🧮",
        "Konstanterne, nørdetallene, Sheldons 73, palindromerne og de "
        "eksotiske enheder.",
        "The constants, the nerd numbers, Sheldon's 73, the palindromes and "
        "the exotic units.",
        groups=("constants", "nerd", "s73", "repeat", "exotic"),
    ),
    Bundle(
        "spacepack", "Rumpakken", "Space pack", "🚀",
        "Månen, kilometrene rundt om Solen, stjernerne dit fødselslys når — "
        "og hele Jordens historie.",
        "The Moon, the kilometres around the Sun, the stars your birth light "
        "reaches — and the whole history of Earth.",
        groups=("space", "moon", "geo"),
    ),
    Bundle(
        "bodypack", "Kropspakken", "Body pack", "❤️",
        "Hjerteslag, åndedrag, søvntimer, måltider og skridt — plus hvor "
        "langt du er i livet.",
        "Heartbeats, breaths, hours slept, meals and steps — plus how far "
        "through life you are.",
        groups=("body", "century"),
    ),
    Bundle(
        "pairpack", "Jer to", "The two of you", "👥",
        "Alt det, der kræver to fødselsdatoer: hvornår I er lige gamle i "
        "forhold, og hvornår I har levet et bestemt antal år tilsammen.",
        "Everything that needs two dates of birth: when your ages line up in "
        "ratio, and when you have lived a given number of years between you.",
        groups=("pair",),
    ),
    Bundle(
        "soon", "Alt inden for 10 år", "Everything within 10 years", "⏳",
        "Alt fra hele kataloget, der falder i de næste ti år. Den korteste "
        "vej til en kalender, der faktisk sker noget i.",
        "Everything in the catalogue falling in the next ten years. The "
        "shortest route to a calendar where things actually happen.",
        within_years=10,
    ),
    Bundle(
        "legends", "Legenderne", "The legends", "🎸",
        "De 30 personer, du kan nå at overhale.",
        "The 30 people you can outlive.",
        groups=("legend",),
    ),
    Bundle(
        "popbundle", "Popkulturpakken", "Pop culture pack", "🍿",
        "Dagene folk faktisk fejrer: 4. maj, Towel Day, Dollys 9 to 5 — og de "
        "danske, hvor tallene rimer. Bagerens fødselsdag er den 11.11.",
        "The days people actually celebrate: May the Fourth, Towel Day, "
        "Dolly's 9 to 5 — plus the Danish ones, where the numbers rhyme.",
        groups=("pop", "dkday", "techday", "birthdays"),
    ),
    Bundle(
        "fictionbundle", "Fiktionspakken", "Fiction pack", "🎬",
        "Helligdage, der kun findes inde i værket — Festivus, Hogswatch, "
        "Gondors nytår — og fødselsdagene på de figurer, der holder dem.",
        "Holidays that exist only inside the story — Festivus, Hogswatch, "
        "Gondorian New Year — and the birthdays of the characters who keep them.",
        groups=("fiction", "chars"),
    ),
    Bundle(
        "scifibundle", "Science fiction-pakken", "Science fiction pack", "🛸",
        "Datoerne inde i historierne: Skynet vågner, lynet rammer Hill Valley, "
        "Nostromo vækker besætningen. Kun de af dem, der falder i dit liv.",
        "The dates inside the stories: Skynet wakes, lightning strikes Hill "
        "Valley, the Nostromo wakes its crew. Only the ones inside your life.",
        groups=("scifi",),
    ),
    Bundle(
        "scidaybundle", "Videnskabspakken", "Science pack", "🔭",
        "Pi-dagen, Mol-dagen, Darwin Day og Newtonmas — og de dage, hvor noget "
        "blev bevist: formørkelsen i 1919, rumstøjen i 1964, tyngdebølgerne.",
        "Pi Day, Mole Day, Darwin Day and Newtonmas — plus the days something "
        "was proved: the 1919 eclipse, the 1964 hiss, the gravitational waves.",
        groups=("sciday", "scihist"),
    ),
    Bundle(
        "nerdhistbundle", "Nørdehistorien", "Nerd history", "🕹️",
        "Den dag DOOM udkom, den dag Sputnik fløj, den dag Game Boy'en kom i "
        "butikkerne. Kun det, der skete, mens du var her.",
        "The day DOOM shipped, the day Sputnik flew, the day the Game Boy hit "
        "the shops. Only what happened while you were around.",
        groups=("nerdhist",),
    ),
    Bundle(
        "annivbundle", "Runde årsdage", "Round anniversaries", "🎊",
        "50-året for Alien, 100-året for månelandingen, 150-året for det "
        "første telefonopkald. Kun dem, der falder i dit liv.",
        "Fifty years since Alien, a hundred since the Moon landing, a hundred "
        "and fifty since the first telephone call. Only the ones inside your "
        "life.",
        groups=("anniversary",),
    ),
    Bundle(
        "earthyearbundle", "Jordens år", "Earth's year", "🌍",
        "Jordens 4,54 milliarder år lagt ned i ét kalenderår: 1. januar er "
        "dannelsen, 31. december er i dag. Dinosaurerne dør anden juledag.",
        "Earth's 4.54 billion years folded into a single calendar year: "
        "1 January is the formation, 31 December is today. The dinosaurs die "
        "the day after Christmas.",
        groups=("geoyear",),
    ),
    Bundle(
        "patternbundle", "Talmønsterpakken", "Number pattern pack", "🔢",
        "Dagene, hvor datoen selv går op: 22.02.2022, 11.12.13, 11.11.11 — "
        "og 06.07.42, hvor seks gange syv er toogfyrre. Ingen har bestemt "
        "dem; en regel finder dem.",
        "The days where the date itself works out: 22.02.2022, 11.12.13, "
        "11.11.11 — and 06.07.42, where six times seven is forty-two. Nobody "
        "chose them; a rule finds them.",
        groups=("palindrome", "sequence", "repunit", "binday", "pyth",
                "sqrtday", "fibday", "product", "sumday"),
    ),
    Bundle(
        "wackybundle", "Verden rundt på det skæve", "Round the world sideways", "🤪",
        "Vaffeldagen, der opstod af en hørefejl. Byen, der kaster appelsiner "
        "efter hinanden. Osten, ingen kan indhente. Dagen for at mislykkes.",
        "The waffle holiday that began as a mishearing. The town that pelts "
        "itself with oranges. The cheese nobody can catch. The day for failing.",
        groups=("wacky",),
    ),
    Bundle(
        "fsmbundle", "Spaghettimonsteret", "The Spaghetti Monster", "🍝",
        "Hele den pastafarianske kalender — og den har en helligdag for hver "
        "eneste dag i året. Pastover, Ramendan, dørslaget og 361 til.",
        "The entire Pastafarian calendar — and it has a holy day for every "
        "single day of the year. Pastover, Ramendan, the colander and 361 "
        "more.",
        groups=("fsm",),
    ),
    Bundle(
        "partybundle", "Hele festkalenderen", "The whole party calendar", "🎉",
        "Alle de skrevne festdage på én gang: popkultur, dansk, fiktion, "
        "figurer, science fiction, videnskab og nørdehistorie.",
        "Every written celebration day at once: pop culture, Danish, fiction, "
        "characters, science fiction, science and nerd history.",
        groups=("pop", "dkday", "wacky", "fsm", "techday", "birthdays",
                "fiction", "chars", "scifi", "sciday", "scihist", "nerdhist",
                "geoyear", "anniversary"),
    ),
)

BUNDLES_BY_KEY: dict[str, Bundle] = {b.key: b for b in BUNDLES}


def _M(*args, **kwargs) -> Milestone:
    return Milestone(*args, **kwargs)


# =========================================================================
# ⏱️  SEKUNDER
# =========================================================================

_SECONDS: list[Milestone] = [
    _M("sec_1e6", "sec", "sec", 1_000_000, live=True),
    _M("sec_1e7", "sec", "sec", 10_000_000, live=True),
    _M("sec_1e8", "sec", "sec", 100_000_000, live=True),
    _M("sec_123456789", "sec", "sec", 123_456_789, live=True,
       why_da="Cifrene 1 til 9 i rækkefølge — det mest velopdragne tal i hele kataloget.",
       why_en="The digits 1 through 9 in order — the best-behaved number in the catalogue."),
    _M("sec_25e7", "sec", "sec", 250_000_000),
    _M("sec_5e8", "sec", "sec", 500_000_000, live=True),
    _M("sec_666666666", "sec", "sec", 666_666_666,
       why_da="Ni seksere. 666 er „dyrets tal“ fra Johannes' Åbenbaring — en god anledning til djævelsk kage.",
       why_en="Nine sixes. 666 is the “number of the beast” — a fine excuse for devil's food cake."),
    _M("sec_75e7", "sec", "sec", 750_000_000),
    _M("sec_777777777", "sec", "sec", 777_777_777,
       why_da="Ni syvere. 7 er det mest populære lykketal i næsten alle kulturer.",
       why_en="Nine sevens. Seven is the most popular lucky number in almost every culture."),
    _M("sec_888888888", "sec", "sec", 888_888_888,
       why_da="Ni ottere. I kinesisk talkultur er 8 det heldigste ciffer, fordi ordet lyder som „velstand“ — derfor åbnede OL i Beijing 8.8.2008 kl. 20.08.",
       why_en="Nine eights. In Chinese number culture 8 is the luckiest digit because it sounds like “prosperity” — which is why the Beijing Olympics opened on 8.8.2008 at 8:08pm."),
    _M("sec_1e9", "sec", "sec", 1_000_000_000, star=True, live=True,
       why_da="ET GIGASEKUND — den klassiske nørdefødselsdag. 10⁹ sekunder er præcis 11.574 døgn, 1 time, 46 minutter og 40 sekunder, altså cirka 31 år og 8 måneder.",
       why_en="ONE GIGASECOND — the classic nerd birthday. 10^9 seconds is exactly 11,574 days, 1 hour, 46 minutes and 40 seconds, or about 31 years and 8 months."),
    _M("sec_1111111111", "sec", "sec", 1_111_111_111, live=True,
       why_da="Ti ettere i træk. Unix-tiden ramte netop dette tal 18. marts 2005.",
       why_en="Ten ones in a row. Unix time hit this exact number on 18 March 2005."),
    _M("sec_1234567890", "sec", "sec", 1_234_567_890, star=True, live=True,
       why_da="Det mest fejrede tal i Unix-historien. Her er det dit helt eget 1234567890. sekund.",
       why_en="The most celebrated number in Unix history. This is your very own 1234567890th second."),
    _M("sec_13e8", "sec", "sec", 1_300_000_000),
    _M("sec_1_5e9", "sec", "sec", 1_500_000_000, live=True),
    _M("sec_2e9", "sec", "sec", 2_000_000_000, star=True, live=True),
    _M("sec_2_5e9", "sec", "sec", 2_500_000_000),
    _M("sec_3e9", "sec", "sec", 3_000_000_000, live=True),
    _M("sec_3_5e9", "sec", "sec", 3_500_000_000),
    _M("sec_4e9", "sec", "sec", 4_000_000_000),
]

# =========================================================================
# 🕐  MINUTTER OG TIMER
# =========================================================================

_MIN_HOUR: list[Milestone] = [
    _M("min_525600", "minhour", "min", 525_600,
       why_da="525.600 minutter er præcis ét år — som i sangen „Seasons of Love“ fra musicalen RENT.",
       why_en="525,600 minutes is exactly one year — as in “Seasons of Love” from the musical RENT."),
    _M("min_1e6", "minhour", "min", 1_000_000, star=True, live=True),
    _M("min_2e6", "minhour", "min", 2_000_000),
    _M("min_3628800", "minhour", "min", 3_628_800,
       why_da="10 fakultet: 1×2×3×…×10 = 3.628.800.",
       why_en="10 factorial: 1x2x3x...x10 = 3,628,800."),
    _M("min_5e6", "minhour", "min", 5_000_000, live=True),
    _M("min_1e7", "minhour", "min", 10_000_000, star=True, live=True),
    _M("min_15e6", "minhour", "min", 15_000_000),
    _M("min_2e7", "minhour", "min", 20_000_000, live=True),
    _M("min_22222222", "minhour", "min", 22_222_222,
       why_da="Otte toere i træk.",
       why_en="Eight twos in a row."),
    _M("min_25e6", "minhour", "min", 25_000_000),
    _M("min_33554432", "minhour", "min", 33_554_432,
       why_da="2²⁵ minutter. Computere tæller i toerpotenser, og dette er en rund halv milliard for en maskine.",
       why_en="2^25 minutes. Computers count in powers of two, and this is a round half-billion to a machine."),
    _M("min_4e7", "minhour", "min", 40_000_000),
    _M("min_5e7", "minhour", "min", 50_000_000),
    _M("min_67108864", "minhour", "min", 67_108_864,
       why_da="2²⁶ minutter.",
       why_en="2^26 minutes."),
    _M("hour_1e4", "minhour", "hour", 10_000, live=True),
    _M("hour_25e3", "minhour", "hour", 25_000),
    _M("hour_5e4", "minhour", "hour", 50_000),
    _M("hour_1e5", "minhour", "hour", 100_000, star=True, live=True),
    _M("hour_15e4", "minhour", "hour", 150_000),
    _M("hour_2e5", "minhour", "hour", 200_000),
    _M("hour_25e4", "minhour", "hour", 250_000, live=True),
    _M("hour_3e5", "minhour", "hour", 300_000),
    _M("hour_4e5", "minhour", "hour", 400_000),
    _M("hour_5e5", "minhour", "hour", 500_000, live=True),
    _M("hour_75e4", "minhour", "hour", 750_000),
    _M("hour_1e6", "minhour", "hour", 1_000_000, star=True),
    _M("hour_1048576", "minhour", "hour", 1_048_576,
       why_da="2²⁰ timer — en „megatime“ i computersprog.",
       why_en="2^20 hours — one “megahour” in computer terms."),
]

# =========================================================================
# 📅  DAGE OG UGER
# =========================================================================

_DAY_WEEK: list[Milestone] = [
    _M("day_100", "dayweek", "day", 100),
    _M("day_365", "dayweek", "day", 365),
    _M("day_500", "dayweek", "day", 500),
    _M("day_1000", "dayweek", "day", 1_000, star=True),
    _M("day_1500", "dayweek", "day", 1_500),
    _M("day_2000", "dayweek", "day", 2_000),
    _M("day_2500", "dayweek", "day", 2_500),
    _M("day_3000", "dayweek", "day", 3_000),
    _M("day_4000", "dayweek", "day", 4_000),
    _M("day_5000", "dayweek", "day", 5_000, star=True),
    _M("day_6000", "dayweek", "day", 6_000),
    _M("day_7000", "dayweek", "day", 7_000),
    _M("day_7500", "dayweek", "day", 7_500),
    _M("day_8000", "dayweek", "day", 8_000),
    _M("day_9000", "dayweek", "day", 9_000),
    _M("day_10000", "dayweek", "day", 10_000, star=True),
    _M("day_12345", "dayweek", "day", 12_345,
       why_da="Cifrene 1 til 5 i rækkefølge.",
       why_en="The digits 1 through 5 in order."),
    _M("day_15000", "dayweek", "day", 15_000),
    _M("day_17500", "dayweek", "day", 17_500),
    _M("day_20000", "dayweek", "day", 20_000, star=True),
    _M("day_23456", "dayweek", "day", 23_456,
       why_da="Cifrene 2 til 6 i rækkefølge.",
       why_en="The digits 2 through 6 in order."),
    _M("day_25000", "dayweek", "day", 25_000),
    _M("day_27500", "dayweek", "day", 27_500),
    _M("day_30000", "dayweek", "day", 30_000, star=True),
    _M("day_35000", "dayweek", "day", 35_000),
    _M("day_40000", "dayweek", "day", 40_000),
    _M("day_45000", "dayweek", "day", 45_000),
    _M("day_50000", "dayweek", "day", 50_000),
    _M("week_100", "dayweek", "week", 100),
    _M("week_250", "dayweek", "week", 250),
    _M("week_404", "dayweek", "week", 404,
       why_da="404 er HTTP-fejlkoden „Not Found“ — internettets mest berømte fejlmeddelelse.",
       why_en="404 is the HTTP status code “Not Found” — the most famous error message on the internet."),
    _M("week_500", "dayweek", "week", 500),
    _M("week_666", "dayweek", "week", 666),
    _M("week_750", "dayweek", "week", 750),
    _M("week_1000", "dayweek", "week", 1_000, star=True),
    _M("week_1024", "dayweek", "week", 1_024,
       why_da="2¹⁰ uger. For en programmør er 1024 „en rund tusind“.",
       why_en="2^10 weeks. To a programmer, 1024 is “a round thousand”."),
    _M("week_1250", "dayweek", "week", 1_250),
    _M("week_1500", "dayweek", "week", 1_500),
    _M("week_1750", "dayweek", "week", 1_750),
    _M("week_2000", "dayweek", "week", 2_000, star=True),
    _M("week_2500", "dayweek", "week", 2_500),
    _M("week_3000", "dayweek", "week", 3_000),
    _M("week_4000", "dayweek", "week", 4_000),
    _M("week_5000", "dayweek", "week", 5_000),
    _M("week_6000", "dayweek", "week", 6_000),
    _M("week_7000", "dayweek", "week", 7_000),
]

# =========================================================================
# 🗓️  MÅNEDER OG ÅR  (kalenderregning — samme dag i måneden, samme klokkeslæt)
# =========================================================================

_MONTH_YEAR: list[Milestone] = [
    _M("month_100", "monthyear", "cal_month", 100),
    _M("month_200", "monthyear", "cal_month", 200),
    _M("month_250", "monthyear", "cal_month", 250),
    _M("month_300", "monthyear", "cal_month", 300),
    _M("month_400", "monthyear", "cal_month", 400),
    _M("month_444", "monthyear", "cal_month", 444),
    _M("month_500", "monthyear", "cal_month", 500, star=True),
    _M("month_555", "monthyear", "cal_month", 555),
    _M("month_600", "monthyear", "cal_month", 600,
       why_da="600 måneder er præcis 50 år — samme dag, samme klokkeslæt.",
       why_en="600 months is exactly 50 years — same date, same time of day."),
    _M("month_666", "monthyear", "cal_month", 666),
    _M("month_750", "monthyear", "cal_month", 750),
    _M("month_777", "monthyear", "cal_month", 777),
    _M("month_888", "monthyear", "cal_month", 888),
    _M("month_1000", "monthyear", "cal_month", 1_000, star=True),
    _M("month_1234", "monthyear", "cal_month", 1_234),
    _M("month_1500", "monthyear", "cal_month", 1_500),
    _M("year_42", "monthyear", "cal_year", 42,
       why_da="42 er „svaret på det ultimative spørgsmål om livet, universet og det hele“ fra Douglas Adams' Hitchhiker's Guide to the Galaxy. Spørgsmålet kender man stadig ikke.",
       why_en="42 is “the Answer to the Ultimate Question of Life, the Universe, and Everything” from Douglas Adams' Hitchhiker's Guide to the Galaxy. The Question remains unknown."),
    _M("year_64", "monthyear", "cal_year", 64,
       why_da="2⁶ år — og alderen i Beatles' „When I'm Sixty-Four“.",
       why_en="2^6 years — and the age in the Beatles' “When I'm Sixty-Four”."),
    _M("tyear_pi", "monthyear", "trop_year", 3.14159265,
       why_da="π år gammel.",
       why_en="π years old."),
    _M("tyear_e", "monthyear", "trop_year", 2.718281828,
       why_da="e år gammel.",
       why_en="e years old."),
    _M("tyear_tau", "monthyear", "trop_year", 6.283185307,
       why_da="τ år gammel — tau, altså 2π.",
       why_en="τ years old — tau, that is 2π."),
    _M("tyear_10pi", "monthyear", "trop_year", 31.4159265,
       why_da="10π år.",
       why_en="10π years."),
    _M("tyear_10e", "monthyear", "trop_year", 27.18281828,
       why_da="10e år.",
       why_en="10e years."),
    _M("tyear_10phi", "monthyear", "trop_year", 16.18033989,
       why_da="10φ år — ti gange det gyldne snit.",
       why_en="10φ years — ten times the golden ratio."),
    _M("tyear_gelfond", "monthyear", "trop_year", 23.14069263,
       why_da="e^π år — Gelfonds konstant, et beviseligt transcendent tal.",
       why_en="e^π years — Gelfond's constant, a provably transcendental number."),
    _M("tyear_100", "monthyear", "cal_year", 100, star=True,
       why_da="Hundrede år på dagen — den fødselsdag, hvor kongehuset traditionelt sender en lykønskning.",
       why_en="A hundred years to the day — the birthday where, in Denmark, the royal house traditionally sends its congratulations."),
]

# =========================================================================
# 🔬  KONSTANTER  (alle i sekunder, saa de rammer midt i livet)
# =========================================================================

_CONSTANTS: list[Milestone] = [
    _M("c_pi_e8", "constants", "sec", 314_159_265, live=True,
       why_da="π × 10⁸ sekunder. π ≈ 3,14159 er forholdet mellem en cirkels omkreds og dens diameter — det samme for enhver cirkel i universet.",
       why_en="π x 10^8 seconds. π ≈ 3.14159 is the ratio of a circle's circumference to its diameter — the same for every circle in the universe."),
    _M("c_e_e8", "constants", "sec", 271_828_182, live=True,
       why_da="e × 10⁸ sekunder. e ≈ 2,71828 er Eulers tal: vækstens konstant, og den eneste funktion der er sin egen afledede.",
       why_en="e x 10^8 seconds. e ≈ 2.71828 is Euler's number: the constant of growth, and the only function that is its own derivative."),
    _M("c_tau_e8", "constants", "sec", 628_318_530,
       why_da="τ × 10⁸ sekunder. τ ≈ 6,28318 er tau, simpelthen 2π. Tilhængerne mener, τ er den rigtige cirkelkonstant, fordi én hel omgang er τ radianer.",
       why_en="τ x 10^8 seconds. τ ≈ 6.28318 is tau, simply 2π. Its advocates argue τ is the true circle constant, since one full turn is τ radians."),
    _M("c_gamma_e9", "constants", "sec", 577_215_664,
       why_da="γ × 10⁹ sekunder. γ ≈ 0,57722 er Euler-Mascheronis konstant: præcis hvor meget den harmoniske række løber foran den naturlige logaritme. Efter 300 år ved ingen, om den er rationel.",
       why_en="γ x 10^9 seconds. γ ≈ 0.57722 is the Euler-Mascheroni constant: exactly how far the harmonic series runs ahead of the natural logarithm. After 300 years nobody knows whether it is rational."),
    _M("c_avogadro", "constants", "sec", 602_214_076,
       why_da="Avogadros tal, 6,02214076×10²³, er antallet af partikler i ét mol. Her er cifrene skaleret ned til noget, et menneske kan nå.",
       why_en="Avogadro's number, 6.02214076x10^23, is the number of particles in one mole. Here the digits are scaled down to human range."),
    _M("c_light", "constants", "sec", 299_792_458, star=True, live=True,
       why_da="Lysets fart er pr. definition præcis 299.792.458 meter i sekundet — ikke målt, men defineret, siden metren i 1983 blev defineret ud fra den. Nu har du levet ét sekund for hver meter.",
       why_en="The speed of light is exactly 299,792,458 metres per second by definition — not measured but defined, since the metre was defined from it in 1983. You have now lived one second for every metre."),
    _M("c_sqrt2", "constants", "sec", 1_414_213_562,
       why_da="√2 × 10⁹ sekunder. √2 ≈ 1,41421 er diagonalen i et kvadrat med siden 1 og det første tal, mennesket beviste var irrationelt.",
       why_en="√2 x 10^9 seconds. √2 ≈ 1.41421 is the diagonal of a unit square and the first number humans proved irrational."),
    _M("c_phi", "constants", "sec", 1_618_033_988, star=True,
       why_da="φ × 10⁹ sekunder. φ ≈ 1,61803 er DET GYLDNE SNIT, (1+√5)/2 — det ene forhold hvor a/b = (a+b)/a. Fordi φ er det „mest irrationelle“ tal, der findes, er det den bedste måde at pakke ting, der ikke må ligge oven i hinanden: deraf spiralerne i solsikker og kogler.",
       why_en="φ x 10^9 seconds. φ ≈ 1.61803 is THE GOLDEN RATIO, (1+√5)/2 — the one ratio where a/b = (a+b)/a. Because φ is the “most irrational” number there is, it is the best way to pack things that must not overlap: hence the spirals in sunflowers and pine cones."),
    _M("c_pi_e9", "constants", "sec", 3_141_592_653,
       why_da="π × 10⁹ sekunder — du er knap 100 år.",
       why_en="π x 10^9 seconds — you are just under 100 years old."),
    _M("c_e_e9", "constants", "sec", 2_718_281_828,
       why_da="e × 10⁹ sekunder.",
       why_en="e x 10^9 seconds."),
    _M("c_12fact", "constants", "sec", 479_001_600,
       why_da="12 fakultet, 1×2×3×…×12. Det største fakultet, der kan rummes i en 32-bit variabel.",
       why_en="12 factorial, 1x2x3x...x12. The largest factorial that fits in a 32-bit integer."),
]

# =========================================================================
# 🧮  NØRDETAL
# =========================================================================

_NERD: list[Milestone] = [
    _M("n_day_1024", "nerd", "day", 1_024,
       why_da="2¹⁰ dage.",
       why_en="2^10 days."),
    _M("n_day_1337", "nerd", "day", 1_337,
       why_da="1337 er „leet“ — hacker- og gamerslang for „elite“, skrevet med tal i stedet for bogstaver (l=1, e=3, t=7). Fra 1990'ernes BBS- og internetkultur.",
       why_en="1337 is “leet” — hacker and gamer slang for “elite”, spelled with digits instead of letters (l=1, e=3, t=7). Straight out of 1990s BBS and internet culture."),
    _M("n_day_1729", "nerd", "day", 1_729,
       why_da="Taxitallet. Hardy besøgte Ramanujan på sygehuset og bemærkede, at hans taxi havde det kedelige nummer 1729. Ramanujan svarede straks fra sengen, at det tværtimod er det mindste tal, der kan skrives som en sum af to terninger på to måder: 1³+12³ = 9³+10³.",
       why_en="The taxicab number. Hardy visited Ramanujan in hospital and remarked that his taxi had the dull number 1729. Ramanujan replied at once that on the contrary it is the smallest number expressible as a sum of two cubes in two ways: 1^3+12^3 = 9^3+10^3."),
    _M("n_day_2048", "nerd", "day", 2_048,
       why_da="2¹¹ dage.",
       why_en="2^11 days."),
    _M("n_day_2520", "nerd", "day", 2_520,
       why_da="Det mindste tal, der kan deles med alle tal fra 1 til 10.",
       why_en="The smallest number divisible by every number from 1 to 10."),
    _M("n_day_3125", "nerd", "day", 3_125,
       why_da="5⁵ dage.",
       why_en="5^5 days."),
    _M("n_day_4096", "nerd", "day", 4_096,
       why_da="2¹² dage = 0x1000 hexadecimalt. Størrelsen på en klassisk hukommelsesside.",
       why_en="2^12 days = 0x1000 in hexadecimal. The size of a classic memory page."),
    _M("n_day_5050", "nerd", "day", 5_050,
       why_da="Summen af alle tal fra 1 til 100 — og dermed også et trekanttal. Gauss regnede den ud i hovedet som skoledreng: han parrede 1+100, 2+99, 3+98 og så videre, fik 50 par à 101, og var færdig, før læreren havde sat sig.",
       why_en="The sum of every number from 1 to 100 — and therefore a triangular number too. Gauss worked it out in his head as a schoolboy: he paired 1+100, 2+99, 3+98 and so on, got 50 pairs of 101, and was done before the teacher had sat down."),
    _M("n_day_6174", "nerd", "day", 6_174,
       why_da="Kaprekars konstant. Tag et vilkårligt firecifret tal med mindst to forskellige cifre, sortér cifrene op og ned, træk det mindste fra det største, og gentag. Du ender altid på 6174 — og altid inden for syv skridt.",
       why_en="Kaprekar's constant. Take any four-digit number with at least two different digits, sort its digits up and down, subtract the smaller from the larger, and repeat. You always end at 6174 — and always within seven steps."),
    _M("n_day_6765", "nerd", "day", 6_765,
       why_da="Fibonacci-tal nr. 20. Hvert tal i rækken er summen af de to foregående: 1, 1, 2, 3, 5, 8, 13, 21 …",
       why_en="The 20th Fibonacci number. Each number in the sequence is the sum of the two before it: 1, 1, 2, 3, 5, 8, 13, 21 ..."),
    _M("n_day_8128", "nerd", "day", 8_128,
       why_da="Et perfekt tal: summen af alle dets egne divisorer er præcis tallet selv. Kun 51 perfekte tal kendes, og man ved stadig ikke, om der findes ulige af slagsen.",
       why_en="A perfect number: the sum of its own divisors is exactly itself. Only 51 perfect numbers are known, and nobody knows whether any odd ones exist."),
    _M("n_day_8191", "nerd", "day", 8_191,
       why_da="2¹³ − 1, et Mersenne-primtal. Fundet i 1588 og i 300 år det største kendte primtal.",
       why_en="2^13 - 1, a Mersenne prime. Found in 1588 and for 300 years the largest prime known."),
    _M("n_day_8192", "nerd", "day", 8_192,
       why_da="2¹³ dage.",
       why_en="2^13 days."),
    _M("n_day_10007", "nerd", "day", 10_007,
       why_da="Det mindste femcifrede primtal.",
       why_en="The smallest five-digit prime."),
    _M("n_day_10946", "nerd", "day", 10_946,
       why_da="Fibonacci-tal nr. 21.",
       why_en="The 21st Fibonacci number."),
    _M("n_day_11high", "nerd", "day", 11_111,
       why_da="Et repunit — et tal, der kun består af ettaller.",
       why_en="A repunit — a number made only of ones."),
    _M("n_day_15127", "nerd", "day", 15_127,
       why_da="Lucas-tal. Lucas-rækken følger samme regel som Fibonacci, men starter med 2 og 1 i stedet for 1 og 1: 2, 1, 3, 4, 7, 11, 18, 29 …",
       why_en="A Lucas number. The Lucas sequence follows the same rule as Fibonacci but starts 2, 1 instead of 1, 1: 2, 1, 3, 4, 7, 11, 18, 29 ..."),
    _M("n_day_16384", "nerd", "day", 16_384,
       why_da="2¹⁴ dage.",
       why_en="2^14 days."),
    _M("n_day_16807", "nerd", "day", 16_807,
       why_da="7⁵ dage.",
       why_en="7^5 days."),
    _M("n_day_17711", "nerd", "day", 17_711,
       why_da="Fibonacci-tal nr. 22.",
       why_en="The 22nd Fibonacci number."),
    _M("n_day_19683", "nerd", "day", 19_683,
       why_da="3⁹ dage.",
       why_en="3^9 days."),
    _M("n_day_20100", "nerd", "day", 20_100,
       why_da="Trekanttal. Læg prikker i en fyldt trekant: 1 prik, så en række med 2 nedenunder (i alt 3), så en med 3 (i alt 6), så en med 4 (i alt 10). Det er præcis sådan keglerne står, når du bowler (10), og kuglerne i en pooltrekant (15). 20.100 er trekanttal nummer 200 — altså 1+2+3+…+200, eller kort sagt 200×201/2.",
       why_en="A triangular number. Stack dots in a filled triangle: 1 dot, then a row of 2 beneath it (3 in all), then a row of 3 (6 in all), then a row of 4 (10 in all). That is exactly how the pins stand in ten-pin bowling (10) and the balls sit in a pool rack (15). 20,100 is the 200th triangular number — 1+2+3+...+200, or 200x201/2 for short."),
    _M("n_day_28657", "nerd", "day", 28_657,
       why_da="Fibonacci-tal nr. 23 — og samtidig et primtal. Den kombination er sjælden.",
       why_en="The 23rd Fibonacci number — and prime as well. That combination is rare."),
    _M("n_day_32768", "nerd", "day", 32_768,
       why_da="2¹⁵ dage — grænsen for en 16-bit variabel.",
       why_en="2^15 days — the limit of a signed 16-bit integer."),
    _M("n_day_46368", "nerd", "day", 46_368,
       why_da="Fibonacci-tal nr. 24.",
       why_en="The 24th Fibonacci number."),
    _M("n_day_46656", "nerd", "day", 46_656,
       why_da="6⁶ dage.",
       why_en="6^6 days."),
    _M("n_day_48879", "nerd", "day", 48_879,
       why_da="48.879 er 0xBEEF i hexadecimal. Fordi hex bruger cifrene 0-9 og bogstaverne A-F, kan man stave ord med tal — og det har programmører moret sig med siden 1960'erne. Den slags „magiske tal“ skrives i hukommelsen, så man bagefter kan se, om noget har rørt ved den.",
       why_en="48,879 is 0xBEEF in hexadecimal. Because hex uses the digits 0-9 and the letters A-F, you can spell words with numbers — and programmers have amused themselves with this since the 1960s. Such “magic numbers” get written into memory so you can tell afterwards whether anything touched it."),
    _M("n_day_51966", "nerd", "day", 51_966,
       why_da="0xCAFE. Enhver Java-klassefil begynder med de fire bytes 0xCAFEBABE.",
       why_en="0xCAFE. Every Java class file begins with the four bytes 0xCAFEBABE."),
    _M("n_sec_2_30", "nerd", "sec", 1_073_741_824,
       why_da="2³⁰ sekunder. For en computer er dette „en milliard“ — præcis én gibibyte talt i sekunder.",
       why_en="2^30 seconds. To a computer this is “one billion” — exactly one gibibyte, counted in seconds."),
    _M("n_sec_2_31", "nerd", "sec", 2_147_483_647, star=True,
       why_da="2³¹ − 1, det største tal en 32-bit heltalsvariabel kan rumme. Når Unix-tiden rammer det 19. januar 2038, triller gamle systemer rundt og tror, det er 1901.",
       why_en="2^31 - 1, the largest value a signed 32-bit integer can hold. When Unix time reaches it on 19 January 2038, old systems roll over and think it is 1901."),
    _M("n_sec_2_32", "nerd", "sec", 4_294_967_296,
       why_da="2³² sekunder — antallet af IPv4-adresser i hele verden.",
       why_en="2^32 seconds — the number of IPv4 addresses in the entire world."),
    _M("n_sec_42e6", "nerd", "sec", 42_000_000,
       why_da="42 millioner sekunder. 42 er svaret på det ultimative spørgsmål.",
       why_en="42 million seconds. 42 is the Answer to the Ultimate Question."),
    _M("n_sec_0x10000000", "nerd", "sec", 268_435_456,
       why_da="268.435.456 skrives 0x10000000 i hexadecimal — talsystemet med 16 cifre, som programmører regner i. Præfikset 0x betyder blot „dette er hexadecimalt“. Et ettal med syv nuller efter er lige så rundt et tal i hex, som 10.000.000 er hos os, og det svarer til 2²⁸.",
       why_en="268,435,456 is written 0x10000000 in hexadecimal — the base-16 number system programmers count in. The 0x prefix just means “this is hex”. A one followed by seven zeros is as round a number in hex as 10,000,000 is for us, and it equals 2^28."),
    _M("n_sec_deadbeef", "nerd", "sec", 3_735_928_559,
       why_da="0xDEADBEEF — det mest berømte magiske tal i programmering, brugt siden 1960'erne til at markere ubrugt hukommelse.",
       why_en="0xDEADBEEF — the most famous magic number in programming, used since the 1960s to mark unused memory."),
    _M("n_week_1337", "nerd", "week", 1_337,
       why_da="1337 uger — leet, nu i uger. Godt 25 år.",
       why_en="1337 weeks — leet, now in weeks. A little over 25 years."),
    _M("n_month_144", "nerd", "cal_month", 144,
       why_da="Fibonacci-tal nr. 12 — og det eneste Fibonacci-tal (ud over 1), der også er et kvadrattal: 12².",
       why_en="The 12th Fibonacci number — and the only Fibonacci number besides 1 that is also a perfect square: 12^2."),
]

# =========================================================================
# 🧪  73 — TALLENES CHUCK NORRIS
#
# De tre 5318008-poster nederst har med vilje ingen forklaring.
# =========================================================================

_S73: list[Milestone] = [
    _M("s73_day_73", "s73", "day", 73,
       why_da="73 døgn — det bedste tal i den mindste enhed, der kan nå at føles som noget.",
       why_en="73 days — the best number in the smallest unit that has time to feel like anything."),
    _M("s73_day_730", "s73", "day", 730,
       why_da="10 × 73 døgn. Og tilfældigvis næsten præcis to år.",
       why_en="10 x 73 days. And as it happens, almost exactly two years."),
    _M("s73_day_7300", "s73", "day", 7_300,
       why_da="100 × 73 døgn — og kun fem døgn fra at være 20 år.",
       why_en="100 x 73 days — and only five days short of 20 years."),
    _M("s73_day_14600", "s73", "day", 14_600,
       why_da="200 × 73 døgn, omkring 40 år.",
       why_en="200 x 73 days, around 40 years."),
    _M("s73_day_21900", "s73", "day", 21_900,
       why_da="300 × 73 døgn, omkring 60 år.",
       why_en="300 x 73 days, around 60 years."),
    _M("s73_day_29200", "s73", "day", 29_200,
       why_da="400 × 73 døgn, omkring 80 år.",
       why_en="400 x 73 days, around 80 years."),
    _M("s73_day_36500", "s73", "day", 36_500,
       why_da="500 × 73 døgn. Det er også 365 × 100, så du er kun en uges tid fra at være 100 år.",
       why_en="500 x 73 days. It is also 365 x 100, so you are about a week short of 100 years."),
    _M("s73_week_73", "s73", "week", 73,
       why_da="73 uger, altså 511 døgn.",
       why_en="73 weeks, that is 511 days."),
    _M("s73_week_730", "s73", "week", 730,
       why_da="10 × 73 uger — 5.110 døgn, eller godt 14 år.",
       why_en="10 x 73 weeks — 5,110 days, or a little over 14 years."),
    _M("s73_week_1460", "s73", "week", 1_460,
       why_da="20 × 73 uger, knap 28 år.",
       why_en="20 x 73 weeks, just under 28 years."),
    _M("s73_week_2190", "s73", "week", 2_190,
       why_da="30 × 73 uger, knap 42 år.",
       why_en="30 x 73 weeks, just under 42 years."),
    _M("s73_week_3650", "s73", "week", 3_650,
       why_da="50 × 73 uger, knap 70 år.",
       why_en="50 x 73 weeks, just under 70 years."),
    _M("s73_month_73", "s73", "cal_month", 73,
       why_da="73 måneder er seks år og en måned — på dagen, på klokkeslættet.",
       why_en="73 months is six years and one month — to the day and to the minute."),
    _M("s73_month_730", "s73", "cal_month", 730,
       why_da="10 × 73 måneder, altså 60 år og 10 måneder på dagen.",
       why_en="10 x 73 months, that is 60 years and 10 months to the day."),
    _M("s73_month_1460", "s73", "cal_month", 1_460,
       why_da="20 × 73 måneder — 121 år og 8 måneder. Rekorden er 122, så den er lige på kanten.",
       why_en="20 x 73 months — 121 years and 8 months. The record is 122, so this one is right at the edge."),
    _M("s73_year_73", "s73", "cal_year", 73, star=True,
       why_da="73 år gammel — det bedste tal, i den bedste alder.",
       why_en="73 years old — the best number, at the best age."),
    _M("s73_hour_73000", "s73", "hour", 73_000,
       why_da="1.000 × 73 timer, godt 8 år.",
       why_en="1,000 x 73 hours, a little over 8 years."),
    _M("s73_hour_730000", "s73", "hour", 730_000,
       why_da="10.000 × 73 timer, godt 83 år.",
       why_en="10,000 x 73 hours, a little over 83 years."),
    _M("s73_min_7300000", "s73", "min", 7_300_000,
       why_da="100.000 × 73 minutter, knap 14 år.",
       why_en="100,000 x 73 minutes, just under 14 years."),
    _M("s73_min_73000000", "s73", "min", 73_000_000,
       why_da="1.000.000 × 73 minutter, knap 139 år.",
       why_en="1,000,000 x 73 minutes, just under 139 years."),
    _M("s73_sec_73e6", "s73", "sec", 73_000_000,
       why_da="73 millioner sekunder, godt 2 år.",
       why_en="73 million seconds, a little over 2 years."),
    _M("s73_sec_730e6", "s73", "sec", 730_000_000, live=True,
       why_da="730 millioner sekunder, godt 23 år.",
       why_en="730 million seconds, a little over 23 years."),
    _M("s73_sec_1460e6", "s73", "sec", 1_460_000_000,
       why_da="To gange 730 millioner sekunder, godt 46 år.",
       why_en="Twice 730 million seconds, a little over 46 years."),
    _M("s73_sec_2190e6", "s73", "sec", 2_190_000_000,
       why_da="Tre gange 730 millioner sekunder, knap 70 år.",
       why_en="Three times 730 million seconds, just under 70 years."),
    _M("s73_min_1001001", "s73", "min", 1_001_001,
       why_da="1001001 minutter — 73 skrevet binært.",
       why_en="1001001 minutes — that is 73 written in binary."),
    _M("s73_5318008_sec", "s73", "sec", 5_318_008, silent=True),
    _M("s73_5318008_min", "s73", "min", 5_318_008, silent=True),
    _M("s73_5318008_hour", "s73", "hour", 53_180.08, silent=True),
]

# =========================================================================
# 🔢  GENTAGNE OG SPEJLVENDTE TAL
# =========================================================================

_REPEAT: list[Milestone] = [
    _M("r_day_1111", "repeat", "day", 1_111),
    _M("r_day_2222", "repeat", "day", 2_222),
    _M("r_day_3333", "repeat", "day", 3_333),
    _M("r_day_4444", "repeat", "day", 4_444),
    _M("r_day_5555", "repeat", "day", 5_555),
    _M("r_day_6666", "repeat", "day", 6_666),
    _M("r_day_7777", "repeat", "day", 7_777),
    _M("r_day_8888", "repeat", "day", 8_888),
    _M("r_day_9999", "repeat", "day", 9_999),
    _M("r_day_22222", "repeat", "day", 22_222),
    _M("r_day_33333", "repeat", "day", 33_333),
    _M("r_day_44444", "repeat", "day", 44_444),
    _M("r_day_1001", "repeat", "day", 1_001,
       why_da="En palindrom — den læses ens begge veje. Og 1001 nat, hvis man er til eventyr.",
       why_en="A palindrome — it reads the same both ways. And 1001 nights, if you like a good story."),
    _M("r_day_2002", "repeat", "day", 2_002),
    _M("r_day_5005", "repeat", "day", 5_005),
    _M("r_day_9009", "repeat", "day", 9_009),
    _M("r_day_10001", "repeat", "day", 10_001),
    _M("r_day_12321", "repeat", "day", 12_321,
       why_da="En palindrom, der tilmed tæller op og ned igen.",
       why_en="A palindrome that counts up and back down again."),
    _M("r_day_20002", "repeat", "day", 20_002),
    _M("r_day_23432", "repeat", "day", 23_432),
    _M("r_day_30003", "repeat", "day", 30_003),
    _M("r_day_34543", "repeat", "day", 34_543),
    _M("r_day_45654", "repeat", "day", 45_654),
    _M("r_week_1111", "repeat", "week", 1_111),
    _M("r_week_2222", "repeat", "week", 2_222),
    _M("r_week_3333", "repeat", "week", 3_333),
    _M("r_month_111", "repeat", "cal_month", 111),
    _M("r_month_222", "repeat", "cal_month", 222),
    _M("r_month_333", "repeat", "cal_month", 333),
    _M("r_month_444", "repeat", "cal_month", 444),
    _M("r_month_555", "repeat", "cal_month", 555),
    _M("r_month_666", "repeat", "cal_month", 666),
    _M("r_month_777", "repeat", "cal_month", 777),
    _M("r_month_888", "repeat", "cal_month", 888),
    _M("r_month_999", "repeat", "cal_month", 999),
    _M("r_year_1111", "repeat", "trop_year", 11.11),
    _M("r_year_2222", "repeat", "trop_year", 22.22),
    _M("r_year_3333", "repeat", "trop_year", 33.33),
    _M("r_year_4444", "repeat", "trop_year", 44.44),
    _M("r_year_5555", "repeat", "trop_year", 55.55),
    _M("r_year_6666", "repeat", "trop_year", 66.66),
    _M("r_year_7777", "repeat", "trop_year", 77.77),
    _M("r_year_8888", "repeat", "trop_year", 88.88),
    _M("r_year_9999", "repeat", "trop_year", 99.99),
    _M("r_hour_111111", "repeat", "hour", 111_111),
    _M("r_min_1111111", "repeat", "min", 1_111_111),
    _M("r_min_11111111", "repeat", "min", 11_111_111),
    _M("r_sec_11111111", "repeat", "sec", 11_111_111),
    _M("r_sec_123454321", "repeat", "sec", 123_454_321,
       why_da="En palindrom, der tæller op til 5 og ned igen.",
       why_en="A palindrome counting up to 5 and back down."),
]

# =========================================================================
# ⚛️  EKSOTISKE ENHEDER
# =========================================================================

_EXOTIC: list[Milestone] = [
    _M("x_cs_1e18", "exotic", "cs133", 1e18,
       why_da="10¹⁸ svingninger i et cæsium-133-atom. Ét sekund er pr. definition 9.192.631.770 af dem.",
       why_en="10^18 oscillations of a caesium-133 atom. One second is by definition 9,192,631,770 of them."),
    _M("x_cs_5e18", "exotic", "cs133", 5e18,
       why_da="Fem trillioner cæsiumsvingninger.",
       why_en="Five quintillion caesium oscillations."),
    _M("x_cs_giga", "exotic", "cs133", 9.19263177e18, star=True,
       why_da="9.192.631.770 × 10⁹ cæsiumperioder — præcis ét gigasekund, udtrykt i den enhed sekundet faktisk er defineret ved. Du fejrer det samme øjeblik to gange.",
       why_en="9,192,631,770 x 10^9 caesium periods — exactly one gigasecond, expressed in the unit the second is actually defined by. You celebrate the same instant twice."),
    _M("x_cs_1e19", "exotic", "cs133", 1e19,
       why_da="Ti trillioner cæsiumsvingninger, godt 34 år.",
       why_en="Ten quintillion caesium oscillations, a little over 34 years."),
    _M("x_cs_2e19", "exotic", "cs133", 2e19,
       why_da="Knap 69 år talt i cæsiumsvingninger.",
       why_en="Just under 69 years, counted in caesium oscillations."),
    _M("x_cs_3e19", "exotic", "cs133", 3e19,
       why_da="Godt 103 år talt i cæsiumsvingninger.",
       why_en="A little over 103 years, counted in caesium oscillations."),
    _M("x_cs_4e19", "exotic", "cs133", 4e19,
       why_da="Knap 138 år talt i cæsiumsvingninger.",
       why_en="Just under 138 years, counted in caesium oscillations."),
    _M("x_jiffy_1e18", "exotic", "jiffy", 1e18,
       why_da="En jiffy er den tid, lyset bruger om at tilbagelægge én centimeter: 33,356 pikosekunder. 10¹⁸ af dem er godt ét år.",
       why_en="A jiffy is the time light takes to travel one centimetre: 33.356 picoseconds. 10^18 of them is a bit over a year."),
    _M("x_jiffy_3e18", "exotic", "jiffy", 3e18,
       why_da="Tre trillioner jiffies, godt tre år.",
       why_en="Three quintillion jiffies, a little over three years."),
    _M("x_jiffy_1e19", "exotic", "jiffy", 1e19,
       why_da="Godt ti et halvt år målt i lysets tid over en centimeter.",
       why_en="A little over ten and a half years, measured in the time light takes to cross a centimetre."),
    _M("x_jiffy_3e19", "exotic", "jiffy", 3e19,
       why_da="3 × 10¹⁹ jiffies — og næsten præcis ét gigasekund.",
       why_en="3 x 10^19 jiffies — and almost exactly one gigasecond."),
    _M("x_jiffy_5e19", "exotic", "jiffy", 5e19,
       why_da="Knap 53 år i jiffies.",
       why_en="Just under 53 years in jiffies."),
    _M("x_jiffy_1e20", "exotic", "jiffy", 1e20,
       why_da="Godt 105 år i jiffies — hundrede trillioner af dem.",
       why_en="A little over 105 years in jiffies — a hundred quintillion of them."),
    _M("x_jiffy_1337e17", "exotic", "jiffy", 1.337e20,
       why_da="1,337 × 10²⁰ jiffies — fordi leet.",
       why_en="1.337 x 10^20 jiffies — because leet."),
    # Kulstof-14. Tidspunkterne er regnet ud af halveringstiden, ikke gaettet.
    _M("x_c14_999", "exotic", "trop_year", c14_years(0.999),
       label_da="99,9 % af kulstof-14 tilbage", label_en="99.9% of carbon-14 left",
       why_da="En prøve kulstof-14, der blev lukket inde den dag du blev født, har nu mistet én promille. Resten er blevet til kvælstof-14.",
       why_en="A sample of carbon-14 sealed away the day you were born has now lost one part in a thousand. The rest has turned into nitrogen-14."),
    _M("x_c14_995", "exotic", "trop_year", c14_years(0.995),
       label_da="99,5 % af kulstof-14 tilbage", label_en="99.5% of carbon-14 left",
       why_da="Et halvt procent er henfaldet. Det tager 41 år og fem måneder.",
       why_en="Half a percent has decayed. That takes 41 years and five months."),
    _M("x_c14_99", "exotic", "trop_year", c14_years(0.99), star=True,
       label_da="99 % af kulstof-14 tilbage", label_en="99% of carbon-14 left",
       why_da="Nu er præcis én procent henfaldet. Det tager 83 år og en måned — regnet ud af halveringstiden på 5730 år, ikke gættet. Se noten om kulstof-14.",
       why_en="Exactly one percent has now decayed. It takes 83 years and one month — computed from the 5730-year half-life, not guessed. See the carbon-14 note."),
    _M("x_c14_985", "exotic", "trop_year", c14_years(0.985),
       label_da="98,5 % af kulstof-14 tilbage", label_en="98.5% of carbon-14 left",
       why_da="Halvandet procent er henfaldet, efter knap 125 år.",
       why_en="One and a half percent has decayed, after just under 125 years."),
]

# =========================================================================
# 🌙  MÅNEN   (skoen — synodisk maaned 29,530589 doegn)
# =========================================================================

_MOON: list[Milestone] = [
    _M("moon_100", "moon", "lunation", 100,
       why_da="100 nymåner siden du blev født, godt otte år. En synodisk måned — nymåne til nymåne — er 29,530589 døgn.",
       why_en="100 new moons since you were born, a little over eight years. A synodic month — new moon to new moon — is 29.530589 days."),
    _M("moon_200", "moon", "lunation", 200,
       why_da="200 nymåner, godt 16 år.",
       why_en="200 new moons, a little over 16 years."),
    _M("moon_250", "moon", "lunation", 250,
       why_da="250 nymåner, godt 20 år. Ved 235 nymåner — den metoniske cyklus — falder månens faser igen på samme kalenderdato, og det er stadig grundlaget for at beregne påsken.",
       why_en="250 new moons, a little over 20 years. At 235 new moons — the Metonic cycle — the moon phases fall on the same calendar date again, and that is still how Easter is calculated."),
    _M("moon_300", "moon", "lunation", 300,
       why_da="300 nymåner, godt 24 år.",
       why_en="300 new moons, a little over 24 years."),
    _M("moon_400", "moon", "lunation", 400,
       why_da="400 nymåner, godt 32 år.",
       why_en="400 new moons, a little over 32 years."),
    _M("moon_500", "moon", "lunation", 500, star=True,
       why_da="Din 500. fuldmåne. En synodisk måned — fra nymåne til nymåne — er 29,530589 døgn.",
       why_en="Your 500th full moon. A synodic month — new moon to new moon — is 29.530589 days."),
    _M("moon_600", "moon", "lunation", 600,
       why_da="600 nymåner, knap 49 år.",
       why_en="600 new moons, just under 49 years."),
    _M("moon_700", "moon", "lunation", 700,
       why_da="700 nymåner, godt 56 år.",
       why_en="700 new moons, a little over 56 years."),
    _M("moon_800", "moon", "lunation", 800,
       why_da="800 nymåner, knap 65 år.",
       why_en="800 new moons, just under 65 years."),
    _M("moon_900", "moon", "lunation", 900,
       why_da="900 nymåner, godt 72 år.",
       why_en="900 new moons, a little over 72 years."),
    _M("moon_1000", "moon", "lunation", 1_000, star=True,
       why_da="1.000 nymåner, godt 80 år. Du har set månen blive fuld tusind gange.",
       why_en="1,000 new moons, a little over 80 years. You have watched the moon fill a thousand times."),
    _M("moon_1234", "moon", "lunation", 1_234,
       why_da="1.234 nymåner — cifrene 1 til 4 i rækkefølge, og knap 100 år.",
       why_en="1,234 new moons — the digits 1 to 4 in order, and just under 100 years."),
    _M("moon_1500", "moon", "lunation", 1_500,
       why_da="1.500 nymåner, godt 121 år.",
       why_en="1,500 new moons, a little over 121 years."),
]

# =========================================================================
# 🚀  RUMREJSEN
# =========================================================================

_SPACE: list[Milestone] = [
    _M("sp_km_1e9", "space", "orbit_km", 1e9, star=True,
       why_da="Én milliard kilometer rundt om Solen. Jorden kører 29,8 km/s, så du har rejst langt uden at løfte en finger.",
       why_en="One billion kilometres around the Sun. The Earth moves at 29.8 km/s, so you have travelled a long way without lifting a finger."),
    _M("sp_lighthour", "space", "orbit_km", 1_079_252_848.8,
       why_da="Du har fulgt Jorden én lystime gennem rummet — 1.079.252.849 km.",
       why_en="You have ridden the Earth one light-hour through space — 1,079,252,849 km."),
    _M("sp_km_5e9", "space", "orbit_km", 5e9,
       why_da="Fem milliarder kilometer — lidt længere end fra Solen ud til Neptun.",
       why_en="Five billion kilometres — slightly further than from the Sun out to Neptune."),
    _M("sp_km_1e10", "space", "orbit_km", 1e10,
       why_da="Ti milliarder kilometer: forbi Pluto og et godt stykke ud i Kuiperbæltet.",
       why_en="Ten billion kilometres: past Pluto and well into the Kuiper belt."),
    _M("sp_lightday", "space", "orbit_km", 25_902_068_371.2,
       why_da="Ét lysdøgn gennem rummet — 25,9 milliarder km i din bane om Solen.",
       why_en="One light-day through space — 25.9 billion km along your orbit around the Sun."),
    _M("sp_km_25e9", "space", "orbit_km", 25e9,
       why_da="25 milliarder kilometer — omtrent så langt, som Voyager 1 er nået fra Jorden.",
       why_en="25 billion kilometres — roughly as far as Voyager 1 has travelled from Earth."),
    _M("sp_km_5e10", "space", "orbit_km", 5e10,
       why_da="50 milliarder kilometer, det dobbelte af Voyager 1s rejse indtil nu.",
       why_en="50 billion kilometres, twice the journey Voyager 1 has made so far."),
    _M("sp_km_1e11", "space", "orbit_km", 1e11,
       why_da="Hundrede milliarder kilometer, knap fire lysdøgn. Alt sammen i ring om Solen, så du er ikke kommet nogen steder.",
       why_en="A hundred billion kilometres, just under four light-days. All of it in a circle around the Sun, so you have got precisely nowhere."),
    # Lyset fra foedselsoejeblikket naar frem til ...
    _M("sp_star_proxima", "space", "julian_year", 4.2465,
       label_da="Dit fødselslys når Proxima Centauri",
       label_en="Your birth light reaches Proxima Centauri",
       why_da="Lyset, der forlod Jorden i det sekund du blev født, har nu nået den nærmeste stjerne ud over Solen — 4,25 lysår væk.",
       why_en="The light that left Earth the second you were born has now reached the nearest star beyond the Sun — 4.25 light-years away."),
    _M("sp_star_alphacen", "space", "julian_year", 4.3650,
       label_da="Dit fødselslys når Alfa Centauri",
       label_en="Your birth light reaches Alpha Centauri",
       why_da="4,37 lysår. Solens nærmeste naboer er et trippelsystem, hvor Proxima er den mindste og nærmeste af de tre.",
       why_en="4.37 light-years. The nearest neighbours to the Sun are a triple system, with Proxima the smallest and closest of the three."),
    _M("sp_star_barnard", "space", "julian_year", 5.963,
       label_da="Dit fødselslys når Barnards Stjerne",
       label_en="Your birth light reaches Barnard's Star",
       why_da="5,96 lysår. Barnards Stjerne bevæger sig hurtigere hen over himlen end nogen anden — en fuldmånebredde på 180 år.",
       why_en="5.96 light-years. Barnards Star moves across the sky faster than any other — a full moon width every 180 years."),
    _M("sp_star_sirius", "space", "julian_year", 8.709, star=True,
       label_da="Dit fødselslys når Sirius",
       label_en="Your birth light reaches Sirius",
       why_da="Sirius er himlens klareste stjerne. Nu kunne man i princippet se din fødsel derfra.",
       why_en="Sirius is the brightest star in the sky. In principle, your birth could now be seen from there."),
    _M("sp_star_procyon", "space", "julian_year", 11.46,
       label_da="Dit fødselslys når Procyon",
       label_en="Your birth light reaches Procyon",
       why_da="11,46 lysår. Den klareste stjerne i Lille Hund og nummer otte på hele himlen.",
       why_en="11.46 light-years. The brightest star in Canis Minor and eighth brightest in the whole sky."),
    _M("sp_star_altair", "space", "julian_year", 16.73,
       label_da="Dit fødselslys når Altair",
       label_en="Your birth light reaches Altair",
       why_da="16,73 lysår. Et hjørne af Sommertrekanten. Den roterer så hurtigt, at den er mærkbart fladtrykt ved polerne.",
       why_en="16.73 light-years. One corner of the Summer Triangle. It spins so fast that it is visibly flattened at the poles."),
    _M("sp_star_vega", "space", "julian_year", 25.04, star=True,
       label_da="Dit fødselslys når Vega",
       label_en="Your birth light reaches Vega",
       why_da="Vega var stjernen, de rettede antennen mod i filmen Contact.",
       why_en="Vega is the star they pointed the antenna at in the film Contact."),
    _M("sp_star_pollux", "space", "julian_year", 33.78,
       label_da="Dit fødselslys når Pollux",
       label_en="Your birth light reaches Pollux",
       why_da="33,8 lysår. Det ene af Tvillingernes to hoveder, og den nærmeste kæmpestjerne med en kendt planet.",
       why_en="33.8 light-years. One of the two heads of Gemini, and the nearest giant star with a known planet."),
    _M("sp_star_denebola", "space", "julian_year", 36.2,
       label_da="Dit fødselslys når Denebola",
       label_en="Your birth light reaches Denebola",
       why_da="36,2 lysår. Løvens hale — navnet betyder præcis det på arabisk.",
       why_en="36.2 light-years. The tail of the lion — the name means exactly that in Arabic."),
    _M("sp_star_arcturus", "space", "julian_year", 36.7,
       label_da="Dit fødselslys når Arcturus",
       label_en="Your birth light reaches Arcturus",
       why_da="36,7 lysår. Den klareste stjerne på den nordlige himmel. Lyset herfra åbnede verdensudstillingen i Chicago i 1933.",
       why_en="36.7 light-years. The brightest star in the northern sky. Its light opened the Chicago World Fair in 1933."),
    _M("sp_star_capella", "space", "julian_year", 42.9,
       label_da="Dit fødselslys når Capella",
       label_en="Your birth light reaches Capella",
       why_da="42,9 lysår. Kuskens klareste. Ser ud som én stjerne, men er fire.",
       why_en="42.9 light-years. The brightest in Auriga. Looks like one star, but is four."),
    _M("sp_star_castor", "space", "julian_year", 51.0,
       label_da="Dit fødselslys når Castor",
       label_en="Your birth light reaches Castor",
       why_da="51 lysår. Tvillingernes andet hoved — og i virkeligheden seks stjerner i ét system.",
       why_en="51 light-years. The other head of Gemini — and in fact six stars in one system."),
    _M("sp_star_aldebaran", "space", "julian_year", 65.3,
       label_da="Dit fødselslys når Aldebaran",
       label_en="Your birth light reaches Aldebaran",
       why_da="65,3 lysår. Tyrens røde øje. Pioneer 10 er på vej derhen og ankommer om godt to millioner år.",
       why_en="65.3 light-years. The red eye of Taurus. Pioneer 10 is heading there and arrives in about two million years."),
    _M("sp_star_regulus", "space", "julian_year", 79.3,
       label_da="Dit fødselslys når Regulus",
       label_en="Your birth light reaches Regulus",
       why_da="79,3 lysår. Løvens hjerte. Den snurrer så hurtigt rundt, at den er tæt på at flyve fra hinanden.",
       why_en="79.3 light-years. The heart of Leo. It spins so fast it is close to tearing itself apart."),
    _M("sp_star_algol", "space", "julian_year", 90.0,
       label_da="Dit fødselslys når Algol",
       label_en="Your birth light reaches Algol",
       why_da="90 lysår. Djævlestjernen blinker hver 2,87 døgn, fordi en ledsager går forbi den. Det opdagede man i 1667.",
       why_en="90 light-years. The Demon Star blinks every 2.87 days because a companion passes in front of it. Noticed in 1667."),
]

# =========================================================================
# ❤️  KROPPEN  (skoen — satserne saettes i sidepanelet)
# =========================================================================

_BODY: list[Milestone] = [
    _M("b_hb_1e8", "body", "heartbeat", 1e8,
       why_da="Ved 70 slag i minuttet rammer de 100 millioner efter godt to et halvt år.",
       why_en="At 70 beats per minute, 100 million arrives after a little over two and a half years."),
    _M("b_hb_5e8", "body", "heartbeat", 5e8,
       why_da="Knap 14 år, hvis hjertet slår 70 gange i minuttet.",
       why_en="Just under 14 years, if the heart beats 70 times a minute."),
    _M("b_hb_1e9", "body", "heartbeat", 1e9, star=True,
       why_da="Din milliardte hjerteslag. Et pattedyrs hjerte slår omtrent en milliard gange i løbet af et liv — mus hurtigt og kort, elefanter langsomt og længe. Mennesket snyder og når tre gange så mange.",
       why_en="Your billionth heartbeat. A mammal's heart beats roughly a billion times in a lifetime — fast and briefly for a mouse, slowly and long for an elephant. Humans cheat and manage about three times as many."),
    _M("b_hb_2e9", "body", "heartbeat", 2e9,
       why_da="Godt 54 år ved 70 slag i minuttet — omtrent det dobbelte af, hvad et pattedyr normalt når på et helt liv.",
       why_en="A little over 54 years at 70 beats a minute — roughly twice what a mammal normally manages in a whole lifetime."),
    _M("b_hb_3e9", "body", "heartbeat", 3e9,
       why_da="Godt 81 år. Her er du langt ude over, hvad nogen anden art når.",
       why_en="A little over 81 years. By now you are far beyond what any other species manages."),
    _M("b_br_1e8", "body", "breath", 1e8,
       why_da="Ved 16 åndedrag i minuttet tager det knap 12 år at nå 100 millioner.",
       why_en="At 16 breaths a minute it takes just under 12 years to reach 100 million."),
    _M("b_br_25e7", "body", "breath", 2.5e8,
       why_da="Knap 30 år med 16 åndedrag i minuttet.",
       why_en="Just under 30 years at 16 breaths a minute."),
    _M("b_br_5e8", "body", "breath", 5e8,
       why_da="Knap 60 år med 16 åndedrag i minuttet.",
       why_en="Just under 60 years at 16 breaths a minute."),
    _M("b_br_1e9", "body", "breath", 1e9,
       why_da="En milliard åndedrag, knap 119 år. Næppe nogen har nået det.",
       why_en="A billion breaths, just under 119 years. Probably nobody has managed it."),
    _M("b_sleep_1e4", "body", "sleep_hour", 1e4,
       why_da="Ved otte timer i døgnet har du sovet sammenlagt tre år og fire måneder.",
       why_en="At eight hours a night, you have slept for three years and four months in total."),
    _M("b_sleep_5e4", "body", "sleep_hour", 5e4,
       why_da="Godt 17 år med lukkede øjne, ved otte timer i døgnet.",
       why_en="A little over 17 years with your eyes shut, at eight hours a night."),
    _M("b_sleep_1e5", "body", "sleep_hour", 1e5, star=True,
       why_da="100.000 timer i søvn — knap elleve et halvt år med lukkede øjne.",
       why_en="100,000 hours asleep — just under eleven and a half years with your eyes shut."),
    _M("b_sleep_2e5", "body", "sleep_hour", 2e5,
       why_da="200.000 timer, altså 68 år i seng — hvis du når de hundrede.",
       why_en="200,000 hours, that is 68 years in bed — if you reach a hundred."),
    _M("b_meal_1e4", "body", "meal", 1e4,
       why_da="Ved tre måltider om dagen rammer det tiende tusinde efter godt ni år.",
       why_en="At three meals a day, the ten-thousandth arrives after a little over nine years."),
    _M("b_meal_5e4", "body", "meal", 5e4,
       why_da="Godt 45 år ved tre måltider om dagen.",
       why_en="A little over 45 years at three meals a day."),
    _M("b_meal_1e5", "body", "meal", 1e5,
       why_da="Dit 100.000. måltid.",
       why_en="Your 100,000th meal."),
    _M("b_step_1e8", "body", "step", 1e8,
       why_da="100 millioner skridt — omkring 75.000 km, eller næsten to gange rundt om Jorden.",
       why_en="100 million steps — about 75,000 km, or nearly twice around the Earth."),
    _M("b_step_25e7", "body", "step", 2.5e8,
       why_da="250 millioner skridt er omkring 190.000 km — næsten halvvejs til Månen.",
       why_en="250 million steps is about 190,000 km — almost half way to the Moon."),
]

# =========================================================================
# 📊  PROCENT AF ET LIV
# =========================================================================

_CENTURY: list[Milestone] = [
    _M("p_10", "century", "pct_life", 0.10,
       why_da="En tiendedel af vejen gennem den levetid, du har sat i sidepanelet.",
       why_en="One tenth of the way through the lifespan you set in the sidebar."),
    _M("p_25", "century", "pct_life", 0.25,
       why_da="En fjerdedel af vejen.",
       why_en="One quarter of the way."),
    _M("p_3333", "century", "pct_life", 1 / 3,
       why_da="En tredjedel af vejen.",
       why_en="One third of the way."),
    _M("p_50", "century", "pct_life", 0.50, star=True,
       why_da="Halvvejs. Herfra er der lige så langt tilbage, som der er gået.",
       why_en="Half way. From here there is exactly as far left as you have come."),
    _M("p_6667", "century", "pct_life", 2 / 3,
       why_da="To tredjedele af vejen.",
       why_en="Two thirds of the way."),
    _M("p_75", "century", "pct_life", 0.75,
       why_da="Tre fjerdedele af vejen.",
       why_en="Three quarters of the way."),
    _M("p_90", "century", "pct_life", 0.90,
       why_da="Ni tiendedele. Den sidste tiendedel er stadig ti år.",
       why_en="Nine tenths. The final tenth is still ten years."),
]


def _geo_milestones() -> list[Milestone]:
    """Jordens historie som maerkedage — skaleret efter den antagne levetid."""
    out: list[Milestone] = []
    for event in GEO_EVENTS:
        if event.key == "hadean":
            continue  # Hadeisk tid er selve foedslen.
        out.append(
            Milestone(
                key=f"geo_{event.key}",
                group="geo",
                unit="geo_ma",
                amount=event.start_ma,
                label_da=f"{event.emoji} {event.da}",
                label_en=f"{event.emoji} {event.en}",
                why_da=event.desc_da,
                why_en=event.desc_en,
                star=event.key in {"cambrian", "triassic", "paleogene", "holocene"},
            )
        )
    return out


# =========================================================================
# 👥  JER TO
# =========================================================================
#
# Disse maerkedage kraever to foedselsoejeblikke og regnes derfor anderledes:
# ``pair_ratio`` er det oejeblik, hvor den aeldstes alder er et bestemt
# multiplum af den yngstes, og ``pair_sum_*`` er det oejeblik, hvor de to
# aldre lagt sammen naar et bestemt tal. Uden en anden foedselsdato giver de
# ingenting, og saa falder de helt ud af listen.

_PAIR: list[Milestone] = [
    _M("pair_ratio_10", "pair", "pair_ratio", 10.0,
       why_da="Lige efter den yngste er født, er forholdet mellem de to aldre "
              "astronomisk. Derefter falder det hele livet, så hvert forhold "
              "passeres præcis én gang. 10 : 1 kommer meget tidligt — med ti "
              "års aldersforskel sker det, før den yngste fylder to.",
       why_en="Just after the younger one is born the ratio between the two "
              "ages is astronomical. From then on it falls for life, so every "
              "ratio is passed exactly once. 10 : 1 comes very early — with a "
              "ten-year age gap it happens before the younger turns two."),
    _M("pair_ratio_5", "pair", "pair_ratio", 5.0,
       why_da="5 : 1. Den yngste er på det tidspunkt en fjerdedel af "
              "aldersforskellen gammel — med ti års forskel altså to og et halvt år.",
       why_en="5 : 1. At that point the younger one is a quarter of the age "
              "gap old — with a ten-year gap, two and a half years."),
    _M("pair_ratio_4", "pair", "pair_ratio", 4.0,
       why_da="4 : 1. Den yngste er en tredjedel af aldersforskellen gammel. "
              "Med ti års forskel indtræffer det ved tre år og fire måneder.",
       why_en="4 : 1. The younger one is a third of the age gap old. With a "
              "ten-year gap that falls at three years and four months."),
    _M("pair_ratio_3", "pair", "pair_ratio", 3.0,
       why_da="3 : 1. Nu er den yngste halvt så gammel som aldersforskellen "
              "mellem jer.",
       why_en="3 : 1. The younger one is now half as old as the age gap "
              "between you."),
    _M("pair_ratio_2", "pair", "pair_ratio", 2.0, star=True,
       why_da="Det sker én gang og aldrig igen. Forholdet mellem to aldre "
              "falder hele livet, så det passerer 2 præcis én gang — og "
              "øjeblikket kan regnes ud i hovedet: tag den yngstes fødselsdag "
              "og læg aldersforskellen til. Det er nemlig samme sekund, som "
              "den yngste bliver lige så gammel, som den ældste var den dag, "
              "den yngste blev født.",
       why_en="It happens once and never again. The ratio between two ages "
              "falls for life, so it passes 2 exactly once — and the moment "
              "can be worked out in your head: take the younger one's "
              "birthday and add the age gap. It is the very same second the "
              "younger reaches the age the older one was on the day the "
              "younger was born."),
    _M("pair_ratio_1_5", "pair", "pair_ratio", 1.5,
       why_da="3 : 2 — den sidste pæne brøk, der er værd at fejre. Den yngste "
              "er dobbelt så gammel som aldersforskellen, og derefter nærmer "
              "jeres to aldre sig hinanden for evigt uden nogensinde at nå det.",
       why_en="3 : 2 — the last tidy fraction worth celebrating. The younger "
              "one is twice as old as the age gap, and from here your two "
              "ages close on each other forever without ever meeting."),

    _M("pair_days_10000", "pair", "pair_sum_day", 10_000,
       why_da="Jeres to aldre lagt sammen giver 10.000 døgn. Summen vokser med "
              "to døgn om dagen, så den slags mærkedage kommer dobbelt så "
              "hurtigt som en enkelt persons.",
       why_en="Your two ages added together come to 10,000 days. The sum grows "
              "by two days a day, so milestones like this arrive twice as fast "
              "as one person's."),
    _M("pair_days_20000", "pair", "pair_sum_day", 20_000,
       why_da="20.000 døgn tilsammen — 54 år og 9 måneder fordelt på to mennesker.",
       why_en="20,000 days between you — 54 years and 9 months shared between "
              "two people."),
    _M("pair_days_25000", "pair", "pair_sum_day", 25_000,
       why_da="Et kvart hundredtusind døgn tilsammen, altså godt 68 år.",
       why_en="A quarter of a hundred thousand days between you: a little over "
              "68 years."),
    _M("pair_days_30000", "pair", "pair_sum_day", 30_000,
       why_da="30.000 døgn tilsammen. Er I jævnaldrende, har I begge rundet "
              "15.000 dage samme dag.",
       why_en="30,000 days between you. If you are the same age, you both "
              "passed 15,000 days on the same day."),
    _M("pair_days_40000", "pair", "pair_sum_day", 40_000,
       why_da="40.000 døgn tilsammen — knap 110 år delt mellem to.",
       why_en="40,000 days between you — just under 110 years shared between two."),
    _M("pair_days_50000", "pair", "pair_sum_day", 50_000,
       why_da="50.000 døgn tilsammen. Ingen enkelt person har nået det tal; "
              "to kan.",
       why_en="50,000 days between you. No single person has ever reached that "
              "number; two can."),

    _M("pair_sec_1e9", "pair", "pair_sum_sec", 1_000_000_000,
       why_da="Et gigasekund tilsammen. Alene tager det 31 år og 8 måneder — "
              "to om det klarer det på det halve.",
       why_en="A gigasecond between you. Alone it takes 31 years and 8 months; "
              "two of you manage it in half that."),
    _M("pair_sec_2e9", "pair", "pair_sum_sec", 2_000_000_000,
       why_da="To gigasekunder tilsammen. For to jævnaldrende betyder det, at "
              "I begge har rundet jeres eget gigasekund.",
       why_en="Two gigaseconds between you. For two people the same age it "
              "means you have both passed your own gigasecond."),
    _M("pair_sec_3e9", "pair", "pair_sum_sec", 3_000_000_000,
       why_da="Tre gigasekunder tilsammen — godt 95 år fordelt på to.",
       why_en="Three gigaseconds between you — a little over 95 years shared "
              "between two."),

    _M("pair_years_50", "pair", "pair_sum_year", 50,
       why_da="Halvtreds år tilsammen. For et par, der er født samme år, "
              "falder det sammen med den fælles 25-års fødselsdag.",
       why_en="Fifty years between you. For two people born the same year it "
              "coincides with both turning 25."),
    _M("pair_years_75", "pair", "pair_sum_year", 75,
       why_da="Trekvart århundrede tilsammen.",
       why_en="Three quarters of a century between you."),
    _M("pair_years_100", "pair", "pair_sum_year", 100, star=True,
       why_da="Hundrede år tilsammen — den fælles version af den fødselsdag, "
              "hvor kongehuset sender en lykønskning. Er I lige gamle, sker "
              "det, når I begge er halvtreds.",
       why_en="A hundred years between you — the shared version of the "
              "birthday that gets a letter from the head of state. If you are "
              "the same age, it happens when you both turn fifty."),
    _M("pair_years_125", "pair", "pair_sum_year", 125,
       why_da="125 år tilsammen.",
       why_en="125 years between you."),
    _M("pair_years_150", "pair", "pair_sum_year", 150,
       why_da="Halvandet hundrede år tilsammen. For to jævnaldrende betyder "
              "det, at I begge er fyldt 75.",
       why_en="A century and a half between you. For two people the same age "
              "it means you have both turned 75."),
]


MILESTONES: tuple[Milestone, ...] = tuple(
    _SECONDS
    + _MIN_HOUR
    + _DAY_WEEK
    + _MONTH_YEAR
    + _CONSTANTS
    + _NERD
    + _S73
    + _REPEAT
    + _EXOTIC
    + _MOON
    + _SPACE
    + _geo_milestones()
    + _BODY
    + _CENTURY
    + _PAIR
)

MILESTONES_BY_KEY: dict[str, Milestone] = {m.key: m for m in MILESTONES}

