"""Test af levetidsberegneren.

Den vigtigste test her er ``test_the_curve_agrees_with_the_table``. Tavlerne
leverer baade ``lx`` og ``ex``, og vi bruger kun ``lx`` til at bygge kurven
med. At den kurve saa giver praecis den ``ex``, tavlen selv angiver, er et
uafhaengigt tjek af hele regnestykket — omregningen fra overlevende til
doedssandsynlighed, halen efter sidste alder og summeringen til sidst.

Koer dem med:
    python -m pytest -q
"""

from __future__ import annotations

import pytest

from utils import lifetable as lt
from utils.i18n import LANGUAGES

COUNTRIES = lt.load().countries
PAIRS = [(country, sex) for country in COUNTRIES for sex in lt.SEXES]


# -------------------------------------------------------------------------
# Datafilen
# -------------------------------------------------------------------------


def test_the_tables_are_there():
    catalogue = lt.load()
    assert catalogue.countries, "ingen dødelighedstavler indlæst"
    assert len(catalogue.countries) >= 20
    assert "DK" in catalogue.countries
    assert catalogue.default == "DK"
    assert catalogue.fetched


def test_denmark_comes_from_the_danish_statistics_office():
    """Det nationale tal er det rigtige for Danmark, og det naar laengere op."""
    table = lt.load().get("DK", "M")
    assert "Danmarks Statistik" in table.source
    assert table.last_age >= 99


@pytest.mark.parametrize("country, sex", PAIRS)
def test_every_table_is_a_table(country, sex):
    table = lt.load().get(country, sex)
    assert table is not None
    assert len(table.ages) == len(table.lx) == len(table.ex)
    assert table.ages[0] == 0
    assert table.ages == tuple(range(table.ages[0], table.ages[-1] + 1))
    assert table.source and table.source_url and table.period


@pytest.mark.parametrize("country, sex", PAIRS)
def test_nobody_comes_back_to_life(country, sex):
    """``lx`` er de overlevende. Den kan kun falde."""
    table = lt.load().get(country, sex)
    assert table.lx[0] == pytest.approx(100_000, rel=0.01)
    for here, nxt in zip(table.lx, table.lx[1:]):
        assert nxt <= here
    assert table.lx[-1] < table.lx[0]


@pytest.mark.parametrize("country, sex", PAIRS)
def test_life_expectancy_falls_as_you_age(country, sex):
    """Restlevetiden bliver kortere — men alderen plus den bliver stoerre.

    Tallene er offentliggjort med én decimal, og i de smaa lande vipper de
    af og til et trin op igen, fordi afrundingen og det lille befolknings-
    grundlag stoejer. Derfor er kravet "falder", ikke "falder altid": over
    fem aar skal den vaere nede uanset hvad.
    """
    table = lt.load().get(country, sex)
    steady_ex = table.ex[: len(table.ex) - 10]
    for here, nxt in zip(steady_ex, table.ex[1:]):
        assert nxt <= here + 0.15
    # De sidste aldre undtages: i den aabne toppegruppe er tallene saa smaa,
    # at enkelte tavler lader restlevetiden stige igen. Se
    # test_a_table_that_wobbles_at_the_top_does_not_get_a_long_tail.
    steady = len(table.ex) - 10
    for here, later in zip(table.ex[:steady], table.ex[5:]):
        assert later < here
    assert all(value > 0 for value in table.ex)
    reached = [age + value for age, value in zip(table.ages, table.ex)]
    assert reached == sorted(reached)


def test_the_danish_numbers_are_the_ones_the_office_publishes():
    """Et fast holdepunkt: gaar det her i stykker, er datafilen skiftet ud."""
    catalogue = lt.load()
    assert catalogue.get("DK", "M").ex[0] == pytest.approx(80.25, abs=0.01)
    assert catalogue.get("DK", "F").ex[0] == pytest.approx(83.90, abs=0.01)


def test_women_outlive_men_everywhere_in_the_data():
    for country in COUNTRIES:
        men = lt.load().get(country, "M").ex[0]
        women = lt.load().get(country, "F").ex[0]
        assert women > men, country


# -------------------------------------------------------------------------
# Doedeligheden
# -------------------------------------------------------------------------


@pytest.mark.parametrize("country, sex", PAIRS)
def test_a_probability_is_a_probability(country, sex):
    qx = lt.mortality(country, sex)
    assert len(qx) == lt.MAX_AGE
    assert all(0.0 <= value <= 1.0 for value in qx)


