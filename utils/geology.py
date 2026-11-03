"""Jordens historie klemt ned i ét menneskeliv.

Hvis dit liv var hele Jordens historie, hvornaar skete der saa hvad? Jorden er
4,54 milliarder aar gammel, saa med en antaget levetid paa 100 aar svarer ét
leveaar til godt 45 millioner aars planethistorie.

Pointen — og grunden til at det er sjovt — er, at Jorden var en bakteriekultur
i naesten hele sin levetid. Du naar at vaere encellet gennem barndom, ungdom og
midtvejskrise. Alt det kendte (trilobitter, dinosaurer, mammutter, mennesker)
klemmes sammen i de sidste tolv aar, og hele den menneskelige civilisation
ligger i de sidste par timer foer din 100-aars fodselsdag.

Aldrene regnes som ``levetid * (4540 - alder_i_mio_aar) / 4540`` og bruger
ICS/IUGS' officielle graenser, ikke runde tal.
"""

from __future__ import annotations

from dataclasses import dataclass

from .units import EARTH_AGE_MA


@dataclass(frozen=True)
class GeoEvent:
    """En graense i Jordens historie."""

    key: str
    start_ma: float          # Millioner aar foer nu.
    da: str
    en: str
    desc_da: str
    desc_en: str
    emoji: str = "🌍"

    def age_at(self, lifespan_years: float) -> float:
        """Hvor gammel du er, naar du naar hertil paa den skalerede tidslinje."""
        return lifespan_years * (EARTH_AGE_MA - self.start_ma) / EARTH_AGE_MA

    def name(self, lang: str) -> str:
        return self.da if lang == "da" else self.en

    def description(self, lang: str) -> str:
        return self.desc_da if lang == "da" else self.desc_en


