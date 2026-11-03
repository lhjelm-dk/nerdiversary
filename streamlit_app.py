"""Nørdilæum / Nerdiversary — dine næste skæve mærkedage.

Kør appen med:
    streamlit run streamlit_app.py
"""

from __future__ import annotations

import hashlib
import json
from datetime import date, datetime, time, timedelta, timezone
from zoneinfo import ZoneInfo, available_timezones

import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from streamlit_calendar import calendar as fullcalendar

from dateutil.relativedelta import relativedelta

from utils import formatting as fmt
from utils import stardate as sd
from utils import timeline as tl
from utils.catalog import (
    BUNDLES,
    BUNDLES_BY_KEY,
    GROUPS,
    GROUPS_BY_KEY,
    Bundle,
    milestones_in_group,
)
from utils.engine import (
    SCOPES,
    Occasion,
    Profile,
    Rates,
    age_seconds,
    age_days,
    age_hours,
    age_months,
    age_years,
    all_milestones,
    build_label,
    bundle_keys,
    bundle_scope,
    compute,
    explanation,
    duration_breakdown,
    last_occasions,
    next_occasions,
)
from utils.exporters import (
    build_google_csv,
    build_ics,
    google_calendar_link,
    suggested_filename,
)
from utils.i18n import LANGUAGES, t
from utils.leapseconds import born_before_utc, leap_seconds_since_birth
from utils.legends import legend_milestones
from utils.notes import NOTE_TITLES, note

st.set_page_config(
    page_title="Nørdilæum · Nerdiversary",
    page_icon="🎉",
    layout="wide",
)

DEFAULT_TZ = "Europe/Copenhagen"
DEFAULT_BIRTH_DATE = date(2018, 6, 3)
DEFAULT_BIRTH_TIME = time(7, 10, 0)

# Farver til kalenderen — én pr. gruppe, valgt så de kan skelnes fra hinanden.
GROUP_COLORS: dict[str, str] = {
    "sec": "#3b7dd8",
    "minhour": "#4aa3a2",
    "dayweek": "#2f9e68",
    "monthyear": "#7a9e2f",
    "constants": "#b8860b",
    "nerd": "#d2691e",
    "s73": "#c43b5a",
    "repeat": "#9b59b6",
    "exotic": "#00897b",
    "moon": "#5c6bc0",
    "space": "#1f3a93",
    "geo": "#8d6e63",
    "body": "#e53935",
    "century": "#607d8b",
    "legend": "#795548",
    # Festdagene. De skrevne foerst, saa de udregnede talmoenstre.
    "pop": "#e91e63",
    "dkday": "#c62828",
    "fiction": "#8e24aa",
    "chars": "#f57c00",
    "scifi": "#00838f",
    "sciday": "#5e35b1",
    "scihist": "#00695c",
    "nerdhist": "#6d4c41",
    "palindrome": "#ad1457",
    "sequence": "#2e7d32",
    "repunit": "#9e9d24",
    "binday": "#37474f",
    "pyth": "#1565c0",
    "sqrtday": "#0277bd",
    "fibday": "#7b1fa2",
    "product": "#ef6c00",
    "sumday": "#558b2f",
    "techday": "#0097a7",
    "birthdays": "#d81b60",
    "geoyear": "#8d6e63",
}


# =========================================================================
# Sidepanel
# =========================================================================

with st.sidebar:
    lang = st.segmented_control(
        "Sprog / Language",
        options=list(LANGUAGES.keys()),
        format_func=lambda code: LANGUAGES[code],
        default="en",
        key="lang",
    ) or "en"

    st.subheader(t("who", lang))
    person_name = st.text_input(
        t("name_label", lang),
        placeholder=t("name_placeholder", lang),
        key="person_name",
    )

    birth_date = st.date_input(
        t("birth_date", lang),
        value=DEFAULT_BIRTH_DATE,
        min_value=date(1900, 1, 1),
        max_value=date.today(),
        format="DD.MM.YYYY",
        key="birth_date",
    )

    time_unknown = st.checkbox(
        t("time_unknown", lang),
        help=t("time_unknown_help", lang),
        key="time_unknown",
    )
    birth_time = st.time_input(
        t("birth_time", lang),
        value=DEFAULT_BIRTH_TIME,
        step=1,
        disabled=time_unknown,
        key="birth_time",
    )
    if time_unknown:
        birth_time = time(12, 0, 0)

    zone_names = sorted(available_timezones())
    tz_name = st.selectbox(
        t("timezone", lang),
        options=zone_names,
        index=zone_names.index(DEFAULT_TZ) if DEFAULT_TZ in zone_names else 0,
        help=t("timezone_help", lang),
        key="tz_name",
    )

    with st.expander(t("pair_section", lang), icon=":material/group:"):
        st.caption(t("pair_hint", lang))
        use_pair = st.checkbox(t("pair_use", lang), key="use_pair")
        partner_name = st.text_input(
            t("pair_name", lang),
            placeholder=t("name_placeholder", lang),
            disabled=not use_pair,
            key="partner_name",
        )
        partner_date = st.date_input(
            t("pair_date", lang),
            value=date(1973, 10, 9),
            min_value=date(1900, 1, 1),
            max_value=date.today(),
            format="DD.MM.YYYY",
            disabled=not use_pair,
            key="partner_date",
        )
        partner_time = st.time_input(
            t("pair_time", lang),
            value=time(12, 0, 0),
            step=1,
            help=t("pair_time_help", lang),
            disabled=not use_pair,
            key="partner_time",
        )

    with st.expander(t("assumptions", lang), icon=":material/tune:"):
        lifespan = st.slider(
            t("lifespan", lang),
            min_value=60,
            max_value=120,
            value=100,
            step=1,
            help=t("lifespan_help", lang),
            key="lifespan",
        )
        max_age = st.slider(
            t("max_age", lang), min_value=80, max_value=150, value=150, step=5, key="max_age"
        )
        bpm = st.number_input(t("bpm", lang), 30.0, 140.0, 70.0, 1.0, key="bpm")
        breaths = st.number_input(t("breaths", lang), 6.0, 30.0, 16.0, 1.0, key="breaths")
        sleep_hours = st.number_input(t("sleep", lang), 3.0, 14.0, 8.0, 0.5, key="sleep")
        meals = st.number_input(t("meals", lang), 1.0, 8.0, 3.0, 0.5, key="meals")
        steps = st.number_input(t("steps", lang), 1000.0, 30000.0, 7000.0, 500.0, key="steps")

