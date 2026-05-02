---
name: ris-rechtsprechung
description: Österreichische Rechtsprechung über die offene RIS-API (data.bka.gv.at v2.6) abfragen — OGH, OLG, LG, BG, VfGH, VwGH, BVwG, LVwG, DSB, GBK u. a. Liefert pro Treffer Metadaten (Geschäftszahl, Entscheidungsdatum, Leitsatz) und einen Direkt-Link in das RIS. TRIGGER bei Fragen wie "Gibt es OGH-Judikatur zu §1319a ABGB?", "Verfassungsgerichtshof Erkenntnis G 12/2020", "Aktuelle BVwG-Asylentscheidungen zu Afghanistan", "Mietzinsminderung OGH 2023".
---

# Skill: RIS Rechtsprechung (Österreich)

Du recherchierst österreichische Gerichtsentscheidungen über die offene
**RIS-API v2.6** (Rechtsinformationssystem des Bundes, betrieben vom
Bundeskanzleramt). Die API ist authentifizierungsfrei und liefert JSON.

**Scope dieses Skills:** nur **Rechtsprechung (Judikatur)**, nur **Metadaten +
Link**. Es wird **kein** Volltext heruntergeladen oder konvertiert. Bundes- und
Landesrecht sind nicht enthalten.

## Wann diesen Skill anwenden

Bei jeder Anfrage, in der konkrete österreichische Judikatur gesucht wird:
- nach Geschäftszahl / Aktenzeichen
- nach Norm (Paragraph + Gesetz, z. B. `1319a ABGB`)
- nach Stichworten / Schlagworten
- nach Zeitraum (`EntscheidungsdatumVon`/`Bis`)
- nach Rechtssatz-Nummer (z. B. `RS0123456`)

Nicht anwenden bei rein dogmatischen oder rechtspolitischen Fragen ohne
Bezug zu konkreten Entscheidungen, oder wenn Bundes-/Landesrecht gemeint ist.

## API-Grundlagen

- Base-URL: `https://data.bka.gv.at/ris/api/v2.6/`
- Endpoint Rechtsprechung: `GET /Judikatur`
- Response-Format: JSON (`Accept: application/json`)
- Keine Auth, keine Quotas, aber:
  - **Bei Pagination 1–2 s Pause zwischen Seiten einlegen.**
  - Massenabfragen außerhalb 06–18 Uhr (MEZ) oder am Wochenende.
  - Bei Fehlern Geduld haben — das System teilt sich Ressourcen mit dem Web-Frontend.

## Pflichtparameter

`Applikation` (genau einer):

| Wert | Gericht/Behörde |
|---|---|
| `Justiz` | OGH, OLG, LG, BG (Zivil-/Strafgerichtsbarkeit) — Standard |
| `Vfgh` | Verfassungsgerichtshof |
| `Vwgh` | Verwaltungsgerichtshof |
| `Bvwg` | Bundesverwaltungsgericht |
| `Lvwg` | Landesverwaltungsgerichte |
| `Dsk` | Datenschutzbehörde (vormals -kommission) |
| `AsylGH` | Asylgerichtshof (historisch, bis 2013) |
| `Normenliste` | Normprüfungs-/Normenliste |
| `Pvak` | Personalvertretungs-Aufsichtskommission |
| `Gbk` | Gleichbehandlungskommission |
| `Dok` | Disziplinarkommission |

Plus **mindestens einer** dieser Suchparameter (sonst HTTP 400):

| Parameter | Beispiel | Hinweis |
|---|---|---|
| `Suchworte` | `Mietzinsminderung` | URL-encoden; `*` nur am Wortende; AND/OR/NOT |
| `Geschaeftszahl` | `5Ob234/20b` | exakte Aktenzeichen-Suche |
| `Norm` | `1319a ABGB` | Paragraph plus Gesetz |
| `Rechtssatznummer` | `RS0123456` | bei OGH-Rechtssatz-Suche |
| `EntscheidungsdatumVon` / `Bis` | `2024-01-01` | ISO-Datum |

Optional:
- `SucheNachRechtssatz=True`, `SucheNachText=True` (bei `Suchworte` empfohlen)
- `ImRisSeit` ∈ {`Undefined`, `EinerWoche`, `EinemMonat`, `DreiMonaten`, `SechsMonaten`, `EinemJahr`}
- `Sortierung`, `SortDirection` ∈ {`Ascending`, `Descending`}

Pagination:
- `DokumenteProSeite` ∈ {`Ten`, `Twenty`, `Fifty`, `OneHundred`} — Default `Twenty`
- `Seitennummer` (1-basiert)

## Empfohlenes Vorgehen

**Verwende immer das beigelegte Skript `scripts/ris_search.py`** (Python 3,
nur Standardbibliothek). Es kapselt URL-Bau, Pflichtparameter-Validierung,
JSON-Parsing und Rendering in einem Aufruf.

1. **Mapping**: User-Frage → `--applikation` + Suchparameter. Bei Unsicherheit
   `--applikation Justiz` + Volltext-Suche.
