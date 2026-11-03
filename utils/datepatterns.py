"""Dage, hvor selve datoen gaar op i et talmoenster.

Disse dage staar ikke i nogen datafil, for de behoever det ikke: en regel
finder dem. 22.02.2022 er et palindrom, fordi cifrene er, som de er — ikke
fordi nogen har besluttet det. Derfor er hver familie her en lille funktion,
der sigter et aarhundrede igennem, og ikke en liste, nogen skal holde ved lige.

Datoerne laeses i dansk raekkefoelge, dag foerst: 11.12.13 er den 11. december
2013. Det er ikke en detalje. De fleste af moenstrene findes kun i den
raekkefoelge, og det er netop dér, de sekventielle dage stopper: 12.13.14
findes ikke, for der er ingen trettende maaned.

Hver familie har sin egen gruppe i kataloget. Det er med vilje — man skal
kunne slaa palindromerne til uden ogsaa at faa flere hundrede sumdage.

Der regnes paa tre aarhundreder, fordi et menneskeliv kan naa over to
aarhundredeskift, men ikke tre. Motoren smider bagefter alt vaek, der ikke
falder inden for det liv, der er indtastet.
"""

from __future__ import annotations

from collections.abc import Callable, Iterator
from dataclasses import dataclass
from datetime import date
from math import isqrt

from .catalog import Milestone

# Noeglerne faar alle sammen dette foran, saa en festdag aldrig kan komme til
# at hedde det samme som en maerkedag i kataloget.
PREFIX = "cel_"

CENTURIES: tuple[int, ...] = (1900, 2000, 2100)


@dataclass(frozen=True)
class Hit:
    """Én dag, et moenster har fundet, med forklaringen paa hvorfor."""

    year: int
    month: int
    day: int
    da: str
    en: str

    @property
    def short(self) -> str:
        """Datoen som 11.12.13 — den form, moensteret kan ses i."""
        return f"{self.day:02d}.{self.month:02d}.{self.year % 100:02d}"

    @property
    def long(self) -> str:
        """Datoen med helt aarstal: 11.12.2013.

        Etiketten skal bruge denne og ikke ``short``. Der regnes paa tre
        aarhundreder, saa den samme korte form rammer tre gange — 04.03.05 er
        baade 1905, 2005 og 2105 — og tre ens linjer i en liste ligner en fejl,
        ogsaa naar de er tre forskellige dage.
        """
        return f"{self.day:02d}.{self.month:02d}.{self.year}"


def _real(year: int, month: int, day: int) -> bool:
    """Findes datoen? Den 31. februar goer ikke, hvor paent moensteret saa er."""
    try:
        date(year, month, day)
    except ValueError:
        return False
    return True


# -------------------------------------------------------------------------
# Cifferlegene
# -------------------------------------------------------------------------

# To palindromer har noget ekstra at sige om sig selv.
_PALINDROME_EXTRA: dict[tuple[int, int, int], tuple[str, str]] = {
    (2020, 2, 2): (
        " Den eneste, der også er et palindrom i amerikansk rækkefølge, hvor "
        "måneden står først — altså den samme dato over hele verden.",
        " The only one that is also a palindrome in month-first order — the "
        "same date the whole world over.",
    ),
    (2022, 2, 22): (
        " Den faldt på en tirsdag, hvilket gav den navnet „Twosday“, og de to "
        "ens cifre står ens, hvis man vender en lommeregner på hovedet.",
        " It fell on a Tuesday, which earned it the name “Twosday”, and the "
        "repeated digits read the same upside down on a calculator.",
    ),
}


def palindromes(century: int) -> Iterator[Hit]:
    """Datoer, der laeses ens forfra og bagfra som DD.MM.AAAA.

    Aarstallet er spejlingen af dag og maaned, saa det er dagen og maaneden,
    der bestemmer aaret — ikke omvendt. Det er derfor alle tolv i 2000-tallet
    ligger i februar: et aarstal, der begynder med 20, kan kun spejle en
    maaned, der ender paa 02. Og det er derfor der slet ikke er nogen i
    1900-tallet.
    """
    for month in range(1, 13):
        for day in range(1, 32):
            year = int(f"{day:02d}{month:02d}"[::-1])
            if year // 100 * 100 != century or not _real(year, month, day):
                continue
            extra = _PALINDROME_EXTRA.get((year, month, day), ("", ""))
            yield Hit(
                year, month, day,
                f"{day:02d}.{month:02d}.{year} læses ens forfra og bagfra."
                + extra[0],
                f"{day:02d}.{month:02d}.{year} reads the same backwards as "
                "forwards." + extra[1],
            )


