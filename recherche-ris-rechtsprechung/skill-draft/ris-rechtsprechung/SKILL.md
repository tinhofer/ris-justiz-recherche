---
name: ris-rechtsprechung
description: Österreichische Rechtsprechung über die offene RIS-API (data.bka.gv.at v2.6) abfragen — OGH, OLG, LG, BG, VfGH, VwGH, BVwG, LVwG, DSB, GBK u. a. Gibt strukturierte Treffer mit Geschäftszahl, Entscheidungsdatum, Leitsatz und Direkt-Link zurück. TRIGGER bei Fragen wie "Gibt es OGH-Judikatur zu §1319a ABGB?", "Verfassungsgerichtshof Entscheidung G 12/2020", "Aktuelle Asylentscheidungen des BVwG zu Afghanistan", "Mietzinsminderung OGH 2023".
---

# Skill: RIS Rechtsprechung (Österreich)

Du recherchierst österreichische Gerichtsentscheidungen über die offene
**RIS-API v2.6** (Rechtsinformationssystem des Bundes, betrieben vom
Bundeskanzleramt). Die API ist authentifizierungsfrei und liefert JSON.

## Wann diesen Skill anwenden

Bei jeder Anfrage, in der konkrete österreichische Judikatur gesucht wird:
- nach Geschäftszahl / Aktenzeichen
- nach Norm (Paragraph + Gesetz, z. B. `1319a ABGB`)
- nach Stichworten / Schlagworten
- nach Zeitraum (`EntscheidungsdatumVon`/`Bis`)
- nach Rechtssatz-Nummer

Nicht anwenden bei rein dogmatischen oder rechtspolitischen Fragen ohne
Bezug zu konkreten Entscheidungen.

## API-Grundlagen

- Base-URL: `https://data.bka.gv.at/ris/api/v2.6/`
- Endpoint Rechtsprechung: `GET /Judikatur`
- Response-Format: JSON (`Accept: application/json`)
- Keine Auth, keine Quotas, aber:
  - **Bei Pagination 1–2 s Pause zwischen Seiten einlegen**
  - Massenabfragen außerhalb 06–18 Uhr (MEZ) oder am Wochenende
  - Bei Fehlern Geduld haben (das System ist gemeinsam mit dem Web-Frontend)

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

Plus **mindestens einer** dieser Suchparameter (sonst wirft die API einen
Validierungsfehler):

| Parameter | Beispiel | Hinweis |
|---|---|---|
| `Suchworte` | `Mietzinsminderung` | URL-encoden; `*` nur am Wortende; AND/OR/NOT |
| `Geschaeftszahl` | `5Ob234/20b` | exakte Aktenzeichen-Suche |
| `Norm` | `1319a ABGB` | Paragraph plus Gesetz |
| `Rechtssatznummer` | `RS0123456` | bei OGH-Rechtssatz-Suche |
| `EntscheidungsdatumVon` / `Bis` | `2024-01-01` | ISO-Datum |

Optional:
- `SucheNachRechtssatz=True`, `SucheNachText=True` (bei `Suchworte` empfohlen)
- `ImRisSeit` ∈ {`Undefined`, `EinerWoche`, `EinemMonat`, `DreiMonaten`,
  `SechsMonaten`, `EinemJahr`}
- `Schlagworte`, `IndexAb`, `IndexBis`
- `Sortierung`, `SortDirection` ∈ {`Ascending`, `Descending`}

Pagination:
- `DokumenteProSeite` ∈ {`Ten`, `Twenty`, `Fifty`, `OneHundred`} — Default `Twenty`
- `Seitennummer` (1-basiert)

## Vorgehen

1. **Mapping**: User-Frage → `Applikation` + Suchparameter. Bei Unsicherheit
   `Applikation=Justiz` und Volltext.
2. **Anfrage**: GET-Request an `/Judikatur`. URL-Parameter encoden.
3. **Antwort lesen**: Pfad `OgdSearchResult.OgdDocumentResults`:
   - `Hits.#text` = Treffer gesamt; `@pageNumber`, `@pageSize` = aktuelle Seite
   - `OgdDocumentReference` = Trefferliste (kann Single-Object oder Array sein —
     immer normalisieren!)
4. **Pro Treffer extrahieren**:
   - `Data.Metadaten.Technisch.ID` (Dokumentennummer)
   - `Data.Metadaten.Judikatur.Geschaeftszahl.item` (kann String oder Array sein)
   - `Data.Metadaten.Judikatur.Entscheidungsdatum`
   - `Data.Metadaten.Judikatur.{Justiz|Vfgh|Vwgh|Bvwg}.Leitsatz` (sofern vorhanden)
   - `Data.Metadaten.Allgemein.DokumentUrl` (direkter Web-Link)
   - `Data.Dokumentliste.ContentReference.Urls.ContentUrl[]` mit `DataType`
     ∈ {`Html`, `Pdf`, `Xml`, `Rtf`}
