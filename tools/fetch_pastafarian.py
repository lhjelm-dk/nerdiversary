"""Hent hele den pastafarianske kalender og skriv den som en datafil.

Kilden, pastafariancalendar.com, har en helligdag for HVER eneste dag i
aaret — 365 af dem — og det er en del af vitsen. Feedet er en .ics-fil med
et par tusind begivenheder fordelt over nogle aar; de fleste gentager sig
uaendret, saa her samles de til én dag pr. kalenderdato.

De dage, der har faaet en rigtig forklaring skrevet i haanden, staar i
``WRITTEN`` nedenfor og overskriver det hentede. Resten faar kildens navn
og ``medium: "fsm"``, som ``utils.celebrations`` oversaetter til én linje
om, hvor dagen kommer fra.

Koer den med:
    python tools/fetch_pastafarian.py
"""

from __future__ import annotations

import json
import pathlib
import re
import sys
import urllib.request

FEED = "https://www.pastafariancalendar.com/feed.ics"
OUT = pathlib.Path(__file__).resolve().parent.parent / "data" / "celebrations" / "13_pastafarian.json"

# Emoji, variationsvaelgere, sammenbindere og de flagtegn, kilden bruger i
# navnene. De skal vaek, for gruppen har allerede sin egen emoji.
_DECOR = re.compile(
    "[\U0001F000-\U0001FAFF←-⯿✀-➿︀-️​-‍"
    "\U0001F1E6-\U0001F1FF\U000E0000-\U000E007F〰〽©®]"
)

