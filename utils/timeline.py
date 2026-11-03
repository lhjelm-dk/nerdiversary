"""Tidslinjen: kaskadevisningen og den logaritmiske skala.

390 maerkedage ligger meget ujaevnt i et liv. Det foerste million sekunder
falder paa dag 11, mens det foerste gigasekund foerst kommer ved 31 aar — og
sidst i livet kan der gaa ti aar mellem to maerkedage. En almindelig, lineaer
tidslinje over hundrede aar bliver derfor en sort stribe i barndommen og tom
bagefter. En skydeknap flytter det problem; den loeser det ikke.

Derfor er her to skalaer, og begge gaar lige til roden af det:

* **Kaskaden** er den geologiske tidsskalas opbygning: faa raekker over
  hinanden, hvor hver raekke zoomer ind paa et udsnit af raekken over, som
  Æon → Æra → Periode → Epoke → Alder. Man ser helheden og detaljen paa samme
  tid uden at traekke i noget.
* **Den logaritmiske skala** saetter aksen i tierpotenser fra foedslen. Saa
  ligger 10⁶, 10⁷, 10⁸ og 10⁹ sekunder lige langt fra hinanden, og hele livet
  fra foerste sekund til 150 aar staar paa én skaerm uden at klumpe sammen.
  Det virker, fordi kataloget i forvejen er bygget paa tierpotenser.

Modulet tegner ren SVG. Det er valgt, fordi etiketterne skal placeres i baner
med henvisningslinjer, som paa Wikipedias livstidslinjer — den slags har intet
graflib en knap til, og SVG kan staa direkte i siden uden en iframe.
"""

from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import datetime, timedelta
from xml.sax.saxutils import escape

from dateutil.relativedelta import relativedelta

from . import formatting as fmt
from .i18n import t
from .units import TROPICAL_YEAR_DAYS

# -------------------------------------------------------------------------
# Tidsrum
# -------------------------------------------------------------------------

DAY = 86_400.0
WEEK = 7 * DAY
YEAR = TROPICAL_YEAR_DAYS * DAY
MONTH = YEAR / 12

# De tidsrum, et menneske kan laese. Kaskadens mellemraekker rundes til et af
# dem, saa der staar "10 aar" og ikke "11,4 aar".
_LADDER: tuple[float, ...] = (
    100 * YEAR,
    50 * YEAR,
    25 * YEAR,
    10 * YEAR,
    5 * YEAR,
    2 * YEAR,
    YEAR,
    6 * MONTH,
    3 * MONTH,
    MONTH,
    2 * WEEK,
    WEEK,
    DAY,
)

# Valgmulighederne paa skydeknappen: hvor taet den nederste raekke zoomer ind.
SPAN_CHOICES: tuple[float, ...] = (
    50 * YEAR,
    20 * YEAR,
    10 * YEAR,
    5 * YEAR,
    2 * YEAR,
    YEAR,
    3 * MONTH,
    MONTH,
    WEEK,
)


def describe_span(seconds: float) -> tuple[int, str]:
    """Et tidsrum som (antal, enhedsnoegle) — fx (10, "year")."""
    for unit, size in (("year", YEAR), ("month", MONTH), ("week", WEEK), ("day", DAY)):
        if seconds >= size * 0.9:
            return max(1, round(seconds / size)), unit
    return 1, "day"


def span_text(seconds: float, lang: str) -> str:
    """"10 år" / "10 years"."""
    count, unit = describe_span(seconds)
    return fmt.unit_phrase(count, unit, lang)


# -------------------------------------------------------------------------
# Kaskadens raekker
# -------------------------------------------------------------------------


