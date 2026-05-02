# Recherche-Notizen: RIS-API Rechtsprechungs-Abfragen

## Auftrag
- Repo `tinhofer/ris-justiz-recherche` analysieren
- Verstehen, wie über die RIS-API Rechtsprechung abgefragt wird
- Auf den Erkenntnissen aufbauend einen **Claude-Code-Skill** entwerfen
- User-Hinweis: Organisation https://github.com/shrinkwrap-legal als Referenz

## Beobachtung zum Untersuchungs-Repo
- `tinhofer/ris-justiz-recherche` selbst enthält **keinen** RIS-spezifischen Code,
  sondern nur ein Claude-Code-Scaffold (README, CONTRIBUTING, GitHub-Templates,
  `scripts/apply-best-practices.sh`).
- `Agent.md` weist an, einen Recherche-Ordner mit `notes.md`/`README.md` anzulegen
  und nur eigene Artefakte (keine Fremd-Repos) zu committen.
- Der Untersuchungsgegenstand muss extern beschafft werden.

## Quellen, auf die ich mich stütze

| Quelle | Wert |
|---|---|
| `shrinkwrap-legal/shrinkwrap-legal-api`, Datei `RisAdapterImpl.java` | Konkreter REST-Client, Base-URL & URL-Templates |
| `shrinkwrap-legal/shrinkwrap-legal-api`, Pakete `dto/` und `dto/enums/` | DTO-Struktur der JSON-Antwort, Werte des Parameters `Applikation` |
| Kommentar in `RisAdapter.java`: `https://data.bka.gv.at/ris/ogd/v2.6/Documents/Dokumentation_OGD-RIS_API.pdf` | Offizielle PDF-Doku (im Sandbox nicht ladbar, Verweis dokumentiert) |
| `philrox/ris-mcp-ts` (TypeScript MCP-Server) | Vollständigere Parameterliste, Document-Number-Präfixe, SSRF-Whitelist, Response-Parsing |
| `data.gv.at` Katalog `ris2_6` | Open-Government-Data-Eintrag der API |
| `ris.bka.gv.at/RisInfo/OGD-FAQ.pdf` | Offizielle Hinweise (Last-Limits, Office-Hours-Regel) |

## RIS-OGD-API v2.6 — technische Fakten

### Base
- Base-URL: `https://data.bka.gv.at/ris/api/v2.6/`
- Authentifizierung: **keine**, kein API-Key
- Format: JSON (per `Accept: application/json`); XML ist auch möglich
- Rate-Limit-Empfehlung der RIS-Betreiber: 1–2 s Pause beim Paginieren,
  Massenabrufe **außerhalb 06–18 Uhr** oder am Wochenende
- Kontakt für API-Fragen: `ris.it@bka.gv.at`

### Endpoints (REST, alle GET)
| Pfad | Zweck |
|---|---|
| `/version` | Versionsinfo des Service |
| `/Bundesrecht` | Bundesrecht konsolidiert / Bundesgesetzblatt usw. |
| `/Landesrecht` | Landesrecht konsolidiert / LGBl |
| `/Judikatur` | **Rechtsprechung – das ist unser Ziel** |
| `/Bezirke` | Bezirksverwaltungsbehörden |
| `/Gemeinden` | Gemeinderecht |
| `/Sonstige` | Sonstige Sammlungen |
| `/History` | Änderungs-/Entstehungsgeschichte von Dokumenten |

### Parameter `/Judikatur`
Pflichtparameter:
- `Applikation` — eines von:
  - `Justiz` — OGH, OLG, LG, BG (Zivil-/Strafgerichtsbarkeit)
  - `Vfgh` — Verfassungsgerichtshof
  - `Vwgh` — Verwaltungsgerichtshof
  - `Bvwg` — Bundesverwaltungsgericht
  - `Lvwg` — Landesverwaltungsgerichte
  - `Dsk` — Datenschutzbehörde
  - `AsylGH` — historisch (Asylgerichtshof, bis 2013)
  - `Normenliste` — Normprüfungslisten
  - `Pvak` — Personalvertretungs-Aufsichtskommission
  - `Gbk` — Gleichbehandlungskommission
  - `Dok` — Disziplinarkommission

Plus **mind. einen** Suchparameter:
- `Suchworte` — Volltextsuche (operatoren AND/OR/NOT, `*` nur am Wortende)
- `Norm` — Suche nach Rechtsnorm, z. B. `1319a ABGB`
- `Geschaeftszahl` — Aktenzeichen, z. B. `5Ob234/20b`
- `Rechtssatznummer` — RS-Nummer eines Rechtssatzes
- `EntscheidungsdatumVon` / `EntscheidungsdatumBis` — `YYYY-MM-DD`
- `Entscheidungsart`, `Gericht` (verfeinert innerhalb einer Applikation)
- `SucheNachRechtssatz=True`, `SucheNachText=True` — was durchsucht wird
- `ImRisSeit` — neu seit Intervall (`Undefined`, `EinerWoche`, `EinemMonat`,
  `DreiMonaten`, `SechsMonaten`, `EinemJahr`)
- `Schlagworte`, `IndexAb`, `IndexBis`

Pagination und Sortierung:
- `DokumenteProSeite` ∈ {`Ten`, `Twenty`, `Fifty`, `OneHundred`}
- `Seitennummer` (1-basiert)
- `Sortierung` — z. B. `Datum`, `Geschaeftszahl`
- `SortDirection` ∈ {`Ascending`, `Descending`}

