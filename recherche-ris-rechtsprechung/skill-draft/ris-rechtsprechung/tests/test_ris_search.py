"""Smoke tests for ris_search.py.

Two test classes:

* TestDocnumberMapping — pure unit tests, no network. Verifies the
  Dokumentennummer → HTML-URL mapping (regression guard for the JWT/Vwgh
  bug fixed in the Code-Review-Commit).

* TestRisLiveApi — live integration tests against data.bka.gv.at.
  Skipped when env RIS_SKIP_LIVE=1 is set. CI runs them weekly via
  workflow_dispatch / cron.

Pure stdlib + unittest, no Pip dependency.
"""

from __future__ import annotations

import io
import os
import re
import sys
import time
import unittest
import urllib.error
from pathlib import Path
from unittest.mock import patch

HERE = Path(__file__).resolve().parent
SCRIPT_DIR = HERE.parent / "scripts"
sys.path.insert(0, str(SCRIPT_DIR))

import ris_search  # noqa: E402

LIVE_SLEEP = 1.5  # RIS asks for 1–2 s between paginated requests
SKIP_LIVE = os.environ.get("RIS_SKIP_LIVE") == "1"


class TestDocnumberMapping(unittest.TestCase):
    def test_jwt_prefix_maps_to_vwgh(self):
        url = ris_search.docnumber_to_html_url("JWT_20210415_2020110034_00")
        self.assertIsNotNone(url)
        self.assertIn("/Dokumente/Vwgh/", url)

    def test_jjt_prefix_maps_to_justiz(self):
        url = ris_search.docnumber_to_html_url("JJT_20210415_OGH0002_0050OB00234_20B0000_000")
        self.assertIsNotNone(url)
        self.assertIn("/Dokumente/Justiz/", url)

    def test_jft_prefix_maps_to_vfgh(self):
        url = ris_search.docnumber_to_html_url("JFT_20200612_20G00012_2000_00")
        self.assertIsNotNone(url)
        self.assertIn("/Dokumente/Vfgh/", url)

    def test_bvwg_prefix_maps_to_bvwg(self):
        url = ris_search.docnumber_to_html_url("BVWGT_20240101_W123_2000000_1_00")
        self.assertIsNotNone(url)
        self.assertIn("/Dokumente/Bvwg/", url)

    def test_invalid_docnumber_returns_none(self):
        self.assertIsNone(ris_search.docnumber_to_html_url(""))
        self.assertIsNone(ris_search.docnumber_to_html_url("abc"))
        self.assertIsNone(ris_search.docnumber_to_html_url("X"))
        self.assertIsNone(ris_search.docnumber_to_html_url("a" * 60))


class TestDocnrClassification(unittest.TestCase):
    def test_rechtssatz_prefixes(self):
        for docnr in ("JJR_19880601_OGH0002_009OBA00110_8800000_003",
                      "JFR_19990101_19G00012_1900_00",
                      "JWR_2024050094_20260326L01"):
            self.assertEqual(ris_search.classify_docnr(docnr), "Rechtssatz", docnr)

    def test_volltext_prefixes(self):
        for docnr in ("JJT_19880601_OGH0002_009OBA00110_8800000_000",
                      "JFT_19990101_19G00012_1900_00",
                      "JWT_2024050094_20260326L01"):
            self.assertEqual(ris_search.classify_docnr(docnr), "Volltext", docnr)

    def test_unknown_prefixes_return_none(self):
        # BVWG/LVWG/Dsk-Dokumentnummern folgen der J{Court}{T|R}-Konvention
        # nicht und bleiben unklassifiziert.
        self.assertIsNone(ris_search.classify_docnr("BVWGT_20240101_W123_2000000_1_00"))
        self.assertIsNone(ris_search.classify_docnr("DSB_2023_X_001"))
        self.assertIsNone(ris_search.classify_docnr(None))
        self.assertIsNone(ris_search.classify_docnr(""))
        self.assertIsNone(ris_search.classify_docnr("XY"))


class TestNormalizeNorm(unittest.TestCase):
    def test_inserts_paragraph_sign_when_missing(self):
        self.assertEqual(ris_search.normalize_norm("ArbVG 105"),
                         ("ArbVG §105", "ArbVG 105"))
        self.assertEqual(ris_search.normalize_norm("ABGB 1319a"),
                         ("ABGB §1319a", "ABGB 1319a"))

    def test_canonical_form_unchanged(self):
        self.assertEqual(ris_search.normalize_norm("ABGB §1319a"),
                         ("ABGB §1319a", None))
        self.assertEqual(ris_search.normalize_norm("ArbVG §105"),
                         ("ArbVG §105", None))

    def test_whitespace_stripped_no_fix(self):
        self.assertEqual(ris_search.normalize_norm("  ABGB §1319a  "),
                         ("ABGB §1319a", None))

    def test_no_digit_after_kuerzel_unchanged(self):
        # Kein Pflicht-Muster — wird nicht angefasst.
        self.assertEqual(ris_search.normalize_norm("ABGB Allgemein"),
                         ("ABGB Allgemein", None))

    def test_single_token_unchanged(self):
        self.assertEqual(ris_search.normalize_norm("ABGB"), ("ABGB", None))

    def test_empty_and_none(self):
        self.assertEqual(ris_search.normalize_norm(""), ("", None))
        self.assertEqual(ris_search.normalize_norm(None), (None, None))


