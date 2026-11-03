"""Hent doedelighedstavler og skriv dem til ``data/lifetables.json``.

To kilder, og de er valgt med omhu:

**Danmarks Statistik, tabel HISB8.** Den danske nationale tavle, opdateret
hvert aar, med aldre 0-99 og toaars-perioder. Det er den mest aktuelle og den
rigtige for Danmark.

**Eurostat, tabel demo_mlifetable.** Den samme opgoerelse for fyrre lande,
saa tallene kan sammenlignes. Aldre 0-94 plus en aaben gruppe fra 95.

Begge er frit tilgaengelige uden registrering og uden noegle.

Af hver tavle bruges to kolonner:

``lx``  hvor mange af 100.000 nyfoedte der stadig lever ved hver alder
``ex``  den forventede restlevetid ved hver alder

``lx`` er den vigtige. Middellevetiden er bare et gennemsnit, men ``lx`` er
hele fordelingen, og det er den, der kan svare paa "hvad er chancen for, at
jeg naar de halvfems".

Koer den med:
    .venv/Scripts/python.exe tools/fetch_lifetables.py
"""

from __future__ import annotations

import json
import sys
import urllib.parse
import urllib.request
from datetime import date
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
TARGET = ROOT / "data" / "lifetables.json"

TIMEOUT = 120

DST_TABLE = "https://api.statbank.dk/v1/tableinfo/HISB8?format=JSON"
DST_DATA = "https://api.statbank.dk/v1/data/HISB8/CSV"
DST_PAGE = "https://www.statbank.dk/HISB8"

EUROSTAT = (
    "https://ec.europa.eu/eurostat/api/dissemination/statistics/1.0/data/"
    "demo_mlifetable"
)
EUROSTAT_PAGE = (
    "https://ec.europa.eu/eurostat/databrowser/view/demo_mlifetable/default/table"
)

# Aggregater og dubletter, der ikke er lande.
NOT_A_COUNTRY = {"EU27_2020", "EA21", "EA20", "EA19", "EFTA", "DE_TOT"}

# Landenavne paa dansk. Eurostat leverer dem kun paa engelsk.
DANISH_NAMES = {
    "AL": "Albanien", "AT": "Østrig", "BE": "Belgien", "BG": "Bulgarien",
    "CH": "Schweiz", "CY": "Cypern", "CZ": "Tjekkiet", "DE": "Tyskland",
    "DK": "Danmark", "EE": "Estland", "EL": "Grækenland", "ES": "Spanien",
    "FI": "Finland", "FR": "Frankrig", "GE": "Georgien", "HR": "Kroatien",
    "HU": "Ungarn", "IE": "Irland", "IS": "Island", "IT": "Italien",
    "LI": "Liechtenstein", "LT": "Litauen", "LU": "Luxembourg",
    "LV": "Letland", "MD": "Moldova", "ME": "Montenegro", "MT": "Malta",
    "NL": "Nederlandene", "NO": "Norge", "PL": "Polen", "PT": "Portugal",
    "RO": "Rumænien", "RS": "Serbien", "SE": "Sverige", "SI": "Slovenien",
    "SK": "Slovakiet", "TR": "Tyrkiet", "UK": "Storbritannien",
}


def get(url: str) -> bytes:
    with urllib.request.urlopen(url, timeout=TIMEOUT) as response:
        return response.read()


def get_json(url: str) -> dict:
    return json.loads(get(url).decode("utf-8-sig"))


# -------------------------------------------------------------------------
# Danmarks Statistik
# -------------------------------------------------------------------------


def fetch_denmark() -> dict:
    """Den danske tavle, aldre 0-99, seneste toaarsperiode."""
    info = get_json(DST_TABLE)
    periods = next(v for v in info["variables"] if v["id"] == "Tid")["values"]
    latest = periods[-1]["id"]

    query = urllib.parse.urlencode(
        {
            "ALDER": "*",
            "KØN": "*",
            "TAVLE": "*",
            "Tid": latest,
            "delimiter": "Semicolon",
        }
    )
    rows = get(f"{DST_DATA}?{query}").decode("utf-8-sig").splitlines()

    sexes: dict[str, dict[str, dict[int, float]]] = {
        "M": {"lx": {}, "ex": {}},
        "F": {"lx": {}, "ex": {}},
    }
    for row in rows[1:]:
        age_text, sex_text, table, _, value = row.split(";")
        age = int(age_text.split()[0])
        sex = "M" if sex_text == "Mænd" else "F"
        if table.startswith("Overlevende"):
            sexes[sex]["lx"][age] = float(value.replace(",", "."))
        elif table.startswith("Middellevetid"):
            sexes[sex]["ex"][age] = float(value.replace(",", "."))

    ages = sorted(sexes["M"]["lx"])
    return {
        "name_da": "Danmark",
        "name_en": "Denmark",
        "source": f"Danmarks Statistik, HISB8 ({latest})",
        "source_url": DST_PAGE,
        "period": latest,
        "ages": ages,
        "sexes": {
            sex: {
                "lx": [round(data["lx"][age], 1) for age in ages],
                "ex": [round(data["ex"][age], 2) for age in ages],
            }
            for sex, data in sexes.items()
        },
    }