def cascade_spans(total: float, target: float, levels: int) -> list[float]:
    """Raekkernes tidsrum i sekunder, fra hele livet ned til det mindste.

    Forholdet mellem to naboraekker er det samme hele vejen ned, saa zoomet
    foeles jaevnt — som paa den geologiske skala, hvor hver raekke udvider en
    fast brik af den over. Mellemraekkerne rundes derefter til noget laeseligt;
    foerste og sidste raekke staar fast, for de er dem, brugeren selv har valgt.
    """
    if total <= 0:
        return [max(total, DAY)]
    target = min(max(target, DAY), total)
    levels = max(2, min(levels, 6))
    if target >= total * 0.95:
        return [total]

    factor = (total / target) ** (1.0 / (levels - 1))
    spans = [total]
    for step in range(1, levels - 1):
        rung = _snap(total / factor**step)
        # Kun hvis raekken rummer noget nyt: baade klart mindre end den over
        # og klart stoerre end den nederste.
        if rung < spans[-1] * 0.95 and rung > target * 1.3:
            spans.append(rung)
    spans.append(target)
    return spans


def _snap(seconds: float) -> float:
    """Naermeste menneskelige tidsrum, maalt som logaritmisk afstand."""
    return min(_LADDER, key=lambda rung: abs(math.log(rung) - math.log(seconds)))


def cascade_windows(
    start: datetime, end: datetime, focus: datetime, spans: list[float]
) -> list[tuple[datetime, datetime]]:
    """Et vindue pr. raekke, centreret om fokuspunktet.

    Hvert vindue holdes inde i vinduet over sig. Ellers kunne en raekke komme
    til at vise tid, dens egen forgaenger ikke daekker, og saa holder
    kaskadens loefte ikke laengere: at hver raekke er et udsnit af den over.
    """
    windows = [(start, end)]
    for span in spans[1:]:
        parent_start, parent_end = windows[-1]
        available = (parent_end - parent_start).total_seconds()
        width = timedelta(seconds=min(span, available))
        low = focus - width / 2
        low = max(low, parent_start)
        low = min(low, parent_end - width)
        windows.append((low, low + width))
    return windows


# -------------------------------------------------------------------------
# Etiketter i baner
# -------------------------------------------------------------------------


@dataclass(frozen=True)
class Placed:
    """En etiket, der fik plads: hvilken post, hvilken bane, og hvor."""

    index: int
    lane: int
    x: float        # Selve maerket paa tidslinjen.
    text_x: float   # Hvor teksten begynder.
    width: float


def text_width(text: str, size: float = 10.5) -> float:
    """Groft skoen over en tekst' bredde i px.

    SVG kan ikke maale en tekst, foer den er tegnet, og placeringen skal ligge
    fast inden. Skoennet er derfor med vilje en smule rundhaandet: bliver en
    etiket bredere end beregnet, sker der det, at to naboer rykker en smule
    taettere — ikke at de lapper over hinanden.
    """
    units = 0.0
    for char in text:
        if ord(char) > 0x2100:            # Emoji og andre brede tegn.
            units += 1.40
        elif char in "iljtfr.,:;'|!()[] ":
            units += 0.34
        elif char.isupper() or char in "mwMW%—–":
            units += 0.72
        else:
            units += 0.55
    return units * size


def place_labels(
    entries: list[tuple[float, float, int]],
    left: float,
    right: float,
    max_lanes: int = 4,
    gap: float = 7.0,
) -> tuple[list[Placed], int]:
    """Fordel etiketter paa baner under tidslinjen uden overlap.

    ``entries`` er (x, bredde, prioritet). Lav prioritet kommer foerst, saa
    de fremhaevede klassikere altid faar en etiket, mens det er de jaevne
    maerkedage, der maa noejes med sit maerke, naar pladsen er brugt op.

    Det er grebet fra Wikipedias livstidslinjer: naar to navne ikke kan staa
    ved siden af hinanden, saettes det ene en linje laengere ned og forbindes
    til sit punkt med en henvisningslinje.
    """
    lanes: list[list[tuple[float, float]]] = [[] for _ in range(max(1, max_lanes))]
    placed: list[Placed] = []
    hidden = 0

    order = sorted(range(len(entries)), key=lambda i: (entries[i][2], entries[i][0]))
    for index in order:
        x, width, _ = entries[index]
        text_x = min(max(x - width / 2, left), max(left, right - width))
        low, high = text_x - gap, text_x + width + gap
        for lane, taken in enumerate(lanes):
            if all(high <= a or low >= b for a, b in taken):
                taken.append((text_x, text_x + width))
                placed.append(Placed(index, lane, x, text_x, width))
                break
        else:
            hidden += 1

    placed.sort(key=lambda p: p.index)
    return placed, hidden


