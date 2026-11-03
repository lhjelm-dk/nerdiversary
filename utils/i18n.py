"""Alle tekster i braendefladen, paa dansk og engelsk."""

from __future__ import annotations

LANGUAGES = {"da": "Dansk", "en": "English"}

T: dict[str, dict[str, str]] = {
    # --- Hoved ---
    "app_title": {"da": "Nørdilæum", "en": "Nerdiversary"},
    "app_tagline": {
        "da": "Dine næste skæve mærkedage — regnet på sekundet",
        "en": "Your next special celebrations — calculated to the second",
    },
    "intro": {
        "da": "Indtast fødselsdato og -tidspunkt i sidepanelet. Så finder appen "
              "de skæve mærkedage, du ellers ville gå glip af — og lægger dem i "
              "din kalender.",
        "en": "Enter your birth date and time in the sidebar. The app finds the "
              "offbeat milestones you would otherwise miss — and puts them in "
              "your calendar.",
    },
    # --- Sidepanel ---
    "language": {"da": "Sprog", "en": "Language"},
    "who": {"da": "Hvem", "en": "Who"},
    "name_label": {"da": "Navn", "en": "Name"},
    "name_placeholder": {"da": "valgfrit", "en": "optional"},
    "birth_date": {"da": "Fødselsdato", "en": "Date of birth"},
    "birth_time": {"da": "Fødselstidspunkt", "en": "Time of birth"},
    "time_unknown": {"da": "Jeg kender ikke klokkeslættet", "en": "I don't know the time"},
    "time_unknown_help": {
        "da": "Så regnes der med kl. 12.00.00, og alle klokkeslæt markeres som omtrentlige.",
        "en": "12:00:00 is assumed, and every clock time is marked as approximate.",
    },
    "timezone": {"da": "Tidszone ved fødslen", "en": "Time zone at birth"},
    "timezone_help": {
        "da": "Alt regnes på absolut tid og vises i denne zone. Sommertid er regnet med.",
        "en": "Everything is computed on absolute time and shown in this zone. DST is handled.",
    },
    "assumptions": {"da": "Antagelser og satser", "en": "Assumptions and rates"},
    "lifespan": {"da": "Forventet levetid (år)", "en": "Assumed lifespan (years)"},
    "lifespan_help": {
        "da": "Bruges til den geologiske tidslinje og til procent-af-et-liv.",
        "en": "Used for the geological timeline and percent-of-a-life milestones.",
    },
    "bpm": {"da": "Hjerteslag pr. minut", "en": "Heartbeats per minute"},
    "breaths": {"da": "Åndedrag pr. minut", "en": "Breaths per minute"},
    "sleep": {"da": "Timers søvn pr. døgn", "en": "Hours of sleep per day"},
    "meals": {"da": "Måltider pr. døgn", "en": "Meals per day"},
    "steps": {"da": "Skridt pr. døgn", "en": "Steps per day"},
    "max_age": {"da": "Regn højst til alder", "en": "Compute up to age"},
    # --- Levende tællere ---
    "live_header": {"da": "Lige nu", "en": "Right now"},
    "age_seconds": {"da": "Din alder i sekunder", "en": "Your age in seconds"},
    "age_days": {"da": "Din alder i dage", "en": "Your age in days"},
    "age_hours": {"da": "Din alder i timer", "en": "Your age in hours"},
    "age_months": {"da": "Din alder i måneder", "en": "Your age in months"},
    "age_years": {"da": "Din alder i år", "en": "Your age in years"},
    "si_help": {
        "da": "Forløbet tid, regnet i SI-enheder fra fødselsøjeblikket. Ved "
              "sommertidsskift forskydes væguret en time i forhold til dette tal.",
        "en": "Elapsed time in SI units from the birth instant. At a DST change "
              "the wall clock shifts an hour relative to this number.",
    },
    "calendar_help": {
        "da": "Kalenderregning, ikke gennemsnit: tælleren står på rundt 100,00 "
              "netop når mærkedagen „100 måneder“ indtræffer. Brøkdelen "
              "måles mod den igangværende måneds faktiske længde, så februar "
              "tikker hurtigere end januar.",
        "en": "Calendar arithmetic, not averages: the counter reads exactly "
              "100.00 at the moment the “100 months” milestone fires. The "
              "fraction is measured against the current month's actual length, "
              "so February ticks faster than January.",
    },
    "calendar_year_help": {
        "da": "Kalenderår, ikke tropiske år. 8,00 betyder, at du fyldte 8 i dag.",
        "en": "Calendar years, not tropical years. 8.00 means you turned 8 today.",
    },
    "unix_now": {"da": "Unix-tid lige nu", "en": "Unix time right now"},
    "unix_birth": {"da": "Dit fødselstidsstempel", "en": "Your birth timestamp"},
    "leap_seconds": {"da": "Skudsekunder siden fødslen", "en": "Leap seconds since birth"},
    "leap_help": {
        "da": "Ekstra sekunder indsat i UTC for at følge Jordens uregelmæssige rotation.",
        "en": "Extra seconds added to UTC to account for Earth's irregular rotation.",
    },
    "stardate_now": {"da": "Stjernedato", "en": "Stardate"},
    "stardate_help": {
        "da": "Ja, Star Trek. Der findes ingen officiel formel — Paramount har "
              "aldrig udgivet en. Her bruges TNG-konventionen, hvor 1000 "
              "enheder er ét år og stardate 41000.0 er år 2364. Nutiden "
              "forskydes 340 år frem, så du lander midt i TNG-æraen i stedet "
              "for på et negativt tal. Hele forklaringen står under Noter.",
        "en": "Yes, Star Trek. There is no official formula — Paramount never "
              "published one. This uses the TNG convention where 1000 units is "
              "one year and stardate 41000.0 is the year 2364. The present day "
              "is shifted 340 years forward so you land in the middle of the "
              "TNG era instead of on a negative number. Full explanation under "
              "Notes.",
    },
    "born_before_utc": {
        "da": "Du er født før 1. januar 1972, hvor UTC fik skudsekunder. Tallet "
              "tæller fra 1972.",
        "en": "You were born before 1 January 1972, when UTC adopted leap seconds. "
              "The count starts in 1972.",
    },
    # --- Næste mærkedag ---
    "next_up": {"da": "Næste mærkedag", "en": "Next milestone"},
    "countdown": {"da": "Nedtælling", "en": "Countdown"},
    "progress": {"da": "Fremdrift", "en": "Progress"},
    "nothing_ahead": {
        "da": "Ingen valgte mærkedage ligger i fremtiden. Prøv at vælge flere grupper.",
        "en": "None of the selected milestones lie ahead. Try selecting more groups.",
    },
    "most_recent": {"da": "Senest passerede", "en": "Most recently passed"},
    "that_was": {"da": "Det var", "en": "That was"},
    "days_ago": {"da": "dage siden", "en": "days ago"},
    # --- Faneblade ---
    "tab_list": {"da": "Liste", "en": "List"},
    "tab_calendar": {"da": "Kalender", "en": "Calendar"},
    "tab_timeline": {"da": "Tidslinje", "en": "Timeline"},
    "tab_select": {"da": "Vælg mærkedage", "en": "Choose milestones"},
    "tab_export": {"da": "Eksport", "en": "Export"},
    "tab_notes": {"da": "Noter", "en": "Notes"},
    # --- Tabel ---
    "filters": {"da": "Filtre", "en": "Filters"},
    "filters_scope": {
        "da": "Filtre — gælder liste, kalender og eksport",
        "en": "Filters — apply to list, calendar and export",
    },
    "filter_groups": {"da": "Grupper", "en": "Groups"},
    "filter_window": {"da": "Tidsrum", "en": "Time window"},
    "window_all": {"da": "Alt", "en": "Everything"},
    "window_1": {"da": "Næste år", "en": "Next year"},
    "window_5": {"da": "Næste 5 år", "en": "Next 5 years"},
    "window_10": {"da": "Næste 10 år", "en": "Next 10 years"},
    "window_25": {"da": "Næste 25 år", "en": "Next 25 years"},
    "when": {"da": "Hvornår", "en": "When"},
    "only_future": {"da": "Kun fremtidige", "en": "Future only"},
    "only_past": {"da": "Kun passerede", "en": "Past only"},
    "both": {"da": "Begge", "en": "Both"},
    "search": {"da": "Søg", "en": "Search"},
    "search_placeholder": {"da": "fx gigasekund, 73, måne", "en": "e.g. gigasecond, 73, moon"},
    "col_milestone": {"da": "Mærkedag", "en": "Milestone"},
    "col_date": {"da": "Dato (DD.MM.ÅÅÅÅ)", "en": "Date (DD.MM.YYYY)"},
    "col_estimate": {"da": "Skøn", "en": "Est."},
    "estimate_help": {
        "da": "⚠ betyder, at tidspunktet bygger på en gennemsnitssats — "
              "hjerteslag, åndedrag, søvn, måltider, skridt, månemåneder eller "
              "kilometer om Solen. Satserne står i sidepanelet.",
        "en": "⚠ means the moment rests on an average rate — heartbeats, "
              "breaths, sleep, meals, steps, lunar months or kilometres around "
              "the Sun. The rates are in the sidebar.",
    },
    "col_time": {"da": "Klokkeslæt", "en": "Time"},
    "col_weekday": {"da": "Ugedag", "en": "Weekday"},
    "col_age": {"da": "Din alder", "en": "Your age"},
    "col_countdown": {"da": "Om / siden", "en": "In / ago"},
    "col_group": {"da": "Gruppe", "en": "Group"},
    "col_stardate": {"da": "Stjernedato", "en": "Stardate"},
    "col_note": {"da": "Forklaring", "en": "Explanation"},
    "showing_n": {"da": "Viser {n} mærkedage", "en": "Showing {n} milestones"},
    "no_results": {
        "da": "Ingen mærkedage matcher filtrene.",
        "en": "No milestones match the filters.",
    },
    "estimate_marker": {"da": "⚠ skøn", "en": "⚠ estimate"},
    # --- Kalender ---
    "calendar_hint": {
        "da": "Hold musen over en begivenhed for at se forklaringen, eller klik "
              "for at få den stående. Kalenderen åbner på måneden for din næste "
              "mærkedag.",
        "en": "Hover an event to read its explanation, or click to keep it on "
              "screen. The calendar opens on the month of your next milestone.",
    },
    "calendar_tooltip_hint": {
        "da": "Værktøjstippet viser dato, din alder og forklaringen.",
        "en": "The tooltip shows the date, your age and the explanation.",
    },
    "cal_view": {"da": "Visning", "en": "View"},
    "cal_month": {"da": "Måned", "en": "Month"},
    "cal_year": {"da": "År", "en": "Year"},
    "cal_list": {"da": "Liste", "en": "Agenda"},
    "jump_next": {"da": "Spring til næste mærkedag", "en": "Jump to next milestone"},
    "jump_prev": {"da": "Spring til forrige", "en": "Jump to previous"},
    "calendar_empty": {
        "da": "Ingen valgte mærkedage at vise.",
        "en": "No selected milestones to show.",
    },
    # --- Tidslinje ---
    "timeline_hint": {
        "da": "Tidslinjen viser **hele livet — både fortid og fremtid** — "
              "uanset hvad *Hvornår* og *Tidsrum* står på ovenfor. Gruppefilteret "
              "og fritekstsøgningen gælder stadig. Hold musen over et mærke "
              "eller en etiket for at se forklaringen.",
        "en": "The timeline shows **a whole life — past as well as future** — "
              "whatever *When* and *Time window* are set to above. The group "
              "filter and the free-text search still apply. Hover a mark or a "
              "label to read its explanation.",
    },
    "tl_mode": {"da": "Skala", "en": "Scale"},
    "tl_cascade": {"da": "Kaskade", "en": "Cascade"},
    "tl_log": {"da": "Logaritmisk", "en": "Logarithmic"},
    "tl_cascade_help": {
        "da": "Den geologiske tidsskalas opbygning: hver række zoomer ind på et "
              "udsnit af rækken over. Du ser helheden og detaljen på samme tid.",
        "en": "The geologic time scale's structure: each row zooms in on a slice "
              "of the row above it. You see the whole and the detail at once.",
    },
    "tl_log_help": {
        "da": "Aksen i tierpotenser fra fødslen. Så ligger 10⁶, 10⁷, 10⁸ og 10⁹ "
              "sekunder lige langt fra hinanden, og hele livet fra første sekund "
              "til 150 år er på én skærm.",
        "en": "The axis in powers of ten from birth. 10⁶, 10⁷, 10⁸ and 10⁹ "
              "seconds then sit evenly apart, and a whole life from the first "
              "second to 150 years fits on one screen.",
    },
    "tl_focus": {"da": "Zoom ind omkring", "en": "Zoom in around"},
    "tl_focus_help": {
        "da": "Det punkt i livet, de nederste rækker skal udvide. Står på i dag.",
        "en": "The point in the life the lower rows expand. Starts at today.",
    },
    "tl_span": {"da": "Nederste række dækker", "en": "Bottom row covers"},
    "tl_span_help": {
        "da": "Hvor tæt den nederste række zoomer ind. Rækkerne derimellem "
              "fordeler sig jævnt op til hele livet.",
        "en": "How closely the bottom row zooms in. The rows in between spread "
              "evenly up to the whole life.",
    },
    "tl_levels": {"da": "Rækker", "en": "Rows"},
    "tl_levels_help": {
        "da": "Hvor mange trin der skal være fra hele livet ned til den "
              "nederste række.",
        "en": "How many steps there should be from the whole life down to the "
              "bottom row.",
    },
    "tl_today": {"da": "I dag", "en": "Today"},
    "tl_now": {"da": "NU", "en": "NOW"},
    "tl_whole_life": {"da": "Hele livet", "en": "A whole life"},
    "tl_log_axis": {"da": "Logaritmisk", "en": "Logarithmic"},
    "tl_from_birth": {"da": "sekunder fra fødslen", "en": "seconds from birth"},
    "tl_hidden": {
        "da": "+{n} uden plads til en etiket",
        "en": "+{n} with no room for a label",
    },
    "tl_empty_row": {
        "da": "ingen mærkedage i dette tidsrum",
        "en": "no milestones in this stretch",
    },
    "tl_before_birth": {
        "da": "{n} ligger før første sekund",
        "en": "{n} fall before the first second",
    },
    "tl_lived": {"da": "Levet", "en": "Lived"},
    "tl_behind": {"da": "Passeret", "en": "Behind you"},
    "tl_ahead": {"da": "Forude", "en": "Ahead"},
    "tl_quiet": {"da": "Længste stille stræk", "en": "Longest quiet stretch"},
    "tl_quiet_help": {
        "da": "Det længste tidsrum i livet uden en eneste af de valgte "
              "mærkedage. De stille år er der også.",
        "en": "The longest stretch of the life without a single one of the "
              "chosen milestones. The quiet years count too.",
    },
    "tl_empty": {
        "da": "Ingen valgte mærkedage at tegne.",
        "en": "No selected milestones to draw.",
    },
    "tl_shown": {
        "da": "{n} mærkedage tegnet over {span}.",
        "en": "{n} milestones drawn across {span}.",
    },
    "tl_download": {"da": "Hent tidslinjen (SVG)", "en": "Download the timeline (SVG)"},
    "tl_download_help": {
        "da": "Vektorgrafik — den kan skaleres til en plakat uden at blive "
              "grynet. Åbnes i en browser, Inkscape eller Illustrator.",
        "en": "Vector graphics — it scales to a poster without going grainy. "
              "Opens in a browser, Inkscape or Illustrator.",
    },
    # --- Valg ---
    "select_hint": {
        "da": "Alle grupper er slået til fra start, undtagen legenderne. "
              "Fjern fluebenene ved det, du ikke gider fejre.",
        "en": "Every group is on by default except the legends. Untick whatever "
              "you cannot be bothered to celebrate.",
    },
    "bundles": {"da": "Pakker", "en": "Bundles"},
    "bundles_hint": {
        "da": "Ét klik på en pakke erstatter hele dit nuværende valg.",
        "en": "One click on a bundle replaces your whole current selection.",
    },
    "bundle_applied": {
        "da": "{name} slået til — {n} mærkedage valgt.",
        "en": "{name} applied — {n} milestones selected.",
    },
    "select_all": {"da": "Vælg alle", "en": "Select all"},
    "clear_all": {"da": "Ryd alle", "en": "Clear all"},
    "group_all": {"da": "Alle i gruppen", "en": "All in group"},
    "group_none": {"da": "Ingen", "en": "None"},
    "selected_count": {
        "da": "{n} af {total} mærkedage valgt",
        "en": "{n} of {total} milestones selected",
    },
    "select_search": {"da": "Søg i kataloget", "en": "Search the catalogue"},
    "select_search_placeholder": {
        "da": "fx fibonacci, hexadecimal, måne, 5318008",
        "en": "e.g. fibonacci, hexadecimal, moon, 5318008",
    },
    "select_search_help": {
        "da": "Søger i navn, forklaring, gruppe og i selve tallet uden "
              "tusindtalsskilletegn.",
        "en": "Searches the name, the explanation, the group and the raw number "
              "without thousands separators.",
    },
    "select_matches": {
        "da": "{n} af {total} mærkedage matcher — de står samlet nedenfor, "
              "uanset hvilken gruppe de hører til.",
        "en": "{n} of {total} milestones match — they are listed together "
              "below, whatever group they belong to.",
    },
    "select_no_matches": {
        "da": "Ingen mærkedage matcher. Søgningen leder i navn, forklaring, "
              "gruppe og tal.",
        "en": "No milestones match. The search looks at the name, the "
              "explanation, the group and the number.",
    },
    "match_all": {"da": "Slå alle fundne til", "en": "Turn all matches on"},
    "match_none": {"da": "Slå alle fundne fra", "en": "Turn all matches off"},
    # --- Jer to ---
    "pair_section": {"da": "Jer to", "en": "The two of you"},
    "pair_hint": {
        "da": "Udfyld en anden fødselsdato, og gruppen 👥 Jer to vågner: "
              "det ene øjeblik, hvor den ene er dobbelt så gammel som den "
              "anden, og de datoer hvor jeres to aldre lagt sammen runder et "
              "pænt tal.",
        "en": "Fill in a second date of birth and the 👥 The two of you group "
              "wakes up: the single moment one of you is twice as old as the "
              "other, and the dates where your two ages added together reach a "
              "round number.",
    },
    "pair_use": {"da": "Sammenlign med en anden", "en": "Compare with someone else"},
    "pair_name": {"da": "Den andens navn", "en": "Their name"},
    "pair_date": {"da": "Den andens fødselsdato", "en": "Their date of birth"},
    "pair_time": {"da": "Den andens fødselstidspunkt", "en": "Their time of birth"},
    "pair_time_help": {
        "da": "Kender du ikke klokkeslættet, så lad det stå på 12.00.00.",
        "en": "If you do not know the time, leave it at 12:00:00.",
    },
    "pair_gap": {"da": "Aldersforskel til {name}", "en": "Age gap to {name}"},
    "pair_twins": {
        "da": "I er født i samme sekund. Forholdsmærkedagene findes ikke for "
              "tvillinger — til gengæld rammer I alle sum-mærkedagene på "
              "jeres fælles halve tal.",
        "en": "You were born in the same second. The ratio milestones do not "
              "exist for twins — but you hit every combined-age milestone at "
              "exactly half the number each.",
    },
    "pair_someone": {"da": "den anden", "en": "the other"},
    # --- Eksport ---
    "export_hint": {
        "da": "Hent en .ics-fil og importér den i Google Kalender, Outlook eller "
              "Apple Kalender. Begivenhederne har stabile id'er, så en ny import "
              "opdaterer dem i stedet for at lave dubletter.",
        "en": "Download an .ics file and import it into Google Calendar, Outlook "
              "or Apple Calendar. Events carry stable IDs, so re-importing "
              "updates them instead of creating duplicates.",
    },
    "export_settings": {"da": "Indstillinger", "en": "Settings"},
    "all_day": {"da": "Heldagsbegivenheder", "en": "All-day events"},
    "all_day_help": {
        "da": "Slå til, hvis klokkeslættet er ligegyldigt for dig.",
        "en": "Turn on if the time of day does not matter to you.",
    },
    "duration": {"da": "Varighed (minutter)", "en": "Duration (minutes)"},
    "alarm_day": {"da": "Påmindelse 1 dag før", "en": "Reminder 1 day before"},
    "alarm_hour": {"da": "Påmindelse 1 time før", "en": "Reminder 1 hour before"},
    "download_ics": {"da": "Hent .ics-fil", "en": "Download .ics file"},
    "download_csv": {"da": "Hent Google-CSV", "en": "Download Google CSV"},
    "csv_hint": {
        "da": "CSV'en er til Google Kalenders egen importfunktion. Den bruger "
              "amerikansk datoformat, fordi Google kræver det.",
        "en": "The CSV is for Google Calendar's own import. It uses US date "
              "format because Google insists.",
    },
    "direct_links": {"da": "Direkte links", "en": "Direct links"},
    "links_hint": {
        "da": "Ét klik lægger én begivenhed i Google Kalender. Her er de "
              "førstkommende.",
        "en": "One click adds a single event to Google Calendar. Here are the "
              "next few.",
    },
    "add_to_google": {"da": "Læg i Google Kalender", "en": "Add to Google Calendar"},
    "export_count": {
        "da": "Eksporten indeholder {n} begivenheder (det, filtrene i Liste viser).",
        "en": "The export contains {n} events (whatever the List filters show).",
    },
    # --- Noter ---
    "notes_hint": {
        "da": "Baggrunden for de mærkeligste tal i appen.",
        "en": "The background to the strangest numbers in the app.",
    },
    # --- Diverse ---
    "approximate_warning": {
        "da": "Fødselstidspunktet er sat til kl. 12.00.00, fordi du ikke kender "
              "det. Datoerne holder; klokkeslættene er omtrentlige.",
        "en": "The birth time is set to 12:00:00 because you don't know it. The "
              "dates hold; the clock times are approximate.",
    },
    "footer": {
        "da": "Regnet på absolut tid i UTC og vist i din tidszone. Skudsekunder "
              "er ikke talt med — se Noter.",
        "en": "Computed on absolute time in UTC and shown in your time zone. "
              "Leap seconds are not counted — see Notes.",
    },
}


def t(key: str, lang: str = "da", **kwargs: object) -> str:
    """Hent en tekst. Ukendte noegler returneres raat, saa fejl er synlige."""
    entry = T.get(key)
    if entry is None:
        return key
    text = entry.get(lang, entry.get("da", key))
    return text.format(**kwargs) if kwargs else text