class TestDeriveVolltextDocnr(unittest.TestCase):
    def test_jjr_to_jjt_with_index_to_zero(self):
        derived = ris_search.derive_volltext_docnr(
            "JJR_19880601_OGH0002_009OBA00110_8800000_003"
        )
        self.assertEqual(derived, "JJT_19880601_OGH0002_009OBA00110_8800000_000")

    def test_jfr_to_jft(self):
        derived = ris_search.derive_volltext_docnr("JFR_19990101_19G00012_1900_005")
        self.assertEqual(derived, "JFT_19990101_19G00012_1900_000")

    def test_jwr_to_jwt(self):
        derived = ris_search.derive_volltext_docnr("JWR_2024050094_20260326L01_007")
        self.assertEqual(derived, "JWT_2024050094_20260326L01_000")

    def test_volltext_input_returns_none(self):
        # Eingabe ist bereits ein Volltext-Dokument — nichts abzuleiten.
        self.assertIsNone(ris_search.derive_volltext_docnr(
            "JJT_19880601_OGH0002_009OBA00110_8800000_000"
        ))

    def test_unknown_input_returns_none(self):
        self.assertIsNone(ris_search.derive_volltext_docnr("BVWGT_20240101_W123_2000000_1_00"))
        self.assertIsNone(ris_search.derive_volltext_docnr(None))
        self.assertIsNone(ris_search.derive_volltext_docnr(""))


def _fetch(**overrides):
    """Build args, fetch live, normalize. Returns the structured dict."""
    argv = ["--applikation", overrides.pop("applikation", "Justiz")]
    for flag, value in overrides.items():
        argv.append(f"--{flag.replace('_', '-')}")
        if value is not True:
            argv.append(str(value))
    args = ris_search.parse_args(argv)
    url = ris_search.build_url(args)
    raw = ris_search.fetch_with_retries(url, args)
    if raw is None:
        raise unittest.SkipTest(f"RIS API unreachable for {argv}")
    return ris_search.normalize(raw)


@unittest.skipIf(SKIP_LIVE, "Live RIS-API tests disabled (RIS_SKIP_LIVE=1)")
class TestRisLiveApi(unittest.TestCase):
    def setUp(self):
        time.sleep(LIVE_SLEEP)

    def test_suchworte_returns_hits(self):
        result = _fetch(applikation="Justiz", suchworte="Mietzinsminderung",
                        pro_seite="Ten")
        self.assertGreater(result["total_hits"], 0)
        self.assertGreaterEqual(len(result["documents"]), 1)
        doc = result["documents"][0]
        for key in ("dokumentnummer", "applikation", "geschaeftszahl",
                    "entscheidungsdatum", "link", "content_urls"):
            self.assertIn(key, doc, f"missing key: {key}")
        self.assertEqual(doc["applikation"], "Justiz")
        self.assertTrue(doc["link"], "expected link to be populated")

    def test_norm_canonical_format_returns_hits(self):
        # Regression guard: the canonical form "{Kürzel} §{Paragraph}"
        # was the very fix in the Code-Review-Commit.
        result = _fetch(applikation="Justiz", norm="ABGB §1319a",
                        pro_seite="Ten")
        self.assertGreater(
            result["total_hits"], 0,
            "ABGB §1319a should return hits in Justiz; if 0, the canonical "
            "Norm-format may have changed on the API side.",
        )

    def test_empty_result_does_not_error(self):
        # Improbable Suchworte → 0 hits, no exception, valid shape.
        result = _fetch(applikation="Justiz",
                        suchworte="XQZJUNK_NICHT_EXISTENT_4242_zzz",
                        pro_seite="Ten")
        self.assertEqual(result["total_hits"], 0)
        self.assertEqual(result["documents"], [])


class TestFormatDateDe(unittest.TestCase):
    def test_iso_to_de(self):
        self.assertEqual(ris_search.format_date_de("2023-02-28"), "28.02.2023")
        self.assertEqual(ris_search.format_date_de("1988-06-01"), "01.06.1988")

    def test_passes_through_when_unparseable(self):
        self.assertEqual(ris_search.format_date_de("28.02.2023"), "28.02.2023")
        self.assertEqual(ris_search.format_date_de("nope"), "nope")

    def test_falsy_returns_none(self):
        self.assertIsNone(ris_search.format_date_de(""))
        self.assertIsNone(ris_search.format_date_de(None))


