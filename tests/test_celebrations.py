"""Test af festdagene — datoangivelserne, importen, moenstrene og Jordens aar.

Det foelsomme sted her er ikke regnestykkerne, men *indlaesningen*: dagene
staar i datafiler, og en tastefejl i en fil maa ikke forsvinde i stilhed.
Derfor foerer de fleste af disse test an paa, at importen siger fra.

Koer dem med:
    python -m pytest -q
"""

from __future__ import annotations

import json
from datetime import date, datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from utils import datepatterns as dp
from utils import geoyear as gy
from utils.catalog import BUNDLES, BUNDLES_BY_KEY, GROUPS, GROUPS_BY_KEY, MILESTONES, Bundle
from utils.celebrations import (
    DATA_DIR,
    PREFIX,
    SpecError,
    celebration_milestones,
    format_note,
    load_days,
    load_dir,
    parse_spec,
    spec_in_year,
)
from utils.engine import (
    BIRTH_SCOPE,
    BOTH_SCOPES,
    CALENDAR_SCOPE,
    SCOPES,
    Profile,
    all_milestones,
    build_label,
    bundle_keys,
    bundle_scope,
    compute,
    milestone_instant,
)
from utils.geology import GEO_BY_KEY
from utils.i18n import t
from utils.units import CALENDAR_DAY_UNITS, EARTH_AGE_MA, ONE_OFF_UNITS

CPH = ZoneInfo("Europe/Copenhagen")
UTC = timezone.utc

NOW = datetime(2026, 11, 3, 9, 0, tzinfo=UTC)


def profile_at(year=1980, month=6, day=15, tz=CPH, **kwargs) -> Profile:
    return Profile(birth_local=datetime(year, month, day, 12, 0, tzinfo=tz), **kwargs)


def celebrations_by_key() -> dict[str, object]:
    return {m.key: m for m in celebration_milestones()}


# -------------------------------------------------------------------------
# Datoangivelserne
# -------------------------------------------------------------------------


@pytest.mark.parametrize(
    "text, kind, month, day",
    [
        ("05-04", "annual", 5, 4),
        ("11-11", "annual", 11, 11),
        ("02-29", "annual", 2, 29),          # Skuddagen maa gerne staa i en fil.
        ("1969-07-21", "once", 7, 21),
        ("1955-11-12 22:04", "once", 11, 12),
    ],
)
def test_a_date_is_read_as_what_it_says(text, kind, month, day):
    spec = parse_spec(text)
    assert (spec.kind, spec.month, spec.day) == (kind, month, day)


def test_a_clock_time_is_kept():
    spec = parse_spec("11-05 20:59")
    assert (spec.hour, spec.minute) == (20, 59)
    assert spec.kind == "annual"


def test_an_nth_rule_names_a_weekday_and_a_count():
    spec = parse_spec("nth:11:fri:1")
    assert spec.kind == "nth"
    assert (spec.month, spec.weekday, spec.nth) == (11, 4, 1)


@pytest.mark.parametrize(
    "text",
    [
        "",
        "   ",
        "maj",
        "13-01",                 # Der er ingen 13. maaned.
        "02-30",                 # Februar har ikke 30 dage i noget aar.
        "1969-02-30",
        "05-04 25:00",
        "05-04 12:99",
        "05-04 middag",
        "nth:11:fri",            # For faa led.
        "nth:11:friday:1",       # Ukendt ugedag.
        "nth:13:fri:1",
        "nth:11:fri:0",          # Den nulte fredag findes ikke.
        "nth:11:fri:9",
        "802701-01-01",          # Uden for enhver kalender.
    ],
)
def test_a_date_that_does_not_make_sense_is_rejected(text):
    """Importen skal kunne stole paa, at en angivelse, der slipper igennem, holder."""
    with pytest.raises(SpecError):
        parse_spec(text)


def test_the_same_text_is_only_read_once():
    """Motoren slaar den samme angivelse op for hver udregning, saa den huskes."""
    assert parse_spec("05-04") is parse_spec("05-04")


# --- Hvilken dag falder reglen paa? --------------------------------------


def test_a_fixed_day_is_the_same_every_year():
    for year in (2024, 2025, 2026):
        assert spec_in_year(parse_spec("05-04"), year) == date(year, 5, 4)


