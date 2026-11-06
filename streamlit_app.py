"""Nørdilæum / Nerdiversary — dine næste skæve mærkedage.

Kør appen med:
    streamlit run streamlit_app.py
"""

from __future__ import annotations

import hashlib
import json
import subprocess
import sys
from datetime import date, datetime, time, timedelta, timezone
from pathlib import Path
from zoneinfo import ZoneInfo, available_timezones

import altair as alt
import pandas as pd
import streamlit as st
import streamlit.components.v1 as components
from streamlit_calendar import calendar as fullcalendar

from dateutil.relativedelta import relativedelta

from utils import formatting as fmt
from utils import lifetable as lt
from utils import stardate as sd
from utils import timeline as tl
from utils.catalog import (
    BUNDLES,
    BUNDLES_BY_KEY,
    FAMILIES,
    FAMILIES_BY_KEY,
    FAMILY_OF,
    GROUPS,
    GROUPS_BY_KEY,
    Bundle,
)
from utils.engine import (
    BIRTH_SCOPE,
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
    group_scopes,
    milestones_by_group,
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

# Standardprofilen er en opdigtet person og ikke en rigtig. Den skal vaere
# voksen: et barn paa faa aar har hverken naaet sit gigasekund eller sine
# 10.000 doegn, saa den halve app staar tom, foerste gang nogen aabner den.
DEFAULT_NAME = "Bossie Bossman"
DEFAULT_BIRTH_DATE = date(1981, 6, 3)
DEFAULT_BIRTH_TIME = time(7, 10, 0)

# Og den anden. Gruppen "Jer to" har hele tiden vaeret slaaet til, men den gav
# ingenting, saa laenge feltet stod tomt — saa det, der er appens mest
# overraskende regnestykke, var det, faerrest fik at se. Nu er der nogen i
# feltet fra start.
DEFAULT_PARTNER_NAME = "Chefy Sherif"
DEFAULT_PARTNER_DATE = date(1986, 10, 9)
DEFAULT_PARTNER_TIME = time(12, 23, 30)

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
    "anniversary": "#ad7c1f",
}


# =========================================================================
# Levetidsberegneren
# =========================================================================


def _fetch_lifetables() -> None:
    """Hent doedelighedstavlerne forfra fra DST og Eurostat.

    Hentningen ligger i et selvstaendigt script, og den koeres som sin egen
    proces. Saa kan et netvaerk, der er nede, ikke vaelte appen — det bliver
    en fejlbesked i stedet.
    """
    script = Path(__file__).resolve().parent / "tools" / "fetch_lifetables.py"
    try:
        done = subprocess.run(
            [sys.executable, str(script)],
            capture_output=True,
            text=True,
            timeout=300,
        )
    except (OSError, subprocess.SubprocessError) as problem:
        st.session_state.lifetable_fetch = ("error", str(problem))
        return

    if done.returncode != 0:
        why = done.stderr.strip().splitlines()[-1] if done.stderr.strip() else "?"
        st.session_state.lifetable_fetch = ("error", why[:200])
        return

    # Datafilen er skrevet om, saa det indlaeste skal glemmes.
    lt.load.cache_clear()
    lt.mortality.cache_clear()
    st.session_state.lifetable_fetch = ("ok", len(lt.load().countries))


def _use_lifespan(years: int) -> None:
    """Flyt beregnerens tal over i den antagne levetid.

    Foer skete det af sig selv: skyderen fik tallet som ``value``. Det
    virkede praecis én gang — saa snart ``lifespan`` stod i session state,
    blev ``value`` ignoreret, og skiftede man derefter land eller livsstil,
    rykkede skyderen sig aldrig igen. Nu er flytningen en knap, saa den
    sker, naar man beder om den, og kan ses, naar den sker.
    """
    st.session_state.lifespan = int(years)


def seed_lifespan() -> int:
    """Skyderens startvaerdi: beregnerens tal for standardprofilen.

    Den saettes ÉN gang, foer noget er tegnet. Paa foerste koersel ER
    standardprofilen den, der staar i felterne, saa tallet passer; bagefter
    ejer skyderen det, og knappen i beregneren er vejen til at flytte det.
    """
    catalogue = lt.load()
    if not catalogue.countries:
        return 100
    country = (
        catalogue.default
        if catalogue.default in catalogue.countries
        else catalogue.countries[0]
    )
    age_now = relativedelta(date.today(), DEFAULT_BIRTH_DATE).years
    curve = lt.survival_curve(
        country, lt.SEXES[0], age_now, improvement=lt.IMPROVEMENT
    )
    if not curve:
        return 100
    return int(min(120, max(60, round(age_now + lt.expectancy(curve)))))


# Kurvens farver. Ét datasaet, saa én kuloer — og de er valgt ved at regne
# kontrasten mod den hvide bund ud, ikke ved at kigge paa dem: #1F6F8B
# giver 5,7:1, #5A5A5A 6,9:1 og #8A8A8A 3,5:1, alle over de 3:1, en tynd
# streg skal have. Appens egen koralfarve naaede 2,8:1 og bruges derfor
# ikke til en streg her.
CURVE_INK = "#1F6F8B"
TARGET_INK = "#5A5A5A"
HOVER_INK = "#8A8A8A"
GRID_INK = "#E8E8E8"
TEXT_INK = "#1E1E1E"