tz = ZoneInfo(tz_name)

# Den anden person regnes i samme zone. Det er en forenkling, men den rigtige
# at vaelge: aldersforskellen skal laeses paa ét ur, ikke paa to.
partner_birth = (
    datetime.combine(partner_date, partner_time, tzinfo=tz) if use_pair else None
)

profile = Profile(
    birth_local=datetime.combine(birth_date, birth_time, tzinfo=tz),
    name=person_name,
    lifespan_years=float(lifespan),
    rates=Rates(
        bpm=bpm,
        breaths_per_min=breaths,
        sleep_hours_per_day=sleep_hours,
        meals_per_day=meals,
        steps_per_day=steps,
    ),
    time_is_approximate=time_unknown,
    partner_birth=partner_birth,
    partner_name=partner_name if use_pair else "",
)


# =========================================================================
# Valg af mærkedage — gemmes i session state
# =========================================================================

CATALOGUE = all_milestones()
GROUP_OF = {m.key: m.group for m in CATALOGUE}
DEFAULT_ON = {g.key: g.default_on for g in GROUPS}


def _cb(key: str) -> str:
    """Session state-nøglen for ét afkrydsningsfelt."""
    return f"cb_{key}"


# Valget ligger i ét sæt, der overlever, at et afkrydsningsfelt ikke bliver
# tegnet. Det er nødvendigt nu, hvor søgningen skjuler de felter, der ikke
# matcher: Streamlit rydder op i tilstanden for widgets, der forsvinder, og
# et valg, der kun lå i widgetnøglerne, ville gå tabt hver gang man søgte.
#
# Felterne skriver derfor deres svar ind i sættet gennem ``_remember``, og
# ``_set_keys`` sætter begge steder, så de to aldrig kan komme ud af trit.
seen_keys: set[str] = st.session_state.setdefault("seen_keys", set())
chosen: set[str] = st.session_state.setdefault("chosen", set())

# Samme løkke klarer både første kørsel og det tilfælde, at kataloget er
# vokset siden sidst — en ny gruppe følger sin egen standardindstilling.
for milestone in CATALOGUE:
    if milestone.key not in seen_keys:
        seen_keys.add(milestone.key)
        if DEFAULT_ON.get(milestone.group, True):
            chosen.add(milestone.key)


def _remember(key: str) -> None:
    """Flyt et afkrydsningsfelts svar over i det varige valg."""
    if st.session_state[_cb(key)]:
        st.session_state.chosen.add(key)
    else:
        st.session_state.chosen.discard(key)


def _set_keys(keys, value: bool) -> None:
    """Sæt en hel flok på én gang — både i sættet og i de tegnede felter."""
    for key in keys:
        st.session_state[_cb(key)] = value
        if value:
            st.session_state.chosen.add(key)
        else:
            st.session_state.chosen.discard(key)


selected_keys = {m.key for m in CATALOGUE if m.key in chosen}
occasions = compute(profile, keys=selected_keys, lang=lang, max_age_years=float(max_age))


# =========================================================================
# Overskrift
# =========================================================================

title = t("app_title", lang)
if person_name.strip():
    title = f"{title} — {person_name.strip()}"
st.title(title, anchor=False)
st.caption(t("app_tagline", lang))

if time_unknown:
    st.warning(t("approximate_warning", lang), icon=":material/schedule:")


# =========================================================================
# Levende tællere
# =========================================================================


