# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Added
- CC-BY-4.0-Namensnennung am Ende jedes Markdown-Outputs und als
  `attribution`-Feld im JSON-Output. RIS-OGD-Daten stehen unter
  CC BY 4.0; bei Wiedergabe ist die Quelle zu nennen — der Footer
  enthält zusätzlich den Hinweis, dass nur das Bundes-/
  Landesgesetzblatt rechtlich verbindlich ist (OGD-FAQ, BKA).
- `SKILL.md`-Abschnitte zur `*`-Suchoperator-Einschränkung der API
  (nur ein Platzhalter pro Wort, im Web mehrere möglich), zur
  Norm-Suche → Rechtssatz-Verteilung und zum Massendownload-
  Schwellwert (`ris.it@bka.gv.at` informieren).
- Smoke-Tests für `ris_search.py` (Unit + Live-Integration) und
  GitHub-Action `ris-smoke-test.yml`, die die Tests sonntags um
  03:00 UTC gegen die Live-API laufen lässt (#3).
- GitHub-Action `ris-query.yml` — `workflow_dispatch`-Workflow für
  ad-hoc Live-Recherchen aus dem Browser/Mobile, Ergebnis im
  Step-Summary (#6).
- Doktyp-Label (`[Volltext]` / `[Rechtssatz <RS-Nr.>]`) im
  Markdown-Output und automatisch abgeleiteter Volltext-Link bei
  Rechtssatz-Treffern aus der OGH/VfGH/VwGH-Konvention `J{Court}{T|R}`
  (#8).
- `--norm`-Eingabe ohne `§`-Zeichen wird automatisch zur kanonischen
  Form `{Kürzel} §{Paragraph}` ergänzt; Hinweis im Markdown-/JSON-Output (#9).
- Hinweisblock bei 0 Treffern auf `Suchworte`-Anfragen, der die
  bekannte OGD-Volltext-Index-Lücke (alte Entscheidungen vor ~1990)
  erklärt (#10).
- Web-Search-Fallback (Etappe 1): bei 0 `Suchworte`-Treffern erzeugt
  das Skript automatisch eine Google `site:`-Such-Query; im
  JSON-Output als `websearch_query`-Feld, im Markdown im
  Hinweis-Block (#14).

### Changed
- Output-Politur (Etappe 3): Heading im Legal-Citation-Stil
  (`OGH 8ObA2/23x vom 28.02.2023 [Volltext]`), Datum DE-formatiert,
  Norm/Fachgebiet als eigene Zeilen, Markdown-Link-Syntax,
  „Auch zitiert in N weiteren Entscheidungen"-Counter bei
  Rechtssätzen (#15).
- Rechtssatz-Heading nutzt Stamm-Entscheidung
  (`Entscheidungstexte.item[0]`) als Quelle für Geschäftszahl
  und Datum statt der API-internen verketteten Werte; Volltext-URL
  kommt direkt aus der API statt aus der Heuristik (#17).

### Fixed
- `Vwgh`-Live-Test akzeptiert beide RIS-URL-Formen
  (`/Dokumente/Vwgh/...` und `Dokument.wxe?Abfrage=Vwgh&...`) (#5).
- Hinweis-Link zur RIS-Web-Suche zeigte auf 404 — jetzt korrekter
  Pfad `https://www.ris.bka.gv.at/Judikatur/` (#13).

### Removed
- Rechtsgebiet- und ECLI-Felder aus dem Output entfernt (in der
  API-Antwort sind sie für Judikatur leer oder unzuverlässig) (#18).
- `Add (temp)`-Diagnose-Workflow `ris-query-raw.yml` (eingeführt
  in #16, nach erfolgter API-Pfad-Diagnose entfernt in #17).

### Docs
- Whitelist-Hinweise für Claude.ai-Custom-Skills um `ris.bka.gv.at`
  und `www.ris.bka.gv.at` ergänzt (#11, #12).

### Removed (Scaffold-Aufräumen)
- Kaputtes Scaffold-CI `ci.yml` aus dem Initial-Setup entfernt
  (kollidierte mit den späteren RIS-spezifischen Workflows) (#4).

## [0.2.0] - 2026-05-02

### Added
- Recherche-Bericht zur RIS-OGD-API v2.6 unter
  `recherche-ris-rechtsprechung/` (README, notes, Referenz-Auszüge).
- Claude-Code-Skill `ris-rechtsprechung` (SKILL.md + Python-Wrapper
  `scripts/ris_search.py`) für Abfragen am `/Judikatur`-Endpoint.
  Liefert Metadaten + RIS-Link, kein Volltext-Download.
- `--schlagworte` als eigener Suchparameter im Wrapper.
- Mapping der Dokumentennummer-Präfixe auf direkte HTML-URLs für alle
  unterstützten Applikationen.

### Changed
- Skill-Wrapper auf Python 3 (Standardbibliothek) umgestellt; Scope auf
  Metadaten + Link festgezurrt.
- `SucheNachRechtssatz` / `SucheNachText` werden nur noch bei
  `Suchworte`-Anfragen gesendet (verhinderte zuvor unnötig Treffer bei
  Geschäftszahl-/Norm-/Schlagwort-Suche).
- `--norm`-Beispiel auf kanonische Form `{Kürzel} §{Paragraph}` korrigiert
  (A/B-Test gegen Live-API: 138×–300× mehr Treffer).
- Aufruf-Block in `SKILL.md` umgebungsneutral: `cd` in den Skill-Ordner +
  relativer Pfad. Pfad-Tabelle für Claude Code (Linux/macOS/Windows) und
  Claude.ai-Sandbox; Python-Launcher-Reihenfolge dokumentiert.
- Installationsanleitung um Claude.ai-Custom-Skill-Upload (ZIP +
  Network-Access für `data.bka.gv.at`) erweitert.

### Fixed
- `JWT`-Präfix zeigt nun korrekt auf `Vwgh` statt `Justiz` (verifiziert via
  Live-Requests).
- Retry-Logik in `fetch_with_retries()` konsolidiert; `JSONDecodeError`
  ist Teil des Retry-Tupels.
- `normalize()` liefert für `Entscheidungsdatum` einen String statt eines
  `{'#text': …}`-Dicts; Leitsatz-Lookup deckt nun alle 11 Applikationen ab
  (vorher 5).

## [0.1.0] - 2026-01-02

### Added
- Initiales Repository-Scaffold (README, CONTRIBUTING, MIT-Lizenz,
  EditorConfig, `.gitignore`, GitHub-Issue-/PR-Templates, CI-Workflow,
  `scripts/apply-best-practices.sh`).