# -------------------------------------------------------------------------
# Aksens inddeling
# -------------------------------------------------------------------------


def axis_ticks(start: datetime, end: datetime, lang: str) -> list[tuple[datetime, str]]:
    """Inddelingen under en raekke, valgt efter hvor langt et tidsrum den viser."""
    days = (end - start).total_seconds() / DAY
    if days > 150 * 365:
        return _year_ticks(start, end, 25)
    if days > 60 * 365:
        return _year_ticks(start, end, 10)
    if days > 18 * 365:
        return _year_ticks(start, end, 5)
    if days > 4 * 365:
        return _year_ticks(start, end, 1)
    if days > 300:
        return _month_ticks(start, end, 3, lang)
    if days > 70:
        return _month_ticks(start, end, 1, lang)
    if days > 20:
        return _day_ticks(start, end, 7, lang)
    return _day_ticks(start, end, 2, lang)


def _year_ticks(start: datetime, end: datetime, step: int) -> list[tuple[datetime, str]]:
    year = start.year if step == 1 else start.year - start.year % step
    out: list[tuple[datetime, str]] = []
    while year <= end.year:
        moment = start.replace(
            year=year, month=1, day=1, hour=0, minute=0, second=0, microsecond=0
        )
        if start <= moment <= end:
            out.append((moment, str(year)))
        year += step
    return out


def _month_ticks(
    start: datetime, end: datetime, step: int, lang: str
) -> list[tuple[datetime, str]]:
    moment = start.replace(day=1, hour=0, minute=0, second=0, microsecond=0)
    out: list[tuple[datetime, str]] = []
    while moment <= end:
        if moment >= start and (moment.month - 1) % step == 0:
            name = fmt.MONTHS_ABBR[lang][moment.month - 1]
            label = f"{name} {moment.year}" if moment.month == 1 or not out else name
            out.append((moment, label))
        moment += relativedelta(months=1)
    return out


def _day_ticks(
    start: datetime, end: datetime, step: int, lang: str
) -> list[tuple[datetime, str]]:
    moment = start.replace(hour=0, minute=0, second=0, microsecond=0)
    out: list[tuple[datetime, str]] = []
    while moment <= end:
        if moment >= start:
            name = fmt.MONTHS_ABBR[lang][moment.month - 1]
            out.append(
                (
                    moment,
                    f"{moment.day}. {name}" if lang == "da" else f"{moment.day} {name}",
                )
            )
        moment += timedelta(days=step)
    return out


# -------------------------------------------------------------------------
# Det, der skal tegnes
# -------------------------------------------------------------------------


@dataclass(frozen=True)
class Entry:
    """Én maerkedag, gjort klar til at blive tegnet."""

    when: datetime      # Lokal tid.
    label: str          # Den korte tekst paa tidslinjen.
    tip: str            # Hele forklaringen, til mus-over.
    color: str          # Gruppens farve.
    star: bool = False  # Fremhaevet klassiker — faar etiket foerst.


# Maal i brugerkoordinater. SVG'en skalerer selv til vinduets bredde.
_W = 1200.0
_GUTTER = 162.0          # Plads til raekkens navn til venstre.
_RIGHT = _W - 22.0
_BAND_H = 30.0
_LANE_H = 14.0
_AXIS_H = 17.0
_ROW_GAP = 20.0
_LABEL_SIZE = 10.5