def test_the_leap_day_only_exists_in_a_leap_year():
    spec = parse_spec("02-29")
    assert spec_in_year(spec, 2024) == date(2024, 2, 29)
    assert spec_in_year(spec, 2025) is None


@pytest.mark.parametrize(
    "text, year, expected",
    [
        ("nth:11:fri:1", 2026, date(2026, 11, 6)),      # J-dag 2026.
        ("nth:05:sun:2", 2026, date(2026, 5, 10)),      # Mors dag 2026.
        ("nth:07:fri:-1", 2026, date(2026, 7, 31)),     # Sidste fredag i juli.
        ("nth:09:fri:-1", 2026, date(2026, 9, 25)),     # Sidste fredag i september.
        ("nth:10:tue:2", 2026, date(2026, 10, 13)),     # Anden tirsdag i oktober.
    ],
)
def test_an_nth_rule_lands_on_the_right_weekday(text, year, expected):
    found = spec_in_year(parse_spec(text), year)
    assert found == expected
    assert found.weekday() == parse_spec(text).weekday


def test_a_fifth_weekday_that_does_not_exist_answers_nothing():
    """Februar 2026 har fire soendage. Den femte skal give None, ikke marts."""
    assert spec_in_year(parse_spec("nth:02:sun:5"), 2026) is None


def test_a_one_off_date_only_exists_in_its_own_year():
    spec = parse_spec("1969-07-21")
    assert spec_in_year(spec, 1969) == date(1969, 7, 21)
    assert spec_in_year(spec, 1970) is None


# -------------------------------------------------------------------------
# Noten om datoformat
# -------------------------------------------------------------------------


def test_a_date_that_can_be_misread_says_so():
    da, en = format_note(parse_spec("05-04"))
    assert "amerikansk" in da and "to forskellige dage" in da
    assert "month-first" in en


def test_a_date_that_reads_the_same_both_ways_says_that():
    da, en = format_note(parse_spec("11-11"))
    assert "står ens" in da
    assert "reads the same" in en


def test_a_date_past_the_twelfth_is_left_alone():
    """Der er ingen 25. maaned, saa 25.05 kan ikke laeses forkert — og saa tier noten."""
    assert format_note(parse_spec("05-25")) == ("", "")


def test_a_weekday_rule_has_no_format_to_confuse():
    assert format_note(parse_spec("nth:11:fri:1")) == ("", "")


# -------------------------------------------------------------------------
# Indlaesningen af datafilerne
# -------------------------------------------------------------------------


def test_the_data_files_are_there_and_hold_days():
    assert DATA_DIR.is_dir(), f"datamappen mangler: {DATA_DIR}"
    assert len(load_days().milestones) > 250


def test_every_file_is_valid_json_with_a_known_group():
    for path in sorted(DATA_DIR.glob("*.json")):
        payload = json.loads(path.read_text(encoding="utf-8"))
        assert payload["group"] in GROUPS_BY_KEY, f"{path.name} peger på en ukendt gruppe"
        assert payload["days"], f"{path.name} er tom"


def test_the_only_thing_skipped_is_the_date_no_calendar_can_hold():
    """Aar 802.701 staar der med vilje. Alt andet skal gaa igennem."""
    skipped = load_days().skipped
    assert [s.key for s in skipped] == ["time_machine"]
    assert "802701" in skipped[0].reason


def test_a_bad_entry_is_skipped_with_a_reason_and_the_rest_survives(tmp_path):
    (tmp_path / "test.json").write_text(
        json.dumps(
            {
                "group": "pop",
                "days": [
                    {"key": "god", "when": "05-04", "name": "Den gode"},
                    {"key": "skaev", "when": "13-45", "name": "Den skæve"},
                    {"key": "navnloes", "when": "05-05"},
                    {"key": "god", "when": "06-06", "name": "Den dobbelte"},
                    {"key": "", "when": "07-07", "name": "Den navnløse nøgle"},
                ],
            }
        ),
        encoding="utf-8",
    )
    found = load_dir(tmp_path)
    assert [m.key for m in found.milestones if m.group == "pop"] == [f"{PREFIX}god"]
    reasons = {s.key: s.reason for s in found.skipped}
    assert set(reasons) == {"skaev", "navnloes", "god", "—"}
    assert "to gange" in reasons["god"]
    assert "navn" in reasons["navnloes"]


