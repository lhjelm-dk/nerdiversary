"""Test af tidslinjen — kaskadens regnestykker og etiketternes placering.

Koer dem med:
    python -m pytest -q
"""

from __future__ import annotations

import random
from datetime import datetime, timezone
from zoneinfo import ZoneInfo

import pytest
from dateutil.relativedelta import relativedelta

from utils import timeline as tl
from utils.catalog import GROUPS
from utils.engine import (
    BIRTH_SCOPE,
    Profile,
    all_milestones,
    compute,
    explanation,
    group_scope,
)

CPH = ZoneInfo("Europe/Copenhagen")

BIRTH = datetime(2018, 6, 3, 7, 10, 0, tzinfo=CPH)
END = BIRTH + relativedelta(years=150)
TOTAL = (END - BIRTH).total_seconds()
NOW = datetime(2026, 11, 2, 12, 0, tzinfo=timezone.utc).astimezone(CPH)

# Raekkens kanter i brugerkoordinater, som ``timeline`` tegner dem.
LEFT, RIGHT = 162.0, 1178.0


def entry_at(when: datetime, label: str = "x", star: bool = False) -> tl.Entry:
    return tl.Entry(when=when, label=label, tip=label, color="#333", star=star)


# -------------------------------------------------------------------------
# Raekkernes tidsrum
# -------------------------------------------------------------------------


@pytest.mark.parametrize("levels", [2, 3, 4, 5, 6])
@pytest.mark.parametrize(
    "target", [tl.WEEK, tl.MONTH, 3 * tl.MONTH, tl.YEAR, 10 * tl.YEAR, 50 * tl.YEAR]
)
def test_the_rows_run_from_the_whole_life_down_to_the_chosen_span(levels, target):
    spans = tl.cascade_spans(TOTAL, target, levels)
    assert spans[0] == pytest.approx(TOTAL)
    assert spans[-1] == pytest.approx(target)
    assert 2 <= len(spans) <= levels


@pytest.mark.parametrize("levels", [2, 3, 4, 5, 6])
def test_every_row_is_clearly_smaller_than_the_one_above(levels):
    """En raekke, der naesten er magen til den over, viser ikke noget nyt."""
    spans = tl.cascade_spans(TOTAL, tl.MONTH, levels)
    for larger, smaller in zip(spans, spans[1:]):
        assert smaller < larger * 0.95


def test_a_span_as_long_as_the_life_gives_a_single_row():
    assert tl.cascade_spans(TOTAL, TOTAL, 4) == [TOTAL]
    assert tl.cascade_spans(TOTAL, TOTAL * 3, 4) == [TOTAL]


def test_the_middle_rows_are_rounded_to_something_readable():
    """Mellemraekkerne skal staa paa "10 aar", ikke paa "11,4 aar"."""
    spans = tl.cascade_spans(TOTAL, tl.YEAR, 4)
    for span in spans[1:-1]:
        count, unit = tl.describe_span(span)
        size = {"year": tl.YEAR, "month": tl.MONTH, "week": tl.WEEK, "day": tl.DAY}[unit]
        assert span == pytest.approx(count * size)


# -------------------------------------------------------------------------
# Vinduerne
# -------------------------------------------------------------------------


@pytest.mark.parametrize("focus_year", [2018, 2026, 2095, 2167, 2168])
def test_each_window_sits_inside_the_one_above_it(focus_year):
    """Kaskadens loefte: hver raekke er et udsnit af raekken over.

    Holder det ikke, viser en raekke tid, dens egen forgaenger ikke daekker —
    og saa betyder zoomkilen mellem dem ingenting.
    """
    focus = min(max(datetime(focus_year, 6, 3, 12, tzinfo=CPH), BIRTH), END)
    spans = tl.cascade_spans(TOTAL, tl.YEAR, 5)
    windows = tl.cascade_windows(BIRTH, END, focus, spans)

    assert windows[0] == (BIRTH, END)
    for level, (low, high) in enumerate(windows):
        assert (high - low).total_seconds() == pytest.approx(spans[level], abs=1.0)
        if level:
            parent_low, parent_high = windows[level - 1]
            assert parent_low <= low <= high <= parent_high


