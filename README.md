# ris-justiz-recherche

Recherche zur österreichischen **RIS-API** (Rechtsinformationssystem des
Bundes, `data.bka.gv.at`) und ein einsatzfertiger **Claude-Code-Skill**, der
Rechtsprechung über die offene API v2.6 abfragt.

## Inhalt

```
ris-justiz-recherche/
├── recherche-ris-rechtsprechung/        # Recherche-Bericht und Skill-Paket
│   ├── README.md                        # Bericht: API-Fakten und Designentscheidungen
│   ├── notes.md                         # Recherche-Notizen
│   ├── referenz-auszuege.md             # Auszüge aus Vergleichs-Implementierungen
│   └── skill-draft/
│       └── ris-rechtsprechung/          # → das fertige Skill-Paket
│           ├── SKILL.md                 #   Anleitung für Claude
│           └── scripts/ris_search.py    #   Python-Wrapper für /Judikatur
├── Agent.md                             # Anweisungen für den Recherche-Agent
└── scripts/apply-best-practices.sh      # Repo-Scaffold (aus dem Initial-Setup)
```

## Skill `ris-rechtsprechung`

**Zweck:** Österreichische Gerichtsentscheidungen (OGH, OLG, LG, BG, VfGH,
VwGH, BVwG, LVwG, DSB u. a.) über die authentifizierungsfreie RIS-OGD-API
finden. Liefert pro Treffer Geschäftszahl, Entscheidungsdatum, Leitsatz und
einen Direkt-Link in das RIS.

**Scope (festgelegt):** nur Judikatur, nur Metadaten + Link — kein
Volltext-Download.

**Stack:** Python 3.9+, ausschließlich Standardbibliothek.

### Installation (Claude Code, Linux/macOS)

```bash
mkdir -p ~/.claude/skills
cp -r recherche-ris-rechtsprechung/skill-draft/ris-rechtsprechung \
      ~/.claude/skills/
```

Für Windows und Claude.ai-Custom-Skill-Upload siehe Abschnitt
*Installation* in
[`recherche-ris-rechtsprechung/skill-draft/ris-rechtsprechung/SKILL.md`](recherche-ris-rechtsprechung/skill-draft/ris-rechtsprechung/SKILL.md).

### Direkt-Aufruf des Skripts (ohne Claude)

```bash
cd recherche-ris-rechtsprechung/skill-draft/ris-rechtsprechung
python scripts/ris_search.py \
  --applikation Justiz \
  --suchworte "Mietzinsminderung" \
  --von 2020-01-01 --bis 2024-12-31 \
  --pro-seite Twenty --seite 1
```

`--json` liefert ein normalisiertes Objekt; `--raw` gibt die unveränderte
API-Antwort aus.

## Recherche-Bericht

Der Bericht in
[`recherche-ris-rechtsprechung/README.md`](recherche-ris-rechtsprechung/README.md)
fasst zusammen:

- Endpoints und Parameter der RIS-OGD-API v2.6 (`/Judikatur` im Detail)
- erlaubte `Applikation`-Werte und deren Trefferräume
- JSON-Response-Struktur
- Mapping der Dokumentennummer-Präfixe auf direkte HTML-URLs
- Referenz-Implementierungen (`shrinkwrap-legal/shrinkwrap-legal-api`,
  `philrox/ris-mcp-ts`)

## Mitwirken

Siehe [CONTRIBUTING.md](CONTRIBUTING.md). Änderungen werden in
[CHANGELOG.md](CHANGELOG.md) festgehalten.

## Lizenz

MIT — siehe [LICENSE](LICENSE).