def test_a_file_with_an_unknown_group_is_skipped_whole(tmp_path):
    (tmp_path / "test.json").write_text(
        json.dumps({"group": "findes-ikke", "days": [{"key": "a", "when": "05-04", "name": "A"}]}),
        encoding="utf-8",
    )
    found = load_dir(tmp_path)
    assert not [m for m in found.milestones if m.group == "findes-ikke"]
    assert "ukendt gruppe" in found.skipped[0].reason


def test_a_missing_folder_is_reported_and_not_a_crash(tmp_path):
    found = load_dir(tmp_path / "findes-ikke")
    assert found.milestones == ()
    assert "findes ikke" in found.skipped[0].reason


def test_a_file_that_is_not_json_is_reported(tmp_path):
    (tmp_path / "test.json").write_text("{dette er ikke json", encoding="utf-8")
    assert "kunne ikke læses" in load_dir(tmp_path).skipped[0].reason


def test_one_name_can_serve_both_languages(tmp_path):
    """Titler bliver ikke oversat — DOOM hedder DOOM paa begge sprog."""
    (tmp_path / "test.json").write_text(
        json.dumps({"group": "pop", "days": [{"key": "d", "when": "12-10", "name": "DOOM"}]}),
        encoding="utf-8",
    )
    milestone = load_dir(tmp_path).milestones[0]
    assert milestone.label_da == milestone.label_en == "DOOM"


def test_a_medium_gives_the_entry_its_explanation(tmp_path):
    (tmp_path / "test.json").write_text(
        json.dumps(
            {"group": "pop", "days": [{"key": "d", "when": "12-10", "name": "X", "medium": "film"}]}
        ),
        encoding="utf-8",
    )
    milestone = load_dir(tmp_path).milestones[0]
    assert "Biografpremieren" in milestone.why_da
    assert "cinemas" in milestone.why_en


def test_the_work_is_put_in_the_label(tmp_path):
    """Paa en fiktiv helligdag er vaerket den oplysning, man leder efter."""
    (tmp_path / "test.json").write_text(
        json.dumps(
            {
                "group": "fiction",
                "days": [{"key": "f", "when": "12-23", "name": "Festivus", "work": "Seinfeld"}],
            }
        ),
        encoding="utf-8",
    )
    assert load_dir(tmp_path).milestones[0].label_da == "Festivus · Seinfeld"


# -------------------------------------------------------------------------
# Festdagene i kataloget
# -------------------------------------------------------------------------


def test_every_celebration_key_is_marked_as_one_and_is_unique():
    keys = [m.key for m in celebration_milestones()]
    assert len(keys) == len(set(keys))
    assert all(key.startswith(PREFIX) for key in keys)


def test_no_celebration_collides_with_the_catalogue():
    """Kataloget og festdagene maa aldrig kunne kalde to ting det samme."""
    assert not {m.key for m in MILESTONES} & {m.key for m in celebration_milestones()}


def test_every_celebration_belongs_to_a_group_the_app_knows():
    for milestone in celebration_milestones():
        assert milestone.group in GROUPS_BY_KEY, milestone.key


def test_every_celebration_is_a_calendar_day_with_a_date():
    for milestone in celebration_milestones():
        assert milestone.unit in CALENDAR_DAY_UNITS, milestone.key
        assert milestone.when, milestone.key
        parse_spec(milestone.when)          # Rejser, hvis den ikke kan laeses.


@pytest.mark.parametrize("lang", ["da", "en"])
def test_every_celebration_is_named_and_explained_in_both_languages(lang):
    profile = profile_at()
    for milestone in celebration_milestones():
        assert build_label(milestone, profile, lang).strip(), milestone.key
        assert milestone.why(lang).strip(), milestone.key


def test_the_celebration_groups_are_all_switched_off_to_begin_with():
    """Der er flere tusind festdage. De maa ikke drukne de maerkedage, appen handler om."""
    groups = {m.group for m in celebration_milestones()}
    for key in groups:
        assert not GROUPS_BY_KEY[key].default_on, f"{key} er slaaet til fra start"