class TestRenderMarkdownPolish(unittest.TestCase):
    """Smoke-Tests für die Output-Politur (Etappe 3)."""

    def _render(self, doc_overrides):
        base = {
            "dokumentnummer": "JJT_19890315_OGH0002_009OBA00279_8800000_000",
            "applikation": "Justiz",
            "gericht": None,
            "doc_type": "Volltext",
            "rechtssatznummer": None,
            "geschaeftszahl": "8ObA2/23x",
            "geschaeftszahlen": ["8ObA2/23x"],
            "entscheidungsdatum": "2023-02-28",
            "leitsatz": None,
            "normen": [],
            "fachgebiete": [],
            "entscheidungstexte_count": 0,
            "link": "https://ris.bka.gv.at/Dokumente/Justiz/JJT_…/JJT_….html",
            "volltext_url": None,
            "content_urls": {},
        }
        base.update(doc_overrides)
        result = {"total_hits": 1, "page": 1, "page_size": 10,
                  "documents": [base]}
        return ris_search.render_markdown(result)

    def test_heading_uses_de_date_and_court_when_present(self):
        out = self._render({"gericht": "OGH"})
        self.assertIn("OGH 8ObA2/23x vom 28.02.2023", out)
        self.assertIn("[Volltext]", out)

    def test_heading_falls_back_to_applikation_without_gericht(self):
        out = self._render({"gericht": None})
        self.assertIn("Justiz 8ObA2/23x vom 28.02.2023", out)

    def test_rechtssatz_label_includes_rs_number(self):
        out = self._render({"doc_type": "Rechtssatz",
                            "rechtssatznummer": "RS0051942"})
        self.assertIn("[Rechtssatz RS0051942]", out)

    def test_norm_and_fachgebiet_render_when_present(self):
        out = self._render({"normen": ["ArbVG §96", "ABGB §879"],
                            "fachgebiete": ["Arbeitsrecht"]})
        self.assertIn("**Norm:** ArbVG §96, ABGB §879", out)
        self.assertIn("**Fachgebiet:** Arbeitsrecht", out)
        self.assertNotIn("**Rechtsgebiet:**", out)
        self.assertNotIn("**ECLI:**", out)

    def test_link_uses_markdown_link_syntax(self):
        out = self._render({})
        self.assertIn(
            "- [Zur Entscheidung im RIS](https://ris.bka.gv.at/Dokumente/Justiz/",
            out,
        )

    def test_rechtssatz_renders_stamm_volltext_link(self):
        out = self._render({
            "doc_type": "Rechtssatz",
            "link": "https://www.ris.bka.gv.at/Dokument.wxe?...JJR_..._003",
            "volltext_url": "https://www.ris.bka.gv.at/Dokument.wxe?Abfrage=Justiz&Dokumentnummer=JJT_...",
        })
        self.assertIn("[Rechtssatz im RIS](", out)
        self.assertIn("[Volltext der Stammentscheidung](", out)

    def test_zitate_count_appended_when_more_than_one(self):
        out = self._render({"doc_type": "Rechtssatz",
                            "entscheidungstexte_count": 22})
        self.assertIn("Auch zitiert in 21 weiteren Entscheidungen", out)

    def test_zitate_count_hidden_when_one_or_zero(self):
        out = self._render({"entscheidungstexte_count": 1})
        self.assertNotIn("Auch zitiert", out)


class TestNullHint(unittest.TestCase):
    """Smoke-Test für den Hinweis bei 0 Suchworte-Treffern."""

    def test_template_has_placeholders(self):
        self.assertIn("{query}", ris_search.SUCHWORTE_NULL_HINT_TEMPLATE)
        self.assertIn("{query_url}", ris_search.SUCHWORTE_NULL_HINT_TEMPLATE)
        self.assertIn("Volltext-Index", ris_search.SUCHWORTE_NULL_HINT_TEMPLATE)
        self.assertIn("site:`-Suche", ris_search.SUCHWORTE_NULL_HINT_TEMPLATE)