def test_dying_gets_likelier_with_age():
    """Doedeligheden stiger med alderen — maalt over aartier, ikke aar.

    Fra aar til aar vipper den: ved de yngre aldre doer der saa faa, at et
    enkelt aar kan ligge under det foregaaende. Det er stoej i tallene, ikke
    i udregningen. Tendensen er der til gengæld uden undtagelse.
    """
    qx = lt.mortality("DK", "M")
    decades = [qx[age] for age in range(20, 100, 10)]
    assert decades == sorted(decades)
    assert qx[90] > qx[40] * 50


def test_the_tail_keeps_going_past_the_end_of_the_table():
    """Tavlen stopper ved 99. Kurven skal ikke stoppe samme sted."""
    table = lt.load().get("DK", "M")
    qx = lt.mortality("DK", "M")
    beyond = qx[table.last_age + 1 :]
    assert beyond
    assert all(0.2 < value < 1.0 for value in beyond)


# -------------------------------------------------------------------------
# Kurven
# -------------------------------------------------------------------------


@pytest.mark.parametrize("country, sex", PAIRS)
def test_the_curve_agrees_with_the_table(country, sex):
    """Kurven bygges kun af ``lx``. Den skal give tavlens egen ``ex`` igen.

    Det er det uafhaengige tjek: tavlens to kolonner er regnet ud hver for
    sig af statistikkontoret, og hvis vores vej fra den ene til den anden
    rammer, er omregningen rigtig — ogsaa halen efter sidste alder.
    """
    table = lt.load().get(country, sex)
    for age in (0, 1, 20, 40, 60, 80, table.last_age - 5):
        curve = lt.survival_curve(country, sex, age)
        assert lt.expectancy(curve) == pytest.approx(
            table.table_expectancy(age), abs=0.1
        ), f"{country}/{sex} ved {age}"


def test_a_curve_starts_whole_and_only_falls():
    curve = lt.survival_curve("DK", "F", 30)
    assert curve[0] == 1.0
    for here, nxt in zip(curve, curve[1:]):
        assert nxt <= here
    assert curve[-1] < 0.01


def test_an_unknown_country_gives_nothing_rather_than_a_crash():
    assert lt.survival_curve("ZZ", "M", 40) == ()
    assert lt.expectancy(()) == 0.0
    assert lt.age_at_quantile((), 40, 0.5) == 40.0
    assert lt.chance_of_reaching((), 40, 80) == 0.0


# --- Periode mod kohorte -------------------------------------------------


def test_expected_improvement_adds_years():
    for age in (0, 30, 60):
        period = lt.expectancy(lt.survival_curve("DK", "M", age))
        cohort = lt.expectancy(
            lt.survival_curve("DK", "M", age, improvement=lt.IMPROVEMENT)
        )
        assert cohort > period


def test_the_young_gain_most_from_improvement():
    """En fyrreaarig moeder foerst de hoeje aldre om mange aar. En nioghalvfems-
    aarig moeder dem i morgen, og saa naar bedringen ikke at virke."""
    def gain(age: int) -> float:
        period = lt.expectancy(lt.survival_curve("DK", "F", age))
        cohort = lt.expectancy(
            lt.survival_curve("DK", "F", age, improvement=lt.IMPROVEMENT)
        )
        return cohort - period

    assert gain(0) > gain(40) > gain(80) > gain(95) >= 0


def test_no_improvement_is_the_period_table():
    assert lt.survival_curve("DK", "M", 50, improvement=0.0) == lt.survival_curve(
        "DK", "M", 50
    )


# -------------------------------------------------------------------------
# Livsstilen
# -------------------------------------------------------------------------


def test_saying_nothing_changes_nothing():
    assert lt.combined_hazard({}) == pytest.approx(1.0)
    assert lt.combined_hazard(
        {factor.key: factor.default for factor in lt.FACTORS}
    ) == pytest.approx(1.0)


def test_every_factor_has_a_reference_level_that_counts_as_nothing():
    for factor in lt.FACTORS:
        assert factor.levels[0].key == "unknown"
        assert factor.levels[0].hazard == 1.0
        assert factor.source, factor.key
        assert len(factor.levels) >= 3


def test_every_level_is_named_in_both_languages():
    for factor in lt.FACTORS:
        for lang in LANGUAGES:
            assert factor.name(lang).strip(), factor.key
            for level in factor.levels:
                assert level.name(lang).strip(), f"{factor.key}/{level.key}"


def test_the_level_keys_are_unique_within_a_factor():
    for factor in lt.FACTORS:
        keys = [level.key for level in factor.levels]
        assert len(keys) == len(set(keys)), factor.key