def test_every_new_bundle_points_at_groups_that_exist():
    known = {g.key for g in GROUPS}
    for bundle in BUNDLES:
        assert set(bundle.groups) <= known, bundle.key


def test_every_celebration_group_can_be_reached_from_a_bundle():
    """En gruppe, ingen pakke naevner, kan kun findes ved at lede."""
    covered = {key for bundle in BUNDLES for key in bundle.groups}
    assert {m.group for m in celebration_milestones()} <= covered


# -------------------------------------------------------------------------
# Motoren: hvornaar falder en festdag?
# -------------------------------------------------------------------------


def test_a_recurring_day_is_the_next_time_it_falls():
    profile = profile_at(1980)
    milestone = celebrations_by_key()[f"{PREFIX}starwars"]
    when = milestone_instant(milestone, profile, NOW)
    assert when > NOW
    local = when.astimezone(CPH)
    assert (local.month, local.day) == (5, 4)
    assert local.year == 2027          # 4. maj 2026 er passeret den 3. november.


def test_a_recurring_day_still_to_come_this_year_is_this_year():
    milestone = celebrations_by_key()[f"{PREFIX}festivus"]
    local = milestone_instant(milestone, profile_at(), NOW).astimezone(CPH)
    assert (local.year, local.month, local.day) == (2026, 12, 23)


def test_a_clock_time_is_kept_in_local_time():
    """J-dag begynder 20.59 dansk tid — ikke 20.59 UTC."""
    milestone = celebrations_by_key()[f"{PREFIX}jdag"]
    local = milestone_instant(milestone, profile_at(), NOW).astimezone(CPH)
    assert (local.hour, local.minute) == (20, 59)
    assert local.weekday() == 4 and local.day <= 7      # Foerste fredag i november.
    assert local.month == 11


def test_a_one_off_date_is_the_day_it_is():
    milestone = celebrations_by_key()[f"{PREFIX}doom"]
    local = milestone_instant(milestone, profile_at(), NOW).astimezone(CPH)
    assert (local.year, local.month, local.day) == (1993, 12, 10)


def test_a_one_off_date_does_not_move_with_the_clock():
    """En premiere i 1993 er den samme dag, uanset hvornaar man spoerger."""
    milestone = celebrations_by_key()[f"{PREFIX}doom"]
    profile = profile_at()
    first = milestone_instant(milestone, profile, NOW)
    later = milestone_instant(milestone, profile, NOW + timedelta(days=4000))
    assert first == later


def test_a_date_from_before_you_were_born_is_not_your_milestone():
    """Maanelandingen er ikke din maerkedag, hvis du blev foedt i 1980."""
    occasions = compute(profile_at(1980), lang="da", now=NOW)
    keys = {o.milestone.key for o in occasions}
    assert f"{PREFIX}moon_landing" not in keys
    assert f"{PREFIX}doom" in keys


def test_a_date_from_your_own_lifetime_is():
    occasions = compute(profile_at(1960), lang="da", now=NOW)
    assert f"{PREFIX}moon_landing" in {o.milestone.key for o in occasions}


def test_a_date_beyond_the_horizon_is_dropped():
    """Ripley bliver fundet i 2179. Det naar de fleste ikke."""
    keys = {o.milestone.key for o in compute(profile_at(1980), lang="da", now=NOW)}
    assert f"{PREFIX}ripley_rescued" not in keys


def test_a_celebration_knows_how_old_you_were():
    """Det personlige ved en fast dato er netop alderen paa dagen."""
    occasion = next(
        o
        for o in compute(profile_at(1980, 6, 15), lang="da", now=NOW)
        if o.milestone.key == f"{PREFIX}doom"
    )
    assert occasion.age_at(profile_at(1980, 6, 15)).years == 13


def test_the_date_that_cannot_be_read_never_reaches_the_catalogue():
    assert f"{PREFIX}time_machine" not in {m.key for m in all_milestones()}


# -------------------------------------------------------------------------
# Talmoenstrene
# -------------------------------------------------------------------------


def test_every_family_has_its_own_group_in_the_catalogue():
    for family in dp.FAMILIES:
        assert family.group in GROUPS_BY_KEY, family.group