def sequences(century: int) -> Iterator[Hit]:
    """01.02.03 og de andre, hvor dag, maaned og aar taeller op med samme skridt.

    Raekken med skridt 1 er den beroemte: 01.02.03, 02.03.04 og saa fremdeles
    op til 11.12.13. Den stopper dér, fordi den naeste skulle have vaeret
    12.13.14, og der er ingen trettende maaned. Naeste gang bliver 01.02.2103.
    """
    for step in (1, 2, 3):
        for day in range(1, 32):
            month = day + step
            short = month + step
            if not 1 <= month <= 12 or not 1 <= short <= 99:
                continue
            year = century + short
            if not _real(year, month, day):
                continue
            yield Hit(
                year, month, day,
                f"Dag, måned og år tæller op med {step} ad gangen: "
                f"{day}, {month}, {short}.",
                f"Day, month and year climb by {step} at a time: "
                f"{day}, {month}, {short}.",
            )


def repunits(century: int) -> Iterator[Hit]:
    """Datoer, hvor alle seks cifre er det samme.

    Der er praecis én i hvert aarhundrede. 22.22.22 ville ogsaa vaere paen,
    men der er hverken en 22. maaned eller en 22. maaned at laegge den i.
    """
    for digit in range(1, 10):
        value = digit * 11
        if not 1 <= value <= 12:
            continue
        year = century + value
        if not _real(year, value, value):
            continue
        yield Hit(
            year, value, value,
            f"Alle seks cifre er det samme: {value}.{value}.{value}. "
            "Det sker én gang i hvert århundrede.",
            f"All six digits are the same: {value}.{value}.{value}. "
            "It happens once a century.",
        )


def binaries(century: int) -> Iterator[Hit]:
    """Datoer, der kan skrives med kun nuller og ettere."""
    for month in (1, 10, 11):
        for day in (1, 10, 11):
            for short in (0, 1, 10, 11):
                year = century + short
                if not _real(year, month, day):
                    continue
                yield Hit(
                    year, month, day,
                    f"Hele datoen bruger kun nuller og ettere: "
                    f"{day:02d}.{month:02d}.{short:02d}.",
                    f"The whole date uses nothing but noughts and ones: "
                    f"{day:02d}.{month:02d}.{short:02d}.",
                )


# -------------------------------------------------------------------------
# Regnestykkerne
# -------------------------------------------------------------------------


def products(century: int) -> Iterator[Hit]:
    """Datoer, hvor dagen gange maaneden giver aaret — og de to er nabotal.

    Uden det sidste krav er der over to hundrede om aaret hundrede, og de
    fleste af dem er to tilfaeldige tal, der tilfaeldigvis rammer: 15 × 4 =
    60 siger ingenting. Med nabotal bliver regnestykket til en raekke, man
    kan se: 6, 7, 42.

    Kvadraterne (5 × 5 = 25) er med vilje holdt udenfor. De er de samme dage
    som kvadratrodsdagene, og den samme dag skal ikke staa to steder med to
    navne.
    """
    for first in range(2, 10):
        second = first + 1
        for day, month in ((first, second), (second, first)):
            short = day * month
            year = century + short
            if not 1 <= short <= 99 or not _real(year, month, day):
                continue
            extra = (
                " Og 42 er svaret på Det Store Spørgsmål om Livet, Universet "
                "og Alting."
                if short == 42
                else ""
            )
            extra_en = (
                " And 42 is the Answer to the Ultimate Question of Life, the "
                "Universe and Everything."
                if short == 42
                else ""
            )
            yield Hit(
                year, month, day,
                f"Dagen og måneden er nabotal, og ganget sammen giver de året: "
                f"{day} × {month} = {short}." + extra,
                f"The day and the month are neighbours, and multiplied they "
                f"give the year: {day} × {month} = {short}." + extra_en,
            )


def sums(century: int) -> Iterator[Hit]:
    """Datoer, hvor dagen og maaneden er det samme tal, og summen er aaret.

    Uden kravet om, at de to er ens, gaar det op over tre hundrede gange i et
    aarhundrede — flere gange om maaneden. En maerkedag, der falder saa tit,
    er ingen maerkedag. Med kravet er der tolv: 01.01.02, 02.02.04 og saa
    fremdeles op til 12.12.24, og regnestykket er det samme tal to gange.
    """
    for number in range(1, 13):
        short = number * 2
        year = century + short
        if not _real(year, number, number):
            continue
        yield Hit(
            year, number, number,
            f"Dagen og måneden er det samme tal, og lagt sammen giver de "
            f"året: {number} + {number} = {short}.",
            f"The day and the month are the same number, and added together "
            f"they give the year: {number} + {number} = {short}.",
        )


