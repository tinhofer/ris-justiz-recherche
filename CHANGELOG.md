# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

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