class TestWebsearchQueryBuilder(unittest.TestCase):
    def _build(self, **overrides):
        argv = ["--applikation", overrides.pop("applikation", "Justiz")]
        for flag, value in overrides.items():
            argv.append(f"--{flag.replace('_', '-')}")
            argv.append(str(value))
        # Mindestens ein Suchparam pflicht — für Tests mitgeben falls nicht da.
        if not any(f in overrides for f in
                   ("suchworte", "geschaeftszahl", "norm",
                    "rechtssatznummer", "schlagworte")):
            argv.extend(["--suchworte", "dummy"])
        return ris_search.build_websearch_query(ris_search.parse_args(argv))

    def test_basic_suchworte(self):
        q = self._build(suchworte="Lackierungsabteilung")
        self.assertEqual(q, "site:ris.bka.gv.at Justiz Lackierungsabteilung")

    def test_geschaeftszahl_quoted(self):
        q = self._build(geschaeftszahl="9ObA279/88")
        self.assertIn('"9ObA279/88"', q)

    def test_combined_norm_and_suchworte(self):
        q = self._build(suchworte="Kündigung", norm="ArbVG §105")
        self.assertIn("Kündigung", q)
        self.assertIn("ArbVG §105", q)
        self.assertTrue(q.startswith("site:ris.bka.gv.at Justiz"))

    def test_applikation_vfgh_appears(self):
        q = self._build(applikation="Vfgh", suchworte="Versammlungsfreiheit")
        self.assertIn("Vfgh", q)

    def test_date_range_adds_after_before(self):
        q = self._build(suchworte="Mietzins",
                        von="2020-01-01", bis="2024-12-31")
        self.assertIn("after:2020", q)
        self.assertIn("before:2024", q)

    def test_vwgh_result_has_vwgh_link(self):
        # Live regression guard for the JWT-prefix → Vwgh fix.
        # Die API liefert den Link je nach Treffer entweder als
        # /Dokumente/Vwgh/{nr}/{nr}.html oder als
        # Dokument.wxe?Abfrage=Vwgh&Dokumentennummer={nr} — beides ist
        # eine valide RIS-URL für Vwgh; wir akzeptieren beide.
        result = _fetch(applikation="Vwgh", suchworte="Bescheid",
                        pro_seite="Ten")
        self.assertGreater(result["total_hits"], 0)
        for doc in result["documents"]:
            docnr = doc["dokumentnummer"] or ""
            link = doc["link"] or ""
            if re.match(r"^JW[TR]", docnr):
                self.assertRegex(
                    link, r"(?:/Vwgh/|Abfrage=Vwgh)",
                    f"JW* docnr {docnr!r} should yield a Vwgh-marked link; got {link!r}",
                )
                # Unabhängig prüfen: die abgeleitete URL aus dem
                # Prefix-Mapping muss /Vwgh/ enthalten — das ist die
                # eigentliche Regression-Garantie für den JWT-Bug.
                derived = ris_search.docnumber_to_html_url(docnr)
                self.assertIsNotNone(derived)
                self.assertIn(
                    "/Vwgh/", derived,
                    f"docnumber_to_html_url({docnr!r}) must map to /Vwgh/",
                )
                return
        self.skipTest("No JW-prefixed result on first page; cannot assert mapping.")


class TestBuildUrlSortDefault(unittest.TestCase):
    def _build(self, *extra):
        argv = ["--applikation", "Justiz", "--suchworte", "x"] + list(extra)
        return ris_search.build_url(ris_search.parse_args(argv))

    def test_default_is_datum_descending(self):
        url = self._build()
        self.assertIn("Sortierung=Datum", url)
        self.assertIn("SortDirection=Descending", url)

    def test_explicit_sortierung_overrides_default(self):
        url = self._build("--sortierung", "Relevanz")
        self.assertIn("Sortierung=Relevanz", url)
        # Wenn der User Sortierung explizit setzt, soll der Default-
        # Sort-Direction NICHT zusaetzlich gesetzt werden.
        self.assertNotIn("SortDirection=", url)

    def test_explicit_sort_direction_only(self):
        url = self._build("--sort-direction", "Ascending")
        self.assertIn("SortDirection=Ascending", url)
        self.assertNotIn("Sortierung=Datum", url)