5. **Antwort formatieren** (siehe unten).
6. **Pagination**: bei mehr als einer Seite vor jeder weiteren Anfrage
   `sleep 1.5`.

## Antwort-Format

Pro Anfrage zuerst eine Trefferzusammenfassung:

```
Treffer: 412 (Seite 1 von 21, 20 pro Seite)
Anfrage: Applikation=Justiz, Suchworte=Mietzinsminderung
```

Dann pro Entscheidung:

```
1. OGH 5Ob234/20b — 15.04.2021
   Leitsatz: …
   https://ris.bka.gv.at/Dokumente/Justiz/JJT_20210415_OGH0002_0050OB00234_20B0000_000/...
```

Bei vielen Treffern: maximal Top 10 voll ausführlich, Rest verdichtet als
Bullet-Liste mit Geschäftszahl, Datum und Link.

## Direkte HTML-Volltext-URLs

Aus der Dokumentennummer ableitbar (Präfix bestimmt Pfad):

| Präfix | Pfad |
|---|---|
| `JJT`, `JJR` | `https://ris.bka.gv.at/Dokumente/Justiz/{nr}/{nr}.html` |
| `JFR`, `JFT` | `https://ris.bka.gv.at/Dokumente/Vfgh/{nr}/{nr}.html` |
| `JWR` | `https://ris.bka.gv.at/Dokumente/Vwgh/{nr}/{nr}.html` |
| `BVWG` | `https://ris.bka.gv.at/Dokumente/Bvwg/{nr}/{nr}.html` |
| `LVWG` | `https://ris.bka.gv.at/Dokumente/Lvwg/{nr}/{nr}.html` |
| `DSB`  | `https://ris.bka.gv.at/Dokumente/Dsk/{nr}/{nr}.html` |

Wenn der User den Volltext einer konkreten Entscheidung will: HTML
herunterladen (z. B. via `WebFetch` oder `curl -fsSL`) und auf die
relevanten Abschnitte (Spruch, Begründung, Leitsatz) reduzieren.

## Helfer-Skript

Für strukturierte Aufrufe steht das Skript `scripts/ris-search.sh` bereit
(siehe Skill-Verzeichnis). Beispiel:

```bash
scripts/ris-search.sh \
  --applikation Justiz \
  --suchworte "Mietzinsminderung" \
  --von 2020-01-01 --bis 2024-12-31 \
  --pro-seite 20 --seite 1
```

## Fehlerfälle

- **HTTP 400** → mindestens einen Suchparameter ergänzen.
- **Empty `OgdDocumentReference`** → 0 Treffer; Suche entschärfen
  (allgemeinere Suchworte, größerer Zeitraum, andere `Applikation`).
- **`OgdDocumentReference` als Single-Object** → wie ein 1-elementiges Array
  behandeln.
- **Timeout** → einmal mit kleinerem `DokumenteProSeite` wiederholen.

## Beispiel-Workflow

User: *"Gibt es VfGH-Erkenntnisse zur Vorratsdatenspeicherung?"*

```bash
curl -fsSL -G "https://data.bka.gv.at/ris/api/v2.6/Judikatur" \
  -H 'Accept: application/json' \
  --data-urlencode "Applikation=Vfgh" \
  --data-urlencode "Suchworte=Vorratsdatenspeicherung" \
  --data-urlencode "SucheNachRechtssatz=True" \
  --data-urlencode "SucheNachText=True" \
  --data-urlencode "DokumenteProSeite=Ten" \
  --data-urlencode "Seitennummer=1"
```

Antwort parsen, Top-Treffer als Liste mit Geschäftszahl, Datum, Leitsatz und
Link an den User zurückgeben.

## Quellen

- Offizielle Doku-PDF (Verweis im shrinkwrap-Adapter):
  `https://data.bka.gv.at/ris/ogd/v2.6/Documents/Dokumentation_OGD-RIS_API.pdf`
- OGD-FAQ: `https://www.ris.bka.gv.at/RisInfo/OGD-FAQ.pdf`
- Datensatz-Eintrag: `https://www.data.gv.at/katalog/dataset/ris2_6`
- Referenz-Implementierungen:
  - `shrinkwrap-legal/shrinkwrap-legal-api` (Java/Spring)
  - `philrox/ris-mcp-ts` (TypeScript MCP-Server)
- Kontakt für API-Fragen: `ris.it@bka.gv.at`
