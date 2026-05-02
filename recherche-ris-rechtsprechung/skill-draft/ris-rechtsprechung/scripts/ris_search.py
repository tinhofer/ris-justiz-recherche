#!/usr/bin/env python3
"""Suchwrapper fuer die RIS-OGD-API v2.6 (Endpoint /Judikatur).

Liefert Metadaten + Direkt-Link pro Treffer. Volltext-Download ist
ausserhalb des Scopes dieses Skills.

Quelle: https://data.bka.gv.at/ris/api/v2.6/
Nur Standardbibliothek, keine Pip-Installation noetig.

Beispiele:
  ris_search.py --applikation Justiz --suchworte "Mietzinsminderung"
  ris_search.py --applikation Vfgh   --geschaeftszahl "G 12/2020"
  ris_search.py --applikation Vwgh   --norm "1319a ABGB" \\
                --von 2020-01-01 --bis 2024-12-31 --pro-seite 50
  ris_search.py --applikation Justiz --suchworte "Datenschutz" --json
"""

from __future__ import annotations

import argparse
import json
import re
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from typing import Any

BASE_URL = "https://data.bka.gv.at/ris/api/v2.6/Judikatur"

APPLIKATIONEN = [
    "Justiz", "Vfgh", "Vwgh", "Bvwg", "Lvwg",
    "Dsk", "AsylGH", "Normenliste", "Pvak", "Gbk", "Dok",
]

PRO_SEITE_VALUES = ["Ten", "Twenty", "Fifty", "OneHundred"]

IM_RIS_SEIT_VALUES = [
    "Undefined", "EinerWoche", "EinemMonat",
    "DreiMonaten", "SechsMonaten", "EinemJahr",
]

DOCNUMBER_PREFIX_TO_PATH = [
    ("BVWG",   "Bvwg"),
    ("LVWG",   "Lvwg"),
    ("ASYLGH", "AsylGH"),
    ("PVAK",   "Pvak"),
    ("GBK",    "Gbk"),
    ("DSB",    "Dsk"),
    ("JJT",    "Justiz"),
    ("JJR",    "Justiz"),
    ("JWT",    "Justiz"),
    ("JWR",    "Vwgh"),
    ("JFR",    "Vfgh"),
    ("JFT",    "Vfgh"),
]

DOCNUMBER_RE = re.compile(r"^[A-Z][A-Z0-9_]+$")


def docnumber_to_html_url(docnr: str) -> str | None:
    if not (5 <= len(docnr) <= 50 and DOCNUMBER_RE.match(docnr)):
        return None
    for prefix, path in DOCNUMBER_PREFIX_TO_PATH:
        if docnr.startswith(prefix):
            return f"https://ris.bka.gv.at/Dokumente/{path}/{docnr}/{docnr}.html"
    return None


def build_url(args: argparse.Namespace) -> str:
    params: list[tuple[str, str]] = [
        ("Applikation", args.applikation),
        ("DokumenteProSeite", args.pro_seite),
        ("Seitennummer", str(args.seite)),
        ("SucheNachRechtssatz", "False" if args.no_rechtssatz else "True"),
        ("SucheNachText", "False" if args.no_text else "True"),
    ]
    optional = [
        (args.suchworte, "Suchworte"),
        (args.geschaeftszahl, "Geschaeftszahl"),
        (args.norm, "Norm"),
        (args.rechtssatznummer, "Rechtssatznummer"),
        (args.von, "EntscheidungsdatumVon"),
        (args.bis, "EntscheidungsdatumBis"),
        (args.im_ris_seit, "ImRisSeit"),
        (args.sortierung, "Sortierung"),
        (args.sort_direction, "SortDirection"),
    ]
    for value, key in optional:
        if value:
            params.append((key, value))
    return f"{BASE_URL}?{urllib.parse.urlencode(params)}"