@pytest.mark.parametrize("focus_year", [2018, 2026, 2095, 2167, 2168])
def test_the_focus_point_is_always_inside_the_bottom_window(focus_year):
    focus = min(max(datetime(focus_year, 6, 3, 12, tzinfo=CPH), BIRTH), END)
    spans = tl.cascade_spans(TOTAL, tl.YEAR, 4)
    low, high = tl.cascade_windows(BIRTH, END, focus, spans)[-1]
    assert low <= focus <= high


def test_a_focus_at_the_very_edge_does_not_push_a_window_outside_the_life():
    """Zoomer man helt ud til fødslen, skal vinduet klemmes ind, ikke flyttes ud."""
    for focus in (BIRTH, END):
        windows = tl.cascade_windows(
            BIRTH, END, focus, tl.cascade_spans(TOTAL, tl.WEEK, 5)
        )
        for low, high in windows:
            assert BIRTH <= low <= high <= END


# -------------------------------------------------------------------------
# Etiketterne
# -------------------------------------------------------------------------


def test_labels_in_the_same_lane_never_overlap():
    random.seed(73)
    entries = [
        (random.uniform(LEFT, RIGHT), random.uniform(30, 150), random.choice((0, 1)))
        for _ in range(400)
    ]
    placed, hidden = tl.place_labels(entries, LEFT, RIGHT, max_lanes=5)

    assert len(placed) + hidden == len(entries)
    lanes: dict[int, list[tuple[float, float]]] = {}
    for spot in placed:
        lanes.setdefault(spot.lane, []).append(
            (spot.text_x, spot.text_x + spot.width)
        )
    for boxes in lanes.values():
        boxes.sort()
        for (_, earlier_end), (later_start, _) in zip(boxes, boxes[1:]):
            assert later_start >= earlier_end


def test_no_label_is_pushed_outside_the_row():
    entries = [(LEFT, 200.0, 1), (RIGHT, 200.0, 1), (640.0, 1200.0, 1)]
    placed, _ = tl.place_labels(entries, LEFT, RIGHT, max_lanes=4)
    for spot in placed:
        assert spot.text_x >= LEFT - 0.01
        # Den sidste er bredere end hele raekken og kan kun begynde i venstre
        # kant. Alle andre skal ligge helt inden for.
        if spot.width <= RIGHT - LEFT:
            assert spot.text_x + spot.width <= RIGHT + 0.01


def test_the_starred_classics_get_a_label_before_the_rest():
    """Naar pladsen slipper op, er det de jaevne maerkedage, der maa vige."""
    crowd = [(500.0 + index * 0.5, 120.0, 1) for index in range(40)]
    crowd.append((500.0, 120.0, 0))          # Stjernen, midt i klumpen.
    placed, hidden = tl.place_labels(crowd, LEFT, RIGHT, max_lanes=2)

    assert hidden > 0, "testen siger intet, hvis alting faar plads"
    assert any(spot.index == len(crowd) - 1 for spot in placed)


def test_more_lanes_fit_more_labels():
    random.seed(1729)
    entries = [(random.uniform(LEFT, RIGHT), 90.0, 1) for _ in range(200)]
    counts = [
        len(tl.place_labels(entries, LEFT, RIGHT, max_lanes=lanes)[0])
        for lanes in (1, 2, 4, 8)
    ]
    assert counts == sorted(counts)
    assert counts[0] < counts[-1]


def test_an_empty_row_places_nothing_and_hides_nothing():
    placed, hidden = tl.place_labels([], LEFT, RIGHT)
    assert placed == [] and hidden == 0


def test_text_width_grows_with_the_text():
    assert tl.text_width("i") < tl.text_width("W")
    assert tl.text_width("1.000.000 sekunder") > tl.text_width("42 år")
    assert tl.text_width("🚀 x") > tl.text_width("x")


# -------------------------------------------------------------------------
# Aksen
# -------------------------------------------------------------------------