def test_every_pattern_day_is_a_real_date_in_its_own_group():
    for milestone in dp.pattern_milestones():
        assert milestone.group in dp.FAMILIES_BY_GROUP
        year, month, day = (int(part) for part in milestone.when.split("-"))
        date(year, month, day)          # Rejser, hvis dagen ikke findes.


def test_a_pattern_day_is_not_counted_twice():
    keys = [m.key for m in dp.pattern_milestones()]
    assert len(keys) == len(set(keys))


# --- Palindromerne ------------------------------------------------------


def test_this_century_has_twenty_nine_palindrome_days_and_they_are_all_in_february():
    """Det tal bliver ofte sagt at vaere tolv. Det er det ikke.

    Aarstallet er spejlingen af dag og maaned, saa i 2000-tallet skal
    maaneden ende paa 02 — altsaa februar — og dagen kan vaere alt fra den 1.
    til den 29. Det giver 29, ikke 12.
    """
    found = list(dp.palindromes(2000))
    assert len(found) == 29
    assert {hit.month for hit in found} == {2}
    assert {hit.day for hit in found} == set(range(1, 30))


def test_a_palindrome_day_really_reads_the_same_both_ways():
    for century in dp.CENTURIES:
        for hit in dp.palindromes(century):
            text = f"{hit.day:02d}{hit.month:02d}{hit.year}"
            assert text == text[::-1], text


def test_the_twentieth_century_had_no_palindrome_days_at_all():
    """Et aarstal paa 19xx skulle spejle en 91. maaned. Den findes ikke."""
    assert list(dp.palindromes(1900)) == []


def test_the_two_famous_palindromes_say_what_else_they_are():
    notes = {(h.year, h.month, h.day): h.da for h in dp.palindromes(2000)}
    assert "Twosday" in notes[(2022, 2, 22)]
    assert "lommeregner" in notes[(2022, 2, 22)]
    assert "amerikansk" in notes[(2020, 2, 2)]


# --- Sekvenserne --------------------------------------------------------


def test_the_sequence_run_goes_from_the_first_to_the_eleventh():
    """01.02.03 til 11.12.13, og saa ikke mere: der er ingen 13. maaned."""
    step_one = [h for h in dp.sequences(2000) if h.month == h.day + 1]
    assert len(step_one) == 11
    assert (step_one[0].day, step_one[0].month, step_one[0].year) == (1, 2, 2003)
    assert (step_one[-1].day, step_one[-1].month, step_one[-1].year) == (11, 12, 2013)


@pytest.mark.parametrize("century", dp.CENTURIES)
def test_a_sequence_day_climbs_by_the_same_step_twice(century):
    for hit in dp.sequences(century):
        step = hit.month - hit.day
        assert step in (1, 2, 3)
        assert hit.year % 100 - hit.month == step


# --- De oevrige familier -------------------------------------------------


def test_there_is_exactly_one_repdigit_day_a_century():
    for century in dp.CENTURIES:
        found = list(dp.repunits(century))
        assert len(found) == 1
        assert (found[0].day, found[0].month, found[0].year % 100) == (11, 11, 11)


def test_a_binary_day_uses_nothing_but_noughts_and_ones():
    for century in dp.CENTURIES:
        for hit in dp.binaries(century):
            assert set(f"{hit.day:02d}{hit.month:02d}{hit.year % 100:02d}") <= {"0", "1"}


@pytest.mark.parametrize("century", dp.CENTURIES)
def test_there_are_twelve_pythagorean_days_a_century_and_the_sum_holds(century):
    found = list(dp.pythagoreans(century))
    assert len(found) == 12
    for hit in found:
        root = hit.year % 100
        assert hit.day**2 + hit.month**2 == root**2


def test_the_classic_three_four_five_triangle_is_in_there_both_ways():
    days = {(h.month, h.day) for h in dp.pythagoreans(2000)}
    assert (3, 4) in days and (4, 3) in days


@pytest.mark.parametrize("century", dp.CENTURIES)
def test_there_are_nine_square_root_days_a_century(century):
    found = list(dp.square_roots(century))
    assert len(found) == 9
    for hit in found:
        assert hit.day == hit.month
        assert hit.day**2 == hit.year % 100