GEO_EVENTS: tuple[GeoEvent, ...] = (
    GeoEvent(
        "hadean", 4540.0, "Hadeisk tid begynder", "The Hadean begins",
        "Fødslen. Planeten er en glohed kugle af magma, bombarderet af det, "
        "der er tilbage af solsystemets byggemateriale. Ingen skorpe, intet "
        "hav, ingen luft at tale om.",
        "Birth. The planet is a red-hot ball of magma, bombarded by whatever "
        "is left of the solar system's building material. No crust, no ocean, "
        "no air to speak of.",
        "🌋",
    ),
    GeoEvent(
        "archean", 4031.0, "Arkæisk tid", "The Archean",
        "Skorpen er kølet af, havene er dannet, og det første encellede liv "
        "dukker op. Herfra sker der dybest set ingenting i rigtig, rigtig "
        "lang tid.",
        "The crust has cooled, the oceans have formed, and the first "
        "single-celled life appears. From here essentially nothing happens "
        "for a very, very long time.",
        "🦠",
    ),
    GeoEvent(
        "proterozoic", 2500.0, "Proterozoisk tid", "The Proterozoic",
        "Ilt fylder atmosfæren — for datidens liv en katastrofal forurening — "
        "og udløser Jordens første globale istid. De komplekse celler med "
        "cellekerne opstår.",
        "Oxygen fills the atmosphere — a catastrophic pollution event for the "
        "life of the day — and triggers Earth's first global ice age. Complex "
        "cells with a nucleus emerge.",
        "❄️",
    ),
    GeoEvent(
        "cambrian", 538.8, "Kambrium", "The Cambrian",
        "Den kambriske eksplosion. På geologisk set ingen tid fyldes havene "
        "med sære, hårdskallede dyr og trilobitter. Næsten alle nulevende "
        "dyrerækker opstår her.",
        "The Cambrian explosion. In no time at all, geologically speaking, "
        "the oceans fill with bizarre hard-shelled creatures and trilobites. "
        "Almost every animal phylum alive today appears here.",
        "🦐",
    ),
    GeoEvent(
        "ordovician", 486.85, "Ordovicium", "The Ordovician",
        "Rigt og mangfoldigt liv i havet — og så en voldsom istid, der "
        "udsletter omkring 85 % af alle arter.",
        "Rich and diverse marine life — followed by a severe ice age that "
        "wipes out around 85% of all species.",
        "🐚",
    ),
    GeoEvent(
        "silurian", 443.1, "Silur", "The Silurian",
        "Koralrevene breder sig, og de allerførste primitive planter får "
        "fodfæste på land.",
        "Coral reefs spread, and the very first primitive plants gain a "
        "foothold on land.",
        "🪸",
    ),
    GeoEvent(
        "devonian", 419.2, "Devon", "The Devonian",
        "Fiskenes tidsalder. De første firbenede dyr kravler op af vandet og "
        "sætter fod på land.",
        "The Age of Fish. The first tetrapods crawl out of the water and set "
        "foot on land.",
        "🐟",
    ),
    GeoEvent(
        "carboniferous", 358.9, "Kultiden", "The Carboniferous",
        "Kæmpe sumpskove dækker Jorden og presses siden sammen til vore dages "
        "kullag. Iltindholdet er så højt, at insekterne bliver meterstore.",
        "Giant swamp forests cover the Earth and are later compressed into "
        "today's coal beds. Oxygen levels are so high that insects grow to a "
        "metre across.",
        "🌿",
    ),
    GeoEvent(
        "permian", 298.9, "Perm", "The Permian",
        "Superkontinentet Pangæa samler sig. Krybdyrene breder sig ud over "
        "enorme, tørre ørkener.",
        "The supercontinent Pangaea assembles. Reptiles spread across vast, "
        "dry deserts.",
        "🏜️",
    ),
    GeoEvent(
        "triassic", 251.902, "Trias — Den Store Død", "The Triassic — the Great Dying",
        "Historiens dødeligste masseuddøen udsletter 96 % af alt liv i havet. "
        "Oven på ruinerne udvikler de allerførste små dinosaurer sig — og de "
        "første pattedyr.",
        "The deadliest mass extinction in history wipes out 96% of marine "
        "life. On top of the ruins the very first small dinosaurs evolve — "
        "and the first mammals.",
        "💀",
    ),
    GeoEvent(
        "jurassic", 201.4, "Jura", "The Jurassic",
        "Endnu en masseuddøen rydder konkurrenterne af vejen, og dinosaurerne "
        "overtager: de enorme langhalsede sauropoder og Stegosaurus.",
        "Another mass extinction clears out the competition and the dinosaurs "
        "take over: the enormous long-necked sauropods and Stegosaurus.",
        "🦕",
    ),
    GeoEvent(
        "cretaceous", 143.1, "Kridt", "The Cretaceous",
        "De store kødæderes guldalder — T. rex — og de behornede dinosaurer "
        "som Triceratops. De første fugle letter, og blomsterplanterne "
        "dukker op.",
        "The golden age of the great carnivores — T. rex — and the horned "
        "dinosaurs like Triceratops. The first birds take flight and "
        "flowering plants appear.",
        "🦖",
    ),
    GeoEvent(
        "paleogene", 66.0, "Palæogen — asteroiden", "The Paleogene — the asteroid",
        "En asteroide på størrelse med en by rammer Jorden og gør det af med "
        "alle dinosaurer undtagen fuglene. Små pattedyr overlever og udvikler "
        "sig lynhurtigt ud i den tomme verden.",
        "A city-sized asteroid hits the Earth and finishes off every dinosaur "
        "except the birds. Small mammals survive and evolve at speed into the "
        "empty world.",
        "☄️",
    ),
    GeoEvent(
        "neogene", 23.04, "Neogen", "The Neogene",
        "Megalodon hersker i de varme have, og de store græssletter opstår og "
        "driver udviklingen af heste, mammutter og de tidlige menneskeaber.",
        "Megalodon rules the warm oceans, and vast grasslands emerge, driving "
        "the evolution of horses, mammoths and the early apes.",
        "🦣",
    ),
    GeoEvent(
        "quaternary", 2.58, "Kvartær — istiderne", "The Quaternary — the ice ages",
        "De moderne istider begynder. Slægten Homo udvikler redskaber.",
        "The modern ice ages begin. The genus Homo develops tools.",
        "🧊",
    ),
    GeoEvent(
        "holocene", 0.0117, "Holocæn — civilisationen", "The Holocene — civilisation",
        # Beskrivelsen skal kunne staa paa begge skalaer — baade i et liv og i
        # et kalenderaar — saa den naevner ikke en alder. Hver skala laegger
        # selv sin pointe til: "de sidste par timer" eller "81 sekunder".
        "Gletsjerne trækker sig tilbage. Mennesket bygger pyramider, fører "
        "verdenskrige, opfinder computeren og holder nørdilæumsfest — alt "
        "sammen i den allersidste stump af skalaen.",
        "The glaciers retreat. Humans build pyramids, fight world wars, "
        "invent computing and throw a nerdiversary party — all in the very "
        "last sliver of the scale.",
        "🏛️",
    ),
)

GEO_BY_KEY: dict[str, GeoEvent] = {event.key: event for event in GEO_EVENTS}


def years_per_human_year(lifespan_years: float) -> float:
    """Hvor mange aar af Jordens historie ét leveaar svarer til."""
    return EARTH_AGE_MA * 1_000_000 / lifespan_years