@st.fragment(run_every="1s")
def live_panel() -> None:
    """Tæller, der tikker uden at genberegne resten af siden."""
    now = datetime.now(timezone.utc)
    now_local = now.astimezone(tz)
    seconds_old = age_seconds(profile, now)

    with st.container(border=True):
        st.caption(t("age_seconds", lang).upper())
        st.markdown(f"# {fmt.fmt_num(seconds_old, lang, 1)}")

        # Aldersstigen: SI-enheder først, derefter kalenderenhederne.
        ladder = st.container(horizontal=True)
        ladder.metric(
            t("age_hours", lang),
            fmt.fmt_num(age_hours(profile, now), lang, 2),
            help=t("si_help", lang),
        )
        ladder.metric(
            t("age_days", lang),
            fmt.fmt_num(age_days(profile, now), lang, 2),
            help=t("si_help", lang),
        )
        ladder.metric(
            t("age_months", lang),
            fmt.fmt_num(age_months(profile, now), lang, 2),
            help=t("calendar_help", lang),
        )
        ladder.metric(
            t("age_years", lang),
            fmt.fmt_num(age_years(profile, now), lang, 2),
            help=t("calendar_year_help", lang),
        )

        technical = st.container(horizontal=True)
        technical.metric(t("unix_birth", lang), fmt.fmt_int(profile.unix_birth, lang))
        technical.metric(
            t("leap_seconds", lang),
            leap_seconds_since_birth(profile.birth_utc, now),
            help=t("leap_help", lang),
        )
        technical.metric(
            t("stardate_now", lang),
            sd.format_tng(now_local),
            help=t("stardate_help", lang),
        )

        if born_before_utc(profile.birth_utc):
            st.caption(t("born_before_utc", lang))

        gap = profile.age_gap()
        if gap is not None:
            other = profile.partner_name.strip() or t("pair_someone", lang)
            if gap.years == 0 and gap.months == 0 and gap.days == 0:
                st.caption(t("pair_twins", lang))
            else:
                st.caption(
                    f"{t('pair_gap', lang, name=other)}: "
                    f"**{fmt.fmt_relativedelta(gap, lang)}**"
                )

    upcoming = next_occasions(occasions, now, count=4)
    if not upcoming:
        st.info(t("nothing_ahead", lang), icon=":material/hourglass_empty:")
        return

    # Kun den førstkommende får det store kort. Resten står som linjer, så
    # fanerne ikke bliver skubbet under skærmkanten.
    head, *rest = upcoming
    with st.container(border=True):
        st.caption(t("next_up", lang).upper())
        st.markdown(f"**{head.group.emoji} {head.label}**")
        st.markdown(f"### {fmt.fmt_datetime_full(head.when_local, lang)}")
        st.progress(
            head.progress(profile, now),
            text=f"{fmt.fmt_num(head.progress(profile, now) * 100, lang, 4)} %  ·  "
            f"{fmt.fmt_hms_countdown(head.seconds_from(now), lang)}  ·  "
            f"{head.countdown(now_local, lang)}",
        )
        why = explanation(head.milestone, lang)
        if why:
            st.caption(why)

    for occasion in rest[:3]:
        st.caption(
            f"{occasion.group.emoji} **{occasion.label}** — "
            f"{fmt.fmt_date_both(occasion.when_local, lang)} "
            f"{fmt.fmt_clock(occasion.when_local, lang)} · "
            f"{occasion.countdown(now_local, lang)}"
        )

    recent = last_occasions(occasions, now, count=1)
    if recent:
        passed = recent[0]
        days_ago = (now - passed.when_utc).total_seconds() / 86400
        st.caption(
            f"{t('most_recent', lang)}: {passed.group.emoji} **{passed.label}** — "
            f"{fmt.fmt_date_both(passed.when_local, lang)} · "
            f"{t('that_was', lang)} {fmt.fmt_int(days_ago, lang)} "
            f"{t('days_ago', lang)}"
        )


live_panel()


# =========================================================================
# Faneblade
# =========================================================================

now_utc = datetime.now(timezone.utc)
now_local = now_utc.astimezone(tz)

# --- Filtre ---------------------------------------------------------------
#
# De ligger OVER fanebladene med vilje. De styrer baade Liste, Kalender og
# Eksport, og da de foer laa inde i Liste-fanen, kunne man ikke se, at det var
# dem, der afgjorde, hvad der endte i kalenderfilen.

with st.container(border=True):
    st.caption(t("filters_scope", lang).upper())
    row = st.container(horizontal=True)
    group_choices = row.multiselect(
        t("filter_groups", lang),
        options=[g.key for g in GROUPS],
        format_func=lambda key: next(g.title(lang) for g in GROUPS if g.key == key),
        default=[g.key for g in GROUPS],
        key="filter_groups",
    )
    row.selectbox(
        t("filter_window", lang),
        options=["all", "1", "5", "10", "25"],
        format_func=lambda key: t(f"window_{key}", lang),
        key="filter_window",
    )
    window = st.session_state.filter_window
    second_row = st.container(horizontal=True)
    when_filter = second_row.segmented_control(
        t("when", lang),
        options=["future", "past", "both"],
        format_func=lambda key: {
            "future": t("only_future", lang),
            "past": t("only_past", lang),
            "both": t("both", lang),
        }[key],
        default="future",
        key="when_filter",
    ) or "future"
    query = second_row.text_input(
        t("search", lang),
        placeholder=t("search_placeholder", lang),
        key="query",
    )

tab_list, tab_cal, tab_time, tab_select, tab_export, tab_notes = st.tabs(
    [
        t("tab_list", lang),
        t("tab_calendar", lang),
        t("tab_timeline", lang),
        t("tab_select", lang),
        t("tab_export", lang),
        t("tab_notes", lang),
    ]
)


def apply_scope_filters(items: list[Occasion]) -> list[Occasion]:
    """Hvilke mærkedage der er tale om — uden noget om hvornår.

    Delt ud fra ``apply_filters``, fordi tidslinjen skal vise hele livet.
    En tidslinje, der kun gik fremad, ville mangle halvdelen af pointen og
    hele "du er her"; men gruppevalget og fritekstsøgningen skal naturligvis
    gælde den også.
    """
    out = [o for o in items if o.milestone.group in set(group_choices)]
    if query.strip():
        needle = query.strip().lower()
        out = [
            o
            for o in out
            if needle in o.label.lower()
            or needle in explanation(o.milestone, lang).lower()
            or needle in o.group.name(lang).lower()
        ]
    return out