2. **Aufruf**:
   ```bash
   python3 scripts/ris_search.py \
     --applikation Justiz \
     --suchworte "Mietzinsminderung" \
     --von 2020-01-01 --bis 2024-12-31 \
     --pro-seite 20 --seite 1
   ```
   Ausgabe ist Markdown (Default) oder strukturiertes JSON (`--json`).
3. **Antwort an den User**: die Top-Treffer mit Geschäftszahl, Datum,
   Leitsatz (sofern vorhanden) und RIS-Link weitergeben. Bei mehr als 10
   Treffern die ersten 10 ausführlich, den Rest als Bullet-Liste.
4. **Pagination**: bei mehr als einer Seite vor jeder weiteren Anfrage
   `sleep 1.5`.

## Skript-Output

Default (Markdown):
```
**Treffer:** 412 (Seite 1, 20 pro Seite)

### 1. Justiz 5Ob234/20b — 2021-04-15
_Leitsatz:_ ...
<https://ris.bka.gv.at/Dokumente/Justiz/JJT_20210415_OGH0002_.../JJT_....html>
```

`--json` liefert ein normalisiertes Objekt:
```jsonc
{
  "total_hits": 412, "page": 1, "page_size": 20,
  "documents": [
    {
      "dokumentnummer": "JJT_20210415_OGH0002_...",
      "applikation": "Justiz",
      "geschaeftszahl": "5Ob234/20b",
      "geschaeftszahlen": ["5Ob234/20b"],
      "entscheidungsdatum": "2021-04-15",
      "leitsatz": "...",
      "link": "https://ris.bka.gv.at/Dokumente/Justiz/.../...html",
      "content_urls": { "html": "...", "pdf": "...", "xml": "..." }
    }
  ]
}
```

`--raw` gibt die unveränderte API-Antwort aus, falls du selbst parsen willst.

## Direkte HTML-Volltext-URLs

Aus der Dokumentennummer ableitbar (Präfix → Pfad):

| Präfix | Pfad |
|---|---|
| `JJT`, `JJR`, `JWT` | `https://ris.bka.gv.at/Dokumente/Justiz/{nr}/{nr}.html` |
| `JFR`, `JFT` | `https://ris.bka.gv.at/Dokumente/Vfgh/{nr}/{nr}.html` |
| `JWR` | `https://ris.bka.gv.at/Dokumente/Vwgh/{nr}/{nr}.html` |
| `BVWG` | `https://ris.bka.gv.at/Dokumente/Bvwg/{nr}/{nr}.html` |
| `LVWG` | `https://ris.bka.gv.at/Dokumente/Lvwg/{nr}/{nr}.html` |
| `DSB`  | `https://ris.bka.gv.at/Dokumente/Dsk/{nr}/{nr}.html` |
| `GBK`  | `https://ris.bka.gv.at/Dokumente/Gbk/{nr}/{nr}.html` |
| `PVAK` | `https://ris.bka.gv.at/Dokumente/Pvak/{nr}/{nr}.html` |

Validierung: Dokumentennummern matchen `^[A-Z][A-Z0-9_]+$`, Länge 5–50.
Das Skript leitet diesen Link automatisch ab und stellt ihn unter `link`
bzw. `content_urls.html` bereit.

**Volltext-Download ist explizit nicht Teil dieses Skills.** Wenn der
User den Volltext einer Entscheidung will, gib ihm den Link aus dem
Trefferdatensatz und überlasse ihm das Lesen.

## Fehlerfälle

- **HTTP 400** → mindestens einen Suchparameter ergänzen oder spezifischer machen.
- **0 Treffer** → Suche entschärfen (allgemeinere Suchworte, größerer Zeitraum, andere `Applikation`).
- **Timeout** → einmal mit kleinerem `--pro-seite` wiederholen (das Skript
  retried automatisch zwei Mal mit 2/4 s Pause).
- **API-Pflichtparameter unbekannt** → Default-Pfad: `--applikation Justiz`,
  `--suchworte ...` setzen.

## Installation

Dieser Skill ist als **globaler** Skill konzipiert:

```
~/.claude/skills/ris-rechtsprechung/
├── SKILL.md
└── scripts/ris_search.py
```

Voraussetzung: `python3` ≥ 3.9 im PATH. Keine Pip-Pakete nötig.

## Quellen

- Offizielle Doku-PDF: `https://data.bka.gv.at/ris/ogd/v2.6/Documents/Dokumentation_OGD-RIS_API.pdf`
- OGD-FAQ: `https://www.ris.bka.gv.at/RisInfo/OGD-FAQ.pdf`
- Datensatz-Eintrag: `https://www.data.gv.at/katalog/dataset/ris2_6`
- Referenz-Implementierungen:
  - `shrinkwrap-legal/shrinkwrap-legal-api` (Java/Spring)
  - `philrox/ris-mcp-ts` (TypeScript MCP-Server)
- Kontakt für API-Fragen: `ris.it@bka.gv.at`