_CSS = """
.tl { font-family: "Source Sans Pro", "Segoe UI", system-ui, sans-serif; }
.tl-lvl { font-family: Georgia, "Times New Roman", serif; font-size: 13px;
          font-weight: 600; fill: #3a332a; }
.tl-sub { font-family: Georgia, "Times New Roman", serif; font-size: 10.5px;
          fill: #8b8275; }
.tl-axis { font-size: 9.5px; fill: #8b8275; }
.tl-lab { font-size: 10.5px; fill: #2b2b2b; }
.tl-lab-star { font-size: 10.5px; fill: #1a1a1a; font-weight: 600; }
.tl-now { font-size: 9.5px; font-weight: 700; fill: #c0392b; }
.tl-note { font-size: 10px; fill: #8b8275; font-style: italic; }
.tl-e { cursor: default; }
.tl-e:hover rect { stroke: #1a1a1a; stroke-width: 1; }
"""


@dataclass(frozen=True)
class Drawing:
    """En faerdig tegning og den hoejde, den fylder ved fuld bredde."""

    svg: str
    height: float

    def as_file(self) -> bytes:
        """Tegningen som en selvstaendig SVG-fil, klar til at hente ned."""
        return f'<?xml version="1.0" encoding="UTF-8"?>\n{self.svg}'.encode()

    def as_frame(self) -> str:
        """Tegningen pakket ind i et lille HTML-dokument.

        ``st.html`` kan ikke bruges: Streamlit renser sin HTML med DOMPurify i
        ren HTML-tilstand, og den fjerner hele SVG-traeet uden at sige noget.
        Derfor gaar tegningen i en komponent-iframe i stedet, hvor intet
        bliver renset bort — og hvor browserens egne vaerktoejstip virker.

        Tegningen fylder hele den bredde, den faar, saa teksten vokser med
        vinduet. Hoejden foelger med, og den kan Streamlit ikke regne ud paa
        forhaand — derfor maaler rammen sig selv bagefter og retter iframens
        hoejde. Slaar det fejl, er hoejden den, tegningen ville have ved 1200
        px bredde: for lidt luft under en bred skaerm, for meget under en
        smal. Intet bliver skaaret fra, for iframen ruller selv.
        """
        return (
            "<!doctype html><html><head><meta charset='utf-8'><style>"
            "html,body{margin:0;padding:0;background:#fdfbf6;}"
            "svg{display:block;width:100%;height:auto;}"
            "</style></head><body>"
            f"{self.svg}"
            "<script>(function(){"
            "function fit(){try{var f=window.frameElement;if(!f)return;"
            "var h=Math.ceil(document.documentElement.getBoundingClientRect().height);"
            "if(h>40)f.style.height=h+'px';}catch(err){}}"
            "fit();window.addEventListener('resize',fit);"
            "setTimeout(fit,60);setTimeout(fit,400);})();</script>"
            "</body></html>"
        )


def _x_of(moment: datetime, start: datetime, end: datetime) -> float:
    """Et tidspunkt omsat til en x-koordinat i en raekke."""
    span = (end - start).total_seconds()
    if span <= 0:
        return _GUTTER
    share = (moment - start).total_seconds() / span
    return _GUTTER + max(0.0, min(1.0, share)) * (_RIGHT - _GUTTER)


def _shorten(text: str, limit: int = 42) -> str:
    return text if len(text) <= limit else text[: limit - 1].rstrip() + "…"


def _svg(height: float, body: str) -> str:
    return (
        f'<svg class="tl" viewBox="0 0 {_W:.0f} {height:.0f}" width="100%" '
        f'height="{height:.0f}" preserveAspectRatio="xMidYMid meet" '
        f'xmlns="http://www.w3.org/2000/svg" role="img">'
        f"<style>{_CSS}</style>"
        f'<rect x="0" y="0" width="{_W:.0f}" height="{height:.0f}" fill="#fdfbf6"/>'
        f"{body}</svg>"
    )


def _mark(entry: Entry, x: float, y: float, height: float, past: bool) -> str:
    """Selve maerket paa tidslinjen, med forklaringen som mus-over."""
    opacity = 0.42 if past else 1.0
    width = 3.2 if entry.star else 2.0
    return (
        f'<g class="tl-e"><title>{escape(entry.tip)}</title>'
        f'<rect x="{x - width / 2:.1f}" y="{y:.1f}" width="{width:.1f}" '
        f'height="{height:.1f}" fill="{entry.color}" fill-opacity="{opacity:.2f}"/>'
        f"</g>"
    )


