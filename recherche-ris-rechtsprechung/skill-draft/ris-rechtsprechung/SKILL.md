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
- nach Norm (Format `{Gesetzeskürzel} §{Paragraph}`, z. B. `ABGB §1319a`)
- nach Stichworten / Schlagworten
- nach Zeitraum (`EntscheidungsdatumVon`/`Bis`)
- nach Rechtssatz-Nummer (z. B. `RS0123456`)

Nicht anwenden, wenn:
- die Frage rein dogmatisch / rechtspolitisch ist, ohne Bezug zu einer
  konkreten Entscheidung (z. B. "Was sagt die Lehre zu §..." → Kommentar,
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
| `Suchworte` | `Mietzinsminderung` | URL-encoden; `*` nur am Wortende; AND/OR/NOT |
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
- `SortDirection` ∈ {`Ascending`, `Descending`}

Pagination:
- `DokumenteProSeite` ∈ {`Ten`, `Twenty`, `Fifty`, `OneHundred`} — Default `Twenty`
- `Seitennummer` (1-basiert)

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
   aufrufen:
   ```bash
   cd <skill-folder> && python scripts/ris_search.py \
     --applikation Justiz \
     --suchworte "Mietzinsminderung" \
     --von 2020-01-01 --bis 2024-12-31 \
     --pro-seite Twenty --seite 1
   ```

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

Default (Markdown). Für Volltext-Dokumente:
```
**Treffer:** 412 (Seite 1, 20 pro Seite)

### 1. [Volltext] Justiz 5Ob234/20b — 2021-04-15
_Leitsatz:_ ...
<https://ris.bka.gv.at/Dokumente/Justiz/JJT_20210415_OGH0002_.../JJT_....html>
```

Für Rechtssatz-Dokumente: zusätzlich ein abgeleiteter Volltext-Link.
```
### 2. [Rechtssatz] Justiz 9ObA110/88 — 1988-06-01
_Leitsatz:_ ...
- Rechtssatz: <https://www.ris.bka.gv.at/Dokument.wxe?Abfrage=Justiz&Dokumentennummer=JJR_19880601_OGH0002_009OBA00110_8800000_003>
- Volltext (vermutet): <https://ris.bka.gv.at/Dokumente/Justiz/JJT_19880601_OGH0002_009OBA00110_8800000_000/JJT_19880601_OGH0002_009OBA00110_8800000_000.html>
```

Die Volltext-URL wird per Heuristik aus der Rechtssatz-Dokumentennummer
abgeleitet (`J{Court}R_…_NNN` → `J{Court}T_…_000`). Bei OGH/VfGH/VwGH
trifft das in der überwältigenden Mehrheit der Fälle. Lieferte der
abgeleitete Link 404, ist der Rechtssatz-Link der Fallback — über die
Geschäftszahl findet sich das Volltext-Dokument im RIS-Web zuverlässig.

`--json` liefert ein normalisiertes Objekt:
```jsonc
{
  "total_hits": 412, "page": 1, "page_size": 20,
  "documents": [
    {
      "dokumentnummer": "JJR_19880601_OGH0002_...",
      "applikation": "Justiz",
      "doc_type": "Rechtssatz",          // "Volltext" | "Rechtssatz" | null
      "geschaeftszahl": "9ObA110/88",
      "geschaeftszahlen": ["9ObA110/88"],
      "entscheidungsdatum": "1988-06-01",
      "leitsatz": "...",
      "link": "https://www.ris.bka.gv.at/Dokument.wxe?...JJR_..._003",
      "volltext_url": "https://ris.bka.gv.at/Dokumente/Justiz/JJT_..._000/...html",
      "content_urls": { "html": "...", "pdf": "...", "xml": "..." }
    }
  ]
}
```

`doc_type` und `volltext_url` sind nur bei OGH/VfGH/VwGH-Dokumenten
gesetzt (J{Court}{T|R}-Konvention). Andere Applikationen (BVWG, LVWG,
DSB u. a.) folgen der Konvention nicht; dort bleibt `doc_type = null`
und `volltext_url = null`.

`--raw` gibt die unveränderte API-Antwort aus, falls du selbst parsen willst.

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

## Fehlerfälle

- **HTTP 400** → mindestens einen Suchparameter ergänzen oder spezifischer machen.
- **0 Treffer** → Suche entschärfen (allgemeinere Suchworte, größerer Zeitraum, andere `Applikation`).
- **0 Treffer bei `Suchworte` trotz nachweisbarem Vorkommen** →
  Bekannte Limitation des OGD-Volltext-Index, insbesondere bei alten
  Entscheidungen (vor ca. 1990). Der Volltext kann existieren und das
  Suchwort enthalten, ohne dass der API-Index ihn findet. Das Skript
  ergänzt in diesem Fall automatisch einen Hinweis auf die RIS-Web-Suche
  unter `https://ris.bka.gv.at/Justiz/`.
- **Timeout** → einmal mit kleinerem `--pro-seite` wiederholen (das Skript
  retried automatisch zwei Mal mit 2/4 s Pause).
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
   *Web search & code execution → Network access* zwei Domains freigeben:
   - `data.bka.gv.at` — die OGD-API selbst (Pflicht; ohne das blockt
     die Sandbox alle Skript-Aufrufe).
   - `ris.bka.gv.at` — das RIS-Web-Frontend (empfohlen). Der Skill
     liefert bei 0 Volltext-Treffern einen Hinweis-Link zur
     RIS-Web-Suche `https://ris.bka.gv.at/Justiz/`, der breiter
     indiziert ist als die OGD-API. Ohne diese Freigabe sind die
     im Output verlinkten Volltext-URLs (`Volltext (vermutet): …`
     bei Rechtssatz-Treffern) auch nicht direkt von Claude erreichbar.

### Endstruktur (überall identisch)

```
ris-rechtsprechung/
├── SKILL.md
└── scripts/ris_search.py
```

Voraussetzung: Python ≥ 3.9 in der ausführenden Umgebung. Keine
Pip-Pakete nötig.

## Quellen

- Offizielle Doku-PDF: `https://data.bka.gv.at/ris/ogd/v2.6/Documents/Dokumentation_OGD-RIS_API.pdf`
- OGD-FAQ: `https://www.ris.bka.gv.at/RisInfo/OGD-FAQ.pdf`
- Datensatz-Eintrag: `https://www.data.gv.at/katalog/dataset/ris2_6`
- Referenz-Implementierungen:
  - `shrinkwrap-legal/shrinkwrap-legal-api` (Java/Spring)
  - `philrox/ris-mcp-ts` (TypeScript MCP-Server)
- Kontakt für API-Fragen: `ris.it@bka.gv.at`