def exceedance_chart(
    curve: tuple[float, ...],
    softer: tuple[float, ...] | None,
    age_now: int,
    target: int,
    lang: str,
) -> alt.LayerChart:
    """Overskridelseskurven: chancen for at leve laengere end hver alder.

    Det er praecis den kurve, modulet i forvejen regner paa —
    ``survival_curve`` ER overskridelsessandsynligheden — men som to
    noegletal sagde den ingenting om formen. Tegnet kan man se, hvor stejlt
    det gaar ned, og hvor langt de fire pejlemaerker ligger fra hinanden.

    Baandet er det samme regnestykke med livsstilens virkning sat til det
    halve. Modulet siger selv, at faktorerne overlapper hinanden, saa svaret
    er et spaend — og saa skal spaendet ogsaa kunne ses.
    """
    top = max(lt.last_age_above(curve, age_now) + 1, int(target) + 1)
    ages = list(range(int(age_now), top + 1))

    def pct(from_curve: tuple[float, ...], age: float) -> float:
        return lt.exceedance_at(from_curve, age_now, age) * 100.0

    frame = pd.DataFrame(
        {
            "age": ages,
            "p": [pct(curve, age) for age in ages],
            # Teksten til tooltippet skrives her og ikke i Vega, fordi tallet
            # skal have dansk komma som alle andre tal i appen.
            "age_text": [str(age) for age in ages],
            "p_text": [f"{fmt.fmt_num(pct(curve, age), lang, 1)} %" for age in ages],
        }
    )

    x = alt.X(
        "age:Q",
        title=t("calc_axis_age", lang),
        scale=alt.Scale(domain=[ages[0], ages[-1]], nice=False),
        axis=alt.Axis(format="d", tickMinStep=10, gridColor=GRID_INK),
    )
    # Gitteret ligger paa 10, 50 og 90, saa P90, P50 og P10 falder praecis
    # paa en linje i stedet for at svaeve mellem to.
    y_axis = alt.Axis(
        values=[0, 10, 25, 50, 75, 90, 100],
        labelExpr="datum.value + ' %'",
        gridColor=GRID_INK,
    )
    y = alt.Y(
        "p:Q",
        title=t("calc_axis_p", lang),
        scale=alt.Scale(domain=[0, 100], nice=False),
        axis=y_axis,
    )

    layers: list[alt.Chart] = []

    if softer is not None:
        spans = [sorted((pct(curve, age), pct(softer, age))) for age in ages]
        band = pd.DataFrame(
            {"age": ages, "lo": [s[0] for s in spans], "hi": [s[1] for s in spans]}
        )
        layers.append(
            alt.Chart(band)
            .mark_area(color=CURVE_INK, opacity=0.14)
            .encode(
                x=x,
                y=alt.Y(
                    "lo:Q",
                    title=t("calc_axis_p", lang),
                    scale=alt.Scale(domain=[0, 100], nice=False),
                    axis=y_axis,
                ),
                y2="hi:Q",
            )
        )

    # Skyderens alder som en lodret streg — med sit svar skrevet paa.
    # Stregen alene sagde kun, HVOR man spurgte, ikke hvad svaret var, og
    # saa skulle man laese procenten i saetningen under plottet i stedet
    # for dér, hvor man i forvejen kiggede.
    #
    # Prikken og tallet er i blaek og ikke i kurvens kuloer: det er din
    # markoer og ikke et femte pejlemaerke.
    target_p = pct(curve, target)
    aimed = pd.DataFrame(
        [
            {
                "age": int(target),
                "p": target_p,
                "label": f"{fmt.fmt_num(target_p, lang, 1)} %",
            }
        ]
    )
    layers.append(
        alt.Chart(aimed).mark_rule(color=TARGET_INK, strokeWidth=1.5).encode(x=x)
    )
    layers.append(
        alt.Chart(frame).mark_line(color=CURVE_INK, strokeWidth=2).encode(x=x, y=y)
    )
    layers.append(
        alt.Chart(aimed)
        .mark_point(
            size=110, filled=True, color=TARGET_INK, stroke="white", strokeWidth=2
        )
        .encode(x=x, y=y)
    )
    layers.append(
        alt.Chart(aimed)
        .mark_text(
            align="right", dx=-11, dy=-13, fontWeight="bold", fontSize=12,
            color=TARGET_INK,
        )
        .encode(x=x, y=y, text="label:N")
    )

    # De fire pejlemaerker. P90 er den alder, ni ud af ti overskrider, og
    # P10 den, kun én ud af ti goer: i et overskridelsesplot er tallet
    # sandsynligheden og ikke fraktilen, saa P90 er den lave alder.
    #
    # Hver etiket peger sin egen vej. De blev foerst tegnet i ét lag med én
    # forskydning, og saa laa "P50" oven i "Pmean" — de to ligger kun otte
    # procentpoint fra hinanden — mens "Pmean" samtidig haengte ud over
    # hoejre kant af feltet. De to i midten peger derfor hver sin vej, og
    # P10 peger indad, fordi den ligger yderst til hoejre.
    mean_age = age_now + lt.expectancy(curve)
    spots = (
        ("P90", lt.age_at_quantile(curve, age_now, 0.10), 90.0, "left", 10, -8),
        ("P50", lt.age_at_quantile(curve, age_now, 0.50), 50.0, "left", 10, 16),
        ("Pmean", mean_age, pct(curve, mean_age), "right", -10, -8),
        ("P10", lt.age_at_quantile(curve, age_now, 0.90), 10.0, "right", -10, -8),
    )

    layers.append(
        alt.Chart(
            pd.DataFrame([{"age": spot[1], "p": spot[2]} for spot in spots])
        )
        .mark_point(
            size=110, filled=True, color=CURVE_INK, stroke="white", strokeWidth=2
        )
        .encode(x=x, y=y)
    )
    for label, age, share, align, dx, dy in spots:
        layers.append(
            alt.Chart(pd.DataFrame([{"age": age, "p": share, "label": label}]))
            .mark_text(
                align=align, dx=dx, dy=dy, fontWeight="bold", fontSize=12,
                color=TEXT_INK,
            )
            .encode(x=x, y=y, text="label:N")
        )

    # Musen skal kun ramme den rigtige ALDER, ikke selve stregen: Vega
    # laegger et naermeste-punkt-net ud over feltet, saa markoeren bare skal
    # vaere taettest paa.
    hover = alt.selection_point(
        name="peek",
        nearest=True,
        on="pointerover",
        fields=["age"],
        empty=False,
        clear="pointerout",
    )
    layers.append(
        alt.Chart(frame)
        .mark_point()
        .encode(
            x=x,
            opacity=alt.value(0),
            tooltip=[
                alt.Tooltip("age_text:N", title=t("calc_axis_age", lang)),
                alt.Tooltip("p_text:N", title=t("calc_axis_p", lang)),
            ],
        )
        .add_params(hover)
    )
    layers.append(
        alt.Chart(frame)
        .mark_rule(color=HOVER_INK, strokeWidth=1)
        .encode(x=x)
        .transform_filter(hover)
    )
    layers.append(
        alt.Chart(frame)
        .mark_point(
            size=120, filled=True, color=CURVE_INK, stroke="white", strokeWidth=2
        )
        .encode(x=x, y=y)
        .transform_filter(hover)
    )

    return (
        alt.layer(*layers)
        .properties(height=300)
        .configure_view(strokeWidth=0)
        .configure_axis(
            domainColor=GRID_INK,
            tickColor=GRID_INK,
            labelColor=TARGET_INK,
            titleColor=TARGET_INK,
            labelFontSize=11,
            titleFontSize=11,
        )
    )


