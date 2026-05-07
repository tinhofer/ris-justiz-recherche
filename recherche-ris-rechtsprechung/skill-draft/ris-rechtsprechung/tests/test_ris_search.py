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

import os
import re
import sys
import time
import unittest
from pathlib import Path

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


if __name__ == "__main__":
    unittest.main(verbosity=2)