def apply_filters(items: list[Occasion]) -> list[Occasion]:
    """Filtrene over fanebladene, brugt af Liste, Kalender og Eksport."""
    out = apply_scope_filters(items)

    if when_filter == "future":
        out = [o for o in out if o.when_utc >= now_utc]
    elif when_filter == "past":
        out = [o for o in out if o.when_utc < now_utc]

    if window != "all":
        horizon = now_utc + timedelta(days=365.2422 * int(window))
        out = [o for o in out if o.when_utc <= horizon]

    return out


filtered = apply_filters(occasions)


def to_frame(items: list[Occasion]) -> pd.DataFrame:
    """Tabellen, som den vises."""
    rows = []
    for occasion in items:
        rows.append(
            {
                t("col_milestone", lang): occasion.label,
                # Skønnet står i sin egen kolonne, ikke inde i navnet — ellers
                # roder markøren både sortering og fritekstsøgning.
                t("col_estimate", lang): "⚠" if occasion.is_estimate else "",
                t("col_group", lang): occasion.group.title(lang),
                t("col_date", lang): fmt.fmt_date_numeric(occasion.when_local),
                t("col_weekday", lang): fmt.fmt_weekday(occasion.when_local, lang),
                t("col_time", lang): fmt.fmt_clock(occasion.when_local, lang),
                t("col_age", lang): (
                    "—" if occasion.is_absolute else occasion.age_text(profile, lang)
                ),
                t("col_countdown", lang): occasion.countdown(now_local, lang),
                t("col_note", lang): explanation(occasion.milestone, lang),
            }
        )
    return pd.DataFrame(rows)


def detail_text(occasion: Occasion) -> str:
    """Alt om én mærkedag på linjer — teksten bag mus-over.

    Både kalenderen og tidslinjen bruger den, så de to aldrig kan komme til
    at fortælle hver sin historie om samme mærkedag.
    """
    lines = [
        f"{occasion.group.emoji} {occasion.label}",
        fmt.fmt_datetime_full(occasion.when_local, lang),
    ]
    if not occasion.is_absolute:
        lines.append(f"{t('col_age', lang)}: {occasion.age_text(profile, lang)}")
    if occasion.is_estimate:
        lines.append(t("estimate_marker", lang))
    why = explanation(occasion.milestone, lang)
    if why:
        lines += ["", why]
    return "\n".join(lines)


with tab_list:
    if not filtered:
        st.info(t("no_results", lang), icon=":material/search_off:")
    else:
        st.caption(t("showing_n", lang, n=len(filtered)))
        st.dataframe(
            to_frame(filtered),
            hide_index=True,
            height=560,
            column_config={
                t("col_milestone", lang): st.column_config.TextColumn(width="medium"),
                t("col_estimate", lang): st.column_config.TextColumn(
                    width="small", help=t("estimate_help", lang)
                ),
                t("col_note", lang): st.column_config.TextColumn(width="large"),
            },
        )


# --- Kalender ------------------------------------------------------------


def calendar_tooltips(tips: dict[str, str]) -> None:
    """Giv kalenderens begivenheder et værktøjstip med forklaringen.

    streamlit-calendar kan kun det ene: sende et kald tilbage til serveren ved
    mus-over (``eventMouseEnter``). Det ville genkøre scriptet for hver eneste
    begivenhed, musen strøg hen over — hundredvis af kald for at læse en
    forklaring.

    Komponentens iframe ligger på samme domæne som siden selv, så i stedet
    sættes et almindeligt ``title``-attribut direkte på begivenhederne. Resten
    klarer browseren, og der går ikke ét kald over nettet.

    Tilknytningen er bevidst vedvarende og ikke en enkelt MutationObserver:
    skifter man visning, får komponenten en ny nøgle, og hele iframen bliver
    bygget forfra. En observer ville blive hængende i det dokument, der ikke
    er der længere. Løkken koster et opslag et par gange i sekundet og
    rammer kun de begivenheder, der faktisk er tegnet.
    """
    payload = json.dumps(tips, ensure_ascii=False).replace("<", "\\u003c")
    components.html(
        f"""
<script>
(function () {{
  const TIPS = {payload};
  const FRAME = "iframe[title='streamlit_calendar.calendar']";
  // Maaneds- og aarsvisningen tegner .fc-event; agendaen tegner .fc-list-event
  // med sine helt egne klassenavne.
  const EVENTS = ".fc-event, .fc-list-event";
  const TITLES = ".fc-event-title, .fc-list-event-title";

  function apply() {{
    let page;
    try {{ page = window.parent.document; }} catch (err) {{ return; }}
    const frame = page.querySelector(FRAME);
    const doc = frame && frame.contentDocument;
    if (!doc) return;
    doc.querySelectorAll(EVENTS).forEach(function (el) {{
      const label = el.querySelector(TITLES);
      const tip = label && TIPS[label.textContent.trim()];
      // Kun naar den er ny: ellers skriver vi det samme igen hvert sekund.
      if (tip && el.getAttribute("title") !== tip) el.setAttribute("title", tip);
    }});
  }}

  apply();
  if (window.__nerdTipTimer) clearInterval(window.__nerdTipTimer);
  window.__nerdTipTimer = setInterval(apply, 400);
}})();
</script>
""",
        height=0,
    )