@pytest.mark.parametrize(
    "years, lowest",
    [(150, 4), (60, 4), (20, 4), (5, 4), (1, 4)],
)
def test_the_axis_always_has_something_to_read(years, lowest):
    """Uanset hvor taet man zoomer, skal raekken have en inddeling."""
    end = BIRTH + relativedelta(years=years)
    ticks = tl.axis_ticks(BIRTH, end, "da")
    assert len(ticks) >= lowest
    assert all(BIRTH <= moment <= end for moment, _ in ticks)
    assert all(text for _, text in ticks)


@pytest.mark.parametrize("days", [400, 90, 30, 7, 2])
def test_short_windows_get_months_or_days_on_the_axis(days):
    end = BIRTH + relativedelta(days=days)
    ticks = tl.axis_ticks(BIRTH, end, "en")
    assert ticks, "selv et par døgn skal have en inddeling"
    assert all(BIRTH <= moment <= end for moment, _ in ticks)


def test_the_axis_ticks_come_in_order():
    ticks = tl.axis_ticks(BIRTH, END, "da")
    moments = [moment for moment, _ in ticks]
    assert moments == sorted(moments)


# -------------------------------------------------------------------------
# Tegningen
# -------------------------------------------------------------------------


@pytest.fixture(scope="module")
def real_entries() -> list[tl.Entry]:
    """De maerkedage, der regnes fra foedslen — kataloget uden festdagene.

    Festdagene er holdt ude med vilje. De ligger paa kalenderen i stedet for
    i livet og kan falde hvor som helst — ogsaa paa ens tiende levedoegn.
    Hvordan tidslinjen klarer *dem*, staar i sin egen test laengere nede.

    Udvalget stod foer paa ``default_on``, og det holdt, saa laenge kun de
    personlige grupper var slaaet til fra start. Nu er alt paa naer
    18-pakken taendt, saa det ville traekke hele kalenderen med ind her.
    Skellet, testen er ude efter, er hvad maerkedagen haenger paa, og det
    kan motoren selv svare paa.
    """
    profile = Profile(birth_local=BIRTH)
    switched_on = {
        group.key for group in GROUPS if group_scope(group.key) == BIRTH_SCOPE
    }
    occasions = compute(
        profile,
        keys={m.key for m in all_milestones() if m.group in switched_on},
        lang="da",
        max_age_years=150.0,
    )
    return [
        tl.Entry(
            when=o.when_local,
            label=o.label,
            tip=explanation(o.milestone, "da"),
            color="#3b7dd8",
            star=o.milestone.star,
        )
        for o in occasions
    ]


@pytest.mark.parametrize("lang", ["da", "en"])
def test_the_cascade_draws_one_band_per_row(real_entries, lang):
    spans = tl.cascade_spans(TOTAL, tl.YEAR, 4)
    drawing = tl.render_cascade(real_entries, BIRTH, END, NOW, NOW, spans, lang)

    assert drawing.svg.startswith("<svg") and drawing.svg.endswith("</svg>")
    assert drawing.height > 0
    assert drawing.svg.count('class="tl-lvl"') == len(spans)


def test_the_log_scale_leaves_out_what_happened_before_the_first_second():
    """En maerkedag foer foedslen har ingen plads paa en akse fra foedslen."""
    entries = [
        entry_at(BIRTH - relativedelta(years=5), "før fødslen"),
        entry_at(BIRTH + relativedelta(years=1), "efter"),
        entry_at(BIRTH + relativedelta(years=40), "meget senere"),
    ]
    drawing = tl.render_log(entries, BIRTH, NOW, TOTAL, "da")
    assert "før fødslen" not in drawing.svg
    assert "meget senere" in drawing.svg


@pytest.fixture(scope="module")
def calendar_entries() -> list[tl.Entry]:
    """Festdagene alene — de maerkedage, der ligger paa kalenderen."""
    profile = Profile(birth_local=BIRTH)
    calendar = {m.key for m in all_milestones() if m.unit in {"annual", "date_abs"}}
    occasions = compute(profile, keys=calendar, lang="da", max_age_years=150.0)
    return [
        tl.Entry(
            when=o.when_local,
            label=o.label,
            tip=explanation(o.milestone, "da"),
            color="#8e24aa",
            star=False,
        )
        for o in occasions
    ]