@dataclass(frozen=True)
class _LabelPlan:
    """Etiketterne for én raekke: hvor de staar, og hvor meget plads de kraever."""

    placed: list[Placed]
    texts: list[str]
    height: float
    hidden: int


def _plan_labels(
    entries: list[Entry], xs: list[float], left: float, right: float, max_lanes: int
) -> _LabelPlan:
    """Fordel raekkens etiketter paa baner.

    Det skal gøres, før rækkerne kan lægges ud lodret: hvor høj en række
    bliver, afhænger af hvor mange baner dens etiketter kræver.
    """
    if not entries:
        return _LabelPlan([], [], 0.0, 0)

    texts = [_shorten(entry.label) for entry in entries]
    boxes = [
        (xs[index], text_width(texts[index], _LABEL_SIZE), 0 if entry.star else 1)
        for index, entry in enumerate(entries)
    ]
    placed, hidden = place_labels(boxes, left, right, max_lanes=max_lanes)
    lanes = max((spot.lane for spot in placed), default=-1) + 1
    return _LabelPlan(placed, texts, lanes * _LANE_H, hidden)


def _draw_labels(
    plan: _LabelPlan, entries: list[Entry], pasts: list[bool], top: float
) -> str:
    """Tegn de etiketter, ``_plan_labels`` har fundet plads til."""
    parts: list[str] = []
    for spot in plan.placed:
        entry = entries[spot.index]
        baseline = top + spot.lane * _LANE_H + 9.5
        # Henvisningslinjen: ned fra maerket, saa et lille knaek ind til
        # teksten. Det er den, der goer, at en etiket kan staa forskudt og
        # alligevel pege paa det rigtige punkt.
        parts.append(
            f'<path d="M{spot.x:.1f},{top - 5:.1f} L{spot.x:.1f},{baseline - 6:.1f} '
            f'L{spot.text_x + 1.5:.1f},{baseline - 2.5:.1f}" fill="none" '
            f'stroke="{entry.color}" stroke-opacity="0.45" stroke-width="0.7"/>'
        )
        css = "tl-lab-star" if entry.star else "tl-lab"
        opacity = 0.5 if pasts[spot.index] else 1.0
        parts.append(
            f'<g class="tl-e"><title>{escape(entry.tip)}</title>'
            f'<text class="{css}" x="{spot.text_x:.1f}" y="{baseline:.1f}" '
            f'opacity="{opacity:.2f}">{escape(plan.texts[spot.index])}</text></g>'
        )
    return "".join(parts)


def _now_line(x: float, top: float, bottom: float, lang: str) -> str:
    word = t("tl_now", lang)
    return (
        f'<path d="M{x:.1f},{top:.1f} L{x:.1f},{bottom:.1f}" stroke="#c0392b" '
        f'stroke-width="1.4"/>'
        f'<path d="M{x - 4:.1f},{top:.1f} L{x + 4:.1f},{top:.1f} '
        f'L{x:.1f},{top + 5:.1f} Z" fill="#c0392b"/>'
        f'<text class="tl-now" x="{x + 6:.1f}" y="{top - 2:.1f}">{escape(word)}</text>'
    )


# -------------------------------------------------------------------------
# Kaskaden
# -------------------------------------------------------------------------