# -------------------------------------------------------------------------
# Eurostat
# -------------------------------------------------------------------------


def _age_number(code: str) -> int | None:
    """``Y_LT1`` -> 0, ``Y40`` -> 40, ``Y_GE95`` -> 95."""
    if code == "Y_LT1":
        return 0
    if code.startswith("Y_GE"):
        return int(code[4:])
    if code.startswith("Y") and code[1:].isdigit():
        return int(code[1:])
    return None


def fetch_eurostat() -> dict[str, dict]:
    """De oevrige lande, seneste aar med data."""
    query = urllib.parse.urlencode(
        [
            ("format", "JSON"),
            ("lang", "EN"),
            ("sex", "M"),
            ("sex", "F"),
            ("indic_de", "LIFEXP"),
            ("indic_de", "SURVIVORS"),
            ("sinceTimePeriod", "2024"),
        ]
    )
    payload = get_json(f"{EUROSTAT}?{query}")

    order = payload["id"]
    sizes = payload["size"]
    dims = payload["dimension"]
    values = payload["value"]

    def index_of(name: str) -> dict[str, int]:
        return dims[name]["category"]["index"]

    indic, sex_idx = index_of("indic_de"), index_of("sex")
    age_idx, geo_idx, time_idx = index_of("age"), index_of("geo"), index_of("time")
    names = dims["geo"]["category"]["label"]
    year = max(time_idx, key=lambda key: time_idx[key])

    strides = {}
    stride = 1
    for name, size in zip(reversed(order), reversed(sizes)):
        strides[name] = stride
        stride *= size

    def value_at(indicator: str, sex: str, age: str, geo: str) -> float | None:
        flat = (
            indic[indicator] * strides["indic_de"]
            + sex_idx[sex] * strides["sex"]
            + age_idx[age] * strides["age"]
            + geo_idx[geo] * strides["geo"]
            + time_idx[year] * strides["time"]
        )
        return values.get(str(flat))

    # Aldersstigen. Eurostat har baade ``Y85`` og det tomme levn ``Y_GE85``,
    # og de peger paa det samme aar. Den praecise alder vinder; en aaben
    # gruppe bruges kun, hvor der ikke findes en praecis — det gaelder kun
    # toppen, ``Y_GE95``. Uden det her bliver der et hul midt i hver tavle.
    numbered: dict[int, str] = {}
    for code in age_idx:
        number = _age_number(code)
        if number is None:
            continue
        if number in numbered and code.startswith("Y_GE"):
            continue
        numbered[number] = code
    ladder = [(numbered[number], number) for number in sorted(numbered)]

    out: dict[str, dict] = {}
    skipped: list[str] = []
    for geo in geo_idx:
        if geo in NOT_A_COUNTRY or len(geo) != 2:
            continue
        sexes = {}
        complete = True
        for sex in ("M", "F"):
            lx = [value_at("SURVIVORS", sex, code, geo) for code, _ in ladder]
            ex = [value_at("LIFEXP", sex, code, geo) for code, _ in ladder]
            if any(v is None for v in lx) or any(v is None for v in ex):
                complete = False
                skipped.append(geo)
                break
            sexes[sex] = {
                "lx": [round(float(v), 1) for v in lx],
                "ex": [round(float(v), 2) for v in ex],
            }
        if not complete:
            continue
        out[geo] = {
            "name_da": DANISH_NAMES.get(geo, names.get(geo, geo)),
            "name_en": names.get(geo, geo),
            "source": f"Eurostat, demo_mlifetable ({year})",
            "source_url": EUROSTAT_PAGE,
            "period": year,
            "ages": [number for _, number in ladder],
            "sexes": sexes,
        }
    if skipped:
        print(f"  sprunget over (huller i tavlen): {', '.join(sorted(set(skipped)))}")
    return out


# -------------------------------------------------------------------------


def build() -> dict:
    countries = fetch_eurostat()
    print(f"Eurostat: {len(countries)} lande")
    countries["DK"] = fetch_denmark()
    print(f"Danmarks Statistik: {countries['DK']['source']}")
    return {
        "fetched": date.today().isoformat(),
        "default": "DK",
        "countries": dict(sorted(countries.items())),
    }


def main() -> int:
    try:
        payload = build()
    except Exception as problem:            # noqa: BLE001 — vi vil vide hvad der gik galt
        print(f"Hentningen mislykkedes: {problem}", file=sys.stderr)
        return 1

    TARGET.parent.mkdir(parents=True, exist_ok=True)
    TARGET.write_text(
        json.dumps(payload, ensure_ascii=False, indent=1), encoding="utf-8"
    )
    size = TARGET.stat().st_size / 1024
    print(f"Skrev {TARGET.relative_to(ROOT)} — {len(payload['countries'])} lande, {size:.0f} KB")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