class TestFetchPagesNormalizedAutoPagination(unittest.TestCase):
    def _args(self, **kwargs):
        argv = ["--applikation", "Justiz", "--suchworte", "x",
                "--retries", "0", "--retry-sleep", "0",
                "--pause-pagination", "0"]
        for k, v in kwargs.items():
            flag = f"--{k.replace('_', '-')}"
            if v is True:
                argv.append(flag)
            else:
                argv.extend([flag, str(v)])
        return ris_search.parse_args(argv)

    def _page(self, total: int, docs: list[dict], page_no: int, page_size: int = 10):
        return {
            "OgdSearchResult": {
                "OgdDocumentResults": {
                    "Hits": {
                        "#text": str(total),
                        "@pageNumber": str(page_no),
                        "@pageSize": str(page_size),
                    },
                    "OgdDocumentReference": [
                        {"Data": {"Metadaten": {
                            "Technisch": {"ID": d["id"], "Applikation": "Justiz"},
                            "Allgemein": {"DokumentUrl": d.get("url")},
                            "Judikatur": {},
                        }}}
                        for d in docs
                    ],
                }
            }
        }

    def test_single_page_when_alle_seiten_off(self):
        args = self._args()
        page1 = self._page(7, [{"id": f"JJT_a_{i}_000"} for i in range(7)], 1)
        with patch.object(ris_search, "fetch_with_retries", return_value=page1) as m:
            result = ris_search.fetch_pages_normalized(args)
        self.assertEqual(m.call_count, 1)
        self.assertEqual(len(result["documents"]), 7)
        self.assertNotIn("pages_fetched", result)

    def test_alle_seiten_aggregates_until_total_reached(self):
        args = self._args(alle_seiten=True, max_seiten=5, pro_seite="Ten")
        # 10 + 10 + 5 = 25, total = 25 → should stop after 3 pages
        pages = [
            self._page(25, [{"id": f"JJT_p1_{i}_000"} for i in range(10)], 1, 10),
            self._page(25, [{"id": f"JJT_p2_{i}_000"} for i in range(10)], 2, 10),
            self._page(25, [{"id": f"JJT_p3_{i}_000"} for i in range(5)], 3, 10),
        ]
        with patch.object(ris_search, "fetch_with_retries", side_effect=pages) as m:
            result = ris_search.fetch_pages_normalized(args)
        self.assertEqual(m.call_count, 3)
        self.assertEqual(result["pages_fetched"], 3)
        self.assertEqual(len(result["documents"]), 25)

    def test_alle_seiten_capped_by_max_seiten(self):
        args = self._args(alle_seiten=True, max_seiten=2, pro_seite="Ten")
        pages = [
            self._page(100, [{"id": f"JJT_p1_{i}_000"} for i in range(10)], 1, 10),
            self._page(100, [{"id": f"JJT_p2_{i}_000"} for i in range(10)], 2, 10),
            # Sollte gar nicht abgerufen werden (Cap = 2)
            self._page(100, [{"id": f"JJT_p3_{i}_000"} for i in range(10)], 3, 10),
        ]
        with patch.object(ris_search, "fetch_with_retries", side_effect=pages) as m:
            result = ris_search.fetch_pages_normalized(args)
        self.assertEqual(m.call_count, 2)
        self.assertEqual(result["pages_fetched"], 2)
        self.assertEqual(len(result["documents"]), 20)

    def test_alle_seiten_stops_on_empty_page(self):
        args = self._args(alle_seiten=True, max_seiten=5, pro_seite="Ten")
        pages = [
            self._page(15, [{"id": f"JJT_p1_{i}_000"} for i in range(10)], 1, 10),
            self._page(15, [], 2, 10),  # leere Seite
        ]
        with patch.object(ris_search, "fetch_with_retries", side_effect=pages) as m:
            result = ris_search.fetch_pages_normalized(args)
        self.assertEqual(m.call_count, 2)
        self.assertEqual(result["pages_fetched"], 1)
        self.assertEqual(len(result["documents"]), 10)


class TestRenderMarkdownPagination(unittest.TestCase):
    def test_header_reflects_multi_page_aggregation(self):
        result = {
            "total_hits": 25, "page": 1, "page_size": 10, "pages_fetched": 3,
            "documents": [],
        }
        out = ris_search.render_markdown(result)
        self.assertIn("**Treffer:** 25", out)
        self.assertIn("Seiten 1–3 geholt", out)


class TestAttribution(unittest.TestCase):
    def test_normalize_includes_attribution(self):
        result = ris_search.normalize({"OgdSearchResult": {"OgdDocumentResults": {}}})
        self.assertIn("attribution", result)
        self.assertIn("CC BY 4.0", result["attribution"])
        self.assertIn("RIS", result["attribution"])

    def test_render_markdown_appends_attribution_footer(self):
        result = {
            "total_hits": 0, "page": 1, "page_size": 10,
            "documents": [],
            "attribution": ris_search.ATTRIBUTION_TEXT,
        }
        out = ris_search.render_markdown(result)
        self.assertIn("CC BY 4.0", out)
        self.assertIn("Bundeskanzleramt", out)
        self.assertIn("Bundes-/Landesgesetzblatt", out)
        # Footer steht am Ende, nach dem Trenner
        self.assertTrue(out.rstrip().endswith("Landesgesetzblatt._"),
                        f"Attribution must be the final line; got tail: {out[-200:]!r}")

    def test_render_markdown_falls_back_to_default_attribution(self):
        # Wenn das Result-Dict keine 'attribution' enthaelt (z. B. aus
        # aelterem Code-Pfad), faellt render_markdown auf den Modul-Default
        # zurueck — die Lizenz darf nie aus dem Output verschwinden.
        result = {"total_hits": 0, "page": 1, "page_size": 10, "documents": []}
        out = ris_search.render_markdown(result)
        self.assertIn("CC BY 4.0", out)


def _http_error(code: int, body: bytes = b"") -> urllib.error.HTTPError:
    return urllib.error.HTTPError(
        url="http://x",
        code=code,
        msg="err",
        hdrs=None,
        fp=io.BytesIO(body),
    )