# De dage, der har faaet en forklaring skrevet i haanden. Noeglen er
# maaned og dag. Alt andet end "when" overskriver det hentede.
WRITTEN: dict[str, dict] = {
    "04-19": {"key": "fsm_pastover", "tier": 1, "da": "Pastover", "en": "Pastover", "why_da": "Pastafarianismens påske og en af de store helligdage. Den holdes med pasta, og hele pointen med navnet er, at det er et ordspil. Det er nok.", "why_en": "Pastafarianism's Easter and one of the major holy days. It is kept with pasta, and the entire point of the name is that it is a pun. That is enough."},
    "05-05": {"key": "fsm_ramendan_start", "tier": 1, "da": "Ramendan begynder", "en": "Ramendan begins", "why_da": "En måned, hvor den troende spiser nudler. Ikke undlader at spise — spiser. Faste er ikke rigtig i pastafarianismens ånd.", "why_en": "A month in which the faithful eat noodles. Not abstain from eating — eat. Fasting is not really in the Pastafarian spirit."},
    "06-04": {"key": "fsm_ramendan_end", "tier": 2, "da": "Ramendan slutter", "en": "Ramendan ends", "why_da": "Nudelmåneden er forbi. Man må nu spise andet, men behøver ikke.", "why_en": "The noodle month is over. You may now eat other things, but you need not."},
    "12-25": {"key": "fsm_holiday", "tier": 1, "da": "Holiday", "en": "Holiday", "why_da": "Vinterhelligdagen hedder bare Holiday. Navnet er med vilje det tommeste, man kunne finde på, så ingen kan tage anstød — og så er det selvfølgelig præcis det, der gør det til en pointe.", "why_en": "The winter holy day is simply called Holiday. The name is deliberately the emptiest one available, so that nobody can take offence — which is, of course, exactly what makes it a point."},
    "10-12": {"key": "fsm_headgear", "tier": 1, "da": "Den internationale dørslagsdag", "en": "International Pastafarian Headgear Day", "why_da": "Dørslaget på hovedet er pastafarianismens religiøse hovedbeklædning, og flere lande har måttet tage stilling til, om man må bære det på sit kørekortfoto. Nogle har sagt ja. Det er dagen, hvor man bærer det.", "why_en": "The colander on the head is Pastafarianism's religious headgear, and several countries have had to rule on whether you may wear one in your driving-licence photo. Some have said yes. This is the day you wear it."},
    "01-14": {"key": "fsm_colander", "tier": 2, "da": "Bær et dørslag-dagen", "en": "Wear a Colander Day", "why_da": "Som dørslagsdagen i oktober, bare tidligere på året. Kalenderen har 365 helligdage og er ikke bange for at gentage sig selv.", "why_en": "Like the headgear day in October, only earlier in the year. The calendar has 365 holy days and is not afraid to repeat itself."},
    "07-18": {"key": "fsm_henderson", "tier": 1, "da": "Bobby Hendersons fødselsdag", "en": "Bobby Henderson's Birthday", "why_da": "Manden, hele religionen kom af. Som 24-årig nyuddannet fysiker skrev han i 2005 til Kansas' skoleråd, der ville sidestille intelligent design med evolution i biologitimerne: underviser man i én alternativ skabelsesteori, må man også undervise i hans — at universet blev skabt af et flyvende spaghettimonster. Rådet svarede ikke, så han lagde brevet på nettet. Hvilken dag han sendte det, står ingen steder.", "why_en": "The man the whole religion came from. A 24-year-old physics graduate, he wrote in 2005 to the Kansas school board, which wanted intelligent design taught alongside evolution in biology class: if you teach one alternative creation theory, you must teach his too — that the universe was made by a flying spaghetti monster. The board did not reply, so he put the letter online. What day he sent it is not recorded anywhere."},
    "11-12": {"key": "fsm_drunk_creation", "tier": 2, "da": "Eftertanke over en beruset skabelse", "en": "Drunk Creation Contemplation Day", "why_da": "Det hører til læren, at monsteret var fuldt, da det skabte verden. Det forklarer en hel del, og det er ikke tænkt som en undskyldning.", "why_en": "Doctrine holds that the Monster was drunk when it made the world. That explains a good deal, and it is not meant as an excuse."},
    "05-18": {"key": "fsm_teapot", "tier": 2, "da": "Russells tepotte-dagen", "en": "Russell's Teapot Day", "why_da": "Bertrand Russell forestillede sig en tepotte i kredsløb mellem Jorden og Mars, for lille til at noget teleskop kan se den. Man kan ikke modbevise den. Pointen er, at bevisbyrden ligger hos den, der påstår, ikke hos den, der tvivler — og det er hele spaghettimonsterets argument i én sætning.", "why_en": "Bertrand Russell imagined a teapot orbiting between Earth and Mars, too small for any telescope to see. You cannot disprove it. The point is that the burden of proof lies with whoever asserts, not whoever doubts — which is the whole Spaghetti Monster argument in a single sentence."},
    "04-01": {"key": "fsm_spaghetti_harvest", "tier": 2, "da": "Spaghettihøsten", "en": "Spaghetti Harvest Day", "why_da": "BBC sendte den 1. april 1957 et indslag om schweiziske bønder, der høstede spaghetti fra træer. Seerne ringede ind og spurgte, hvordan man selv dyrker et spaghettitræ. Svaret var: læg en kvist i tomatsauce og håb det bedste.", "why_en": "On 1 April 1957 the BBC broadcast a report on Swiss farmers harvesting spaghetti from trees. Viewers rang in to ask how to grow a spaghetti tree of their own. The answer given was: place a sprig in tomato sauce and hope for the best.", "since": 1957},
    "04-27": {"key": "fsm_86400", "tier": 2, "da": "86.400-sekunders-dagen", "en": "86,400 Seconds Day", "why_da": "Tallet er et helt døgn gjort op i sekunder: 60 × 60 × 24. Hver eneste dag er en 86.400-sekunders-dag, og det er netop derfor, nogen har syntes, at én af dem skulle hedde det.", "why_en": "The number is a full day counted in seconds: 60 × 60 × 24. Every single day is an 86,400-second day, which is precisely why somebody felt one of them ought to be called it."},
    "01-08": {"key": "fsm_hawking", "tier": 2, "da": "Mindedagen for Stephen Hawking", "en": "Stephen Hawking Remembrance Day", "why_da": "Hawking blev født den 8. januar 1942 — tre hundrede år på dagen efter Galileis død, som han selv holdt af at påpege. Han døde den 14. marts, som er pi-dagen og Einsteins fødselsdag.", "why_en": "Hawking was born on 8 January 1942 — three hundred years to the day after Galileo died, as he liked to point out. He died on 14 March, which is Pi Day and Einstein's birthday.", "since": 1942},
    "03-05": {"key": "fsm_momofuku", "tier": 2, "da": "Momofuku Andos fødselsdag", "en": "Momofuku Ando's Birthday", "why_da": "Manden, der fandt på instantnudlerne i 1958 og kopnudlerne i 1971. I en japansk afstemning om århundredets bedste japanske opfindelse slog instantnudlerne både karaoke og walkmanen.", "why_en": "The man who invented instant noodles in 1958 and cup noodles in 1971. In a Japanese poll on the country's finest invention of the century, instant noodles beat both karaoke and the Walkman.", "since": 1910},
    "01-11": {"key": "fsm_spam", "tier": 2, "da": "Spam spam spam spam-dagen", "en": "Spam Spam Spam Spam Day", "why_da": "Monty Python-sketchen om en cafe, hvor alt på menuen indeholder spam, og et bord vikinger synger om det. Derfra har uønsket post sit navn.", "why_en": "The Monty Python sketch about a cafe where everything on the menu comes with spam, and a table of Vikings sings about it. That is where unwanted mail got its name."},
    "11-11": {"key": "fsm_eleven", "tier": 2, "da": "Skru op til elleve-dagen", "en": "Turn it up to Eleven Day", "why_da": "Fra This Is Spinal Tap: guitaristens forstærker går til elleve i stedet for ti. Hvorfor ikke bare gøre ti højere? Fordi den her går til elleve.", "why_en": "From This Is Spinal Tap: the guitarist's amplifier goes to eleven instead of ten. Why not make ten louder? Because this one goes to eleven."},
    "10-27": {"key": "fsm_silly_walks", "tier": 2, "da": "Fjollede gangarters dag", "en": "Silly Walks Day", "why_da": "Ministeriet for Fjollede Gangarter, Monty Python, 1970. John Cleese har senere sagt, at sketchen var ubehagelig at optage, fordi den gjorde ondt i benene.", "why_en": "The Ministry of Silly Walks, Monty Python, 1970. John Cleese has since said the sketch was unpleasant to film, because it hurt his legs."},
    "08-24": {"key": "fsm_pluto", "tier": 2, "da": "Sorg over Plutos degradering", "en": "Pluto Demotion Grieving Day", "why_da": "Den 24. august 2006 vedtog Den Internationale Astronomiske Union en definition af en planet, som Pluto ikke levede op til: den har ikke ryddet sin egen bane. Delstaten Illinois erklærede senere, at Pluto alligevel er en planet, når den er over Illinois.", "why_en": "On 24 August 2006 the International Astronomical Union adopted a definition of a planet that Pluto failed: it has not cleared its own orbit. The state of Illinois later declared that Pluto is a planet anyway whenever it passes over Illinois.", "since": 2006},
    "03-13": {"key": "fsm_cthulhu", "tier": 3, "da": "Cthulhu-eftertankens dag", "en": "Cthulhu Contemplation Day", "why_da": "I sin hus i R'lyeh venter den døde Cthulhu drømmende. Pastafarianismen har ikke noget imod et andet monster i kalenderen.", "why_en": "In his house at R'lyeh dead Cthulhu waits dreaming. Pastafarianism has no objection to another monster in the calendar."},
    "09-11": {"key": "fsm_tinfoil", "tier": 3, "da": "Sølvpapirshattens dag", "en": "Tinfoil Hat Day", "why_da": "En gruppe fra MIT målte i 2005 faktisk efter, om sølvpapirshatte skærmer mod radiobølger. Svaret var nej: ved visse frekvenser forstærker hatten dem.", "why_en": "A group at MIT actually measured in 2005 whether tinfoil hats shield against radio waves. The answer was no: at certain frequencies the hat amplifies them."},
    "01-28": {"key": "fsm_apocalypse", "tier": 3, "da": "Dommedag", "en": "The Apocalypse", "why_da": "Kalenderen har også en dommedag den 7. september, med tilføjelsen „hvis den i januar var en fuser“. Det er den slags religion, det her er.", "why_en": "The calendar also has an apocalypse on 7 September, with the note “if the one in January was a dud”. That is the kind of religion this is."},
    "09-07": {"key": "fsm_apocalypse_again", "tier": 3, "da": "Dommedag igen", "en": "The Apocalypse Again", "why_da": "„Hvis den i januar var en fuser.“ Ingen af dem er indtruffet endnu, men året er ikke omme.", "why_en": "“If the one in January was a dud.” Neither has happened yet, but the year is not over."},
    "12-09": {"key": "fsm_blank", "tier": 3, "da": "Denne dag er med vilje efterladt tom", "en": "This Day Deliberately Left Blank", "why_da": "En kalender med en helligdag hver eneste dag er nødt til at have én, der ikke er noget. Sætningen er lånt fra de tomme sider i tekniske manualer, som netop derved holder op med at være tomme.", "why_en": "A calendar with a holy day every single day has to have one that is nothing. The phrase is borrowed from the blank pages in technical manuals, which thereby stop being blank."},
    "01-19": {"key": "fsm_procrastination", "tier": 3, "da": "Udsættelsens dag er i morgen", "en": "Procrastination Day Tomorrow", "why_da": "Den 19. januar. Dagen efter står der ikke noget om udsættelse, og det er lige netop pointen.", "why_en": "19 January. The following day says nothing about procrastination, and that is exactly the point."},
    "07-16": {"key": "fsm_skip", "tier": 3, "da": "Spring-denne-dag-over-dagen", "en": "Skip This Day Day", "why_da": "Kan ikke holdes uden at blive brudt, og kan ikke brydes uden at blive holdt.", "why_en": "Cannot be kept without being broken, and cannot be broken without being kept."},
    "05-15": {"key": "fsm_time_travellers", "tier": 3, "da": "Velkommen, tidsrejsende — i går", "en": "Welcome Time Travellers Yesterday", "why_da": "Modtagelsen blev holdt dagen før. Enhver rigtig tidsrejsende kunne have nået den.", "why_en": "The reception was held the day before. Any genuine time traveller could have made it."},
    "12-29": {"key": "fsm_backwards", "tier": 3, "da": "Yad sdrawkcab", "en": "Yad sdrawkcab", "why_da": "Baglænsdagen, skrevet baglæns. Kilden staver den endda selv forkert baglæns, og det har vi ladet stå.", "why_en": "Backwards Day, written backwards. The source even gets its own reversal slightly wrong, and we have let that stand."},
    "01-16": {"key": "fsm_nothingness", "tier": 3, "da": "Intethedens dag", "en": "Nothingness Appreciation Day", "why_da": "Holdes ved ikke at gøre noget. Det er den eneste helligdag i kataloget, man ikke kan glemme.", "why_en": "Kept by doing nothing. It is the one holy day in the catalogue you cannot forget."},
    "01-24": {"key": "fsm_invent_a_god", "tier": 3, "da": "Find selv på en gud-dagen", "en": "Invent a God Day", "why_da": "Den dag, hele religionen selv stammer fra, sat på kalenderen. Reglerne er, at din gud skal kunne fremsættes lige så ubeviseligt som alle de andre.", "why_en": "The day the entire religion itself came from, placed on the calendar. The rule is that your god must be as unprovable as all the others."},
    "01-13": {"key": "fsm_sceptics", "tier": 3, "da": "Skeptikernes dag", "en": "Sceptics Day", "why_da": "Hvis du tror på den, har du misforstået den.", "why_en": "If you believe in it, you have missed the point."},
    "10-18": {"key": "fsm_irony", "tier": 3, "da": "Ironiens dag", "en": "Irony Day", "why_da": "Står på en kalender, der er lavet for at gøre grin med kalendere over helligdage.", "why_en": "Listed on a calendar made to poke fun at calendars of holy days."},
    "10-26": {"key": "fsm_onomatopoeia", "tier": 3, "da": "Lydordenes dag", "en": "Onomatopoeia Day", "why_da": "Ord, der lyder som det, de betyder. På dansk: plask, knirke, hviske. Ordet onomatopoietikon lyder i øvrigt ikke som noget som helst.", "why_en": "Words that sound like what they mean. Splash, creak, whisper. The word onomatopoeia, incidentally, sounds like nothing at all."},
}


