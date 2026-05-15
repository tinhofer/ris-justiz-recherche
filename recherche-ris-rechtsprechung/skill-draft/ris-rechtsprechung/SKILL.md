---
name: ris-rechtsprechung
description: Österreichische Rechtsprechung über die offene RIS-API (data.bka.gv.at v2.6) thematisch durchsuchen — OGH, OLG, LG, BG, VfGH, VwGH, BVwG, LVwG, DSB, GBK u. a. Liefert pro Treffer Metadaten (Geschäftszahl, Entscheidungsdatum, Leitsatz) und einen Direkt-Link in das RIS. TRIGGER bei thematischen Fragen wie "Gibt es OGH-Judikatur zu Mietzinsminderung in der Pandemie?", "Aktuelle BVwG-Entscheidungen zu Afghanistan-Asyl", "Was sagt der VfGH zur Versammlungsfreiheit seit 2020?". NICHT TRIGGERN für gezielte Lookups einer bekannten Geschäftszahl oder Rechtssatznummer — das ist im RIS-Web-Frontend schneller.
---

# Skill: RIS Rechtsprechung (Österreich)

Du recherchierst österreichische Gerichtsentscheidungen über die offene
**RIS-API v2.6** (Rechtsinformationssystem des Bundes, betrieben vom
Bundeskanzleramt). Die API ist authentifizierungsfrei und liefert JSON.

**Scope dieses Skills:** nur **Rechtsprechung (Judikatur)**, nur **Metadaten +
Link**. Es wird **kein** Volltext heruntergeladen oder konvertiert. Bundes- und
Landesrecht sind nicht enthalten.

## Wann diesen Skill anwenden

**Hauptpfad — thematische / explorative Recherche** im Chat:
- nach Stichworten / Schlagworten (`--suchworte`, `--schlagworte`)
- in einem bestimmten Zeitraum (`--von` / `--bis`)
- bei einer bestimmten Gerichtsbarkeit (`--applikation`)

Beispiele, die diesen Skill triggern:
- „Gibt es OGH-Judikatur zu Mietzinsminderung in der Pandemie?"
- „Aktuelle BVwG-Entscheidungen zu Afghanistan-Asyl seit 2023"
- „Was sagt der VfGH zur Versammlungsfreiheit?"

**Sekundärpfade** (technisch unterstützt, aber meist im RIS-Web-Frontend
schneller — nur nutzen, wenn der User explizit darum bittet oder die
Suche aus dem Chat-Kontext heraus eindeutig per Skript schneller geht):
- Geschäftszahl-Lookup (`--geschaeftszahl`)
- Norm-Suche (`--norm "ABGB §1319a"`)
- Rechtssatznummer-Lookup (`--rechtssatznummer RS0123456`)

**Norm-Suche → Rechtssätze**: bei reiner `--norm`-Suche (ohne
`--suchworte`) liefert die OGD-API per Default überwiegend
**Rechtssätze**, kaum Volltext-Entscheidungen — Rechtssätze sind im
Norm-Index hinterlegt, Entscheidungstexte erst über die zusätzlichen
Flags `SucheNachRechtssatz` / `SucheNachText`. Das Skript sendet diese
Flags bewusst nur bei `--suchworte`-Suchen, weil bei reiner
Norm-Recherche Rechtssätze i. d. R. die gewollte Trefferart sind.

Nicht anwenden, wenn:
- die Frage rein dogmatisch / rechtspolitisch ist, ohne Bezug zu einer
  konkreten Entscheidung (z. B. „Was sagt die Lehre zu §..." → Kommentar,
  nicht RIS),
- Bundes-/Landesrecht gemeint ist (Gesetzestext, nicht Rechtsprechung),
- nach EuGH/EGMR-Urteilen gefragt wird (RIS enthält nur österreichische
  Gerichte; ggf. wird die österreichische Folgejudikatur gesucht — dann
  Skill anwenden, aber den Hinweis geben),