with tab_cal:
    st.caption(t("calendar_hint", lang))

    if not filtered:
        st.info(t("calendar_empty", lang), icon=":material/event_busy:")
    else:
        view_key = st.segmented_control(
            t("cal_view", lang),
            options=["dayGridMonth", "multiMonthYear", "listYear"],
            format_func=lambda key: {
                "dayGridMonth": t("cal_month", lang),
                "multiMonthYear": t("cal_year", lang),
                "listYear": t("cal_list", lang),
            }[key],
            default="dayGridMonth",
            key="cal_view",
        ) or "dayGridMonth"

        ahead = [o for o in filtered if o.when_utc >= now_utc]
        anchor = (ahead or filtered)[0].when_local.date()

        events = [
            {
                "title": f"{o.group.emoji} {o.label}",
                "start": o.when_local.isoformat(),
                "end": (o.when_local + timedelta(minutes=30)).isoformat(),
                "backgroundColor": GROUP_COLORS.get(o.milestone.group, "#555"),
                "borderColor": GROUP_COLORS.get(o.milestone.group, "#555"),
                "extendedProps": {
                    "why": explanation(o.milestone, lang),
                    "age": "" if o.is_absolute else o.age_text(profile, lang),
                    "when": fmt.fmt_datetime_full(o.when_local, lang),
                    "group": o.group.name(lang),
                    "estimate": o.is_estimate,
                },
            }
            for o in filtered
        ]

        # Værktøjstippet: hvad der står i tabellens kolonner, samlet på
        # linjer. Nøglen er den tekst, FullCalendar faktisk skriver i
        # begivenheden, for det er den, scriptet kan genkende den på.
        tooltips = {
            f"{o.group.emoji} {o.label}": detail_text(o) for o in filtered
        }

        # Året fylder mere end en enkelt måned.
        frame_height = {"dayGridMonth": 800, "multiMonthYear": 1150, "listYear": 800}[
            view_key
        ]

        options = {
            "initialView": view_key,
            "initialDate": anchor.isoformat(),
            "locale": "da" if lang == "da" else "en",
            "firstDay": 1,
            "headerToolbar": {
                "left": "prev,next today",
                "center": "title",
                "right": "dayGridMonth,multiMonthYear,listYear",
            },
            "buttonText": {
                "today": "I dag" if lang == "da" else "Today",
                "dayGridMonth": t("cal_month", lang),
                "multiMonthYear": t("cal_year", lang),
                "listYear": t("cal_list", lang),
            },
            "noEventsText": t("calendar_empty", lang),
            "height": frame_height - 60,
            "navLinks": True,
            # "block" tegner begivenheden som en farvet bjælke med teksten i
            # stedet for en lille prik, man ikke kan læse.
            "eventDisplay": "block",
            "dayMaxEvents": 4,
            "displayEventTime": True,
            "eventTimeFormat": {"hour": "2-digit", "minute": "2-digit", "hour12": False},
        }

        # streamlit-calendar melder ikke sin højde til Streamlit 1.62, så
        # iframen ender på 0 px. Kalenderen tegnes korrekt indeni — den skal
        # bare have plads. Derfor denne ene regel CSS.
        st.html(
            "<style>iframe[title='streamlit_calendar.calendar']"
            f"{{height:{frame_height}px!important;"
            f"min-height:{frame_height}px!important;}}</style>"
        )

        # Komponenten husker sin tilstand pr. nøgle, så nøglen skal ændre sig,
        # når begivenhederne gør.
        signature = hashlib.sha1(
            f"{view_key}{anchor}{len(events)}{events[0]['start']}{events[-1]['start']}".encode()
        ).hexdigest()[:12]

        state = fullcalendar(
            events=events,
            options=options,
            callbacks=["eventClick"],
            key=f"cal_{signature}",
        )

        calendar_tooltips(tooltips)
        st.caption(t("calendar_tooltip_hint", lang))

        clicked = (state or {}).get("eventClick")
        if clicked:
            info = clicked.get("event", {})
            props = info.get("extendedProps", {})
            with st.container(border=True):
                st.markdown(f"**{info.get('title', '')}**")
                if props.get("when"):
                    st.markdown(f"### {props['when']}")
                details = []
                if props.get("group"):
                    details.append(f"{t('col_group', lang)}: {props['group']}")
                if props.get("age"):
                    details.append(f"{t('col_age', lang)}: {props['age']}")
                if props.get("estimate"):
                    details.append(t("estimate_marker", lang))
                if details:
                    st.caption("  ·  ".join(details))
                if props.get("why"):
                    st.write(props["why"])


# --- Tidslinje -----------------------------------------------------------
#
# Hvorfor der er to skalaer og ikke bare én lineær tidslinje med en
# skydeknap: 390 mærkedage ligger ekstremt ujævnt i et liv. Det første million
# sekunder falder på dag 11, det første gigasekund først ved 31 år, og sidst i
# livet kan der gå ti år mellem to. En skydeknap flytter det problem; den
# løser det ikke. Kaskaden løser det ved at vise flere zoomniveauer på samme
# tid, den logaritmiske ved at gøre hver tierpotens lige bred. Selve
# tegningen står i utils/timeline.py.


def quiet_stretch(
    items: list[Occasion], start: datetime
) -> tuple[float, datetime, datetime]:
    """Det længste stykke liv uden en eneste af de valgte mærkedage.

    Strækket efter den sidste mærkedag tælles ikke med. Det ville altid være
    det længste, og det siger kun noget om, hvor langt *Regn højst til alder*
    står — ikke noget om livet.
    """
    edges = [start, *sorted(o.when_local for o in items)]
    best = (0.0, start, start)
    for earlier, later in zip(edges, edges[1:]):
        gap = (later - earlier).total_seconds()
        if gap > best[0]:
            best = (gap, earlier, later)
    return best