def render_cascade(
    entries: list[Entry],
    start: datetime,
    end: datetime,
    focus: datetime,
    now: datetime,
    spans: list[float],
    lang: str,
    max_lanes: int = 4,
) -> Drawing:
    """Hele kaskaden som SVG.

    Raekkerne lægges ud i to omgange: foerst placeres etiketterne, saa vi ved,
    hvor mange baner hver raekke skal have, og derefter kan hoejderne regnes.
    """
    windows = cascade_windows(start, end, focus, spans)

    # Foerste omgang: hvad hoerer hvor hen, og hvor mange baner bliver der brug for.
    rows: list[dict] = []
    for level, (low, high) in enumerate(windows):
        inside = [e for e in entries if low <= e.when <= high]
        xs = [_x_of(e.when, low, high) for e in inside]
        rows.append(
            {
                "low": low,
                "high": high,
                "inside": inside,
                "xs": xs,
                "pasts": [e.when < now for e in inside],
                "plan": _plan_labels(inside, xs, _GUTTER, _RIGHT, max_lanes),
                "span": spans[level] if level < len(spans) else 0.0,
            }
        )

    heights = [
        _AXIS_H + _BAND_H + 8 + row["plan"].height + _ROW_GAP for row in rows
    ]
    total = 10 + sum(heights)

    body: list[str] = []
    tops: list[float] = []
    y = 10.0
    for row, height in zip(rows, heights):
        tops.append(y)
        y += height

    # Zoomkilerne tegnes foerst, saa de ligger bag etiketterne.
    for level in range(len(rows) - 1):
        row, child = rows[level], rows[level + 1]
        band_bottom = tops[level] + _AXIS_H + _BAND_H
        next_top = tops[level + 1] + _AXIS_H
        cx0 = _x_of(child["low"], row["low"], row["high"])
        cx1 = _x_of(child["high"], row["low"], row["high"])
        if cx1 - cx0 < 1.4:   # Et vindue kan vaere tyndere end en streg.
            cx0, cx1 = (cx0 + cx1) / 2 - 0.7, (cx0 + cx1) / 2 + 0.7
        body.append(
            f'<path d="M{cx0:.1f},{band_bottom:.1f} L{cx1:.1f},{band_bottom:.1f} '
            f'L{_RIGHT:.1f},{next_top:.1f} L{_GUTTER:.1f},{next_top:.1f} Z" '
            f'fill="#c7b89a" fill-opacity="0.13" stroke="#b9a885" '
            f'stroke-opacity="0.45" stroke-width="0.7" stroke-dasharray="3 3"/>'
        )
        # Udsnittet markeres ogsaa oppe i baandet, saa man kan se hvor lidt af
        # livet den naeste raekke egentlig daekker.
        body.append(
            f'<rect x="{cx0:.1f}" y="{tops[level] + _AXIS_H:.1f}" '
            f'width="{max(cx1 - cx0, 1.4):.1f}" height="{_BAND_H:.1f}" '
            f'fill="none" stroke="#8a6d3b" stroke-width="1.2"/>'
        )

    for level, (row, top) in enumerate(zip(rows, tops)):
        low, high = row["low"], row["high"]
        band_top = top + _AXIS_H
        band_bottom = band_top + _BAND_H

        body.append(
            f'<rect x="{_GUTTER:.1f}" y="{band_top:.1f}" '
            f'width="{_RIGHT - _GUTTER:.1f}" height="{_BAND_H:.1f}" '
            f'fill="#f4efe3" stroke="#cfc5b2" stroke-width="0.8"/>'
        )
        # Den levede del skyggelaegges. Det er "du er her" fortalt som flade.
        if now > low:
            lived = min(_x_of(now, low, high), _RIGHT)
            body.append(
                f'<rect x="{_GUTTER:.1f}" y="{band_top:.1f}" '
                f'width="{max(lived - _GUTTER, 0):.1f}" height="{_BAND_H:.1f}" '
                f'fill="#ded5c2" fill-opacity="0.75"/>'
            )

        for moment, text in axis_ticks(low, high, lang):
            x = _x_of(moment, low, high)
            body.append(
                f'<path d="M{x:.1f},{band_top:.1f} L{x:.1f},{band_bottom:.1f}" '
                f'stroke="#bdb29c" stroke-width="0.6"/>'
                f'<text class="tl-axis" x="{x:.1f}" y="{band_top - 5:.1f}" '
                f'text-anchor="middle">{escape(text)}</text>'
            )

        for entry, x, past in zip(row["inside"], row["xs"], row["pasts"]):
            body.append(_mark(entry, x, band_top + 2, _BAND_H - 4, past))

        if low <= now <= high:
            body.append(_now_line(_x_of(now, low, high), band_top - 1, band_bottom + 4, lang))

        # Raekkens navn til venstre: hvad den viser, og hvor den ligger.
        title = t("tl_whole_life", lang) if level == 0 else span_text(row["span"], lang)
        body.append(
            f'<text class="tl-lvl" x="8" y="{band_top + 13:.1f}">{escape(title)}</text>'
            f'<text class="tl-sub" x="8" y="{band_top + 26:.1f}">'
            f"{escape(_range_text(low, high, lang))}</text>"
        )

        plan: _LabelPlan = row["plan"]
        body.append(
            _draw_labels(plan, row["inside"], row["pasts"], band_bottom + 13)
        )
        if plan.hidden:
            body.append(
                f'<text class="tl-note" x="{_RIGHT:.1f}" '
                f'y="{band_bottom + 11:.1f}" text-anchor="end">'
                f'{escape(t("tl_hidden", lang, n=plan.hidden))}</text>'
            )
        elif not row["inside"]:
            body.append(
                f'<text class="tl-note" x="{(_GUTTER + _RIGHT) / 2:.1f}" '
                f'y="{band_bottom + 16:.1f}" text-anchor="middle">'
                f'{escape(t("tl_empty_row", lang))}</text>'
            )

    return Drawing(_svg(total, "".join(body)), total)