def http_get_json(url: str, timeout: float) -> dict[str, Any]:
    req = urllib.request.Request(
        url,
        headers={
            "Accept": "application/json",
            "User-Agent": "ris-rechtsprechung-skill/1.0 (+claude-code)",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def as_list(value: Any) -> list[Any]:
    if value is None:
        return []
    return value if isinstance(value, list) else [value]


def first_text(value: Any) -> str | None:
    """Extrahiere String aus Werten, die String, Dict ({'item': ...}, {'#text': ...}) oder Liste sein koennen."""
    if value is None:
        return None
    if isinstance(value, str):
        return value
    if isinstance(value, list):
        for v in value:
            t = first_text(v)
            if t:
                return t
        return None
    if isinstance(value, dict):
        for key in ("item", "#text"):
            if key in value:
                return first_text(value[key])
    return None


def all_texts(value: Any) -> list[str]:
    if value is None:
        return []
    if isinstance(value, str):
        return [value]
    if isinstance(value, list):
        out: list[str] = []
        for v in value:
            out.extend(all_texts(v))
        return out
    if isinstance(value, dict):
        for key in ("item", "#text"):
            if key in value:
                return all_texts(value[key])
    return []


def normalize(raw: dict[str, Any]) -> dict[str, Any]:
    result = (raw.get("OgdSearchResult") or {}).get("OgdDocumentResults") or {}
    hits = result.get("Hits") or {}
    if isinstance(hits, dict):
        total = int(hits.get("#text", 0) or 0)
        page = int(hits.get("@pageNumber", 1) or 1)
        size = int(hits.get("@pageSize", 0) or 0)
    else:
        total, page, size = int(hits or 0), 1, 0

    docs: list[dict[str, Any]] = []
    for ref in as_list(result.get("OgdDocumentReference")):
        data = (ref or {}).get("Data") or {}
        meta = data.get("Metadaten") or {}
        tech = meta.get("Technisch") or {}
        allgemein = meta.get("Allgemein") or {}
        jud = meta.get("Judikatur") or {}

        docnr = tech.get("ID")
        gz = first_text(jud.get("Geschaeftszahl"))
        gz_alle = all_texts(jud.get("Geschaeftszahl"))
        ent_datum = jud.get("Entscheidungsdatum")

        leitsatz = None
        for app_key in ("Justiz", "Vfgh", "Vwgh", "Bvwg", "Lvwg"):
            block = jud.get(app_key) or {}
            if isinstance(block, dict) and block.get("Leitsatz"):
                leitsatz = block["Leitsatz"]
                break

        urls: dict[str, str] = {}
        cref = (data.get("Dokumentliste") or {}).get("ContentReference")
        for c in as_list(cref):
            for u in as_list((c or {}).get("Urls", {}).get("ContentUrl")):
                dt, link = (u or {}).get("DataType"), (u or {}).get("Url")
                if dt and link:
                    urls[dt.lower()] = link

        link = (
            allgemein.get("DokumentUrl")
            or urls.get("html")
            or (docnumber_to_html_url(docnr) if docnr else None)
        )

        docs.append({
            "dokumentnummer": docnr,
            "applikation": tech.get("Applikation"),
            "geschaeftszahl": gz,
            "geschaeftszahlen": gz_alle,
            "entscheidungsdatum": ent_datum,
            "leitsatz": leitsatz,
            "link": link,
            "content_urls": urls,
        })

    return {
        "total_hits": total,
        "page": page,
        "page_size": size,
        "documents": docs,
    }


def render_markdown(result: dict[str, Any]) -> str:
    lines = [
        f"**Treffer:** {result['total_hits']} "
        f"(Seite {result['page']}, {result['page_size']} pro Seite)",
        "",
    ]
    for i, d in enumerate(result["documents"], start=1):
        gz = d["geschaeftszahl"] or "(ohne Geschaeftszahl)"
        datum = d["entscheidungsdatum"] or "?"
        app = d["applikation"] or ""
        lines.append(f"### {i}. {app} {gz} — {datum}")
        if d["leitsatz"]:
            ls = " ".join(d["leitsatz"].split())
            if len(ls) > 400:
                ls = ls[:397] + "..."
            lines.append(f"_Leitsatz:_ {ls}")
        if d["link"]:
            lines.append(f"<{d['link']}>")
        lines.append("")
    return "\n".join(lines).rstrip() + "\n"


def parse_args(argv: list[str]) -> argparse.Namespace:
    p = argparse.ArgumentParser(
        description="RIS-Judikatur-Suche (data.bka.gv.at v2.6) — Metadaten + Link.",
    )
    p.add_argument("--applikation", required=True, choices=APPLIKATIONEN)
    p.add_argument("--suchworte")
    p.add_argument("--geschaeftszahl")
    p.add_argument("--norm", help='z.B. "1319a ABGB"')
    p.add_argument("--rechtssatznummer")
    p.add_argument("--von", metavar="YYYY-MM-DD",
                   help="EntscheidungsdatumVon")
    p.add_argument("--bis", metavar="YYYY-MM-DD",
                   help="EntscheidungsdatumBis")
    p.add_argument("--im-ris-seit", choices=IM_RIS_SEIT_VALUES,
                   dest="im_ris_seit")
    p.add_argument("--pro-seite", choices=PRO_SEITE_VALUES, default="Twenty")
    p.add_argument("--seite", type=int, default=1)
    p.add_argument("--sortierung")
    p.add_argument("--sort-direction", choices=["Ascending", "Descending"],
                   dest="sort_direction")
    p.add_argument("--no-rechtssatz", action="store_true")
    p.add_argument("--no-text", action="store_true")
    p.add_argument("--json", action="store_true",
                   help="Strukturiertes JSON statt Markdown ausgeben")
    p.add_argument("--raw", action="store_true",
                   help="Roh-JSON der RIS-API ausgeben")
    p.add_argument("--timeout", type=float, default=30.0)
    p.add_argument("--retries", type=int, default=2,
                   help="Wiederholungsversuche bei HTTP-/Netzfehlern")
    p.add_argument("--retry-sleep", type=float, default=2.0)
    return p.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv if argv is not None else sys.argv[1:])

    if not any([args.suchworte, args.geschaeftszahl, args.norm,
                args.rechtssatznummer]):
        sys.stderr.write(
            "Fehler: mindestens --suchworte, --geschaeftszahl, --norm oder "
            "--rechtssatznummer angeben.\n"
        )
        return 2

    url = build_url(args)
    last_err: Exception | None = None
    for attempt in range(1 + args.retries):
        try:
            raw = http_get_json(url, timeout=args.timeout)
            break
        except (urllib.error.URLError, urllib.error.HTTPError, TimeoutError) as e:
            last_err = e
            if attempt < args.retries:
                time.sleep(args.retry_sleep * (attempt + 1))
            else:
                sys.stderr.write(f"RIS-Anfrage fehlgeschlagen: {e}\nURL: {url}\n")
                return 1
        except json.JSONDecodeError as e:
            sys.stderr.write(f"Antwort war kein JSON: {e}\nURL: {url}\n")
            return 1
    else:
        sys.stderr.write(f"Unerreichbar: {last_err}\n")
        return 1

    if args.raw:
        json.dump(raw, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
        return 0

    norm = normalize(raw)
    if args.json:
        json.dump(norm, sys.stdout, ensure_ascii=False, indent=2)
        sys.stdout.write("\n")
    else:
        sys.stdout.write(render_markdown(norm))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
