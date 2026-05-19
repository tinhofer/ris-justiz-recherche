# CLAUDE.md

Guidance for AI assistants working in this repository.

## What this repo is

Research + a ready-to-install **Claude-Code skill** for querying Austrian
case law via the open **RIS-OGD-API v2.6** (`data.bka.gv.at`, no auth, JSON).

The deliverable is the skill at
`recherche-ris-rechtsprechung/skill-draft/ris-rechtsprechung/` — a
self-contained folder with `SKILL.md` (instructions for Claude) and
`scripts/ris_search.py` (Python wrapper). Everything else
(`README.md`, `notes.md`, `referenz-auszuege.md`) is the research report
that justifies the skill's design.

**Scope is locked:** Judikatur only, metadata + link only, no full-text
download, no Bundes-/Landesrecht. Don't broaden it without a clear ask.

## Layout

```
ris-justiz-recherche/
├── CLAUDE.md                                  (this file)
├── README.md                                  repo-level overview (DE)
├── Agent.md                                   notes for the original research agent
├── CHANGELOG.md                               Keep-a-Changelog, SemVer
├── CONTRIBUTING.md                            generic scaffold (commit-prefix style lives here)
├── recherche-ris-rechtsprechung/
│   ├── README.md                              the research report — API facts, design rationale
│   ├── notes.md                               investigation trail
│   ├── referenz-auszuege.md                   excerpts from shrinkwrap-legal-api + philrox/ris-mcp-ts
│   └── skill-draft/ris-rechtsprechung/        ← THE SKILL (ships verbatim into ~/.claude/skills/)
│       ├── SKILL.md                           instructions Claude reads at runtime
│       ├── scripts/ris_search.py              CLI wrapper, stdlib-only, Python ≥ 3.9
│       └── tests/test_ris_search.py           unittest, mix of offline + live-API
├── scripts/apply-best-practices.sh            one-off repo scaffold script (initial setup, not for ongoing use)
└── .github/workflows/
    ├── ci.yml                                 offline unit tests on push/PR, py 3.9/3.11/3.12
    ├── ris-smoke-test.yml                     live API test, Sun 03:00 UTC + workflow_dispatch
    └── ris-query.yml                          workflow_dispatch ad-hoc RIS query, result in step summary
```

## Working on the skill

### Hard rules

- **Stdlib only.** `ris_search.py` must run without `pip install`. No
  `requests`, no `pydantic`. Use `urllib`, `argparse`, `json`, `re`,
  stdlib `unittest` for tests. Python ≥ 3.9.
- **No full-text download / parsing.** The skill returns metadata + a
  RIS link. Anything that fetches HTML/PDF/RTF content of a decision is
  out of scope — give the user the link.
- **Don't construct RIS URLs by hand.** Use `docnumber_to_html_url()`
  (prefix→path table) or take `link`/`volltext_url` straight from the
  API response. The prefix table is sorted longest-first at module
  load — preserve that.
- **Sortierung default is `Datum`/`Descending`** (set only when neither
  flag is passed) — chat-context wants "latest first", not the API's
  `Relevanz` default. Tests in `TestBuildUrlSortDefault` lock this in.
- **`SucheNachRechtssatz`/`SucheNachText` are only sent with
  `--suchworte`.** They behave as where-to-search hints for the
  full-text query; sending them on Geschäftszahl/Norm/Schlagworte
  queries silently filters out hits.
- **Norm canonical form is `{Kürzel} §{Paragraph}`** (e.g. `ABGB §1319a`).
  `normalize_norm()` inserts the `§` if the user forgot it and the
  Markdown/JSON output flags the rewrite.
- **HTTP 4xx is NOT retried.** Only 5xx + network errors retry (linear
  backoff). 400 means the request itself is wrong — log a useful
  stderr message and bail.
- **Every Markdown/JSON output carries the CC-BY-4.0 attribution
  footer.** RIS-OGD data is CC BY 4.0 and the BKA OGD-FAQ requires
  source attribution. Don't strip it.

### Testing

Tests live next to the skill at
`recherche-ris-rechtsprechung/skill-draft/ris-rechtsprechung/tests/`.

