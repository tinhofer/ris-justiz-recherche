#!/usr/bin/env bash
# Strukturierter Suchaufruf gegen die RIS-OGD-API v2.6 (Judikatur).
# Quelle: https://data.bka.gv.at/ris/api/v2.6/
#
# Ausgabe: Roh-JSON. Verarbeitung (jq, Markdown-Rendering) macht der Skill.

set -euo pipefail

BASE_URL="https://data.bka.gv.at/ris/api/v2.6/Judikatur"

APPLIKATION="Justiz"
PRO_SEITE="Twenty"
SEITE="1"
SUCHE_RS="True"
SUCHE_TEXT="True"

declare -a EXTRA=()

usage() {
  cat <<'EOF'
ris-search.sh — RIS-Judikatur-Suche

Pflicht: --applikation und mindestens einer von
         --suchworte | --geschaeftszahl | --norm | --rechtssatznummer

Optionen:
  --applikation Justiz|Vfgh|Vwgh|Bvwg|Lvwg|Dsk|Pvak|Gbk|Dok|AsylGH
  --suchworte STRING
  --geschaeftszahl STRING
  --norm STRING                   z.B. "1319a ABGB"
  --rechtssatznummer STRING
  --von YYYY-MM-DD                EntscheidungsdatumVon
  --bis YYYY-MM-DD                EntscheidungsdatumBis
  --im-ris-seit Undefined|EinerWoche|EinemMonat|DreiMonaten|SechsMonaten|EinemJahr
  --pro-seite Ten|Twenty|Fifty|OneHundred   (Default: Twenty)
  --seite N                       (Default: 1)
  --sortierung STRING
  --sort-direction Ascending|Descending
  --no-rechtssatz                 SucheNachRechtssatz=False
  --no-text                       SucheNachText=False
  -h, --help
EOF
}

while [[ $# -gt 0 ]]; do
  case "$1" in
    --applikation)        APPLIKATION="$2"; shift 2;;
    --suchworte)          EXTRA+=(--data-urlencode "Suchworte=$2"); shift 2;;
    --geschaeftszahl)     EXTRA+=(--data-urlencode "Geschaeftszahl=$2"); shift 2;;
    --norm)               EXTRA+=(--data-urlencode "Norm=$2"); shift 2;;
    --rechtssatznummer)   EXTRA+=(--data-urlencode "Rechtssatznummer=$2"); shift 2;;
    --von)                EXTRA+=(--data-urlencode "EntscheidungsdatumVon=$2"); shift 2;;
    --bis)                EXTRA+=(--data-urlencode "EntscheidungsdatumBis=$2"); shift 2;;
    --im-ris-seit)        EXTRA+=(--data-urlencode "ImRisSeit=$2"); shift 2;;
    --pro-seite)          PRO_SEITE="$2"; shift 2;;
    --seite)              SEITE="$2"; shift 2;;
    --sortierung)         EXTRA+=(--data-urlencode "Sortierung=$2"); shift 2;;
    --sort-direction)     EXTRA+=(--data-urlencode "SortDirection=$2"); shift 2;;
    --no-rechtssatz)      SUCHE_RS="False"; shift;;
    --no-text)            SUCHE_TEXT="False"; shift;;
    -h|--help)            usage; exit 0;;
    *) echo "Unbekannte Option: $1" >&2; usage; exit 2;;
  esac
done

# Mindestens einen Suchparameter prüfen
HAS_SEARCH=0
for v in "${EXTRA[@]}"; do
  case "$v" in
    Suchworte=*|Geschaeftszahl=*|Norm=*|Rechtssatznummer=*) HAS_SEARCH=1;;
  esac
done
if [[ $HAS_SEARCH -eq 0 ]]; then
  echo "Fehler: mindestens --suchworte, --geschaeftszahl, --norm oder --rechtssatznummer angeben." >&2
  exit 2
fi

curl -fsSL -G "$BASE_URL" \
  -H 'Accept: application/json' \
  --data-urlencode "Applikation=$APPLIKATION" \
  --data-urlencode "DokumenteProSeite=$PRO_SEITE" \
  --data-urlencode "Seitennummer=$SEITE" \
  --data-urlencode "SucheNachRechtssatz=$SUCHE_RS" \
  --data-urlencode "SucheNachText=$SUCHE_TEXT" \
  "${EXTRA[@]}"