def life_expectancy_panel(birth: date, lang: str) -> None:
    """Levetidsberegneren, med overskridelseskurven.

    Den laa i sidepanelet under "Antagelser og rater", side om side med
    skyderne for puls og skridt pr. doegn. Det var forkert paa to maader:
    den er ikke en antagelse, man skruer paa, men et svar, man laeser — og
    den er det mest omfangsrige i appen, gemt bag to klik i en skuffe. Nu
    staar den under sekundtaelleren, foldet sammen, hvor man kan se, at den
    er der.
    """
    with st.expander(t("calc_title", lang), icon=":material/stacked_line_chart:"):
        note = st.session_state.pop("lifetable_fetch", None)
        if note and note[0] == "ok":
            st.success(
                t("calc_refreshed", lang, n=note[1]), icon=":material/check_circle:"
            )
        elif note:
            st.error(t("calc_refresh_failed", lang, why=note[1]))

        catalogue = lt.load()
        if not catalogue.countries:
            st.info(t("calc_no_data", lang))
            st.button(
                t("calc_refresh", lang),
                on_click=_fetch_lifetables,
                help=t("calc_refresh_help", lang),
                key="calc_refresh_empty",
            )
            return

        st.caption(t("calc_intro", lang))

        countries = catalogue.countries
        start = countries.index(catalogue.default) if catalogue.default in countries else 0
        who = st.container(horizontal=True)
        country = who.selectbox(
            t("calc_country", lang),
            countries,
            index=start,
            format_func=lambda code: catalogue.name(code, lang),
            key="calc_country",
        )
        sex = who.radio(
            t("calc_sex", lang),
            lt.SEXES,
            horizontal=True,
            format_func=lambda code: t(f"calc_sex_{code}", lang),
            key="calc_sex",
        )

        table = catalogue.get(country, sex)
        age_now = relativedelta(date.today(), birth).years
        if table is None or age_now < 0:
            st.info(t("calc_no_data", lang))
            return

        st.caption(t("calc_lifestyle", lang))
        choices: dict[str, str] = {}
        knobs = st.container(horizontal=True)
        for factor in lt.FACTORS:
            choices[factor.key] = knobs.selectbox(
                factor.name(lang),
                [level.key for level in factor.levels],
                format_func=lambda key, chosen=factor: chosen.level(key).name(lang),
                help=factor.source,
                key=f"calc_{factor.key}",
            )

        hazard = lt.combined_hazard(choices)
        period = lt.survival_curve(country, sex, age_now, hazard=hazard)
        cohort = lt.survival_curve(
            country, sex, age_now, improvement=lt.IMPROVEMENT, hazard=hazard
        )
        period_age = age_now + lt.expectancy(period)
        cohort_age = age_now + lt.expectancy(cohort)

        tiles = st.container(horizontal=True)
        tiles.metric(
            t("calc_period", lang),
            fmt.fmt_num(period_age, lang, 1),
            help=t("calc_period_help", lang),
        )
        tiles.metric(
            t("calc_cohort", lang),
            fmt.fmt_num(cohort_age, lang, 1),
            help=t(
                "calc_cohort_help",
                lang,
                pct=fmt.fmt_num(lt.IMPROVEMENT * 100, lang, 1),
            ),
        )

        # Faktorerne overlapper hinanden, saa produktet overdriver. Det
        # uddaempede tal er den samme udregning med halv kraft, og de to
        # spaender svaret ud i stedet for at foregive en praecision.
        softer: tuple[float, ...] | None = None
        if abs(hazard - 1.0) > 1e-9:
            softer = lt.survival_curve(
                country,
                sex,
                age_now,
                improvement=lt.IMPROVEMENT,
                hazard=lt.damped(hazard),
            )
            span = sorted((cohort_age, age_now + lt.expectancy(softer)))
            st.markdown(
                t(
                    "calc_lifestyle_span",
                    lang,
                    low=fmt.fmt_num(span[0], lang, 1),
                    high=fmt.fmt_num(span[1], lang, 1),
                )
            )

        # --- Kurven -------------------------------------------------------
        #
        # Skyderen tegnes FOER kurven, fordi kurven skal vise, hvor den
        # staar. Den er samtidig den vej til det samme tal, der ikke
        # kraever en mus: et tooltip maa gerne vaere en genvej, men det maa
        # ikke vaere den eneste adgang til et tal.
        target = st.slider(
            t("calc_reach", lang),
            min_value=age_now + 1,
            max_value=110,
            value=min(110, max(age_now + 1, 90)),
            key="calc_target",
        )
        st.altair_chart(
            exceedance_chart(cohort, softer, age_now, target, lang),
            width="stretch",
        )
        st.caption(t("calc_curve_help", lang))
        if softer is not None:
            st.caption(t("calc_band", lang))

        st.markdown(
            t(
                "calc_reach_result",
                lang,
                age=target,
                pct=fmt.fmt_num(
                    lt.exceedance_at(cohort, age_now, target) * 100, lang, 1
                ),
            )
        )

        # De fire tal staar ogsaa skrevet. Kurven er den hurtige vej, men
        # den skal ikke vaere den eneste.
        mean_age = age_now + lt.expectancy(cohort)
        marks = st.container(horizontal=True)
        marks.metric(
            t("calc_p90", lang),
            fmt.fmt_num(lt.age_at_quantile(cohort, age_now, 0.10), lang, 1),
            help=t("calc_p90_help", lang),
        )
        marks.metric(
            t("calc_p50", lang),
            fmt.fmt_num(lt.age_at_quantile(cohort, age_now, 0.50), lang, 1),
            help=t("calc_p50_help", lang),
        )
        marks.metric(
            t("calc_pmean", lang),
            fmt.fmt_num(mean_age, lang, 1),
            help=t("calc_pmean_help", lang),
        )
        marks.metric(
            t("calc_p10", lang),
            fmt.fmt_num(lt.age_at_quantile(cohort, age_now, 0.90), lang, 1),
            help=t("calc_p10_help", lang),
        )
        st.caption(
            t(
                "calc_pmean_note",
                lang,
                age=fmt.fmt_num(mean_age, lang, 1),
                pct=fmt.fmt_num(
                    lt.exceedance_at(cohort, age_now, mean_age) * 100, lang, 1
                ),
            )
        )

        # --- Ud i resten af appen -----------------------------------------
        suggested = int(min(120, max(60, round(cohort_age))))
        st.button(
            t("calc_use", lang, years=suggested),
            icon=":material/arrow_outward:",
            on_click=_use_lifespan,
            args=(suggested,),
            key="calc_use",
        )
        st.caption(t("calc_use_now", lang, years=st.session_state.lifespan))

        st.button(
            t("calc_refresh", lang),
            on_click=_fetch_lifetables,
            help=t("calc_refresh_help", lang),
            key="calc_refresh",
        )

        st.caption(
            f"{t('calc_source', lang)}: {table.source} · "
            f"{t('calc_fetched', lang, date=catalogue.fetched)}"
        )
        st.caption(t("calc_caveat", lang))