def _range_text(low: datetime, high: datetime, lang: str) -> str:
    """Raekkens tidsrum skrevet kort: "1973 – 2123" eller "jun 2026"."""
    days = (high - low).total_seconds() / DAY
    if days > 2 * 365:
        return f"{low.year} – {high.year}"
    if days > 50:
        first = fmt.MONTHS_ABBR[lang][low.month - 1]
        last = fmt.MONTHS_ABBR[lang][high.month - 1]
        if low.year == high.year:
            return f"{first} – {last} {high.year}"
        return f"{first} {low.year} – {last} {high.year}"
    return f"{fmt.fmt_date_text(low, lang)} – {fmt.fmt_date_text(high, lang)}"


# -------------------------------------------------------------------------
# Den logaritmiske skala
# -------------------------------------------------------------------------

# Tidsrum, et menneske kender, sat ind paa den logaritmiske akse.
_LOG_ANCHORS: tuple[tuple[float, str, str], ...] = (
    (1.0, "1 s", "1 s"),
    (60.0, "1 minut", "1 minute"),
    (3600.0, "1 time", "1 hour"),
    (DAY, "1 døgn", "1 day"),
    (WEEK, "1 uge", "1 week"),
    (MONTH, "1 måned", "1 month"),
    (YEAR, "1 år", "1 year"),
    (10 * YEAR, "10 år", "10 years"),
    (100 * YEAR, "100 år", "100 years"),
)


