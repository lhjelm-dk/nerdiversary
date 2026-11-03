"""Test af datoregningen — det eneste sted i appen, hvor en fejl er usynlig.

Koer dem med:
    python -m pytest -q
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from zoneinfo import ZoneInfo

import pytest

from utils import formatting as fmt
from utils.catalog import GROUPS_BY_KEY, MILESTONES
from dateutil.relativedelta import relativedelta

from utils.engine import (
    UNIX_EPOCH,
    Profile,
    all_milestones,
    build_label,
    compute,
    explanation,
    fmt_big,
    milestone_instant,
)
from utils.exporters import build_google_csv, build_ics, google_calendar_link
from utils.geology import GEO_BY_KEY
from utils.leapseconds import (
    LEAP_SECOND_DATES,
    TOTAL_LEAP_SECONDS,
    leap_seconds_between,
)
from utils.units import PAIR_UNITS, SECONDS_PER_UNIT, TROPICAL_YEAR_DAYS

CPH = ZoneInfo("Europe/Copenhagen")
UTC = timezone.utc


def profile_at(year, month, day, hour=12, minute=0, second=0, tz=CPH, **kwargs):
    return Profile(
        birth_local=datetime(year, month, day, hour, minute, second, tzinfo=tz),
        **kwargs,
    )


def instant(key: str, profile: Profile) -> datetime:
    milestone = {m.key: m for m in all_milestones()}[key]
    moment = milestone_instant(milestone, profile)
    assert moment is not None, f"{key} kunne ikke regnes ud"
    return moment


# -------------------------------------------------------------------------
# Eksakte sekundbaserede maerkedage
# -------------------------------------------------------------------------


def test_gigasecond_is_exactly_one_billion_seconds():
    profile = profile_at(2000, 1, 1, 12, 0, 0, tz=UTC)
    moment = instant("sec_1e9", profile)
    assert (moment - profile.birth_utc).total_seconds() == 1_000_000_000


def test_gigasecond_lands_on_the_expected_instant():
    """11.574 doegn + 1 t 46 m 40 s efter midnat 1. januar 2000."""
    profile = profile_at(2000, 1, 1, 0, 0, 0, tz=UTC)
    assert instant("sec_1e9", profile) == datetime(2031, 9, 9, 1, 46, 40, tzinfo=UTC)


def test_billion_seconds_decomposition():
    """Et gigasekund er 11.574 doegn og 6400 sekunder — ikke et rundt doegn."""
    assert 11_574 * 86_400 + 6_400 == 1_000_000_000
    assert 6_400 == 1 * 3600 + 46 * 60 + 40


def test_day_milestones_keep_the_birth_time_in_utc():
    profile = profile_at(1980, 4, 12, 9, 41, 33, tz=UTC)
    moment = instant("day_10000", profile)
    assert moment.time() == profile.birth_utc.time()
    assert (moment - profile.birth_utc).days == 10_000


def test_week_and_day_units_agree():
    profile = profile_at(1990, 6, 15, 8, 0, 0, tz=UTC)
    assert (instant("week_1000", profile) - profile.birth_utc).days == 7_000


# -------------------------------------------------------------------------
# Kalenderregning
# -------------------------------------------------------------------------


def test_600_months_is_exactly_50_years():
    profile = profile_at(1975, 3, 20, 14, 30, 0)
    moment = instant("month_600", profile).astimezone(CPH)
    assert (moment.year, moment.month, moment.day) == (2025, 3, 20)
    assert (moment.hour, moment.minute) == (14, 30)


def test_calendar_months_clamp_to_the_last_valid_day():
    """31. januar + 1 maaned findes ikke, saa den rykkes til den 29. februar."""
    from dateutil.relativedelta import relativedelta

    start = datetime(2000, 1, 31, 10, 0)
    assert (start + relativedelta(months=1)).day == 29  # 2000 var skudaar
    assert (datetime(2001, 1, 31, 10, 0) + relativedelta(months=1)).day == 28


def test_leap_day_birth_is_handled():
    profile = profile_at(2000, 2, 29, 10, 0, 0)
    moment = instant("month_100", profile)
    assert moment is not None


# -------------------------------------------------------------------------
# Tidszoner og sommertid
# -------------------------------------------------------------------------


def test_dst_shifts_the_wall_clock_but_not_the_instant():
    """Foedt om vinteren, maerkedag om sommeren: uret viser en time senere."""
    profile = profile_at(2000, 1, 1, 4, 0, 0, tz=CPH)
    milestone = next(m for m in MILESTONES if m.key == "day_100")  # 10. april
    moment = milestone_instant(milestone, profile)
    local = moment.astimezone(CPH)
    assert (moment - profile.birth_utc).total_seconds() == 100 * 86_400
    assert local.hour == 5  # sommertid har flyttet vaegurets visning


def test_calendar_years_keep_the_wall_clock_across_dst():
    """25 kalenderaar skal ramme samme klokkeslaet, uanset sommertid."""
    profile = profile_at(2000, 7, 1, 9, 30, 0, tz=CPH)
    moment = instant("s73_year_73", profile).astimezone(CPH)
    assert (moment.hour, moment.minute) == (9, 30)


# -------------------------------------------------------------------------
# Absolutte tidspunkter (unix_abs)
#
# Kataloget har ikke laengere maerkedage af den slags, men motoren kan stadig
# regne dem ud. Testene bygger derfor deres egen Milestone, saa evnen ikke
# raadner, hvis nogen vil have Unix-tiden tilbage.
# -------------------------------------------------------------------------


def _absolute(stamp: int) -> "object":
    from utils.catalog import Milestone

    return Milestone(key="t", group="sec", unit="unix_abs", amount=stamp)


def test_unix_two_billion_is_a_known_instant():
    profile = profile_at(1980, 1, 1, tz=UTC)
    moment = milestone_instant(_absolute(2_000_000_000), profile)
    assert moment == datetime(2033, 5, 18, 3, 33, 20, tzinfo=UTC)


def test_y2k38_is_the_documented_moment():
    profile = profile_at(1980, 1, 1, tz=UTC)
    moment = milestone_instant(_absolute(2_147_483_647), profile)
    assert moment == datetime(2038, 1, 19, 3, 14, 7, tzinfo=UTC)
    assert 2_147_483_647 == 2**31 - 1


def test_absolute_instants_ignore_the_birth_date():
    """Et absolut tidsstempel er det samme for alle."""
    early = profile_at(1950, 1, 1, tz=UTC)
    late = profile_at(2010, 1, 1, tz=UTC)
    stamp = _absolute(2_000_000_000)
    assert milestone_instant(stamp, early) == milestone_instant(stamp, late)


def test_unix_time_is_gone_from_the_catalogue():
    assert not [m for m in all_milestones() if m.unit == "unix_abs"]
    assert "unix" not in GROUPS_BY_KEY


# -------------------------------------------------------------------------
# Skoen og satser
# -------------------------------------------------------------------------


def test_heartbeat_milestone_follows_the_rate():
    from utils.engine import Rates

    slow = Profile(
        birth_local=datetime(2000, 1, 1, tzinfo=UTC), rates=Rates(bpm=60)
    )
    fast = Profile(
        birth_local=datetime(2000, 1, 1, tzinfo=UTC), rates=Rates(bpm=120)
    )
    assert instant("b_hb_1e9", fast) < instant("b_hb_1e9", slow)
    # 1e9 slag ved 60 i minuttet er praecis 1e9 sekunder.
    assert (instant("b_hb_1e9", slow) - slow.birth_utc).total_seconds() == 1e9


def test_lifespan_scales_the_geological_timeline():
    short = profile_at(2000, 1, 1, tz=UTC, lifespan_years=80)
    long = profile_at(2000, 1, 1, tz=UTC, lifespan_years=120)
    assert instant("geo_cambrian", short) < instant("geo_cambrian", long)


def test_holocene_lands_just_before_the_assumed_end():
    """Civilisationen fylder de sidste par timer af et 100-aars liv."""
    profile = profile_at(2000, 1, 1, tz=UTC, lifespan_years=100)
    age = GEO_BY_KEY["holocene"].age_at(100)
    assert 99.99 < age < 100.0
    hours_left = (100 - age) * 365.242190 * 24
    assert 1 < hours_left < 4


def test_percent_of_life_is_half_the_lifespan():
    profile = profile_at(2000, 1, 1, tz=UTC, lifespan_years=100)
    years = (instant("p_50", profile) - profile.birth_utc).days / 365.242190
    assert abs(years - 50) < 0.01


# -------------------------------------------------------------------------
# Eksotiske enheder
# -------------------------------------------------------------------------


def test_caesium_gigasecond_matches_the_plain_gigasecond():
    """9.192.631.770 x 10^9 perioder er pr. definition ét gigasekund."""
    profile = profile_at(2000, 1, 1, tz=UTC)
    difference = abs(
        (instant("x_cs_giga", profile) - instant("sec_1e9", profile)).total_seconds()
    )
    assert difference < 1.0


def test_jiffy_is_light_across_one_centimetre():
    assert abs(SECONDS_PER_UNIT["jiffy"] - 3.3356409519815204e-11) < 1e-25


# -------------------------------------------------------------------------
# Skudsekunder
# -------------------------------------------------------------------------


def test_leap_second_table_is_complete():
    assert TOTAL_LEAP_SECONDS == 27
    assert LEAP_SECOND_DATES[-1].isoformat() == "2016-12-31"
    assert list(LEAP_SECOND_DATES) == sorted(LEAP_SECOND_DATES)


def test_leap_seconds_since_a_1973_birth():
    born = datetime(1973, 6, 1, tzinfo=UTC)
    now = datetime(2026, 11, 2, tzinfo=UTC)
    assert leap_seconds_between(born, now) == 25


def test_no_leap_seconds_after_2016():
    start = datetime(2017, 1, 1, tzinfo=UTC)
    assert leap_seconds_between(start, datetime(2026, 11, 2, tzinfo=UTC)) == 0


# -------------------------------------------------------------------------
# Sheldons 73
# -------------------------------------------------------------------------


def _nth_prime(n: int) -> int:
    found, candidate = 0, 1
    while found < n:
        candidate += 1
        if all(candidate % d for d in range(2, int(candidate**0.5) + 1)):
            found += 1
    return candidate


def test_73_satisfies_the_product_property():
    assert _nth_prime(21) == 73
    assert 7 * 3 == 21


def test_73_satisfies_the_mirror_property():
    assert _nth_prime(12) == 37
    assert int(str(73)[::-1]) == 37
    assert int(str(21)[::-1]) == 12


def test_73_is_a_binary_palindrome():
    bits = bin(73)[2:]
    assert bits == "1001001"
    assert bits == bits[::-1]


# -------------------------------------------------------------------------
# Katalogets integritet
# -------------------------------------------------------------------------


def test_every_key_is_unique():
    keys = [m.key for m in all_milestones()]
    assert len(keys) == len(set(keys))


def test_every_group_reference_exists():
    for milestone in all_milestones():
        assert milestone.group in GROUPS_BY_KEY, milestone.key


def test_every_milestone_resolves_to_an_instant():
    """Alt undtagen par-maerkedagene skal kunne regnes ud af én foedselsdato."""
    profile = profile_at(1980, 4, 12, 9, 41, 33)
    for milestone in all_milestones():
        if milestone.unit in PAIR_UNITS:
            continue
        assert milestone_instant(milestone, profile) is not None, milestone.key


def test_pair_milestones_need_a_second_birth():
    profile = profile_at(1980, 4, 12, 9, 41, 33)
    for milestone in all_milestones():
        if milestone.unit in PAIR_UNITS:
            assert milestone_instant(milestone, profile) is None, milestone.key
    assert not [o for o in compute(profile) if o.milestone.group == "pair"]


def test_nothing_beyond_the_age_limit_is_returned():
    profile = profile_at(1980, 4, 12)
    occasions = compute(profile, max_age_years=100)
    for occasion in occasions:
        assert occasion.age_years(profile) <= 100.01, occasion.label


def test_results_are_sorted():
    profile = profile_at(1968, 12, 2, 4, 0, 0)
    occasions = compute(profile)
    assert occasions == sorted(occasions, key=lambda o: o.when_utc)
    assert len(occasions) > 300


# -------------------------------------------------------------------------
# Formatering
# -------------------------------------------------------------------------


def test_danish_and_english_number_formats_differ():
    assert fmt.fmt_int(1_234_567, "da") == "1.234.567"
    assert fmt.fmt_int(1_234_567, "en") == "1,234,567"
    assert fmt.fmt_num(1234.5, "da", 2) == "1.234,50"
    assert fmt.fmt_num(1234.5, "en", 2) == "1,234.50"


def test_dates_always_carry_the_month_in_words():
    moment = datetime(1980, 4, 12, 9, 41, 33)
    assert fmt.fmt_date_numeric(moment) == "12.04.1980"
    assert fmt.fmt_date_text(moment, "da") == "12. apr 1980"
    assert fmt.fmt_date_text(moment, "en") == "12 Apr 1980"
    assert "12.04.1980" in fmt.fmt_date_both(moment, "da")
    assert "12. apr 1980" in fmt.fmt_date_both(moment, "da")


def test_danish_clock_uses_dots():
    moment = datetime(1980, 4, 12, 9, 41, 33)
    assert fmt.fmt_clock(moment, "da") == "09.41.33"
    assert fmt.fmt_clock(moment, "en") == "09:41:33"


def test_big_numbers_use_powers_of_ten():
    assert fmt_big(1e18, "da") == "10¹⁸"
    assert fmt_big(1.337e20, "da") == "1,337 × 10²⁰"
    assert fmt_big(4e19, "da") == "4 × 10¹⁹"
    assert fmt_big(1000, "da") == "1.000"


# -------------------------------------------------------------------------
# Eksport
# -------------------------------------------------------------------------


@pytest.fixture
def sample():
    profile = profile_at(1980, 4, 12, 9, 41, 33, name="Lars")
    occasions = compute(profile, keys={"sec_1e9", "day_10000", "moon_500"}, lang="da")
    return profile, occasions


def test_ics_structure(sample):
    profile, occasions = sample
    text = build_ics(occasions, profile, lang="da")
    assert text.startswith("BEGIN:VCALENDAR\r\n")
    assert text.rstrip().endswith("END:VCALENDAR")
    assert text.count("BEGIN:VEVENT") == len(occasions)
    assert text.count("END:VEVENT") == len(occasions)
    assert text.count("BEGIN:VALARM") == 2 * len(occasions)


def test_ics_lines_respect_the_75_octet_fold(sample):
    profile, occasions = sample
    for line in build_ics(occasions, profile).split("\r\n"):
        assert len(line.encode("utf-8")) <= 75, line


def test_ics_folded_lines_decode_cleanly(sample):
    """Foldningen maa ikke dele et UTF-8-tegn midt over."""
    profile, occasions = sample
    text = build_ics(occasions, profile, lang="da")
    assert "æ" in text or "ø" in text or "å" in text
    text.encode("utf-8").decode("utf-8")


def test_ics_escapes_special_characters(sample):
    profile, occasions = sample
    text = build_ics(occasions, profile, lang="da")
    for line in text.split("\r\n"):
        if line.startswith("DESCRIPTION:") or line.startswith("SUMMARY:"):
            body = line.split(":", 1)[1]
            # Et ikke-escapet komma ville dele feltet i to.
            assert ",," not in body


def test_ics_uids_are_stable(sample):
    profile, occasions = sample
    first = build_ics(occasions, profile)
    second = build_ics(occasions, profile)
    uids = lambda text: [l for l in text.split("\r\n") if l.startswith("UID:")]
    assert uids(first) == uids(second)
    assert len(set(uids(first))) == len(occasions)


def test_different_births_get_different_uids(sample):
    profile, occasions = sample
    other = profile_at(1990, 4, 12, 9, 41, 33, name="Lars")
    other_occasions = compute(other, keys={"sec_1e9", "day_10000", "moon_500"})
    uids = lambda text: {l for l in text.split("\r\n") if l.startswith("UID:")}
    assert not uids(build_ics(occasions, profile)) & uids(
        build_ics(other_occasions, other)
    )


def test_all_day_events_use_date_values(sample):
    profile, occasions = sample
    text = build_ics(occasions, profile, all_day=True)
    assert "DTSTART;VALUE=DATE:" in text
    assert "DTSTART:" not in text.replace("DTSTART;VALUE=DATE:", "")


def test_google_csv_has_the_expected_shape(sample):
    profile, occasions = sample
    rows = build_google_csv(occasions, profile).strip().split("\r\n")
    assert rows[0].startswith("Subject,Start Date,Start Time")
    assert len(rows) == len(occasions) + 1


def test_google_link_carries_the_instant(sample):
    profile, occasions = sample
    link = google_calendar_link(occasions[0], profile)
    assert link.startswith("https://calendar.google.com/calendar/render?")
    assert "action=TEMPLATE" in link
    assert "dates=" in link


# -------------------------------------------------------------------------
# Faerdigpakkede udvaelgelser
# -------------------------------------------------------------------------


def test_every_bundle_selects_something():
    from utils.catalog import BUNDLES
    from utils.engine import bundle_keys

    profile = profile_at(1980, 4, 12, 9, 41, 33)
    now = datetime(2026, 11, 2, tzinfo=UTC)
    for bundle in BUNDLES:
        assert bundle_keys(bundle, profile, now), bundle.key


def test_classics_bundle_is_exactly_the_starred_milestones():
    from utils.catalog import BUNDLES_BY_KEY
    from utils.engine import bundle_keys

    profile = profile_at(1980, 4, 12)
    chosen = bundle_keys(
        BUNDLES_BY_KEY["classics"], profile, datetime(2026, 11, 2, tzinfo=UTC)
    )
    assert chosen == {m.key for m in all_milestones() if m.star}
    assert 20 < len(chosen) < 60


def test_group_bundles_cover_exactly_their_groups():
    from utils.catalog import BUNDLES_BY_KEY
    from utils.engine import bundle_keys

    profile = profile_at(1980, 4, 12)
    now = datetime(2026, 11, 2, tzinfo=UTC)
    bundle = BUNDLES_BY_KEY["spacepack"]
    chosen = bundle_keys(bundle, profile, now)
    groups = {m.group for m in all_milestones() if m.key in chosen}
    assert groups == set(bundle.groups)


def test_soon_bundle_only_holds_the_next_ten_years():
    from utils.catalog import BUNDLES_BY_KEY
    from utils.engine import bundle_keys, milestone_instant

    profile = profile_at(1980, 4, 12, 9, 41, 33)
    now = datetime(2026, 11, 2, tzinfo=UTC)
    chosen = bundle_keys(BUNDLES_BY_KEY["soon"], profile, now)
    lookup = {m.key: m for m in all_milestones()}
    for key in chosen:
        moment = milestone_instant(lookup[key], profile)
        assert now <= moment
        assert (moment - now).days <= 10 * 366


def test_legends_bundle_is_only_legends():
    from utils.catalog import BUNDLES_BY_KEY
    from utils.engine import bundle_keys

    chosen = bundle_keys(
        BUNDLES_BY_KEY["legends"], profile_at(1980, 4, 12), datetime(2026, 11, 2, tzinfo=UTC)
    )
    assert len(chosen) == 33
    assert all(key.startswith("legend_") for key in chosen)


# -------------------------------------------------------------------------
# Aldersstigen i det levende panel
# -------------------------------------------------------------------------


def test_si_units_are_plain_division():
    from utils.engine import age_days, age_hours, age_seconds

    profile = profile_at(2018, 6, 3, 7, 10, 0, tz=UTC)
    now = profile.birth_utc + timedelta(seconds=1_000_000)
    assert age_seconds(profile, now) == 1_000_000
    assert age_hours(profile, now) == pytest.approx(1_000_000 / 3600)
    assert age_days(profile, now) == pytest.approx(1_000_000 / 86_400)


def test_age_years_is_exact_on_a_birthday():
    """Fylder man aar i dag, skal taelleren staa paa praecis N,00."""
    from utils.engine import age_years

    profile = profile_at(2018, 6, 3, 7, 10, 0)
    birthday = datetime(2026, 6, 3, 7, 10, 0, tzinfo=CPH)
    assert age_years(profile, birthday) == pytest.approx(8.0, abs=1e-9)


def test_age_months_matches_the_month_milestone_exactly():
    """Naar "100 maaneder" indtraeffer, skal maanedstaelleren staa paa 100,00.

    Det er hele grunden til, at taelleren bruger kalenderregning og ikke en
    gennemsnitsmaaned paa 30,44 doegn.
    """
    from utils.engine import age_months

    profile = profile_at(2018, 6, 3, 7, 10, 0)
    milestone = next(m for m in all_milestones() if m.key == "month_100")
    moment = milestone_instant(milestone, profile)
    assert age_months(profile, moment) == pytest.approx(100.0, abs=1e-9)


def test_average_month_would_have_been_wrong():
    """Dokumenterer hvorfor: gennemsnitsmaaneder rammer flere doegn ved siden af."""
    profile = profile_at(2018, 6, 3, 7, 10, 0)
    milestone = next(m for m in all_milestones() if m.key == "month_100")
    moment = milestone_instant(milestone, profile)
    elapsed_days = (moment - profile.birth_utc).total_seconds() / 86_400
    average_months = elapsed_days / 30.436875
    assert abs(average_months - 100.0) > 0.01


def test_calendar_fractions_stay_in_range():
    from utils.engine import age_months, age_years

    profile = profile_at(2018, 6, 3, 7, 10, 0)
    moment = profile.birth_local
    for _ in range(40):
        moment = moment + timedelta(days=37, hours=5)
        months, years = age_months(profile, moment), age_years(profile, moment)
        assert months >= 0 and years >= 0
        assert 0 <= months - int(months) < 1
        assert 0 <= years - int(years) < 1


def test_leap_day_birth_never_goes_negative():
    """29. februar er det sted, hvor klampning og relativedelta kan blive uenige."""
    from utils.engine import age_months, age_years

    profile = profile_at(2000, 2, 29, 12, 0, 0)
    moment = profile.birth_local
    for _ in range(60):
        moment = moment + timedelta(days=29, hours=1)
        assert age_months(profile, moment) >= 0
        assert age_years(profile, moment) >= 0


def test_months_and_years_agree_at_whole_years():
    from utils.engine import age_months, age_years

    profile = profile_at(2018, 6, 3, 7, 10, 0)
    birthday = datetime(2030, 6, 3, 7, 10, 0, tzinfo=CPH)
    assert age_years(profile, birthday) == pytest.approx(12.0, abs=1e-9)
    assert age_months(profile, birthday) == pytest.approx(144.0, abs=1e-9)


def test_decimal_formatting_does_not_lose_the_carry():
    """Den gamle haandrullede formatering viste 100,97 som "100,0"."""
    assert fmt.fmt_num(100.97, "da", 1) == "101,0"
    assert fmt.fmt_num(100.94, "da", 1) == "100,9"
    assert fmt.fmt_num(3074.0449, "da", 2) == "3.074,04"
    assert fmt.fmt_num(3074.0449, "en", 2) == "3,074.04"


# -------------------------------------------------------------------------
# Forklaringer
# -------------------------------------------------------------------------


def test_every_milestone_has_an_explanation_except_the_silent_ones():
    from utils.engine import explanation

    for lang in ("da", "en"):
        empty = [m.key for m in all_milestones() if not explanation(m, lang)]
        assert all(m.startswith("s73_5318008") for m in empty), empty
        assert len(empty) == 3


def test_silent_milestones_never_get_a_generated_note():
    from utils.engine import explanation, generated_note

    silent = [m for m in all_milestones() if m.silent]
    assert len(silent) == 3
    for milestone in silent:
        assert explanation(milestone, "da") == ""
        # Den automatiske ville have haft noget at sige, hvis den fik lov.
        assert generated_note(milestone, "da")


def test_generated_note_spots_repdigits_and_palindromes():
    from utils.engine import generated_note

    repdigit = next(m for m in all_milestones() if m.key == "r_day_2222")
    palindrome = next(m for m in all_milestones() if m.key == "r_day_10001")
    assert generated_note(repdigit, "da").startswith("Alle cifre er ens.")
    assert generated_note(palindrome, "da").startswith("En palindrom")
    assert generated_note(repdigit, "en").startswith("Every digit is the same.")


def test_generated_note_never_says_zero_years():
    from utils.engine import explanation

    for lang in ("da", "en"):
        for milestone in all_milestones():
            note = explanation(milestone, lang)
            assert "0,0 år" not in note, milestone.key
            assert "0.0 years" not in note, milestone.key


def test_year_milestones_do_not_restate_their_own_years():
    """"11,11 år svarer til ... eller 11,1 år" er ikke en forklaring."""
    from utils.engine import generated_note

    milestone = next(m for m in all_milestones() if m.key == "r_year_1111")
    note = generated_note(milestone, "da")
    assert "døgn" in note
    assert note.count("år") == 1


def test_month_conversion_is_exact():
    from utils.engine import generated_note

    milestone = next(m for m in all_milestones() if m.key == "month_500")
    assert "41 år og 8 måneder" in generated_note(milestone, "da")
    assert "41 years and 8 months" in generated_note(milestone, "en")


# -------------------------------------------------------------------------
# Jer to
# -------------------------------------------------------------------------


def pair_profile(**kwargs):
    """Lars 09.10.1973 02.12.00 og Emma 03.06.2018 07.10.00."""
    return profile_at(
        1973, 10, 9, 2, 12, 0,
        partner_birth=datetime(2018, 6, 3, 7, 10, 0, tzinfo=CPH),
        partner_name="Emma",
        **kwargs,
    )


def milestone(key):
    return next(m for m in all_milestones() if m.key == key)


@pytest.mark.parametrize("key,ratio", [
    ("pair_ratio_10", 10.0),
    ("pair_ratio_5", 5.0),
    ("pair_ratio_4", 4.0),
    ("pair_ratio_3", 3.0),
    ("pair_ratio_2", 2.0),
    ("pair_ratio_1_5", 1.5),
])
def test_ratio_milestones_hit_the_ratio_exactly(key, ratio):
    profile = pair_profile()
    when = milestone_instant(milestone(key), profile)
    older = profile.birth_utc
    younger = profile.partner_utc
    assert (when - older).total_seconds() / (when - younger).total_seconds() == (
        pytest.approx(ratio, abs=1e-9)
    )


def test_twice_as_old_is_the_same_second_as_reaching_the_age_gap():
    """Forklaringen paastaar det; her er beviset.

    Den yngste naar aldersforskellen i samme sekund, som den aeldste er
    dobbelt saa gammel. Forskellen skal regnes paa UTC-vaerdierne: to aware
    datetimes med SAMME tzinfo trakkes fra hinanden paa vaeguret, og det
    giver en times fejl hen over et sommertidsskift.
    """
    profile = pair_profile()
    older, younger = profile.birth_utc, profile.partner_utc
    when = milestone_instant(milestone("pair_ratio_2"), profile)
    assert when == younger + (younger - older)


def test_ratio_milestones_do_not_exist_for_twins():
    same = datetime(1973, 10, 9, 2, 12, 0, tzinfo=CPH)
    profile = profile_at(1973, 10, 9, 2, 12, 0, partner_birth=same)
    assert profile.age_gap() == relativedelta()
    for key in ("pair_ratio_10", "pair_ratio_2", "pair_ratio_1_5"):
        assert milestone_instant(milestone(key), profile) is None, key
    # Summerne gaelder stadig: to jaevnaldrende naar dem paa det halve hver.
    when = milestone_instant(milestone("pair_days_10000"), profile)
    assert (when - profile.birth_utc).total_seconds() == pytest.approx(
        5_000 * 86_400, abs=1
    )


@pytest.mark.parametrize("key,total_seconds", [
    ("pair_days_20000", 20_000 * 86_400),
    ("pair_days_30000", 30_000 * 86_400),
    ("pair_sec_2e9", 2_000_000_000),
    ("pair_years_100", 100 * TROPICAL_YEAR_DAYS * 86_400),
    ("pair_years_150", 150 * TROPICAL_YEAR_DAYS * 86_400),
])
def test_combined_age_milestones_hit_the_sum_exactly(key, total_seconds):
    profile = pair_profile()
    when = milestone_instant(milestone(key), profile)
    combined = (when - profile.birth_utc).total_seconds() + (
        when - profile.partner_utc
    ).total_seconds()
    assert combined == pytest.approx(total_seconds, abs=1)


def test_a_sum_smaller_than_the_age_gap_never_happens():
    """To mennesker kan ikke have 10.000 doegn tilsammen, foer begge findes."""
    profile = profile_at(
        1930, 1, 1, partner_birth=datetime(2020, 1, 1, tzinfo=CPH)
    )
    assert milestone_instant(milestone("pair_days_10000"), profile) is None
    assert milestone_instant(milestone("pair_sec_1e9"), profile) is None
    # Den foerste, der er stoerre end de 90 aars forskel, findes til gengaeld.
    assert milestone_instant(milestone("pair_days_40000"), profile) is not None


def test_no_pair_milestone_lands_before_the_younger_is_born():
    profile = pair_profile()
    for item in all_milestones():
        if item.unit not in PAIR_UNITS:
            continue
        when = milestone_instant(item, profile)
        if when is not None:
            assert when >= profile.partner_utc, item.key


def test_pair_labels_turn_around_when_the_other_one_is_older():
    older = pair_profile()
    younger = profile_at(
        2018, 6, 3, 7, 10, 0,
        partner_birth=datetime(1973, 10, 9, 2, 12, 0, tzinfo=CPH),
        partner_name="Lars",
    )
    assert build_label(milestone("pair_ratio_2"), older, "da") == (
        "Dobbelt så gammel som Emma"
    )
    assert build_label(milestone("pair_ratio_2"), younger, "da") == (
        "Lars dobbelt så gammel som dig"
    )
    assert build_label(milestone("pair_ratio_2"), younger, "en") == (
        "Lars twice as old as you"
    )


def test_pair_labels_work_without_a_partner():
    """Afkrydsningslisten tegner etiketten, foer der er indtastet en anden."""
    solo = profile_at(1973, 10, 9)
    assert build_label(milestone("pair_ratio_2"), solo, "da") == (
        "Dobbelt så gammel som den anden"
    )
    assert build_label(milestone("pair_days_10000"), solo, "en") == (
        "10,000 days between you"
    )


def test_every_pair_milestone_is_explained():
    for item in all_milestones():
        if item.unit in PAIR_UNITS:
            assert explanation(item, "da"), item.key
            assert explanation(item, "en"), item.key


def test_age_gap_is_read_on_one_clock():
    """Aldersforskellen er en vaegursforskel, ikke en SI-forskel."""
    profile = pair_profile()
    gap = profile.age_gap()
    assert (gap.years, gap.months, gap.days) == (44, 7, 25)
    assert (gap.hours, gap.minutes) == (4, 58)