def _slug(name: str) -> str:
    out = re.sub(r"[^a-z0-9]+", "_", name.lower()).strip("_")
    return re.sub(r"_+", "_", out)[:40] or "day"


def fetch(url: str = FEED) -> str:
    request = urllib.request.Request(url, headers={"User-Agent": "noerdilaeum/1.0"})
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8", "replace")


def parse(text: str) -> dict[str, str]:
    """Kalenderens navne, ét pr. maaned-dag. Det nyeste aar vinder.

    Nogle faa dage baerer et aarstal i navnet ("Celebrate Surviving 2025
    Day"). Ved at lade den seneste udgave vinde faar vi den nyeste form og
    ikke en, der allerede er gammel.
    """
    stamp = name = ""
    best: dict[str, tuple[str, str]] = {}
    for line in text.splitlines():
        if line.startswith("DTSTART"):
            stamp = line.rsplit(":", 1)[-1].strip()
        elif line.startswith("SUMMARY"):
            name = line.split(":", 1)[-1].strip()
        elif line.startswith("END:VEVENT"):
            if len(stamp) >= 8 and name:
                month_day = f"{stamp[4:6]}-{stamp[6:8]}"
                if month_day not in best or stamp > best[month_day][0]:
                    best[month_day] = (stamp, name)
            stamp = name = ""
    return {md: name for md, (_, name) in sorted(best.items())}