class TestFetchWithRetriesErrorHandling(unittest.TestCase):
    """4xx werden nicht retried, 5xx + Netzfehler schon."""

    def _args(self, retries: int = 2):
        return ris_search.parse_args([
            "--applikation", "Justiz", "--suchworte", "x",
            "--retries", str(retries), "--retry-sleep", "0",
            "--timeout", "1",
        ])

    def test_http_400_is_not_retried(self):
        args = self._args(retries=2)
        with patch.object(ris_search, "http_get_json",
                          side_effect=_http_error(400, b"Missing parameter")) as m, \
             patch.object(sys, "stderr", new_callable=io.StringIO) as err:
            result = ris_search.fetch_with_retries("http://x", args)
        self.assertIsNone(result)
        self.assertEqual(m.call_count, 1, "HTTP 400 must not retry")
        self.assertIn("HTTP 400", err.getvalue())
        self.assertIn("Missing parameter", err.getvalue())

    def test_http_404_is_not_retried(self):
        args = self._args(retries=2)
        with patch.object(ris_search, "http_get_json",
                          side_effect=_http_error(404)) as m, \
             patch.object(sys, "stderr", new_callable=io.StringIO):
            result = ris_search.fetch_with_retries("http://x", args)
        self.assertIsNone(result)
        self.assertEqual(m.call_count, 1)

    def test_http_500_is_retried_until_exhausted(self):
        args = self._args(retries=2)
        # Diagnose-Ping nach erschoepften Retries wegmocken — er ruft
        # sonst zusaetzlich http_get_json gegen /version auf.
        with patch.object(ris_search, "http_get_json",
                          side_effect=_http_error(500)) as m, \
             patch.object(ris_search, "_emit_unreachable_diagnosis"), \
             patch.object(sys, "stderr", new_callable=io.StringIO):
            result = ris_search.fetch_with_retries("http://x", args)
        self.assertIsNone(result)
        self.assertEqual(m.call_count, 1 + args.retries)

    def test_url_error_is_retried(self):
        args = self._args(retries=2)
        with patch.object(ris_search, "http_get_json",
                          side_effect=urllib.error.URLError("net down")) as m, \
             patch.object(ris_search, "_emit_unreachable_diagnosis"), \
             patch.object(sys, "stderr", new_callable=io.StringIO):
            result = ris_search.fetch_with_retries("http://x", args)
        self.assertIsNone(result)
        self.assertEqual(m.call_count, 1 + args.retries)

    def test_eventual_success_after_transient_failure(self):
        args = self._args(retries=2)
        seq = [urllib.error.URLError("flap"), {"OgdSearchResult": {}}]
        with patch.object(ris_search, "http_get_json", side_effect=seq) as m, \
             patch.object(sys, "stderr", new_callable=io.StringIO):
            result = ris_search.fetch_with_retries("http://x", args)
        self.assertEqual(result, {"OgdSearchResult": {}})
        self.assertEqual(m.call_count, 2)