def timeline_entries(items: list[Occasion]) -> list[tl.Entry]:
    """Mærkedagene gjort klar til tegning — farve, etiket og mus-over."""
    return [
        tl.Entry(
            when=o.when_local,
            label=o.label,
            tip=detail_text(o),
            color=GROUP_COLORS.get(o.milestone.group, "#555"),
            star=o.milestone.star,
        )
        for o in items
    ]


with tab_time:
    st.caption(t("timeline_hint", lang))
    scope = apply_scope_filters(occasions)

    if not scope:
        st.info(t("tl_empty", lang), icon=":material/timeline:")
    else:
        life_start = profile.birth_local
        life_end = life_start + relativedelta(years=int(max_age))

        mode = st.segmented_control(
            t("tl_mode", lang),
            options=["cascade", "log"],
            format_func=lambda key: {
                "cascade": t("tl_cascade", lang),
                "log": t("tl_log", lang),
            }[key],
            default="cascade",
            key="tl_mode",
        ) or "cascade"
        st.caption(t(f"tl_{mode}_help", lang))

        if mode == "cascade":
            with st.container(border=True):
                knobs = st.container(horizontal=True)
                focus_date = knobs.slider(
                    t("tl_focus", lang),
                    min_value=life_start.date(),
                    max_value=life_end.date(),
                    value=min(max(date.today(), life_start.date()), life_end.date()),
                    format="DD.MM.YYYY",
                    help=t("tl_focus_help", lang),
                    key="tl_focus",
                )
                target = knobs.select_slider(
                    t("tl_span", lang),
                    options=list(tl.SPAN_CHOICES),
                    value=tl.YEAR,
                    format_func=lambda seconds: tl.span_text(seconds, lang),
                    help=t("tl_span_help", lang),
                    key="tl_target",
                )
                levels = knobs.slider(
                    t("tl_levels", lang),
                    min_value=2,
                    max_value=6,
                    value=4,
                    help=t("tl_levels_help", lang),
                    key="tl_levels",
                )

        # Tallene over tegningen: hvor man står, og hvad der ligger på hver
        # side. "Stille stræk" er det, ingen af de andre visninger kan vise —
        # de tomme år har ingen række i en tabel.
        behind = sum(1 for o in scope if o.when_utc < now_utc)
        lived_share = (
            (now_local - life_start).total_seconds()
            / max(profile.lifespan_years * tl.YEAR, 1.0)
            * 100
        )
        gap_seconds, gap_from, gap_to = quiet_stretch(scope, life_start)

        tiles = st.container(horizontal=True)
        tiles.metric(t("tl_lived", lang), f"{fmt.fmt_num(lived_share, lang, 1)} %")
        tiles.metric(t("tl_behind", lang), fmt.fmt_int(behind, lang))
        tiles.metric(t("tl_ahead", lang), fmt.fmt_int(len(scope) - behind, lang))
        tiles.metric(
            t("tl_quiet", lang),
            tl.span_text(gap_seconds, lang),
            delta=f"{gap_from.year} – {gap_to.year}",
            delta_color="off",
            help=t("tl_quiet_help", lang),
        )

        entries = timeline_entries(scope)
        if mode == "cascade":
            focus = datetime.combine(focus_date, time(12, 0), tzinfo=tz)
            spans = tl.cascade_spans(
                (life_end - life_start).total_seconds(), float(target), int(levels)
            )
            drawing = tl.render_cascade(
                entries,
                start=life_start,
                end=life_end,
                focus=focus,
                now=now_local,
                spans=spans,
                lang=lang,
                max_lanes=5,
            )
        else:
            drawing = tl.render_log(
                entries,
                birth=life_start,
                now=now_local,
                max_seconds=(life_end - life_start).total_seconds(),
                lang=lang,
                max_lanes=12,
            )

        # Højden er et gæt: den rigtige afhænger af, hvor bred skærmen er, og
        # det ved Python ikke. Rammen retter den selv, når den er tegnet.
        components.html(
            drawing.as_frame(), height=int(drawing.height) + 4, scrolling=True
        )
        st.caption(
            t(
                "tl_shown",
                lang,
                n=len(scope),
                span=tl.span_text((life_end - life_start).total_seconds(), lang),
            )
        )
        st.download_button(
            t("tl_download", lang),
            data=drawing.as_file(),
            file_name=suggested_filename(profile, lang, "svg"),
            mime="image/svg+xml",
            icon=":material/download:",
            help=t("tl_download_help", lang),
            key="dl_svg",
        )


# --- Valg ----------------------------------------------------------------


def set_group(group_key: str, value: bool) -> None:
    _set_keys([m.key for m in CATALOGUE if m.group == group_key], value)


def set_all(value: bool) -> None:
    _set_keys([m.key for m in CATALOGUE], value)


def apply_bundle(bundle_key: str) -> None:
    """Slå en færdigpakket udvælgelse til — den erstatter det hidtidige valg."""
    bundle = BUNDLES_BY_KEY[bundle_key]
    wanted = bundle_keys(bundle, profile, datetime.now(timezone.utc))
    _set_keys([m.key for m in CATALOGUE if m.key not in wanted], False)
    _set_keys(wanted, True)
    st.session_state.last_bundle = (bundle.name(lang), len(wanted))


def matches_search(milestone, needle: str) -> bool:
    """Om en mærkedag passer på søgeteksten.

    Tallet søges ogsaa uden tusindtalsskilletegn, saa "5318008" finder den
    maerkedag, der staar som "5.318.008 minutter" i etiketten.
    """
    haystack = [
        build_label(milestone, profile, lang).lower(),
        explanation(milestone, lang).lower(),
        GROUPS_BY_KEY[milestone.group].name(lang).lower(),
        milestone.key.lower(),
    ]
    if float(milestone.amount).is_integer():
        haystack.append(str(int(milestone.amount)))
    return any(needle in field for field in haystack)