# De dage, der ikke skal staa i en kalender, man aabner foran andre.
#
# Grænsen er trukket ét sted og ikke efter smag: en dag ryger herover, hvis
# den handler udtrykkeligt om sex, koensdele eller afsondringer — eller, i
# ét tilfaelde, om at fejre et doedsfald. Antydninger og underbukser bliver,
# hvor de er. Dagene bliver IKKE kasseret; de faar deres egen gruppe, som
# er slaaet fra, og som ingen af de almindelige pakker naevner.
ADULT: frozenset[str] = frozenset({
    "01-23",  # Cunning Linguine Day
    "02-06",  # Self Stimulation Day
    "02-08",  # Get Naked Day
    "03-09",  # Erotic Dancing Day
    "03-16",  # Kinky Underwear Day
    "04-30",  # Celebrate Hitlers Death Day
    "05-03",  # Pussy Appreciation Day
    "05-13",  # Buttocks Day
    "05-16",  # Advanced Tree Hugging & Arborial Sex Day
    "05-20",  # Find a New Fetish Day
    "05-29",  # Consensual Bum Biting Day
    "06-24",  # Sexual Fantasy Day
    "06-25",  # Seamen Day
    "08-07",  # Intergalactic Intercourse Day
    "08-13",  # Self Love Day
    "08-15",  # Condom Day
    "09-02",  # Nipple Appreciation Day
    "09-08",  # Vicarious Sex Day
    "09-12",  # Nakedness Appreciation Day
    "10-10",  # Rub Things on Your Lover Day
    "10-17",  # Bottom Nibbling Day
    "10-22",  # Intergalactic Peeing Competition
    "10-23",  # Strip for your Lover Day
    "10-28",  # Extra Kinky Day
    "10-30",  # Furry Animal Fondling Day
    "11-05",  # Oral Sex Day
    "12-03",  # Vibrator Day
    "12-24",  # Orgies For World Peace Day
})