# =========================================================================
# Sidepanel
# =========================================================================

# Skyderens startvaerdi er beregnerens tal og ikke et rundt hundrede. Den
# saettes her, foer en eneste widget er tegnet, saa skyderen kan noejes med
# sin ``key`` og slippe for et ``value``, Streamlit alligevel ignorerer,
# saa snart noeglen staar i session state.
st.session_state.setdefault("lifespan", seed_lifespan())

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
        value=DEFAULT_NAME,
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
        use_pair = st.checkbox(t("pair_use", lang), value=True, key="use_pair")
        partner_name = st.text_input(
            t("pair_name", lang),
            value=DEFAULT_PARTNER_NAME,
            placeholder=t("name_placeholder", lang),
            disabled=not use_pair,
            key="partner_name",
        )
        partner_date = st.date_input(
            t("pair_date", lang),
            value=DEFAULT_PARTNER_DATE,
            min_value=date(1900, 1, 1),
            max_value=date.today(),
            format="DD.MM.YYYY",
            disabled=not use_pair,
            key="partner_date",
        )
        partner_time = st.time_input(
            t("pair_time", lang),
            value=DEFAULT_PARTNER_TIME,
            step=1,
            help=t("pair_time_help", lang),
            disabled=not use_pair,
            key="partner_time",
        )

    with st.expander(t("assumptions", lang), icon=":material/tune:"):
        # Her staar kun det, man selv skruer paa. Levetidsberegneren laa
        # ogsaa her og fyldte skuffen; den staar nu under sekundtaelleren,
        # hvor den kan ses, og den har en knap, der flytter sit tal herind.
        lifespan = st.slider(
            t("lifespan", lang),
            min_value=60,
            max_value=120,
            step=1,
            help=t("lifespan_help", lang),
            key="lifespan",
        )
        # Hundrede er standarden, fordi det er den graense, resten af appen
        # allerede regner med: den antagne levetid staar paa hundrede, og
        # Jordens historie og tidslinjen skalerer efter den. Stod den paa
        # hundrede og halvtreds, regnede appen halvtreds aar ud over et liv,
        # som den selv ikke tror paa — og tidslinjen fik en tom hale.
        max_age = st.slider(
            t("max_age", lang), min_value=80, max_value=150, value=100, step=5, key="max_age"
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


# Valget ligger i ét sæt, der overlever, at en mærkedag ikke er synlig.
# Det er nødvendigt, fordi valgtabellen kun viser det, gruppefilteret og
# søgefeltet har sluppet igennem: et valg, der kun lå i widgetnøglerne,
# ville gå tabt hver gang man søgte.
#
# Sættet er kilden. Tabellen læser fra det, når den tegnes, og skriver
# tilbage gennem ``_apply_table_edits``, når nogen sætter et flueben.
seen_keys: set[str] = st.session_state.setdefault("seen_keys", set())
chosen: set[str] = st.session_state.setdefault("chosen", set())

# Samme løkke klarer både første kørsel og det tilfælde, at kataloget er
# vokset siden sidst — en ny gruppe følger sin egen standardindstilling.
for milestone in CATALOGUE:
    if milestone.key not in seen_keys:
        seen_keys.add(milestone.key)
        if DEFAULT_ON.get(milestone.group, True):
            chosen.add(milestone.key)


def _set_keys(keys, value: bool) -> None:
    """Sæt en hel flok på én gang.

    Kun det varige sæt røres. Valgtabellen læser sættet, hver gang den
    tegnes, så den viser svaret af sig selv.
    """
    if value:
        st.session_state.chosen.update(keys)
    else:
        st.session_state.chosen.difference_update(keys)


selected_keys = {m.key for m in CATALOGUE if m.key in chosen}
occasions = compute(profile, keys=selected_keys, lang=lang, max_age_years=float(max_age))


# =========================================================================
# De to kontroller, der staar to steder
# =========================================================================
#
# Gruppevalget og niveauet hoerer logisk til i Vaelg-fanen — de afgoer, hvad
# der overhovedet er med. Men man vil ogsaa kunne naa dem uden at skifte
# faneblad, og derfor staar gruppevalget BEGGE steder.
#
# To widgets kan ikke dele én noegle i Streamlit. Derfor er sandheden et sæt
# i session state, og hver widget er kun et vindue ind til det: tilstanden
# saettes fra saettet, lige foer widgeten tegnes, og ``_sync_groups`` foerer
# svaret tilbage, naar nogen aendrer den ene. Saa kan de to aldrig komme til
# at modsige hinanden — og det kunne de foer, hvor de var to uafhaengige
# filtre, der hed naesten det samme.
GROUP_KEYS: tuple[str, ...] = tuple(g.key for g in GROUPS)
groups_on: set[str] = st.session_state.setdefault("groups_on", set(GROUP_KEYS))
# En ny gruppe i kataloget er taendt fra start, som den altid har vaeret.
groups_on |= {key for key in GROUP_KEYS if key not in st.session_state.setdefault(
    "groups_seen", set())}
st.session_state.groups_seen.update(GROUP_KEYS)

# --- Hvad vaelgeren viser -------------------------------------------------
#
# Fyrre grupper som chips i et flervalgsfelt var 862 tegn i et felt paa
# tres: det scrollede sidelaens, den ufiltrerede tilstand var den mest
# stoejende, og skulle man beholde tre grupper, skulle syvogtredive kryds
# rammes ét ad gangen.
#
# Nu staar de som knapper i en popover, delt i de samme to hylder som
# pakkerne, og de ni talmoensterfamilier staar som ÉN knap med de enkelte
# bag en udfoldning. Det bringer fyrre kontakter ned paa toogtredive, og
# ingen af dem skal rammes paa et lille kryds.

PICKER_BY_SCOPE: dict[str, list[str]] = {scope: [] for scope in SCOPES}
for _group in GROUPS:
    _family = FAMILY_OF.get(_group.key)
    _entry = _family or _group.key
    _shelf = PICKER_BY_SCOPE[group_scopes().get(_group.key, BIRTH_SCOPE)]
    if _entry not in _shelf:
        _shelf.append(_entry)


def option_groups(option: str) -> tuple[str, ...]:
    """Grupperne bag ét punkt i vælgeren — familien eller gruppen selv."""
    family = FAMILIES_BY_KEY.get(option)
    return family.groups if family else (option,)


def option_label(option: str) -> str:
    """Navnet på punktet, med tal nok til at kunne skimmes.

    En familie viser, hvor mange af sine grupper der er tændt, men kun når
    den er delt — ellers er tallet kun støj. En enkelt gruppe viser, hvor
    mange mærkedage den rummer, fordi 🎊 Runde årsdage er 624 og 🎰
    Repunitdage er 3, og det kunne man ikke se før.
    """
    family = FAMILIES_BY_KEY.get(option)
    if family is None:
        count = len(milestones_by_group().get(option, []))
        return f"{GROUPS_BY_KEY[option].title(lang)} · {count}"
    inside = sum(1 for key in family.groups if key in st.session_state.groups_on)
    if inside in (0, len(family.groups)):
        return family.title(lang)
    return f"{family.title(lang)} · {inside}/{len(family.groups)}"


def _sync_picker(widget_key: str) -> None:
    """Flyt knappernes svar over i det sæt, hele appen læser fra.

    Kun det, der FAKTISK blev ændret, røres. Det er ikke pedanteri: en
    familie, hvor fire af ni er tændt, står ikke som valgt, og skrev vi hele
    valget ned i ét hug, ville den blive slukket, hver gang man rørte en
    helt anden knap.
    """
    before = set(st.session_state.get(f"{widget_key}__before", ()))
    after = set(st.session_state[widget_key])
    for option in after - before:
        st.session_state.groups_on.update(option_groups(option))
    for option in before - after:
        st.session_state.groups_on.difference_update(option_groups(option))


def _set_groups(keys, value: bool) -> None:
    if value:
        st.session_state.groups_on.update(keys)
    else:
        st.session_state.groups_on.difference_update(keys)


def draw_pills(options: list[str], widget_key: str) -> None:
    """Én række knapper, bundet til ``groups_on``.

    Tilstanden sættes her og ikke med ``default``. Gav vi begge dele, ville
    Streamlit advare med et helt stakspor — se ``_apply_table_edits``.
    """
    picked = [
        option
        for option in options
        if all(key in st.session_state.groups_on for key in option_groups(option))
    ]
    st.session_state[widget_key] = picked
    st.session_state[f"{widget_key}__before"] = list(picked)
    st.pills(
        widget_key,
        options=options,
        selection_mode="multi",
        format_func=option_label,
        key=widget_key,
        on_change=_sync_picker,
        args=(widget_key,),
        label_visibility="collapsed",
    )


def draw_group_picker(parent, slug: str, help_text: str) -> None:
    """Gruppevælgeren, som den står begge steder.

    Lukket er den én knap med tallet på. Det er hele pointen: tilstanden
    "jeg filtrerer ingenting" skal være den roligste, og det var den stik
    modsatte, da alle fyrre stod som chips.
    """
    on_count = len(st.session_state.groups_on)
    label = t("groups_button", lang, n=on_count, total=len(GROUP_KEYS))
    # Bredden er sat i punkter og ikke overladt til indholdet: den vandrette
    # beholder klemmer ellers knappen sammen, saa der staar "Grupper 40…".
    with parent.popover(label, help=help_text, width=190):
        for scope, options in PICKER_BY_SCOPE.items():
            if not options:
                continue
            inside = [key for option in options for key in option_groups(option)]
            st.caption(
                f"**{t(f'scope_{scope}', lang)}** — "
                f"{sum(1 for k in inside if k in st.session_state.groups_on)}"
                f"/{len(inside)}"
            )
            toggles = st.container(horizontal=True)
            toggles.button(
                t("group_all", lang), key=f"{slug}_{scope}_all",
                on_click=_set_groups, args=(inside, True),
            )
            toggles.button(
                t("group_none", lang), key=f"{slug}_{scope}_none",
                on_click=_set_groups, args=(inside, False),
            )
            draw_pills(options, f"{slug}_{scope}_pills")

        # Finjusteringen. Den er foldet sammen, fordi den sjaeldent skal
        # bruges — men den skal findes, for ellers kunne man ikke slaa
        # palindromerne til uden ogsaa at faa de 108 binaere dage.
        for family in FAMILIES:
            with st.expander(t("family_detail", lang, name=family.name(lang))):
                draw_pills(list(family.groups), f"{slug}_{family.key}_pills")


# Niveauet huskes her og saettes i widgeten, lige foer den tegnes. Ellers
# nulstiller Streamlit den til foerste trin, naar sproget skifter, fordi
# etiketten er en del af widgetens identitet.
st.session_state.setdefault("level_cap", 2)


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
def live_age_panel() -> None:
    """Alderen, der tikker uden at genberegne resten af siden."""
    now = datetime.now(timezone.utc)
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

        # Kun skudsekunderne staar tilbage her. Unix-tiden lige nu,
        # foedselsstemplet og stjernedatoen er taget ud: de to foerste er
        # raatal, man laeser én gang, og alle tre skubbede det, der faktisk
        # tikker, ned ad skaermen. Stjernedatoen staar fortsat som kolonne
        # i listen, hvor den hoerer til hver enkelt maerkedag.
        st.metric(
            t("leap_seconds", lang),
            leap_seconds_since_birth(profile.birth_utc, now),
            help=t("leap_help", lang),
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


@st.fragment(run_every="1s")
def live_next_panel() -> None:
    """Det naeste, der sker.

    Egen fragment, saa levetidsfeltet kan ligge mellem de to uden at blive
    tegnet om hvert sekund — en kurve, der blinker én gang i sekundet, kan
    man ikke holde musen hen over.
    """
    now = datetime.now(timezone.utc)
    now_local = now.astimezone(tz)

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


live_age_panel()

# Levetiden staar mellem de to: lige under sekundtaelleren, hvor spoergsmaalet
# "hvor mange af dem faar jeg?" melder sig af sig selv.
life_expectancy_panel(birth_date, lang)

live_next_panel()


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
#
# Her staar kun det, der handler om UDSNITTET: hvilket stykke af dit liv du
# kigger paa lige nu. Hvad der overhovedet er med, bestemmes i Vaelg-fanen.
# De to spoergsmaal var foer blandet sammen over to raekker og et faneblad,
# og saa kunne listen staa tom af tre forskellige grunde uden at sige hvilken.
#
# Gruppevalget er det eneste, der staar begge steder, fordi man skal kunne
# daempe en hel gruppe uden at skifte faneblad. Det er den SAMME vaelger —
# se ``draw_group_picker``.

with st.container(border=True):
    st.caption(t("filters_scope", lang).upper())
    row = st.container(horizontal=True)
    draw_group_picker(row, "filter", t("filter_groups_help", lang))
    row.selectbox(
        t("filter_window", lang),
        options=["all", "1", "5", "10", "25"],
        format_func=lambda key: t(f"window_{key}", lang),
        key="filter_window",
    )
    window = st.session_state.filter_window

    # Niveauet staar HER, sammen med alt det andet, der skjuler noget.
    #
    # Det laa i Vaelg-fanen, fordi det foeltes som et spoergsmaal om, hvad
    # der er med. Men niveauet aendrer ikke ``chosen`` — det skjuler, helt
    # som gruppefilteret — og stod man paa Liste og saa "Viser 245", var der
    # intet paa skaermen, der forklarede hvorfor. Den skjulte kontakt med
    # den synlige virkning er netop den fejl, vi lige havde rettet ét sted.
    #
    # At den staar her, fjerner ogsaa et stykke maskineri: vaerdien blev
    # laest i toppen af koerslen og widgeten tegnet langt senere, og de to
    # kunne komme ud af trit. Nu tegnes den, foer noget filtreres.
    st.session_state["level_widget"] = int(st.session_state.level_cap)
    level_cap = int(
        row.select_slider(
            t("filter_level", lang),
            options=[1, 2, 3],
            format_func=lambda n: t(f"level_{n}", lang),
            help=t("filter_level_help", lang),
            key="level_widget",
        )
    )
    st.session_state.level_cap = level_cap

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
    # ÉT soegefelt. Der var to, der hed naesten det samme og brugte "maane"
    # i begge eksempler. Dette ene skaerer baade i det, du kigger paa, og i
    # valgtabellen — og i tabellen leder det i HELE kataloget, saa man kan
    # finde noget, man endnu ikke har valgt.
    query = second_row.text_input(
        t("search", lang),
        placeholder=t("search_placeholder", lang),
        help=t("search_help", lang),
        key="query",
    )
    needle = query.strip().lower()

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


def apply_scope_filters(items: list[Occasion]) -> list[Occasion]:
    """Hvilke mærkedage der er tale om — uden noget om hvornår.

    Delt ud fra ``apply_filters``, fordi tidslinjen skal vise hele livet.
    En tidslinje, der kun gik fremad, ville mangle halvdelen af pointen og
    hele "du er her"; men gruppevalget og fritekstsøgningen skal naturligvis
    gælde den også.
    """
    out = [
        o
        for o in items
        if o.milestone.group in st.session_state.groups_on
        and o.milestone.level <= level_cap
    ]
    if needle:
        out = [o for o in out if matches_search(o.milestone, needle)]
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


def narrowing_note(*, in_table: bool = False) -> str:
    """Hvad der er skruet ned ad lige nu, som én laesbar linje.

    "Viser 245 maerkedage" og "Ingen maerkedage matcher filtrene" sagde
    ingenting om HVILKE filtre, og saa var der ikke andet at goere end at
    proeve sig frem. Linjen staar nu under hver eneste taelling — liste,
    kalender, tidslinje, eksport og valgtabellen — og er den samme saetning
    alle fem steder.
    """
    parts: list[str] = []
    if level_cap < 3:
        parts.append(t("narrowed_level", lang, level=t(f"level_{level_cap}", lang)))
    if len(st.session_state.groups_on) < len(GROUP_KEYS):
        parts.append(
            t("narrowed_groups", lang, n=len(st.session_state.groups_on),
              total=len(GROUP_KEYS))
        )
    if needle:
        parts.append(t("narrowed_search", lang, needle=query.strip()))
    if in_table:
        # Tabellen viser hele kataloget og rammes derfor ikke af "hvornaar"
        # og "tidsrum" — men den har sin egen til/fra.
        if st.session_state.get("only_chosen"):
            parts.append(t("narrowed_only_chosen", lang))
    else:
        if when_filter != "both":
            parts.append(
                t("narrowed_when", lang,
                  when=t("only_future" if when_filter == "future" else "only_past", lang))
            )
        if window != "all":
            parts.append(t("narrowed_window", lang, window=t(f"window_{window}", lang)))
    return "  ·  ".join(parts)


def with_note(line: str, *, in_table: bool = False) -> str:
    note = narrowing_note(in_table=in_table)
    return f"{line}  ·  {note}" if note else line


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
                # Stjernedatoen havde sin egen tekst i ordlisten, men var
                # faldet ud af tabellen undervejs. Den er her igen, fordi den
                # er præcis den slags oplysning, appen findes for — og fordi
                # en ubrugt tekst er en halvfærdig tanke.
                t("col_stardate", lang): sd.format_tng(occasion.when_local),
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
        st.info(with_note(t("no_results", lang)), icon=":material/search_off:")
    else:
        st.caption(with_note(t("showing_n", lang, n=len(filtered))))
        st.dataframe(
            to_frame(filtered),
            hide_index=True,
            height=560,
            column_config={
                t("col_milestone", lang): st.column_config.TextColumn(width="medium"),
                t("col_estimate", lang): st.column_config.TextColumn(
                    width="small", help=t("estimate_help", lang)
                ),
                t("col_stardate", lang): st.column_config.TextColumn(
                    width="small", help=t("stardate_help", lang)
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
        st.info(with_note(t("calendar_empty", lang)), icon=":material/event_busy:")
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
        st.info(with_note(t("tl_empty", lang)), icon=":material/timeline:")
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


def apply_bundle(bundle_key: str) -> None:
    """Slå en færdigpakket udvælgelse til — oven i det, der er valgt i forvejen.

    Pakken erstattede før hele valget, og det var en ubehagelig knap: ét
    klik slettede stille alt, man havde sat op, og der var ingen fortrydelse.
    Man kunne heller ikke få Klassikere OG Popkultur — det andet klik smed
    det første væk.

    Nu lægger den til. Vil man starte forfra, er "Ryd alle" lige ved siden af
    og siger netop det, den gør.
    """
    bundle = BUNDLES_BY_KEY[bundle_key]
    wanted = bundle_keys(bundle, profile, datetime.now(timezone.utc))
    before = len(st.session_state.chosen)
    _set_keys(wanted, True)
    added = len(st.session_state.chosen) - before
    st.session_state.last_bundle = (bundle.name(lang), len(wanted), added)


# =========================================================================
# Vælg mærkedage
# =========================================================================
#
# Kataloget står i ÉN tabel, ikke i halvandet tusind afkrydsningsfelter.
#
# Det er ikke en smagssag. Streamlit bygger indholdet i ALLE faneblade, hver
# gang siden tegnes — også de faneblade, man ikke ser på. Med ét felt pr.
# mærkedag udgjorde denne fane 5.324 af sidens 6.209 elementer og 15.884 af
# dens 18.303 DOM-knuder, og appen var sytten sekunder om at åbne. Vi havde
# oven i købet måttet sætte et loft på syv hundrede felter, og det betød, at
# over tusind mærkedage slet ikke kunne vælges enkeltvis.
#
# Én ``st.data_editor`` er én widget, uanset om den har tre eller tre tusind
# rækker, og den ruller, sorterer og kan søges i af sig selv. Loftet er væk,
# og hele kataloget kan vælges.

PICK, GROUP_COL, NAME_COL, WHY_COL = "pick", "group", "name", "why"


def _apply_table_edits(table_key: str) -> None:
    """Flyt tabellens rettelser over i det varige valg.

    ``st.data_editor`` leverer kun de celler, der faktisk blev rettet, med
    rækkens nummer som nøgle. Rækkefølgen ligger i session state ved siden
    af tabellen, og tabellens egen nøgle skifter, når rækkerne skifter — så
    et gammelt rækkenummer aldrig kan ramme en ny mærkedag.
    """
    state = st.session_state.get(table_key)
    edited = state.get("edited_rows", {}) if isinstance(state, dict) else {}
    order = st.session_state.get(f"{table_key}__order", [])
    for row, changes in edited.items():
        if PICK not in changes:
            continue
        try:
            key = order[int(row)]
        except (IndexError, ValueError, TypeError):
            continue
        if changes[PICK]:
            st.session_state.chosen.add(key)
        else:
            st.session_state.chosen.discard(key)


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
        st.markdown(f"**{t(f'scope_{scope}', lang)}**")
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
        name, total, added = applied
        st.success(
            t("bundle_applied", lang, name=name, n=total, added=added),
            icon=":material/check_circle:",
        )

    st.divider()
    st.caption(t("select_hint", lang))
    st.markdown(
        t("selected_count", lang, n=len(selected_keys), total=len(CATALOGUE))
    )

    # Her staar KUN det, der aendrer dit valg. Alt, der blot skjuler —
    # niveau, grupper, tid, soegning — staar i Udsnit-raekken foroven og
    # gaelder ogsaa tabellen hernede. Det er hele skellet mellem de to
    # steder, og det var det, der manglede: en skydeknap i denne fane
    # skar i en liste paa en helt anden fane, uden at nogen kunne se det.
    #
    # Den ene undtagelse hoerer til her, fordi den kun handler om tabellen.
    only_chosen = st.toggle(
        t("only_chosen", lang),
        key="only_chosen",
        help=t("only_chosen_help", lang),
    )

    pool = [
        m
        for m in CATALOGUE
        if m.level <= level_cap and m.group in st.session_state.groups_on
    ]
    if only_chosen:
        pool = [m for m in pool if m.key in chosen]
    if needle:
        pool = [m for m in pool if matches_search(m, needle)]

    if not pool:
        st.info(
            with_note(t("select_no_matches", lang), in_table=True),
            icon=":material/search_off:",
        )
    else:
        shown_keys = [m.key for m in pool]
        picked_here = sum(1 for key in shown_keys if key in chosen)
        st.caption(
            with_note(
                t("select_showing", lang, n=len(pool), picked=picked_here),
                in_table=True,
            )
        )
        sweep = st.container(horizontal=True)
        sweep.button(
            t("shown_all", lang),
            icon=":material/select_all:",
            on_click=_set_keys,
            args=(shown_keys, True),
            key="btn_shown_all",
        )
        sweep.button(
            t("shown_none", lang),
            icon=":material/deselect:",
            on_click=_set_keys,
            args=(shown_keys, False),
            key="btn_shown_none",
        )

        # Tabellens noegle foelger raekkerne. Skifter filteret, er det en ny
        # widget, og ``edited_rows`` starter forfra — ellers kunne en gammel
        # rettelse til "raekke 5" ramme en helt anden maerkedag.
        digest = hashlib.sha1(
            "\x00".join([lang] + shown_keys).encode()
        ).hexdigest()[:12]
        table_key = f"select_table_{digest}"
        st.session_state[f"{table_key}__order"] = shown_keys

        st.data_editor(
            pd.DataFrame(
                {
                    PICK: [key in chosen for key in shown_keys],
                    # ``title`` har allerede gruppens emoji foran sig.
                    GROUP_COL: [
                        GROUPS_BY_KEY[m.group].title(lang) for m in pool
                    ],
                    NAME_COL: [build_label(m, profile, lang) for m in pool],
                    WHY_COL: [explanation(m, lang) for m in pool],
                }
            ),
            key=table_key,
            on_change=_apply_table_edits,
            args=(table_key,),
            hide_index=True,
            height=520,
            disabled=[GROUP_COL, NAME_COL, WHY_COL],
            column_config={
                PICK: st.column_config.CheckboxColumn(
                    t("col_pick", lang), width="small"
                ),
                GROUP_COL: st.column_config.TextColumn(
                    t("col_group", lang), width="small"
                ),
                NAME_COL: st.column_config.TextColumn(
                    t("col_milestone", lang), width="medium"
                ),
                WHY_COL: st.column_config.TextColumn(
                    t("col_why", lang), width="large"
                ),
            },
        )


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
    st.caption(with_note(t("export_count", lang, n=len(filtered))))

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