- nach laufenden Verfahren oder Pressemitteilungen gefragt wird (RIS
  enthält nur veröffentlichte Entscheidungen).

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
| `Suchworte` | `Mietzinsminderung` | URL-encoden; `*` nur am Wortende; AND/OR/NOT. **OGD-API-Einschränkung**: nur _ein_ Platzhalter pro Wort (Web-Frontend toleriert mehrere). |
| `Geschaeftszahl` | `5Ob234/20b` | exakte Aktenzeichen-Suche |
| `Norm` | `ABGB §1319a` | **Format: `{Gesetzeskürzel} §{Paragraph}`** (kanonische Zitierform) — andere Reihenfolgen wie `1319a ABGB` liefern fast keine Treffer. Fehlt nur das `§`-Zeichen (`ArbVG 105`), ergänzt das Skript es automatisch und schreibt einen Hinweis in den Output. Für EU-Verordnungen (z. B. DSGVO) ist der `Norm`-Index unzuverlässig; lieber Volltextsuche via `Suchworte`. |
| `Rechtssatznummer` | `RS0123456` | bei OGH-Rechtssatz-Suche |
| `Schlagworte` | `Datenschutz` | kontrolliertes RIS-Vokabular |
| `EntscheidungsdatumVon` / `Bis` | `2024-01-01` | ISO-Datum |

Optional:
- `SucheNachRechtssatz`, `SucheNachText` — steuern, in welchen Feldern
  das `Suchworte`-Token gesucht wird (Rechtssatz-Text vs.
  Entscheidungstext). **Nicht** ein Filter für Trefferarten — auch mit
  `--no-rechtssatz` können Rechtssatz-Dokumente zurückkommen, wenn der
  Suchbegriff im Volltext gefunden wurde. Das Skript sendet die Flags
  nur bei `--suchworte`-Suchen.