def test_the_log_scale_copes_with_a_day_in_your_first_month(calendar_entries):
    """En festdag kan falde faa doegn efter foedslen, og aksen skal foelge med.

    Den logaritmiske akse begynder en tierpotens under den tidligste
    maerkedag. Da kataloget kun var tal fra foedslen, var det altid 10⁶; med
    kalenderdagene kan det vaere lavere, og tegningen skal stadig holde.
    """
    assert calendar_entries, "der var ingen kalenderdage at tegne"
    earliest = min((e.when - BIRTH).total_seconds() for e in calendar_entries)
    assert 0 < earliest < 1e7, "ingen festdag faldt i det foerste aar"

    drawing = tl.render_log(calendar_entries, BIRTH, NOW, TOTAL, "da")
    assert drawing.svg.startswith("<svg") and drawing.svg.endswith("</svg>")
    assert drawing.height > 0


def test_the_log_axis_starts_where_the_milestones_do(real_entries):
    """Kataloget begynder ved 10⁶ sekunder — dag 11.

    En akse fra ét sekund ville bruge over halvdelen af bredden paa tom tid.
    Derfor begynder den en tierpotens under den tidligste maerkedag, og
    potenserne under det maa ikke staa paa aksen.
    """
    earliest = min((e.when - BIRTH).total_seconds() for e in real_entries)
    assert earliest == pytest.approx(1e6)

    drawing = tl.render_log(real_entries, BIRTH, NOW, TOTAL, "da")
    assert ">10⁵<" in drawing.svg
    assert ">10⁴<" not in drawing.svg
    assert ">10⁰<" not in drawing.svg


def test_a_tooltip_is_escaped_so_it_cannot_break_the_drawing():
    nasty = entry_at(NOW, "<script>alert(1)</script> & co")
    drawing = tl.render_log([nasty], BIRTH, NOW, TOTAL, "en")
    assert "<script>" not in drawing.svg
    assert "&lt;script&gt;" in drawing.svg


def test_the_drawing_survives_having_nothing_to_draw():
    for drawing in (
        tl.render_cascade([], BIRTH, END, NOW, NOW, tl.cascade_spans(TOTAL, tl.YEAR, 4), "da"),
        tl.render_log([], BIRTH, NOW, TOTAL, "da"),
    ):
        assert drawing.svg.startswith("<svg")
        assert drawing.height > 0


def test_the_file_version_is_a_standalone_svg(real_entries):
    spans = tl.cascade_spans(TOTAL, tl.YEAR, 3)
    drawing = tl.render_cascade(real_entries, BIRTH, END, NOW, NOW, spans, "en")
    data = drawing.as_file()
    assert data.startswith(b"<?xml version=")
    assert data.rstrip().endswith(b"</svg>")


def test_the_frame_carries_the_drawing_and_measures_itself(real_entries):
    """``st.html`` renser SVG bort, saa tegningen gaar i en komponent-iframe."""
    drawing = tl.render_log(real_entries, BIRTH, NOW, TOTAL, "en")
    frame = drawing.as_frame()
    assert frame.startswith("<!doctype html>")
    assert drawing.svg in frame
    assert "frameElement" in frame, "rammen skal kunne rette sin egen højde"


# -------------------------------------------------------------------------
# Tidsrum skrevet ud
# -------------------------------------------------------------------------


@pytest.mark.parametrize(
    "seconds, da, en",
    [
        (tl.YEAR, "1 år", "1 year"),
        (10 * tl.YEAR, "10 år", "10 years"),
        (3 * tl.MONTH, "3 måneder", "3 months"),
        (tl.WEEK, "1 uge", "1 week"),
        (2 * tl.DAY, "2 dage", "2 days"),
    ],
)
def test_a_span_is_written_in_both_languages(seconds, da, en):
    assert tl.span_text(seconds, "da") == da
    assert tl.span_text(seconds, "en") == en


def test_every_span_on_the_slider_has_a_name():
    for seconds in tl.SPAN_CHOICES:
        for lang in ("da", "en"):
            text = tl.span_text(seconds, lang)
            assert text and not text.startswith("0 ")
