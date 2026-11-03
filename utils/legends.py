"""30 legender, du kan naa at overhale.

Maerkedagen falder, naar du har levet lige saa mange doegn, som personen naaede.
Levetiden regnes af de faktiske foedsels- og doedsdatoer, ikke af runde aarstal,
saa "lige saa gammel som Mozart" er praecis paa dagen.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import date

from .catalog import Milestone


@dataclass(frozen=True)
class Legend:
    """En person, hvis levetid kan bruges som maalestok."""

    key: str
    name: str
    born: date
    died: date
    role_da: str
    role_en: str

    @property
    def lifespan_days(self) -> int:
        return (self.died - self.born).days

    @property
    def years(self) -> int:
        years = self.died.year - self.born.year
        if (self.died.month, self.died.day) < (self.born.month, self.born.day):
            years -= 1
        return years

    def role(self, lang: str) -> str:
        return self.role_da if lang == "da" else self.role_en


LEGENDS: tuple[Legend, ...] = (
    Legend("dean", "James Dean", date(1931, 2, 8), date(1955, 9, 30),
           "skuespiller", "actor"),
    Legend("hendrix", "Jimi Hendrix", date(1942, 11, 27), date(1970, 9, 18),
           "guitarist", "guitarist"),
    Legend("cobain", "Kurt Cobain", date(1967, 2, 20), date(1994, 4, 5),
           "sanger og sangskriver", "singer-songwriter"),
    Legend("winehouse", "Amy Winehouse", date(1983, 9, 14), date(2011, 7, 23),
           "sanger", "singer"),
    Legend("lee", "Bruce Lee", date(1940, 11, 27), date(1973, 7, 20),
           "kampkunstner", "martial artist"),
    Legend("mozart", "W. A. Mozart", date(1756, 1, 27), date(1791, 12, 5),
           "komponist", "composer"),
    Legend("monroe", "Marilyn Monroe", date(1926, 6, 1), date(1962, 8, 4),
           "skuespiller", "actor"),
    Legend("lovelace", "Ada Lovelace", date(1815, 12, 10), date(1852, 11, 27),
           "verdens første programmør", "the world's first programmer"),
    Legend("vangogh", "Vincent van Gogh", date(1853, 3, 30), date(1890, 7, 29),
           "maler", "painter"),
    Legend("lennon", "John Lennon", date(1940, 10, 9), date(1980, 12, 8),
           "musiker", "musician"),
    Legend("turing", "Alan Turing", date(1912, 6, 23), date(1954, 6, 7),
           "datalogiens grundlægger", "founder of computer science"),
    Legend("kierkegaard", "Søren Kierkegaard", date(1813, 5, 5), date(1855, 11, 11),
           "filosof", "philosopher"),
    Legend("presley", "Elvis Presley", date(1935, 1, 8), date(1977, 8, 16),
           "sanger", "singer"),
    Legend("mercury", "Freddie Mercury", date(1946, 9, 5), date(1991, 11, 24),
           "sanger", "singer"),
    Legend("kahlo", "Frida Kahlo", date(1907, 7, 6), date(1954, 7, 13),
           "maler", "painter"),
    Legend("zappa", "Frank Zappa", date(1940, 12, 21), date(1993, 12, 4),
           "komponist og guitarist", "composer and guitarist"),
    Legend("tycho", "Tycho Brahe", date(1546, 12, 14), date(1601, 10, 24),
           "astronom", "astronomer"),
    Legend("beethoven", "Ludwig van Beethoven", date(1770, 12, 17), date(1827, 3, 26),
           "komponist", "composer"),
    Legend("jobs", "Steve Jobs", date(1955, 2, 24), date(2011, 10, 5),
           "medstifter af Apple", "co-founder of Apple"),
    Legend("curie", "Marie Curie", date(1867, 11, 7), date(1934, 7, 4),
           "fysiker og kemiker", "physicist and chemist"),
    Legend("nielsen", "Carl Nielsen", date(1865, 6, 9), date(1931, 10, 3),
           "komponist", "composer"),
    Legend("leonardo", "Leonardo da Vinci", date(1452, 4, 15), date(1519, 5, 2),
           "alt på én gang", "everything at once"),
    Legend("bowie", "David Bowie", date(1947, 1, 8), date(2016, 1, 10),
           "musiker", "musician"),
    Legend("andersen", "H.C. Andersen", date(1805, 4, 2), date(1875, 8, 4),
           "digter", "writer"),
    Legend("larsen", "Kim Larsen", date(1945, 10, 23), date(2018, 9, 30),
           "sanger og sangskriver", "singer-songwriter"),
    Legend("hawking", "Stephen Hawking", date(1942, 1, 8), date(2018, 3, 14),
           "fysiker", "physicist"),
    Legend("einstein", "Albert Einstein", date(1879, 3, 14), date(1955, 4, 18),
           "fysiker", "physicist"),
    Legend("blixen", "Karen Blixen", date(1885, 4, 17), date(1962, 9, 7),
           "forfatter", "writer"),
    Legend("bohr", "Niels Bohr", date(1885, 10, 7), date(1962, 11, 18),
           "fysiker", "physicist"),
    Legend("chaplin", "Charlie Chaplin", date(1889, 4, 16), date(1977, 12, 25),
           "filmkunstner", "film-maker"),
    Legend("mandela", "Nelson Mandela", date(1918, 7, 18), date(2013, 12, 5),
           "frihedskæmper og præsident", "freedom fighter and president"),
    Legend("lindgren", "Astrid Lindgren", date(1907, 11, 14), date(2002, 1, 28),
           "forfatter", "writer"),
    Legend("borge", "Victor Borge", date(1909, 1, 3), date(2000, 12, 23),
           "pianist og humorist", "pianist and comedian"),
)

LEGENDS_BY_KEY: dict[str, Legend] = {legend.key: legend for legend in LEGENDS}


def legend_milestones() -> list[Milestone]:
    """Legenderne som maerkedage, sorteret efter levetid."""
    out: list[Milestone] = []
    for legend in sorted(LEGENDS, key=lambda item: item.lifespan_days):
        days = legend.lifespan_days
        out.append(
            Milestone(
                key=f"legend_{legend.key}",
                group="legend",
                unit="day",
                amount=days,
                label_da=f"Du overhaler {legend.name}",
                label_en=f"You outlive {legend.name}",
                why_da=(
                    f"{legend.name} ({legend.role_da}) blev {legend.years} år — "
                    f"{days:,} dage. Fra i dag har du levet længere."
                ).replace(",", "."),
                why_en=(
                    f"{legend.name} ({legend.role_en}) lived {legend.years} years — "
                    f"{days:,} days. From today you have lived longer."
                ),
            )
        )
    return out