def pythagoreans(century: int) -> Iterator[Hit]:
    """Datoer, hvor dag² + maaned² = aar². Tolv gange i et aarhundrede.

    04.03.05 er den klassiske 3-4-5-trekant. 24.07.25 er 576 + 49 = 625.
    """
    for month in range(1, 13):
        for day in range(1, 32):
            total = day * day + month * month
            root = isqrt(total)
            if root * root != total or not 1 <= root <= 99:
                continue
            year = century + root
            if not _real(year, month, day):
                continue
            yield Hit(
                year, month, day,
                f"Dagen i anden plus måneden i anden giver året i anden: "
                f"{day}² + {month}² = {root}², altså "
                f"{day * day} + {month * month} = {root * root}. "
                "Det går op tolv gange i et århundrede.",
                f"The day squared plus the month squared equals the year "
                f"squared: {day}² + {month}² = {root}², that is "
                f"{day * day} + {month * month} = {root * root}. "
                "It works out twelve times a century.",
            )


def square_roots(century: int) -> Iterator[Hit]:
    """Datoer, hvor dag og maaned begge er kvadratroden af aaret: 05.05.25."""
    for number in range(1, 10):
        short = number * number
        year = century + short
        if not _real(year, number, number):
            continue
        yield Hit(
            year, number, number,
            f"Dagen og måneden er begge kvadratroden af året: "
            f"√{short} = {number}. Ni gange i et århundrede, og så aldrig "
            "mere i dit liv.",
            f"The day and the month are both the square root of the year: "
            f"√{short} = {number}. Nine times a century, and then never again.",
        )


def fibonaccis(century: int) -> Iterator[Hit]:
    """Datoer, hvor dag, maaned og aar er tre Fibonacci-tal i raekke.

    01.01.02, 01.02.03, 02.03.05, 03.05.08, 05.08.13 — og saa stopper det,
    fordi det naeste tal i raekken er 13, og der er ingen trettende maaned.
    """
    series = (1, 1, 2, 3, 5, 8, 13, 21, 34, 55, 89)
    for index in range(len(series) - 2):
        day, month, short = series[index], series[index + 1], series[index + 2]
        if not 1 <= month <= 12 or not 1 <= short <= 99:
            continue
        year = century + short
        if not _real(year, month, day):
            continue
        yield Hit(
            year, month, day,
            f"Tre Fibonacci-tal i række: {day}, {month}, {short} — hvert tal "
            "er summen af de to foran.",
            f"Three Fibonacci numbers in a row: {day}, {month}, {short} — "
            "each one the sum of the two before it.",
        )


# -------------------------------------------------------------------------
# Familierne samlet
# -------------------------------------------------------------------------


@dataclass(frozen=True)
class Family:
    """Ét moenster: hvad det hedder, hvor det hoerer til, og hvad der finder det."""

    group: str
    slug: str
    da: str
    en: str
    finder: Callable[[int], Iterator[Hit]]


FAMILIES: tuple[Family, ...] = (
    Family("palindrome", "pal", "Palindromdag", "Palindrome day", palindromes),
    Family("sequence", "seq", "Sekvensdag", "Sequence day", sequences),
    Family("repunit", "rep", "Repunitdag", "Repdigit day", repunits),
    Family("binday", "bin", "Binær dag", "Binary day", binaries),
    Family("pyth", "pyth", "Pythagoræisk dag", "Pythagorean day", pythagoreans),
    Family("sqrtday", "sqrt", "Kvadratrodsdag", "Square root day", square_roots),
    Family("fibday", "fib", "Fibonacci-dato", "Fibonacci date", fibonaccis),
    Family("product", "prod", "Produktdag", "Product day", products),
    Family("sumday", "sum", "Sumdag", "Sum day", sums),
)

FAMILIES_BY_GROUP: dict[str, Family] = {f.group: f for f in FAMILIES}


def pattern_milestones() -> tuple[Milestone, ...]:
    """Alle moensterdage i alle tre aarhundreder, som maerkedage.

    En dato kan godt vaere flere ting paa én gang — 05.05.25 er baade en
    kvadratrodsdag og en produktdag — og den staar saa i begge grupper. Det er
    med vilje: det er to forskellige pointer om den samme dag.
    """
    out: list[Milestone] = []
    for family in FAMILIES:
        for century in CENTURIES:
            for hit in family.finder(century):
                out.append(
                    Milestone(
                        key=f"{PREFIX}{family.slug}_{hit.year}"
                            f"_{hit.month:02d}_{hit.day:02d}",
                        group=family.group,
                        unit="date_abs",
                        amount=0.0,
                        when=f"{hit.year}-{hit.month:02d}-{hit.day:02d}",
                        label_da=f"{family.da}: {hit.long}",
                        label_en=f"{family.en}: {hit.long}",
                        why_da=hit.da,
                        why_en=hit.en,
                    )
                )
    return tuple(out)