def test_an_unknown_answer_falls_back_to_the_reference():
    smoking = lt.FACTORS_BY_KEY["smoking"]
    assert smoking.level("findes-ikke").hazard == 1.0


def test_smoking_shortens_and_exercise_lengthens():
    def years(choices: dict[str, str]) -> float:
        hazard = lt.combined_hazard(choices)
        return lt.expectancy(lt.survival_curve("DK", "M", 40, hazard=hazard))

    plain = years({})
    assert years({"smoking": "current"}) < plain
    assert years({"smoking": "never"}) == pytest.approx(plain)
    assert years({"activity": "guideline"}) > plain
    assert years({"bmi": "obese3"}) < plain
    assert years({"alcohol": "very_high"}) < plain


def test_quitting_early_beats_quitting_late():
    smoking = lt.FACTORS_BY_KEY["smoking"]
    assert (
        smoking.level("never").hazard
        < smoking.level("quit_early").hazard
        < smoking.level("quit_late").hazard
        < smoking.level("current").hazard
    )


def test_the_damped_hazard_lies_between_no_effect_and_the_whole_effect():
    for hazard in (0.5, 0.8, 1.2, 2.8):
        soft = lt.damped(hazard)
        assert min(1.0, hazard) <= soft <= max(1.0, hazard)
    assert lt.damped(1.0) == pytest.approx(1.0)


# -------------------------------------------------------------------------
# Fordelingen
# -------------------------------------------------------------------------


def test_the_quantiles_come_in_order():
    curve = lt.survival_curve("DK", "M", 46)
    ages = [lt.age_at_quantile(curve, 46, share) for share in (0.1, 0.25, 0.5, 0.75, 0.9)]
    assert ages == sorted(ages)
    assert all(age > 46 for age in ages)


def test_the_median_is_where_half_are_left():
    curve = lt.survival_curve("DK", "F", 30)
    median = lt.age_at_quantile(curve, 30, 0.5)
    assert lt.chance_of_reaching(curve, 30, int(median)) >= 0.5
    assert lt.chance_of_reaching(curve, 30, int(median) + 1) <= 0.5


def test_the_chance_of_reaching_an_age_only_falls():
    curve = lt.survival_curve("DK", "M", 40)
    chances = [lt.chance_of_reaching(curve, 40, age) for age in range(40, 115)]
    assert chances[0] == 1.0
    for here, nxt in zip(chances, chances[1:]):
        assert nxt <= here
    assert chances[-1] == pytest.approx(0.0, abs=0.001)


def test_you_have_already_reached_your_own_age():
    curve = lt.survival_curve("DK", "F", 70)
    assert lt.chance_of_reaching(curve, 70, 70) == 1.0
    assert lt.chance_of_reaching(curve, 70, 60) == 1.0


def test_half_of_danish_men_of_forty_six_reach_their_eighties():
    """Et holdepunkt i virkeligheden, saa en skaev udregning ikke gaar ubemaerket."""
    curve = lt.survival_curve("DK", "M", 46)
    assert 80 <= lt.age_at_quantile(curve, 46, 0.5) <= 88
    assert 0.15 <= lt.chance_of_reaching(curve, 46, 90) <= 0.35


def test_the_known_wobble_at_the_top_of_the_slovak_table():
    """Eurostats slovakiske maend: restlevetiden STIGER fra 90 til 95 aar.

    Ingen befolkning goer det — det er den aabne 95+-gruppe og de smaa tal
    deroppe, der stoejer. Halen tager tavlens eget tal alligevel, fordi
    ethvert forsoeg paa at klippe den slags ned ogsaa ramte de tavler, der
    var i orden. Testen staar her for at holde afvigelsen synlig: gaar den i
    stykker, har Eurostat rettet tallene, og saa kan denne test ryge.

    Det rammer kun de allerhoejeste aldre i de mindste lande.
    """
    table = lt.load().get("SK", "M")
    assert table.ex[-1] > table.ex[-6]

    # Resten af tavlen er upaavirket: op til firs er den helt almindelig.
    assert lt.expectancy(lt.survival_curve("SK", "M", 80)) == pytest.approx(
        table.table_expectancy(80), abs=0.1
    )


def test_every_other_table_falls_all_the_way_to_the_top():
    """Kun Slovakiet vipper. Kommer der flere, skal det ses her."""
    wobbly = [
        f"{country}/{sex}"
        for country, sex in PAIRS
        if lt.load().get(country, sex).ex[-1] > lt.load().get(country, sex).ex[-6]
    ]
    assert wobbly == ["SK/M"]