### Beispiel-URLs
```
GET https://data.bka.gv.at/ris/api/v2.6/Judikatur
    ?Applikation=Justiz
    &Suchworte=Mietzinsminderung
    &SucheNachRechtssatz=True
    &SucheNachText=True
    &DokumenteProSeite=Twenty
    &Seitennummer=1

GET https://data.bka.gv.at/ris/api/v2.6/Judikatur
    ?Applikation=Vfgh
    &Geschaeftszahl=G%2012%2F2020

GET https://data.bka.gv.at/ris/api/v2.6/Judikatur
    ?Applikation=Justiz
    &Norm=1319a%20ABGB
    &EntscheidungsdatumVon=2020-01-01
    &EntscheidungsdatumBis=2024-12-31
```

### JSON-Response-Struktur (Auszug)
```jsonc
{
  "OgdSearchResult": {
    "OgdDocumentResults": {
      "Hits": { "#text": "412", "@pageNumber": "1", "@pageSize": "20" },
      "OgdDocumentReference": [
        {
          "Data": {
            "Metadaten": {
              "Technisch": { "ID": "...", "Applikation": "Justiz" },
              "Allgemein": { "DokumentUrl": "https://..." },
              "Judikatur": {
                "Geschaeftszahl": { "item": "5Ob234/20b" },
                "Entscheidungsdatum": "2021-04-15",
                "Justiz": { "Leitsatz": "..." }
              }
            },
            "Dokumentliste": {
              "ContentReference": {
                "ContentType": "...",
                "Name": "...",
                "Urls": {
                  "ContentUrl": [
                    { "DataType": "Html", "Url": "https://ris.bka.gv.at/Dokumente/..." },
                    { "DataType": "Pdf",  "Url": "..." },
                    { "DataType": "Xml",  "Url": "..." }
                  ]
                }
              }
            }
          }
        }
      ]
    }
  }
}
```

### Direkte Dokument-URLs (Mapping nach Dokumentennummer-Präfix)
| Präfix | Pfad |
|---|---|
| `JJR`, `JWT` | `https://ris.bka.gv.at/Dokumente/Justiz/{nr}/{nr}.html` |
| `JFR`, `JFT` | `https://ris.bka.gv.at/Dokumente/Vfgh/{nr}/{nr}.html` |
| `JWR` | `https://ris.bka.gv.at/Dokumente/Vwgh/{nr}/{nr}.html` |
| `BVWG` | `https://ris.bka.gv.at/Dokumente/Bvwg/{nr}/{nr}.html` |
| `LVWG` | `https://ris.bka.gv.at/Dokumente/Lvwg/{nr}/{nr}.html` |
| `DSB`  | `https://ris.bka.gv.at/Dokumente/Dsk/{nr}/{nr}.html` |
| `GBK`  | `https://ris.bka.gv.at/Dokumente/Gbk/{nr}/{nr}.html` |
| `PVAK` | `https://ris.bka.gv.at/Dokumente/Pvak/{nr}/{nr}.html` |
| `ASYLGH` | `https://ris.bka.gv.at/Dokumente/AsylGH/{nr}/{nr}.html` |
| `NOR` | `https://ris.bka.gv.at/Dokumente/Bundesnormen/{nr}/{nr}.html` |
| `LBG` | `https://ris.bka.gv.at/Dokumente/LrBgld/{nr}/{nr}.html` |

Validierung: Dokumentennummern matchen `^[A-Z][A-Z0-9_]+$`, Länge 5–50.

## Wie shrinkwrap-legal-api die API nutzt
- Spring `RestClient`, Base-URL fix verdrahtet, JSON-Mapping per Records.
- Methoden: `getVersion()`, `getJustiz(app)`, `getJustiz(app, rechtssatznummer)`,
  `getCaselawByDocNumberAsHtml(app, docNumber)`.
- Beobachtung: Die shrinkwrap-Implementierung deckt nur einen kleinen
  Ausschnitt der API ab (Rechtssatznummer, Volltext, HTML-Doc).
  Für einen umfassenden Skill genügt das nicht — `philrox/ris-mcp-ts` ist
  die deutlich vollständigere Referenz.

## Implikationen für einen Claude-Code-Skill
1. Ein Skill liegt als Markdown mit YAML-Frontmatter unter `.claude/skills/`
   und beschreibt für Claude *wann* und *wie* die API anzurufen ist.
2. Die API ist key-frei → ein Skill kann direkt `curl`/`fetch` per Bash-Tool
   nutzen, optional auch `WebFetch`.
3. Mehrwert eines Skills:
   - Übersetzt natürlichsprachliche Fragen in passende `Applikation`-Werte
     und Suchparameter.
   - Empfiehlt Pagination und Sleep ≥1 s zwischen Seitenabfragen.
   - Erklärt die Response-Struktur und konstruiert direkte HTML/PDF-URLs.
   - Warnt bei Massenabfragen während Office-Hours.
4. Optionaler zweiter Schritt: ein Helper-Script (`scripts/ris.sh` o. ä.) oder
   eine kleine Python/Node-Datei, die der Skill aufruft.

## Designentscheidungen (vom User getroffen)
- **Output**: Metadaten + Link (kein Volltext-Download).
- **Helper-Sprache**: Python 3 (Standardlib, keine Pip-Abhängigkeiten).
- **Skill-Speicherort**: global, `~/.claude/skills/ris-rechtsprechung/`.
- **Scope**: nur Judikatur. Bundes-/Landesrecht ggf. später als eigene Skills.