- `ImRisSeit` ∈ {`Undefined`, `EinerWoche`, `EinemMonat`, `DreiMonaten`, `SechsMonaten`, `EinemJahr`}
- `Sortierung` ∈ {`Datum`, `Geschaeftszahl`, `Relevanz`} — die API toleriert
  weitere Werte; nur die hier gelisteten sind in den RIS-Handbüchern dokumentiert.
  **Skript-Default**: setzt das Skript weder `--sortierung` noch
  `--sort-direction`, sortiert es nach `Datum`/`Descending` (im
  Chat-Kontext meist gewollt — „aktuelle Judikatur zu …"). Der
  API-Default `Relevanz` ist mit `--sortierung Relevanz` zurückzuholen.
- `SortDirection` ∈ {`Ascending`, `Descending`}

Pagination:
- `DokumenteProSeite` ∈ {`Ten`, `Twenty`, `Fifty`, `OneHundred`} — Default `Twenty`
- `Seitennummer` (1-basiert) — bei `--alle-seiten` der Einstiegspunkt
- **Auto-Pagination**: `--alle-seiten` holt mehrere Seiten automatisch,
  bis Treffer erschöpft oder `--max-seiten N` (Default 5) erreicht.
  RIS-konforme Pause zwischen Seiten konfigurierbar via
  `--pause-pagination` (Default 1.5 s). Default-Cap: 5 × 20 = 100
  Treffer. Für breite Themen-Recherchen mit `--pro-seite Fifty
  --alle-seiten --max-seiten 5` bis zu 250 Treffer auf einmal.

## Empfohlenes Vorgehen

**Verwende immer das beigelegte Skript `scripts/ris_search.py`** (Python 3,
nur Standardbibliothek). Es kapselt URL-Bau, Pflichtparameter-Validierung,
JSON-Parsing und Rendering in einem Aufruf.

1. **Mapping**: User-Frage → `--applikation` + Suchparameter. Bei Unsicherheit
   `--applikation Justiz` + Volltext-Suche.

2. **Aufruf** — das Skript liegt **immer** bei `scripts/ris_search.py`
   relativ zum Skill-Ordner (dem Verzeichnis, das diese `SKILL.md` enthält).
   Der absolute Pfad zum Skill-Ordner hängt von der Umgebung ab; Du als
   ausführendes Modell weißt, in welcher Umgebung Du läufst.

   **Generisches Aufrufmuster** — `cd` in den Skill-Ordner, dann relativ
   aufrufen. Standard-Chat-Recherche (Themensuche mit Auto-Pagination):
   ```bash
   cd <skill-folder> && python scripts/ris_search.py \
     --applikation Justiz \
     --suchworte "Mietzinsminderung" \
     --von 2020-01-01 --bis 2024-12-31 \
     --pro-seite Fifty --alle-seiten --max-seiten 3
   ```
   Liefert bis zu 150 Treffer, sortiert nach Datum absteigend (Default).

   **Python-Aufruf je Umgebung** — probiere in dieser Reihenfolge:
   `python` → `python3` → `py -3`. Üblicherweise:
   - Linux / macOS / Claude.ai-Sandbox: `python3` oder `python`
   - Windows (Claude Code): `py -3` (`python3` fehlt meist im PATH)

   **Skill-Ordner je Umgebung** — typische Pfade:
   - Claude Code (Linux/macOS): `~/.claude/skills/ris-rechtsprechung/`
   - Claude Code (Windows): `%USERPROFILE%\.claude\skills\ris-rechtsprechung\`
   - Claude.ai Custom Skills: vom Harness gemounteter Pfad (meist unter
     `/mnt/skills/...` oder `/home/.../skills/...`); folge der Pfadangabe,
     die Dir der Skill-Loader liefert.

   Falls `cd` in der Umgebung nicht zur Verfügung steht (manche Sandboxes),
   verwende den absoluten Pfad zum Skript, z. B.:
   ```bash
   python "<skill-folder>/scripts/ris_search.py" --applikation Justiz ...
   ```

   Ausgabe ist Markdown (Default) oder strukturiertes JSON (`--json`).

3. **Antwort an den User**: die Top-Treffer mit Geschäftszahl, Datum,
   Leitsatz (sofern vorhanden) und RIS-Link weitergeben. Bei mehr als 10
   Treffern die ersten 10 ausführlich, den Rest als Bullet-Liste.

4. **Pagination**: bei mehr als einer Seite vor jeder weiteren Anfrage
   ca. 1,5 s warten (RIS-Empfehlung).

## Skript-Output

Default (Markdown). Für Rechtssatz-Dokumente (häufigster Fall bei
Norm-Suchen — Rechtssätze sind im Norm-Index hinterlegt):
```
**Treffer:** 7 (Seite 1, 10 pro Seite)

### 1. OGH 2 Ob 554/86 vom 28.10.1986 [Rechtssatz RS0051942]
**Norm:** ArbVG §105 Abs3 Z2 litb
- [Rechtssatz im RIS](https://www.ris.bka.gv.at/Dokument.wxe?Abfrage=Justiz&Dokumentnummer=JJR_19861028_OGH0002_0020OB00554_8600000_007)
- [Volltext der Stammentscheidung](https://www.ris.bka.gv.at/Dokument.wxe?Abfrage=Justiz&Dokumentnummer=JJT_19861028_OGH0002_0020OB00554_8600000_000)
_Auch zitiert in 21 weiteren Entscheidungen._
```

Für Volltext-Dokumente:
```
### 2. OGH 5 Ob 234/20b vom 15.04.2021 [Volltext]
_Leitsatz:_ ...
**Norm:** ABGB §1119
- [Zur Entscheidung im RIS](https://ris.bka.gv.at/Dokumente/Justiz/JJT_20210415_OGH0002_.../JJT_....html)
```

### Anmerkungen

- **Heading aus Stamm-Entscheidung:** Bei Rechtssätzen liefert die API
  in `Geschaeftszahl` eine Verkettung *aller* zitierenden Geschäftszahlen
  und in `Entscheidungsdatum` das jüngste Update-Datum. Beides ist
  irreführend. Wir nutzen stattdessen `Justiz.Entscheidungstexte.item[0]`
  — die Stamm-Entscheidung — als Quelle für Heading-GZ + Datum.
- **Volltext-URL bei Rechtssätzen:** kommt direkt aus der API (Stamm-
  `DokumentUrl`), nicht mehr aus der Heuristik. Die Heuristik bleibt
  als Fallback für seltene Sonderfälle.
- **Gericht aus `Technisch.Organ`** (zuverlässiger als
  `Justiz.Gericht`). Fallback auf Applikation.
- **Rechtssatznummer im Doktyp-Label:** `[Rechtssatz RS0051942]` —
  praktisch zum Zitieren.
- **„Auch zitiert in N weiteren Entscheidungen":** Anzahl − 1 (die
  Stamm zählt nicht), nur ausgegeben wenn N > 1.
- **Datumsformat:** ISO-Datum → DD.MM.YYYY.

### JSON-Output

`--json` liefert ein normalisiertes Objekt mit allen Feldern:
```jsonc
{
  "total_hits": 7, "page": 1, "page_size": 10,
  "documents": [
    {
      "dokumentnummer": "JJR_19861028_OGH0002_0020OB00554_8600000_007",
      "applikation": "Justiz",
      "gericht": "OGH",
      "doc_type": "Rechtssatz",          // "Volltext" | "Rechtssatz" | null
      "rechtssatznummer": "RS0051942",   // null bei Volltext-Dokumenten
      "geschaeftszahl": "2 Ob 554/86",   // Stamm-GZ aus Entscheidungstexte[0]
      "geschaeftszahlen": [...],         // ALLE zitierenden GZ
      "entscheidungsdatum": "1986-10-28", // Stamm-Datum
      "leitsatz": null,                  // Bei Rechtssätzen meist null
      "normen": ["ArbVG §105 Abs3 Z2 litb"],
      "fachgebiete": [],
      "entscheidungstexte_count": 22,
      "link": "https://www.ris.bka.gv.at/Dokument.wxe?...JJR_..._007",
      "volltext_url": "https://www.ris.bka.gv.at/Dokument.wxe?...JJT_..._000",
      "content_urls": { "html": "...", "pdf": "...", "xml": "...", "rtf": "..." },

      // Konditionale Audit-Felder — nur vorhanden, wenn die API einen
      // nicht-leeren Wert liefert. Erspart "null überall"-Rauschen und
      // umgeht die Issue-#18-Falle (Felder, die in alten Treffern leer
      // oder unzuverlässig sind, zeigen sich erst gar nicht).
      "veroeffentlicht": "1986-11-05",   // Allgemein.Veroeffentlicht
      "geaendert": "2024-09-02",         // Allgemein.Geaendert (letztes Update)
      "ecli": "ECLI:AT:OGH0002:1986:0020OB00554.8600000.007",
      "api_dokumenttyp": "Rechtssatz",   // API-eigene Doktyp-Angabe
      "schlagworte": ["..."],            // Top-Level Judikatur.Schlagworte
      "entscheidungsart": "Beschluss",   // Urteil / Beschluss / Erkenntnis
      "anmerkung": "...",                // nur Justiz-Block
      "fundstelle": "SZ 2024/15",        // nur Justiz-Block
      "rechtsgebiete": ["Zivilrecht"]    // nur Justiz-Block
    }
  ]
}
```

`doc_type` und `rechtssatznummer` sind nur bei OGH/VfGH/VwGH-Dokumenten
zuverlässig gesetzt (`J{Court}{T|R}`-Konvention). Andere Applikationen
(BVWG, LVWG, DSB u. a.) folgen der Konvention nicht; dort bleibt
`doc_type = null`. Wenn die API ein eigenes `Dokumenttyp`-Feld liefert,
steht es zusätzlich in `api_dokumenttyp`.

`--raw` gibt die unveränderte API-Antwort aus, falls du selbst parsen willst.

### Audit-Felder im Markdown-Output

Sind im JSON-Output Werte gesetzt, taucht im Markdown zusätzlich auf:

```
### 1. OGH 5Ob100/24x vom 01.01.2024 [Volltext] — Beschluss
**Rechtsgebiet:** Zivilrecht, Mietrecht
**Schlagworte:** Miete, Kündigung
**Fundstelle:** SZ 2024/15
**ECLI:** `ECLI:AT:OGH0002:2024:0050OB00100.24X.0101.000`
_Anmerkung:_ Veröffentlicht in SZ 2024/15 ...
```

Alle Audit-Zeilen werden nur gerendert, wenn die API für diesen Treffer
einen Wert liefert. Treffer ohne Wert zeigen die Zeile nicht — das ist
Absicht (siehe Issue-#18-Lehre).

## Direkte HTML-Volltext-URLs

Aus der Dokumentennummer ableitbar (Präfix → Pfad):

| Präfix | Pfad |
|---|---|
| `JJT`, `JJR` | `https://ris.bka.gv.at/Dokumente/Justiz/{nr}/{nr}.html` |
| `JFT`, `JFR` | `https://ris.bka.gv.at/Dokumente/Vfgh/{nr}/{nr}.html` |
| `JWT`, `JWR` | `https://ris.bka.gv.at/Dokumente/Vwgh/{nr}/{nr}.html` |
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

## Web-Search-Fallback (bei 0 API-Treffern)

Bei `Suchworte`-Anfragen mit 0 Treffern erzeugt das Skript automatisch eine
Google `site:`-Such-Query nach dem Muster

```
site:ris.bka.gv.at <Applikation> <Suchworte> [<Norm>] ["<Geschaeftszahl>"] [after:<Jahr>] [before:<Jahr>]
```

und gibt sie zusammen mit dem Hinweis aus. Hintergrund: Google indexiert
das RIS-Web-Frontend deutlich breiter als der OGD-API-Volltext-Index —
insbesondere bei alten Entscheidungen (vor ca. 1990), wo der API-Volltext
oft amputiert oder gar nicht durchsuchbar ist.

**Wenn Du in einem Claude-Kontext mit `web_search`-Tool läufst:** sobald
Du die Query im Output siehst, übergib sie unverändert an das
`web_search`-Tool. Aus den Treffern extrahierst Du RIS-URLs der Form
`https://www.ris.bka.gv.at/Dokument.wxe?Abfrage=…&Dokumentnummer=…` und
holst Dir bei Bedarf den Volltext mit `web_fetch`. Daraus baust Du dann
dieselben Trefferzeilen wie aus der API-Antwort (Geschäftszahl, Datum,
Leitsatz/Rechtssatz, Link).

Das Skript selbst führt **keine** Web-Suche aus — die Logik bleibt bei
Claude. Im JSON-Output ist die Query als `websearch_query`-Feld
verfügbar; im Markdown-Output steht sie im Hinweis-Block am Ende der
Trefferliste.

## Fehlerfälle

- **HTTP 400** → mindestens einen Suchparameter ergänzen oder spezifischer machen.
- **0 Treffer** → Suche entschärfen (allgemeinere Suchworte, größerer Zeitraum, andere `Applikation`).
- **0 Treffer bei `Suchworte` trotz nachweisbarem Vorkommen** →
  Bekannte Limitation des OGD-Volltext-Index, insbesondere bei alten
  Entscheidungen (vor ca. 1990). Der Volltext kann existieren und das
  Suchwort enthalten, ohne dass der API-Index ihn findet. Das Skript
  generiert in diesem Fall automatisch eine Google `site:`-Such-Query
  als Fallback (siehe Abschnitt *Web-Search-Fallback*).
- **Timeout / 5xx / Netzfehler nach allen Retries** → das Skript pingt
  zusätzlich den `/version`-Endpoint und schreibt eine Diagnose nach
  stderr: entweder „RIS-API erreichbar, aber /Judikatur scheitert — Query
  prüfen" oder „RIS-API komplett nicht erreichbar". Bei 4xx wird *nicht*
  diagnostiziert — die Antwort kennt die Ursache schon.
- **API-Pflichtparameter unbekannt** → Default-Pfad: `--applikation Justiz`,
  `--suchworte ...` setzen.

## Installation

Im Repo liegt der Skill unter
`recherche-ris-rechtsprechung/skill-draft/ris-rechtsprechung/` und ist
**self-contained**: ein Ordner mit `SKILL.md` und `scripts/ris_search.py`.
Da das Skript ausschließlich die Python-Standardbibliothek nutzt, ist
keine Build-Phase und keine Pip-Installation nötig.

### Claude Code (lokal, Linux/macOS)

```bash
mkdir -p ~/.claude/skills
cp -r recherche-ris-rechtsprechung/skill-draft/ris-rechtsprechung \
      ~/.claude/skills/
```

### Claude Code (lokal, Windows — PowerShell)

```powershell
$dest = "$env:USERPROFILE\.claude\skills"
New-Item -ItemType Directory -Force -Path $dest | Out-Null
Copy-Item -Recurse -Force `
  "recherche-ris-rechtsprechung\skill-draft\ris-rechtsprechung" `
  $dest
```

### Claude.ai Custom Skills (Web-App)

1. Skill-Ordner als ZIP packen:
   ```bash
   cd recherche-ris-rechtsprechung/skill-draft/
   zip -r ris-rechtsprechung.zip ris-rechtsprechung/
   ```
   PowerShell:
   ```powershell
   Compress-Archive -Path "recherche-ris-rechtsprechung\skill-draft\ris-rechtsprechung" `
                    -DestinationPath ris-rechtsprechung.zip -Force
   ```
2. Claude.ai → *Settings → Capabilities → Skills* → **Upload skill** →
   ZIP-Datei auswählen.
3. **Wichtig:** Im selben Settings-Bereich unter
   *Web search & code execution → Network access* die folgenden Hosts
   freigeben. Falls Claude.ai Wildcards akzeptiert, deckt
   `*.bka.gv.at` alle drei mit einem Eintrag ab.
   - `data.bka.gv.at` — OGD-API (Pflicht; ohne das blockt die Sandbox
     alle Skript-Aufrufe).
   - `ris.bka.gv.at` — RIS-Direkt-HTML-URLs der Form
     `/Dokumente/Justiz/JJT_…/JJT_….html` (abgeleitete „Volltext
     (vermutet)"-Links bei Rechtssatz-Treffern; Hinweis-Link auf
     die RIS-Web-Suche `https://www.ris.bka.gv.at/Judikatur/` bei 0
     Volltext-Treffern).
   - `www.ris.bka.gv.at` — `Dokument.wxe?…`-URLs, die die API selbst
     in der Trefferliste zurückgibt.

### Endstruktur (überall identisch)

```
ris-rechtsprechung/
├── SKILL.md
└── scripts/ris_search.py
```

Voraussetzung: Python ≥ 3.9 in der ausführenden Umgebung. Keine
Pip-Pakete nötig.

## Lizenz, Namensnennung, Disclaimer

Die über die OGD-Schnittstelle bezogenen RIS-Daten stehen unter
**Creative Commons Namensnennung 4.0 International (CC BY 4.0)**.
Bei Wiedergabe ist die Quelle zu nennen — das Skript hängt deshalb
an jeden Markdown-Output automatisch eine Attribution-Zeile
(`Quelle: RIS, Bundeskanzleramt — CC BY 4.0`) und im JSON-Output ein
`attribution`-Feld.

**Rechtlich verbindlich** ist laut Bundeskanzleramt **ausschließlich
der Wortlaut im Bundesgesetzblatt** (Applikation
„Bundesgesetzblatt authentisch") bzw. in den jeweiligen
Landesgesetzblättern. Der OGD-Datenbestand wird ohne Gewähr für
Richtigkeit, Aktualität oder Vollständigkeit bereitgestellt. Wenn Du
RIS-Treffer im Chat ausgibst, formuliere entsprechend — die
zurückgelieferten Texte sind **Recherchehilfe, keine authentische
Rechtsquelle**.

**Massenabfragen**: ein durchschnittlicher Skill-Aufruf (bis 5 Seiten
× 100 Treffer) ist unbedenklich. Wer den Skill systematisch über den
Tag verteilt nutzt oder `--max-seiten` deutlich hochdreht, sollte das
RIS-Team unter `ris.it@bka.gv.at` vorab informieren (siehe OGD-FAQ),
um nicht versehentlich als DDoS-Verkehr klassifiziert zu werden.

## Quellen

- Offizielle Doku-PDF: `https://data.bka.gv.at/ris/ogd/v2.6/Documents/Dokumentation_OGD-RIS_API.pdf`
- OGD-FAQ: `https://www.ris.bka.gv.at/RisInfo/OGD-FAQ.pdf`
- Datensatz-Eintrag: `https://www.data.gv.at/katalog/dataset/ris2_6`
- Referenz-Implementierungen:
  - `shrinkwrap-legal/shrinkwrap-legal-api` (Java/Spring)
  - `philrox/ris-mcp-ts` (TypeScript MCP-Server)
- Kontakt für API-Fragen: `ris.it@bka.gv.at`