def draw_checkbox(milestone) -> None:
    """Ét afkrydsningsfelt, bundet til det varige valg.

    ``value`` bruges kun, naar nøglen er vaek — altsaa naar feltet var skjult
    af en soegning i forrige koersel. Ellers er widgetens egen tilstand og
    saettet det samme, fordi ``_remember`` holder dem sammen.
    """
    st.checkbox(
        build_label(milestone, profile, lang),
        value=milestone.key in st.session_state.chosen,
        key=_cb(milestone.key),
        on_change=_remember,
        args=(milestone.key,),
        help=explanation(milestone, lang) or None,
    )


with tab_select:
    st.subheader(t("bundles", lang), anchor=False)
    st.caption(t("bundles_hint", lang))

    # Pakkerne staar i hylder, fordi de to slags maerkedage ikke svarer til
    # hinanden. Et gigasekund findes kun, fordi netop DU blev foedt; den 4.
    # maj falder samme dag for alle, og dér er det eneste personlige, hvor
    # gammel du er den dag. Blandet i én raekke knapper var det ikke til at
    # se, hvilken slags man var ved at vaelge.
    #
    # Hvilken hylde en pakke hoerer paa, udledes af enhederne i kataloget
    # (``bundle_scope``) og staar ikke skrevet her. En ny pakke havner det
    # rigtige sted af sig selv.
    shelves: dict[str, list[Bundle]] = {scope: [] for scope in SCOPES}
    for bundle in BUNDLES:
        shelves[bundle_scope(bundle)].append(bundle)

    for scope, shelf in shelves.items():
        if not shelf:
            continue
        st.markdown(f"**{t(f'bundles_{scope}', lang)}**")
        st.caption(t(f"bundles_{scope}_help", lang))
        bundle_rows = st.container(horizontal=True)
        for bundle in shelf:
            bundle_rows.button(
                bundle.title(lang),
                on_click=apply_bundle,
                args=(bundle.key,),
                help=bundle.description(lang),
                key=f"bundle_{bundle.key}",
            )

    applied = st.session_state.pop("last_bundle", None)
    if applied:
        st.success(
            t("bundle_applied", lang, name=applied[0], n=applied[1]),
            icon=":material/check_circle:",
        )

    st.divider()
    st.caption(t("select_hint", lang))
    buttons = st.container(horizontal=True)
    buttons.button(
        t("select_all", lang),
        icon=":material/select_all:",
        on_click=set_all,
        args=(True,),
        key="btn_all",
    )
    buttons.button(
        t("clear_all", lang),
        icon=":material/deselect:",
        on_click=set_all,
        args=(False,),
        key="btn_none",
    )
    st.caption(
        t("selected_count", lang, n=len(selected_keys), total=len(CATALOGUE))
    )

    select_query = st.text_input(
        t("select_search", lang),
        placeholder=t("select_search_placeholder", lang),
        help=t("select_search_help", lang),
        key="select_query",
    )

    legend_lookup = {m.key: m for m in legend_milestones()}

    def group_members(group_key: str) -> list:
        return (
            list(legend_lookup.values())
            if group_key == "legend"
            else milestones_in_group(group_key)
        )

    needle = select_query.strip().lower()

    if needle:
        # Under en søgning ophæves grupperingen. At skulle lede gennem seksten
        # foldede grupper efter de tre, der matcher, er netop det, søgefeltet
        # skal løse — så de fundne står samlet, med gruppens emoji som spor.
        matches = [m for m in CATALOGUE if matches_search(m, needle)]
        if not matches:
            st.info(t("select_no_matches", lang), icon=":material/search_off:")
        else:
            st.caption(
                t("select_matches", lang, n=len(matches), total=len(CATALOGUE))
            )
            found = st.container(horizontal=True)
            found.button(
                t("match_all", lang),
                icon=":material/select_all:",
                on_click=_set_keys,
                args=([m.key for m in matches], True),
                key="btn_match_all",
            )
            found.button(
                t("match_none", lang),
                icon=":material/deselect:",
                on_click=_set_keys,
                args=([m.key for m in matches], False),
                key="btn_match_none",
            )
            columns = st.columns(3)
            for index, milestone in enumerate(matches):
                with columns[index % 3]:
                    emoji = GROUPS_BY_KEY[milestone.group].emoji
                    st.checkbox(
                        f"{emoji} {build_label(milestone, profile, lang)}",
                        value=milestone.key in st.session_state.chosen,
                        key=_cb(milestone.key),
                        on_change=_remember,
                        args=(milestone.key,),
                        help=explanation(milestone, lang) or None,
                    )
    else:
        for group in GROUPS:
            members = group_members(group.key)
            if not members:
                continue
            on_count = sum(1 for m in members if m.key in chosen)
            with st.expander(f"{group.title(lang)}  ({on_count}/{len(members)})"):
                toggles = st.container(horizontal=True)
                toggles.button(
                    t("group_all", lang),
                    on_click=set_group,
                    args=(group.key, True),
                    key=f"all_{group.key}",
                )
                toggles.button(
                    t("group_none", lang),
                    on_click=set_group,
                    args=(group.key, False),
                    key=f"none_{group.key}",
                )
                columns = st.columns(3)
                for index, milestone in enumerate(members):
                    with columns[index % 3]:
                        draw_checkbox(milestone)


