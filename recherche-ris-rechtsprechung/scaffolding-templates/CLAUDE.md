# Vorlage: CLAUDE.md fuer das Scaffolding-Repo

> Diese Datei gehoert in das Scaffolding-Repo `tinhofer/Claude-Code` (also
> dort als `CLAUDE.md` im Projekt-Root) und wird per `apply-best-practices.sh`
> in jedes neu angelegte Projekt mitkopiert. Inhalt ist deckungsgleich mit
> der globalen `~/.claude/CLAUDE.md`, damit beide Quellen die gleiche Aussage
> treffen, egal ob Claude global ohne Projekt-Kontext oder im Projekt
> arbeitet.

---

# Projekt-Regeln fuer Claude Code

## Sicherheitspruefung von Fremdcode (Pflicht, risikoabgestuft)

**Bevor** du fremden Code, fremde Repos, fremde Pakete, fremde Container-Images
oder fremde Binaries in einem Projekt verwendest, fuehre eine Sicherheitspruefung
durch. Das Niveau richtet sich danach, **wie** der Code ins Projekt einfliesst.

### Definitionen

- **„Fremdcode"** = alles, was nicht aus diesem Repo, einem User-eigenen Repo
  oder einer offiziellen Standard-Bibliothek (Python stdlib, Node-Built-ins,
  Go std, Rust std) stammt.
- **„Verwenden"** umfasst: zitieren, Fakten extrahieren, Algorithmen abschreiben,
  Code-Schnipsel kopieren, als Dependency hinzufuegen, installieren, ausfuehren,
  als Submodul/Vendor einbinden, oder als Container-Image starten.

### Stufe A — Schnellpruefung (reine Lese-Referenz)

Trigger: Du liest das Repo nur, zitierst es, oder extrahierst Fakten daraus
(Parameter-Namen, URL-Patterns, Datenstrukturen, API-Schemata,
Algorithmen-Beschreibungen). **Kein** Code wandert ins Projekt, **nichts** wird
installiert.

Mindestcheck:
1. **Lizenz** existiert und ist kompatibel; Attribution pruefen.
2. **Plausibilitaets-Scan**:
   - URL korrekt geschrieben (kein Typosquat)
   - Owner-Account nicht offensichtlich neu/leer/verdaechtig
   - Repo-Name passt zur Beschreibung
3. **Provenance-Disclosure** im Bericht/PR/in der Antwort: Quelle nennen mit
   URL und einem Satz zur Einordnung („Drittanbieter-Repo, MIT, von User X,
   Account seit YYYY"). Niemals so tun, als kaeme die Information aus einer
   offiziellen Quelle, wenn sie aus einem Drittanbieter-Repo stammt.

### Stufe B — Tiefenpruefung (Code-Uebernahme oder Ausfuehrung)

Trigger: Du uebernimmst Code-Zeilen, fuegst eine Dependency hinzu
(`pip`/`uv`/`pipx`, `npm`/`pnpm`/`yarn`, `cargo`, `go get`, `gem`, Maven,
Gradle, …), fuehrst ein Binary aus, ziehst ein Container-Image, oder klonst
als Submodul/Vendor.

Pflichtchecks **vor** der Uebernahme/Installation:

1. **Owner-Identitaet**: Account-Alter, andere Repos desselben Owners,
   Repo-Historie/Owner-Transfers.
2. **Lizenz** vorhanden, kompatibel, mit Copyright-Zeile.
3. **`SECURITY.md`** vorhanden? Vulnerability-Disclosure-Pfad?
4. **Lifecycle-Hooks** im Manifest:
   - npm: `preinstall`, `install`, `postinstall`, `prepare`, `postpack`
   - Python: `setup.py`-Code, `pyproject.toml` Entry-Points, `pip install -e .`-Hooks
   - Go: `go generate`, `tools.go`-Imports
   - Rust: `build.rs`
5. **Dependencies** auf Typosquats und unuebliche Pakete pruefen; Lockfile
   committed?
6. **Code-Scan** auf gefaehrliche Muster: `eval`, `Function()`, `exec`,
   `child_process`, `spawn`, `os.system`, `subprocess.Popen`, `unsafe`,
   `transmute`; Hardcoded Credentials; ungewoehnliche Netzwerk-Ziele;
   Filesystem-Schreibvorgaenge ausserhalb des Arbeitsbereichs.
7. **CI-Workflows** sichten: CodeQL/SAST? Dependabot/Renovate?
   Provenance-Publishing?
8. **Registry-Eintrag** (falls Paket): Maintainer-Liste vs. GitHub-Owner,
   Versionshistorie, Download-Anzahl, `dist.shasum`.
9. **Konkrete Version pinnen**, niemals floating (`^`, `~`, `*`).
10. **Bei produktivem Einsatz**: Lockfile committen, automatische Updates nur
    via Dependabot/Renovate-PRs mit Review.

### Red Flags — sofort zurueck zum User

- Lifecycle-Hook fuehrt nicht-trivialen Code aus
- Owner-Account < 30 Tage alt UND nur dieses eine Repo
- Repo-Owner wurde an unbekannte Org transferiert
- Maintainer-Domain im Registry-Eintrag passt nicht zum GitHub-Profil
- Code spricht Hostnames an, die nichts mit der dokumentierten Funktion zu tun haben
- Stark verschleierter Code (Base64-Blobs, Hex-Strings, dynamic require)
- Auf der Registry-Seite andere Maintainer als auf GitHub
- `git log` zeigt einen vor kurzem hinzugefuegten, riesigen Commit

In all diesen Faellen: **erst zurueck zum User mit konkretem Befund**,
**nicht** weiterinstallieren oder ausfuehren.

### Provenance-Pflicht in jedem Output

Jede Aussage, die auf Drittanbieter-Quellen beruht, wird mit URL und einer
kurzen Einordnung („offizielle Doku" / „Drittanbieter-Repo, MIT,
Maintainer X seit YYYY" / „Forum-Post unverifiziert") gekennzeichnet.
Verschleierung der Herkunft ist nicht erlaubt — auch nicht aus Bequemlichkeit.

### Eigene Disziplin

- **Kein** „die wirken vertrauenswuerdig" als Begruendung. Immer mindestens
  Stufe A durchlaufen, dokumentieren, Quelle nennen.
- Wenn Stufe B nicht durchfuehrbar ist (Sandbox blockiert Netzwerkzugriff,
  Rate-Limit, …): ehrlich sagen und **nicht** installieren.
- Bei Unsicherheit lieber den User fragen als annehmen.