def test_the_fibonacci_dates_stop_where_the_months_do():
    found = list(dp.fibonaccis(2000))
    assert [(h.day, h.month, h.year % 100) for h in found] == [
        (1, 1, 2), (1, 2, 3), (2, 3, 5), (3, 5, 8), (5, 8, 13)
    ]


@pytest.mark.parametrize("century", dp.CENTURIES)
def test_a_product_day_multiplies_and_a_sum_day_adds(century):
    for hit in dp.products(century):
        assert hit.day * hit.month == hit.year % 100
    for hit in dp.sums(century):
        assert hit.day + hit.month == hit.year % 100


def test_the_last_sum_day_of_a_century_is_new_years_eve():
    """31 + 12 = 43, og derefter kan summen ikke naa aarstallet mere."""
    last = max(dp.sums(2000), key=lambda hit: (hit.year, hit.month, hit.day))
    assert (last.day, last.month, last.year) == (31, 12, 2043)


def test_a_date_may_belong_to_more_than_one_family():
    """05.05.25 er baade en kvadratrodsdag og en produktdag. Begge er sande."""
    groups = {
        m.group for m in dp.pattern_milestones() if m.when == "2025-05-05"
    }
    assert {"sqrtday", "product"} <= groups


# -------------------------------------------------------------------------
# Jordens aar
# -------------------------------------------------------------------------


def test_the_year_starts_with_the_earth_and_ends_with_now():
    assert gy.day_of_year(EARTH_AGE_MA) == 1
    assert gy.day_of_year(0.0) == gy.DAYS_IN_YEAR


def test_the_dinosaurs_die_the_day_after_christmas():
    """Kridt/Palaeogen-graensen: 66 af 4.540 mio. aar er de sidste 5,3 dage."""
    point = next(p for p in gy.year_points() if p.event.key == "paleogene")
    assert point.day_of_year == 360
    assert (point.month, point.day) == (12, 26)
    assert point.when == "12-26"


def test_civilisation_is_the_last_minute_and_a_half_of_the_year():
    milestone = {m.key: m for m in gy.geoyear_milestones()}[f"{gy.PREFIX}geoyear_holocene"]
    assert "81 sekunder" in milestone.why_da
    assert "81 seconds" in milestone.why_en


def test_the_year_runs_in_the_same_order_as_the_history():
    points = gy.year_points()
    days = [p.day_of_year for p in points]
    assert days == sorted(days)
    assert all(1 <= day <= gy.DAYS_IN_YEAR for day in days)


def test_every_boundary_in_geology_gets_a_day_in_the_year():
    assert {p.event.key for p in gy.year_points()} == set(GEO_BY_KEY)


def test_the_two_earth_scales_are_not_the_same_thing():
    """``geo`` klemmer Jordens historie ned i DIT liv; ``geoyear`` i kalenderaaret.

    Den foerste flytter sig, naar levetiden gaar op; den anden kan ikke.
    """
    geo = [m for m in MILESTONES if m.group == "geo"]
    year = gy.geoyear_milestones()
    assert geo and year
    assert {m.unit for m in geo} == {"geo_ma"}
    assert {m.unit for m in year} == {"annual"}

    short = profile_at(1980, lifespan_years=60.0)
    long = profile_at(1980, lifespan_years=120.0)
    boundary = next(m for m in geo if "paleogene" in m.key)
    assert milestone_instant(boundary, short, NOW) != milestone_instant(boundary, long, NOW)

    in_year = next(m for m in year if "paleogene" in m.key)
    assert milestone_instant(in_year, short, NOW) == milestone_instant(in_year, long, NOW)


# -------------------------------------------------------------------------
# Hele kataloget efter tilskuddet
# -------------------------------------------------------------------------


def test_the_catalogue_still_works_with_nothing_chosen():
    assert compute(profile_at(), keys=set(), lang="da", now=NOW) == []


def test_the_whole_catalogue_can_be_computed_in_both_languages():
    for lang in ("da", "en"):
        occasions = compute(profile_at(1980), lang=lang, now=NOW)
        assert len(occasions) > 1_000
        moments = [o.when_utc for o in occasions]
        assert moments == sorted(moments)