# --- Eksport -------------------------------------------------------------
#
# Streamlit kører koden i ALLE faneblade ved hver gentegning, også dem man
# ikke ser på. Uden cachen nedenfor blev der bygget en kalenderfil på et par
# hundrede kilobyte, hver gang man satte et flueben et helt andet sted i
# appen. Nu bygges den kun, når indholdet faktisk har ændret sig.


def export_signature(
    items: list[Occasion],
    person: Profile,
    language: str,
    all_day: bool,
    duration_minutes: int,
    alarm_day: bool,
    alarm_hour: bool,
) -> str:
    """Et kort fingeraftryk af alt, der kan ændre filernes indhold."""
    parts = [f"{o.milestone.key}@{o.when_utc.timestamp():.0f}" for o in items]
    parts.append(f"{person.birth_utc.isoformat()}|{person.name}")
    parts.append(f"{person.lifespan_years}|{person.rates!r}|{person.partner_name}")
    parts.append(
        f"{language}|{all_day}|{duration_minutes}|{alarm_day}|{alarm_hour}"
    )
    return hashlib.sha1("\x00".join(parts).encode()).hexdigest()


@st.cache_data(show_spinner=False, max_entries=8)
def export_files(
    signature: str,
    _items: list[Occasion],
    _profile: Profile,
    _lang: str,
    _all_day: bool,
    _duration: int,
    _alarm_day: bool,
    _alarm_hour: bool,
) -> tuple[str, str]:
    """ICS og CSV, bygget én gang pr. fingeraftryk.

    Alt andet end ``signature`` har understreg foran, hvilket er Streamlits
    maade at sige "hash ikke dette argument". Fingeraftrykket staar i stedet
    for dem alle, saa en Occasion-liste ikke skal kunne hashes.
    """
    ics = build_ics(
        _items,
        _profile,
        lang=_lang,
        all_day=_all_day,
        duration_minutes=_duration,
        alarm_days_before=1 if _alarm_day else None,
        alarm_hours_before=1 if _alarm_hour else None,
    )
    csv = build_google_csv(
        _items,
        _profile,
        lang=_lang,
        all_day=_all_day,
        duration_minutes=_duration,
    )
    return ics, csv


with tab_export:
    st.caption(t("export_hint", lang))
    st.caption(t("export_count", lang, n=len(filtered)))

    with st.container(border=True):
        st.subheader(t("export_settings", lang), anchor=False)
        settings = st.container(horizontal=True)
        all_day = settings.checkbox(
            t("all_day", lang), value=False, help=t("all_day_help", lang), key="all_day"
        )
        duration = settings.number_input(
            t("duration", lang), 5, 240, 15, 5, key="duration", disabled=all_day
        )
        alarm_day = settings.checkbox(t("alarm_day", lang), value=True, key="alarm_day")
        alarm_hour = settings.checkbox(t("alarm_hour", lang), value=True, key="alarm_hour")

    if filtered:
        ics_text, csv_text = export_files(
            export_signature(
                filtered, profile, lang, all_day, int(duration), alarm_day, alarm_hour
            ),
            filtered,
            profile,
            lang,
            all_day,
            int(duration),
            alarm_day,
            alarm_hour,
        )

        downloads = st.container(horizontal=True)
        downloads.download_button(
            t("download_ics", lang),
            data=ics_text.encode("utf-8"),
            file_name=suggested_filename(profile, lang, "ics"),
            mime="text/calendar",
            icon=":material/calendar_month:",
            type="primary",
            key="dl_ics",
        )
        downloads.download_button(
            t("download_csv", lang),
            data=csv_text.encode("utf-8"),
            file_name=suggested_filename(profile, lang, "csv"),
            mime="text/csv",
            icon=":material/table:",
            key="dl_csv",
        )
        st.caption(t("csv_hint", lang))

        st.divider()
        st.subheader(t("direct_links", lang), anchor=False)
        st.caption(t("links_hint", lang))
        for occasion in [o for o in filtered if o.when_utc >= now_utc][:10]:
            line = st.container(horizontal=True)
            line.markdown(
                f"{occasion.group.emoji} **{occasion.label}** — "
                f"{fmt.fmt_date_both(occasion.when_local, lang)}"
            )
            line.link_button(
                t("add_to_google", lang),
                google_calendar_link(occasion, profile, lang, int(duration)),
                icon=":material/open_in_new:",
            )
    else:
        st.info(t("no_results", lang), icon=":material/search_off:")


# --- Noter ---------------------------------------------------------------

with tab_notes:
    st.caption(t("notes_hint", lang))
    for key, titles in NOTE_TITLES.items():
        with st.expander(titles[lang]):
            st.markdown(note(key, lang))

    with st.expander("1 000 000 000 s"):
        if lang == "da":
            st.markdown(
                "Et gigasekund er **præcis 11.574 døgn, 1 time, 46 minutter og "
                "40 sekunder**. Hvor mange år det svarer til, afhænger af hvor "
                "mange skudår der falder undervejs — for dig er det "
                f"**{duration_breakdown(1_000_000_000, lang)}** regnet fra din "
                "fødselsdag."
            )
        else:
            st.markdown(
                "One gigasecond is **exactly 11,574 days, 1 hour, 46 minutes and "
                "40 seconds**. How many years that comes to depends on how many "
                "leap days fall along the way — for you it is "
                f"**{duration_breakdown(1_000_000_000, lang)}** counted from your "
                "birthday."
            )


st.divider()
st.caption(t("footer", lang))