class TestCheckVersionEndpoint(unittest.TestCase):
    def test_returns_reachable_with_version_text(self):
        with patch.object(ris_search, "http_get_json",
                          return_value={"Version": "2.6.42"}):
            reachable, ver, latency = ris_search.check_version_endpoint()
        self.assertTrue(reachable)
        self.assertEqual(ver, "2.6.42")
        self.assertGreaterEqual(latency, 0)

    def test_returns_reachable_without_version_key(self):
        with patch.object(ris_search, "http_get_json", return_value={}):
            reachable, ver, latency = ris_search.check_version_endpoint()
        self.assertTrue(reachable)
        self.assertIsNone(ver)
        self.assertGreaterEqual(latency, 0)

    def test_unreachable_on_url_error(self):
        with patch.object(ris_search, "http_get_json",
                          side_effect=urllib.error.URLError("down")):
            reachable, ver, latency = ris_search.check_version_endpoint()
        self.assertFalse(reachable)
        self.assertIsNone(ver)
        self.assertEqual(latency, -1)

    def test_unreachable_on_http_error(self):
        with patch.object(ris_search, "http_get_json",
                          side_effect=_http_error(503)):
            reachable, _, _ = ris_search.check_version_endpoint()
        self.assertFalse(reachable)

    def test_emit_diagnosis_when_api_reachable(self):
        with patch.object(ris_search, "check_version_endpoint",
                          return_value=(True, "2.6.42", 87)), \
             patch.object(sys, "stderr", new_callable=io.StringIO) as err:
            ris_search._emit_unreachable_diagnosis("http://x")
        out = err.getvalue()
        self.assertIn("RIS-API erreichbar", out)
        self.assertIn("2.6.42", out)
        self.assertIn("/Judikatur scheitert", out)

    def test_emit_diagnosis_when_api_down(self):
        with patch.object(ris_search, "check_version_endpoint",
                          return_value=(False, None, -1)), \
             patch.object(sys, "stderr", new_callable=io.StringIO) as err:
            ris_search._emit_unreachable_diagnosis("http://x")
        out = err.getvalue()
        self.assertIn("komplett nicht erreichbar", out)

    def test_diagnosis_only_runs_after_5xx_exhausted_not_on_4xx(self):
        """4xx terminiert sofort — kein Diagnose-Ping."""
        args = ris_search.parse_args([
            "--applikation", "Justiz", "--suchworte", "x",
            "--retries", "2", "--retry-sleep", "0", "--timeout", "1",
        ])
        with patch.object(ris_search, "http_get_json",
                          side_effect=_http_error(400, b"bad")), \
             patch.object(ris_search, "check_version_endpoint") as version_mock, \
             patch.object(sys, "stderr", new_callable=io.StringIO):
            ris_search.fetch_with_retries("http://x", args)
        version_mock.assert_not_called()

    def test_diagnosis_runs_after_5xx_exhausted(self):
        args = ris_search.parse_args([
            "--applikation", "Justiz", "--suchworte", "x",
            "--retries", "1", "--retry-sleep", "0", "--timeout", "1",
        ])
        with patch.object(ris_search, "http_get_json",
                          side_effect=_http_error(500)), \
             patch.object(ris_search, "check_version_endpoint",
                          return_value=(True, "2.6.42", 50)) as version_mock, \
             patch.object(sys, "stderr", new_callable=io.StringIO) as err:
            ris_search.fetch_with_retries("http://x", args)
        version_mock.assert_called_once()
        self.assertIn("RIS-API erreichbar", err.getvalue())

    def test_diagnosis_runs_after_network_error_exhausted(self):
        args = ris_search.parse_args([
            "--applikation", "Justiz", "--suchworte", "x",
            "--retries", "1", "--retry-sleep", "0", "--timeout", "1",
        ])
        with patch.object(ris_search, "http_get_json",
                          side_effect=urllib.error.URLError("down")), \
             patch.object(ris_search, "check_version_endpoint",
                          return_value=(False, None, -1)) as version_mock, \
             patch.object(sys, "stderr", new_callable=io.StringIO) as err:
            ris_search.fetch_with_retries("http://x", args)
        version_mock.assert_called_once()
        self.assertIn("komplett nicht erreichbar", err.getvalue())


def _make_doc(judikatur_overrides=None, allgemein_overrides=None,
              technisch_overrides=None):
    """Hilfs-Builder fuer Roh-API-Treffer (ein OgdDocumentReference)."""
    technisch = {"ID": "JJT_20240101_OGH0002_0050OB00100_2400000_000",
                 "Applikation": "Justiz", "Organ": "OGH"}
    technisch.update(technisch_overrides or {})
    allgemein = {"DokumentUrl": "https://ris.bka.gv.at/..."}
    allgemein.update(allgemein_overrides or {})
    judikatur: dict = {}
    judikatur.update(judikatur_overrides or {})
    return {
        "OgdSearchResult": {
            "OgdDocumentResults": {
                "Hits": {"#text": "1", "@pageNumber": "1", "@pageSize": "10"},
                "OgdDocumentReference": [{"Data": {"Metadaten": {
                    "Technisch": technisch,
                    "Allgemein": allgemein,
                    "Judikatur": judikatur,
                }}}],
            }
        }
    }