def test_a_one_off_unit_is_always_inside_the_life_it_belongs_to():
    profile = profile_at(1980)
    horizon = profile.birth_utc + timedelta(days=150 * 365.242190)
    for occasion in compute(profile, lang="da", now=NOW):
        if occasion.milestone.unit in ONE_OFF_UNITS:
            assert profile.birth_utc <= occasion.when_utc <= horizon


# -------------------------------------------------------------------------
# Skellet mellem de to slags pakker
# -------------------------------------------------------------------------
#
# Et gigasekund findes kun, fordi netop du blev foedt. Den 4. maj falder
# samme dag for alle. Pakkerne staar i hver sin hylde efter det, og hylden
# udledes af enhederne — ikke af en liste, nogen skal holde ved lige. Derfor
# foerer testene her an paa, at udledningen holder.


def test_every_bundle_lands_on_exactly_one_shelf():
    for bundle in BUNDLES:
        assert bundle_scope(bundle) in SCOPES, bundle.key


@pytest.mark.parametrize("key", ["round", "nerdpack", "spacepack", "bodypack", "legends"])
def test_a_bundle_counted_from_birth_says_so(key):
    assert bundle_scope(BUNDLES_BY_KEY[key]) == BIRTH_SCOPE


@pytest.mark.parametrize(
    "key",
    ["popbundle", "fictionbundle", "scifibundle", "scidaybundle",
     "nerdhistbundle", "earthyearbundle", "patternbundle", "partybundle"],
)
def test_a_bundle_of_calendar_days_says_so(key):
    assert bundle_scope(BUNDLES_BY_KEY[key]) == CALENDAR_SCOPE


def test_the_classics_are_counted_from_birth():
    """Ingen festdag er fremhaevet, saa stjernerne er alle sammen tal fra foedslen."""
    assert bundle_scope(BUNDLES_BY_KEY["classics"]) == BIRTH_SCOPE
    assert not [m for m in celebration_milestones() if m.star]


def test_a_bundle_that_cuts_by_time_belongs_to_both():
    """"Alt inden for ti aar" tager fra hele kataloget og er ikke én slags."""
    assert bundle_scope(BUNDLES_BY_KEY["soon"]) == BOTH_SCOPES


def test_the_shelf_follows_the_units_and_not_a_list():
    """En opdigtet pakke med begge slags grupper skal lande paa "begge"."""
    mixed = Bundle(
        "blandet", "Blandet", "Mixed", "🔀", "", "", groups=("sec", "pop")
    )
    assert bundle_scope(mixed) == BOTH_SCOPES


def test_a_calendar_bundle_really_only_holds_calendar_days():
    """Hylden skal passe paa indholdet, ikke bare paa gruppenavnene."""
    catalogue = {m.key: m for m in all_milestones()}
    for bundle in BUNDLES:
        if bundle_scope(bundle) != CALENDAR_SCOPE:
            continue
        units = {
            catalogue[key].unit
            for key in bundle_keys(bundle, profile_at(), NOW)
        }
        assert units and units <= CALENDAR_DAY_UNITS, bundle.key


def test_a_birth_bundle_really_holds_nothing_from_the_calendar():
    catalogue = {m.key: m for m in all_milestones()}
    for bundle in BUNDLES:
        if bundle_scope(bundle) != BIRTH_SCOPE:
            continue
        units = {
            catalogue[key].unit
            for key in bundle_keys(bundle, profile_at(), NOW)
        }
        assert units and not units & CALENDAR_DAY_UNITS, bundle.key


def test_both_shelves_have_something_on_them():
    """En tom hylde ville tegne en overskrift uden knapper under."""
    for scope in (BIRTH_SCOPE, CALENDAR_SCOPE):
        assert [b for b in BUNDLES if bundle_scope(b) == scope]


@pytest.mark.parametrize("scope", SCOPES)
@pytest.mark.parametrize("lang", ["da", "en"])
def test_every_shelf_is_named_and_explained_in_both_languages(scope, lang):
    for key in (f"bundles_{scope}", f"bundles_{scope}_help"):
        assert t(key, lang) != key, f"{key} mangler i ordlisten"
