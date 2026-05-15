# Recherche: RIS-API für Rechtsprechung — Bericht

## Auftrag

Das Repository `tinhofer/ris-justiz-recherche` analysieren und verstehen, wie über
die offene **RIS-API** (Rechtsinformationssystem des Bundes,
`data.bka.gv.at`) **Rechtsprechung** abgefragt wird. Auf dieser Basis einen
**Claude-Code-Skill** entwerfen. Als Referenz wurde die Organisation
[shrinkwrap-legal](https://github.com/shrinkwrap-legal) genannt.

## Ergebnis in einem Satz

Das Repo `ris-justiz-recherche` selbst enthält **keinen** RIS-spezifischen
Code (nur ein Claude-Code-Scaffold). Der konkrete API-Zugriff und alle
verwertbaren Erkenntnisse stammen aus zwei externen Quellen:
`shrinkwrap-legal/shrinkwrap-legal-api` (Java) und — als deutlich
vollständigere Referenz — `philrox/ris-mcp-ts` (TypeScript MCP-Server).

## Was ich geprüft habe

1. **Repo selbst** — Inhalt, `Agent.md`-Anweisungen, Branch-Layout.
2. **shrinkwrap-legal** Organisation — drei öffentliche Repos
   (`shrinkwrap-legal-api`, `shrinkwrap-legal-extension`, Website). Nur
   `shrinkwrap-legal-api` enthält RIS-Code unter
   `src/main/java/legal/shrinkwrap/api/adapter/ris/rest/`.
3. **Offizielle RIS-OGD-Dokumentation** — Verweise und Sekundärquellen
   (PDF im Sandbox blockiert; Inhalt über GitHub-Code-Referenzen und
   Web-Suchen rekonstruiert).
4. **Vergleichsimplementierung** — `philrox/ris-mcp-ts`: vollständiges
   Parameter-Mapping, Response-Parsing, SSRF-Schutz, Dokument-URL-Heuristik.

## Wie shrinkwrap-legal-api die RIS-API nutzt

Datei `RisAdapterImpl.java` (Auszug):

```java
private static final String RIS_BASE_URL = "https://data.bka.gv.at";
private static final String RIS_API      = "/ris/api/v2.6";

private static final String RIS_VERSION_INFO = "/version";
private static final String RIS_APP_JUDIKATUR =
    "/Judikatur?Applikation={Applikation}&Rechtssatznummer={Rechtssatznummer}";
private static final String RIS_APP_JUDIKATUR_DOCNUMBER =
    "/Judikatur?Applikation={Applikation}&Suchworte={Suchworte}"
  + "&SucheNachRechtssatz=True&SucheNachText=True";

private static final String RIS_JUDIKATOR_HTML =
    "/Dokumente/{Applikation}/{Dokumentennummer}/{Dokumentennummer}.html";
```

Erlaubte `Applikation`-Werte (Enum):

```java
BundesrechtKonsolidiert("BrKons"),
LandesrechtKonsolidiert("LrKons"),
Justiz("Justiz"),
VfGH("VfGH")
```

**Beobachtung:** Diese Implementation deckt nur einen kleinen Teil der API
ab. `Justiz` und `VfGH` sind enthalten, aber `Vwgh`, `Bvwg`, `Lvwg`, `Dsk`
usw. fehlen. Suchparameter wie `Geschaeftszahl`, `Norm`,
`EntscheidungsdatumVon/Bis` sind nicht modelliert. Pagination
(`DokumenteProSeite`, `Seitennummer`) ebenfalls nicht.

Die Response wird über Records nach `OgdSearchResult.OgdDocumentResults`
gemappt — siehe Datei `OgdDocumentReference.java` mit den verschachtelten
Klassen `Data`, `Metadaten`, `Allgemein`, `Bundesrecht`, `Dokumentliste`,
`ContentReference`, `DokumentlisteUrl`, `ContentUrl`.

## RIS-OGD-API v2.6 — konsolidierte Fakten

| Aspekt | Wert |
|---|---|
| Base-URL | `https://data.bka.gv.at/ris/api/v2.6/` |
| Auth | keine, kein API-Key |
| Format | JSON (`Accept: application/json`), alternativ XML |
| Endpoint Rechtsprechung | `GET /Judikatur` |
| Pflichtparameter | `Applikation` + mindestens ein Suchparameter |
| Pagination | `DokumenteProSeite` ∈ `Ten/Twenty/Fifty/OneHundred`, `Seitennummer` (1-basiert) |
| Rate-Limit-Empfehlung | 1–2 s Pause beim Paginieren, Massenabfragen 18–06 Uhr / WE |
| Kontakt | `ris.it@bka.gv.at` |

Anwendungen (`Applikation`-Werte) für Rechtsprechung:
`Justiz`, `Vfgh`, `Vwgh`, `Bvwg`, `Lvwg`, `Dsk`, `AsylGH` (historisch),
`Normenliste`, `Pvak`, `Gbk`, `Dok`.

Wichtige Suchparameter:
`Suchworte`, `Geschaeftszahl`, `Norm`, `Rechtssatznummer`,
`EntscheidungsdatumVon`, `EntscheidungsdatumBis`, `Schlagworte`,
`ImRisSeit`, `SucheNachRechtssatz`, `SucheNachText`, `Sortierung`,
`SortDirection`.

Beispielabfrage:

```
GET https://data.bka.gv.at/ris/api/v2.6/Judikatur
    ?Applikation=Justiz
    &Suchworte=Mietzinsminderung
    &SucheNachRechtssatz=True&SucheNachText=True
    &EntscheidungsdatumVon=2020-01-01&EntscheidungsdatumBis=2024-12-31
    &DokumenteProSeite=Twenty&Seitennummer=1
```

Responsestruktur (gekürzt):

```jsonc
OgdSearchResult.OgdDocumentResults.Hits          // {#text, @pageNumber, @pageSize}
OgdSearchResult.OgdDocumentResults.OgdDocumentReference[]
  Data.Metadaten.Technisch.ID                    // Dokumentennummer
  Data.Metadaten.Allgemein.DokumentUrl
  Data.Metadaten.Judikatur.Geschaeftszahl.item   // String oder Array
  Data.Metadaten.Judikatur.Entscheidungsdatum
  Data.Metadaten.Judikatur.{Justiz|Vfgh|Vwgh|Bvwg}.Leitsatz
  Data.Dokumentliste.ContentReference.Urls.ContentUrl[].{DataType, Url}
```

Direkte HTML-Volltext-URLs sind aus dem Präfix der Dokumentennummer
ableitbar (z. B. `JJT…` → `…/Dokumente/Justiz/{nr}/{nr}.html`,
`JFR…`/`JFT…` → `…/Vfgh/…`, `JWR…` → `…/Vwgh/…`, `BVWG…` → `…/Bvwg/…`).

## Skill-Entwurf

Im Unterordner `skill-draft/ris-rechtsprechung/` liegt ein
einsatzfertiger Skill für Claude-Code:

```
skill-draft/ris-rechtsprechung/
├── SKILL.md                  # Metadaten + Anleitung für Claude
└── scripts/
    └── ris_search.py         # Python-Wrapper für /Judikatur (Standardlib)
```

`SKILL.md` enthält:
- YAML-Frontmatter mit `name` und `description` (Trigger-Hinweise).
- Beschreibung wann der Skill zu nutzen ist.
- Vollständige Parameter-Tabelle (Pflicht- und Optional-Parameter).
- Anleitung zur Antwort-Auswertung und zum Antwortformat.
- Mapping-Tabelle der Dokumentennummer-Präfixe auf HTML-URLs.
- Fehlerfall-Handling und Pagination-/Rate-Limit-Richtlinien.

`scripts/ris_search.py` ist ein eigenständiges Python-3-Skript ohne
Pip-Abhängigkeiten. Es validiert Pflichtparameter, baut die Anfrage,
parst die Antwort und liefert wahlweise Markdown, normalisiertes JSON
(`--json`) oder die Roh-API-Antwort (`--raw`). Bei Netzfehlern werden
zwei automatische Retries mit Backoff durchgeführt; sind diese
erschöpft, pingt das Skript zusätzlich `/version` und unterscheidet
im stderr-Output zwischen „RIS-API komplett down" und „/Judikatur
scheitert spezifisch — Query prüfen".

Das normalisierte Output-Dict enthält die im shrinkwrap-Mapper
extrahierten Audit-Felder (`veroeffentlicht`, `geaendert`, `ecli`,
`api_dokumenttyp`, `schlagworte`, `entscheidungsart`, `anmerkung`,
`fundstelle`, `rechtsgebiete`) — jeweils nur dann, wenn die API
einen nicht-leeren Wert liefert. So bleibt das JSON kompakt, und der
in Issue #18 dokumentierte Befund („ECLI/Rechtsgebiet in vielen
Treffern leer") führt nicht zu „null-Feld-Rauschen".

## Festgelegte Designentscheidungen

| Frage | Entscheidung |
|---|---|
| Output | nur **Metadaten + Link** (kein Volltext-Download) |
| Helper-Sprache | **Python 3** (Standardlib, keine Dependencies) |
| Skill-Speicherort | **global**: `~/.claude/skills/ris-rechtsprechung/` |
| Scope | **nur Judikatur** (Bundes-/Landesrecht ggf. später als eigene Skills) |

## Referenzen

- Offizielle Doku-PDF: `https://data.bka.gv.at/ris/ogd/v2.6/Documents/Dokumentation_OGD-RIS_API.pdf`
- OGD-FAQ: `https://www.ris.bka.gv.at/RisInfo/OGD-FAQ.pdf`
- Datensatz: `https://www.data.gv.at/katalog/dataset/ris2_6`
- Justiz-Abfragehandbuch: `https://www.ris.bka.gv.at/RisInfo/HandbuchJustiz.pdf`
- VwGH-Abfragehandbuch: `https://www.ris.bka.gv.at/RisInfo/HandbuchVwgh.pdf`
- Vergleichscode:
  - `https://github.com/shrinkwrap-legal/shrinkwrap-legal-api`
  - `https://github.com/philrox/ris-mcp-ts`
- Kontakt: `ris.it@bka.gv.at`