ADULT_OUT = OUT.with_name("13b_pastafarian_adult.json")


def build(names: dict[str, str]) -> tuple[dict, dict]:
    days: list[dict] = []
    adult: list[dict] = []
    used: set[str] = set()
    for month_day, raw in names.items():
        clean = _DECOR.sub("", raw).strip()
        clean = re.sub(r"\s{2,}", " ", clean)
        written = WRITTEN.get(month_day)
        if written:
            entry = {"key": written["key"], "tier": written.get("tier", 2),
                     "when": month_day}
            for field in ("da", "en", "name", "why_da", "why_en", "since"):
                if field in written:
                    entry[field] = written[field]
        else:
            key = f"fsm_{_slug(clean)}"
            if key in used:
                key = f"{key}_{month_day.replace('-', '')}"
            # Navnet er kildens og staar paa engelsk i begge sprog, som en
            # filmtitel goer. At oversaette tre hundrede ordspil ville
            # oedelaegge dem.
            entry = {"key": key, "tier": 3, "when": month_day,
                     "name": clean, "medium": "fsm"}
        used.add(entry["key"])
        (adult if month_day in ADULT else days).append(entry)
    main_file = {
        "group": "fsm",
        "note": (
            "Det Flyvende Spaghettimonsters kalender, hentet fra "
            "pastafariancalendar.com med tools/fetch_pastafarian.py. Kilden "
            "har en helligdag for HVER eneste dag i aaret, og det er en del "
            "af vitsen. De kanoniske helligdage og et udvalg af de bedste "
            "har faaet en forklaring skrevet i haanden og staar paa niveau "
            "1 og 2; resten baerer kildens eget navn og staar paa niveau 3. "
            "De groveste staar i 13b_pastafarian_adult.json."
        ),
        "days": days,
    }
    adult_file = {
        "group": "fsm18",
        "note": (
            "Samme kalender, men de dage, der handler udtrykkeligt om sex, "
            "koensdele eller afsondringer — og den ene om at fejre et "
            "doedsfald. De er ikke kasseret, for kalenderen er kun hel med "
            "dem; de staar bare i en gruppe, der er slaaet fra, og som ingen "
            "af de almindelige pakker naevner. Listen staar i ADULT i "
            "tools/fetch_pastafarian.py og kan aendres dér."
        ),
        "days": adult,
    }
    return main_file, adult_file


def main() -> int:
    try:
        text = fetch()
    except OSError as exc:
        print(f"kunne ikke hente {FEED}: {exc}", file=sys.stderr)
        return 1
    names = parse(text)
    if len(names) < 360:
        print(f"kun {len(names)} dage i feedet — det ser forkert ud", file=sys.stderr)
        return 1
    missing = ADULT - set(names)
    if missing:
        # En dag, der er flyttet eller omdoebt i kilden, maa ikke stille og
        # roligt dukke op igen i den almindelige gruppe.
        print(f"dage i ADULT, der ikke findes i feedet: {sorted(missing)}", file=sys.stderr)
        return 1

    main_file, adult_file = build(names)
    for path, doc in ((OUT, main_file), (ADULT_OUT, adult_file)):
        path.write_text(
            json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
        )
    written = sum(1 for md in names if md in WRITTEN)
    print(
        f"{len(names)} dage i alt — {len(main_file['days'])} i {OUT.name} "
        f"({written} med egen forklaring) og "
        f"{len(adult_file['days'])} i {ADULT_OUT.name}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