class TestShrinkwrapFieldAudit(unittest.TestCase):
    """Konditionale Aufnahme der shrinkwrap-Audit-Felder.

    Wichtig (Issue #18): Felder duerfen NUR im Output erscheinen, wenn
    die API einen nicht-leeren Wert geliefert hat — sonst hat #18 sie
    schon einmal aus dem Output entfernt mit der Begruendung "leer
    oder unzuverlaessig".
    """

    def test_no_extra_fields_when_api_empty(self):
        doc = ris_search.normalize(_make_doc())["documents"][0]
        for key in ("veroeffentlicht", "geaendert", "ecli",
                    "api_dokumenttyp", "schlagworte", "entscheidungsart",
                    "anmerkung", "fundstelle", "rechtsgebiete"):
            self.assertNotIn(key, doc,
                             f"empty {key} must not appear in output dict")

    def test_veroeffentlicht_and_geaendert_extracted(self):
        doc = ris_search.normalize(_make_doc(
            allgemein_overrides={"Veroeffentlicht": "2024-02-15",
                                 "Geaendert": "2024-03-01"},
        ))["documents"][0]
        self.assertEqual(doc["veroeffentlicht"], "2024-02-15")
        self.assertEqual(doc["geaendert"], "2024-03-01")

    def test_ecli_extracted(self):
        doc = ris_search.normalize(_make_doc(
            judikatur_overrides={
                "EuropeanCaseLawIdentifier": "ECLI:AT:OGH0002:2024:0050OB00100.24X.0101.000",
            },
        ))["documents"][0]
        self.assertIn("ecli", doc)
        self.assertTrue(doc["ecli"].startswith("ECLI:AT:OGH"))

    def test_api_dokumenttyp_extracted(self):
        doc = ris_search.normalize(_make_doc(
            judikatur_overrides={"Dokumenttyp": "Entscheidungstext"},
        ))["documents"][0]
        self.assertEqual(doc["api_dokumenttyp"], "Entscheidungstext")

    def test_schlagworte_extracted_as_list(self):
        doc = ris_search.normalize(_make_doc(
            judikatur_overrides={"Schlagworte": {"item": ["Miete", "Kuendigung"]}},
        ))["documents"][0]
        self.assertEqual(doc["schlagworte"], ["Miete", "Kuendigung"])

    def test_court_specific_fields_from_justiz_block(self):
        doc = ris_search.normalize(_make_doc(
            judikatur_overrides={"Justiz": {
                "Gericht": "OGH",
                "Entscheidungsart": "Beschluss",
                "Anmerkung": "Veroeffentlicht: SZ 2024/15.",
                "Fundstelle": "SZ 2024/15",
                "Rechtsgebiete": {"item": ["Zivilrecht", "Mietrecht"]},
            }},
        ))["documents"][0]
        self.assertEqual(doc["entscheidungsart"], "Beschluss")
        self.assertIn("anmerkung", doc)
        self.assertEqual(doc["fundstelle"], "SZ 2024/15")
        self.assertEqual(doc["rechtsgebiete"], ["Zivilrecht", "Mietrecht"])

    def test_entscheidungsart_works_for_vfgh_block(self):
        doc = ris_search.normalize(_make_doc(
            technisch_overrides={"ID": "JFT_20240101_19G00012_2400_00",
                                 "Applikation": "Vfgh", "Organ": "VfGH"},
            judikatur_overrides={"Vfgh": {"Gericht": "VfGH",
                                          "Entscheidungsart": "Erkenntnis"}},
        ))["documents"][0]
        self.assertEqual(doc["entscheidungsart"], "Erkenntnis")


class TestRenderMarkdownAuditFields(unittest.TestCase):
    """Audit-Felder werden im Markdown-Output nur bei Werten angezeigt."""

    def _doc(self, **overrides):
        base = {
            "dokumentnummer": "JJT_…", "applikation": "Justiz",
            "gericht": "OGH", "doc_type": "Volltext",
            "rechtssatznummer": None, "geschaeftszahl": "5Ob100/24x",
            "geschaeftszahlen": ["5Ob100/24x"],
            "entscheidungsdatum": "2024-01-01",
            "leitsatz": None, "normen": [], "fachgebiete": [],
            "entscheidungstexte_count": 0,
            "link": "https://ris.bka.gv.at/x", "volltext_url": None,
            "content_urls": {},
        }
        base.update(overrides)
        return base

    def _render(self, doc):
        return ris_search.render_markdown({
            "total_hits": 1, "page": 1, "page_size": 10, "documents": [doc],
        })

    def test_entscheidungsart_appears_in_heading(self):
        out = self._render(self._doc(entscheidungsart="Beschluss"))
        self.assertIn("— Beschluss", out)

    def test_no_dash_in_heading_when_no_entscheidungsart(self):
        out = self._render(self._doc())
        heading = next(line for line in out.splitlines() if line.startswith("### "))
        self.assertNotIn("—", heading)

    def test_ecli_rendered_when_present(self):
        out = self._render(self._doc(ecli="ECLI:AT:OGH0002:2024:0050OB00100.24X.0101.000"))
        self.assertIn("**ECLI:**", out)
        self.assertIn("ECLI:AT:OGH0002", out)

    def test_rechtsgebiet_rendered_when_present(self):
        out = self._render(self._doc(rechtsgebiete=["Zivilrecht", "Mietrecht"]))
        self.assertIn("**Rechtsgebiet:** Zivilrecht, Mietrecht", out)

    def test_fundstelle_rendered_when_present(self):
        out = self._render(self._doc(fundstelle="SZ 2024/15"))
        self.assertIn("**Fundstelle:** SZ 2024/15", out)

    def test_anmerkung_rendered_and_truncated(self):
        long_note = "Sehr lange Anmerkung. " * 30
        out = self._render(self._doc(anmerkung=long_note))
        self.assertIn("_Anmerkung:_", out)
        self.assertIn("...", out)

    def test_schlagworte_rendered_when_present(self):
        out = self._render(self._doc(schlagworte=["Miete", "Kuendigung"]))
        self.assertIn("**Schlagworte:** Miete, Kuendigung", out)

    def test_audit_field_keys_absent_when_doc_lacks_them(self):
        out = self._render(self._doc())
        for key in ("**ECLI:**", "**Rechtsgebiet:**", "**Fundstelle:**",
                    "_Anmerkung:_", "**Schlagworte:**"):
            self.assertNotIn(key, out, f"unexpected: {key}")


if __name__ == "__main__":
    unittest.main(verbosity=2)