def render_log(
    entries: list[Entry],
    birth: datetime,
    now: datetime,
    max_seconds: float,
    lang: str,
    max_lanes: int = 10,
) -> Drawing:
    """Hele livet paa en logaritmisk akse fra foedselsoejeblikket.

    Her er der ingen kaskade: tierpotenserne goer arbejdet. Et sekund og
    hundrede aar staar paa samme skaerm, og de maerkedage, kataloget bygger paa
    — 10⁶, 10⁷, 10⁸, 10⁹ sekunder — ligger lige langt fra hinanden.
    """
    top = 34.0
    band_top = top + _AXIS_H
    band_bottom = band_top + _BAND_H

    ages = [(e.when - birth).total_seconds() for e in entries]
    before = sum(1 for seconds in ages if seconds < 1.0)
    alive = [seconds for seconds in ages if seconds >= 1.0]

    # Aksen begynder en tierpotens under den tidligste maerkedag i stedet for
    # ved ét sekund. Kataloget starter ved 10⁶ sekunder — altsaa dag 11 — saa
    # en akse fra 1 s ville bruge over halvdelen af bredden paa tom tid, og
    # saa var der ikke vundet noget ved at gaa logaritmisk.
    low = max(0.0, math.floor(math.log10(min(alive, default=1.0))) - 1)
    high = math.log10(max(max_seconds, 10.0))
    if high - low < 2.0:
        low = max(0.0, high - 2.0)

    def x_of(seconds: float) -> float:
        share = (math.log10(max(seconds, 1.0)) - low) / (high - low)
        return _GUTTER + max(0.0, min(1.0, share)) * (_RIGHT - _GUTTER)

    inside = [e for e, seconds in zip(entries, ages) if seconds >= 1.0]
    xs = [x_of(seconds) for seconds in alive]

    pasts = [e.when < now for e in inside]
    plan = _plan_labels(inside, xs, _GUTTER, _RIGHT, max_lanes)
    # Etiketterne begynder under de menneskelige tidsrum, ikke oven i dem.
    labels_top = band_bottom + 30
    total = labels_top + plan.height + 26

    body: list[str] = [
        f'<rect x="{_GUTTER:.1f}" y="{band_top:.1f}" '
        f'width="{_RIGHT - _GUTTER:.1f}" height="{_BAND_H:.1f}" '
        f'fill="#f4efe3" stroke="#cfc5b2" stroke-width="0.8"/>'
    ]

    lived = x_of(max((now - birth).total_seconds(), 1.0))
    body.append(
        f'<rect x="{_GUTTER:.1f}" y="{band_top:.1f}" '
        f'width="{max(lived - _GUTTER, 0):.1f}" height="{_BAND_H:.1f}" '
        f'fill="#ded5c2" fill-opacity="0.75"/>'
    )

    # Tierpotenserne over baandet — selve skalaens egen inddeling.
    power = int(math.ceil(low))
    while power <= high + 0.001:
        x = x_of(10.0**power)
        body.append(
            f'<path d="M{x:.1f},{band_top:.1f} L{x:.1f},{band_bottom:.1f}" '
            f'stroke="#bdb29c" stroke-width="0.6"/>'
            f'<text class="tl-axis" x="{x:.1f}" y="{band_top - 6:.1f}" '
            f'text-anchor="middle">10{_superscript(power)}</text>'
        )
        power += 1

    # Og de menneskelige tidsrum under det, saa potenserne faar en betydning.
    for seconds, word_da, word_en in _LOG_ANCHORS:
        if seconds > max_seconds or math.log10(seconds) < low:
            continue
        x = x_of(seconds)
        word = word_da if lang == "da" else word_en
        body.append(
            f'<path d="M{x:.1f},{band_top - 2:.1f} L{x:.1f},{band_bottom + 8:.1f}" '
            f'stroke="#8a6d3b" stroke-opacity="0.55" stroke-width="0.7" '
            f'stroke-dasharray="2 3"/>'
            f'<text class="tl-sub" x="{x:.1f}" y="{band_bottom + 19:.1f}" '
            f'text-anchor="middle">{escape(word)}</text>'
        )

    for entry, x, past in zip(inside, xs, pasts):
        body.append(_mark(entry, x, band_top + 2, _BAND_H - 4, past))

    body.append(_now_line(lived, band_top - 1, band_bottom + 4, lang))
    body.append(
        f'<text class="tl-lvl" x="8" y="{band_top + 13:.1f}">'
        f'{escape(t("tl_log_axis", lang))}</text>'
        f'<text class="tl-sub" x="8" y="{band_top + 26:.1f}">'
        f'{escape(t("tl_from_birth", lang))}</text>'
    )
    body.append(_draw_labels(plan, inside, pasts, labels_top))

    notes = []
    if plan.hidden:
        notes.append(t("tl_hidden", lang, n=plan.hidden))
    if before:
        notes.append(t("tl_before_birth", lang, n=before))
    if notes:
        body.append(
            f'<text class="tl-note" x="{_RIGHT:.1f}" y="{total - 12:.1f}" '
            f'text-anchor="end">{escape("  ·  ".join(notes))}</text>'
        )

    return Drawing(_svg(total, "".join(body)), total)


_SUPERSCRIPT = str.maketrans("0123456789", "⁰¹²³⁴⁵⁶⁷⁸⁹")


def _superscript(number: int) -> str:
    return str(number).translate(_SUPERSCRIPT)