```bash
cd recherche-ris-rechtsprechung/skill-draft/ris-rechtsprechung

# offline only (what CI runs):
RIS_SKIP_LIVE=1 python -m unittest tests.test_ris_search -v

# full suite incl. live RIS calls (~3-5s of sleeps for politeness):
python -m unittest tests.test_ris_search -v
```

`TestRisLiveApi`, `TestWebsearchQueryBuilder.test_vwgh_result_has_vwgh_link`
hit the live API. They `SkipTest` on network failure rather than fail,
and respect `RIS_SKIP_LIVE=1`. CI sets that flag on push/PR; the weekly
`ris-smoke-test.yml` runs the live tests on its own.

When you change `ris_search.py`, run the offline tests locally before
committing. If you touch URL building, output rendering, or the prefix
table, also add a unit test — the offline suite is the regression net.

### Running the script

```bash
cd recherche-ris-rechtsprechung/skill-draft/ris-rechtsprechung
python scripts/ris_search.py --applikation Justiz \
  --suchworte "Mietzinsminderung" \
  --von 2020-01-01 --bis 2024-12-31 \
  --pro-seite Fifty --alle-seiten --max-seiten 3
```

`--json` → structured object, `--raw` → unmodified API payload (single
page only — incompatible with `--alle-seiten`).

## Skill installation (for end-users)

Documented in `README.md` and the skill's own `SKILL.md` (sections
*Installation*). Three targets: Claude Code Linux/macOS, Claude Code
Windows (PowerShell), Claude.ai Custom Skills (ZIP upload + network
whitelist for `data.bka.gv.at`, `ris.bka.gv.at`, `www.ris.bka.gv.at`).
Don't drop any of those targets — Windows and the Claude.ai sandbox
each catch real users.

## Conventions

- **Project language is German.** READMEs, CHANGELOG entries, `SKILL.md`,
  commit subjects (after the prefix), code comments — all German.
  Identifiers and CLI flags follow the German API vocabulary
  (`Applikation`, `Geschaeftszahl`, `Suchworte`, `--pro-seite`,
  `--alle-seiten`). Keep that consistent.
- **Commit message prefixes** (see `CONTRIBUTING.md`):
  `Add:` / `Fix:` / `Update:` / `Remove:` / `Docs:` / `Test:` /
  `Refactor:` followed by a short German subject. Multi-area commits
  use a freer header (`Polish: …`) — see `git log` for the established
  voice.
- **CHANGELOG.md** is Keep-a-Changelog; user-visible changes land in
  `[Unreleased]` grouped under Added / Changed / Fixed / Removed /
  Docs, each bullet referencing the issue/PR number (`(#NN)`).
- **EditorConfig is authoritative.** UTF-8, LF, trim trailing
  whitespace (except in `.md`), final newline. Python = 4-space indent,
  YAML/JSON/shell = 2-space. Don't fight it.
- **No new top-level directories** unless asked. Investigations follow
  `Agent.md`: a single folder per investigation containing
  `notes.md` + `README.md` + any code you wrote, plus diffs (not full
  copies) of any external code you modified.

## Pull request / branch hygiene

- Default branch: `main`. Feature branches use the `claude/<topic>` form
  for AI-assisted work (e.g. `claude/add-claude-documentation-kLlkg`),
  `feature/<topic>` for everything else.
- PR template at `.github/PULL_REQUEST_TEMPLATE.md`; CODEOWNERS auto-
  requests `@tinhofer`.
- CI (`ci.yml`) must stay green on Python 3.9/3.11/3.12. If you raise
  the floor, update both the matrix and the `Python ≥ 3.9` line in
  `SKILL.md` together.

## Reference material

- API base: `https://data.bka.gv.at/ris/api/v2.6/Judikatur`
- Official docs: `https://data.bka.gv.at/ris/ogd/v2.6/Documents/Dokumentation_OGD-RIS_API.pdf`
- OGD-FAQ: `https://www.ris.bka.gv.at/RisInfo/OGD-FAQ.pdf` (rate-limit
  guidance, attribution requirement)
- Compare-implementations: `shrinkwrap-legal/shrinkwrap-legal-api`
  (Java, partial), `philrox/ris-mcp-ts` (TypeScript MCP, the more
  complete reference)
- BKA RIS contact for bulk-use questions: `ris.it@bka.gv.at`
