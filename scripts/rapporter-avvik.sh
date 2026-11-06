#!/usr/bin/env bash
# Gjør avvik fra den nattlige innlastingen synlige for et menneske.
#
# Leser avviksfilen fra nattlig-innlasting.sh (Markdown, tom fil = ingen avvik) og
#   - skriver en oppsummering på siden for kjøringen i GitHub Actions,
#   - oppretter issuen «Avvik i Grep-dataene» (tildelt repo-eieren, som da får varsel) når det er avvik,
#   - kommenterer issuen bare når avvikene har endret seg siden sist (ingen e-post hver natt for det samme),
#   - lukker issuen når det ikke lenger er avvik.
# Finnes ikke filen, ble innlastingen hoppet over, og ingenting gjøres.
#
# Bruk:  scripts/rapporter-avvik.sh avvik.md
# Miljøvariabler:
#   GH_TOKEN       token med issues: write (i workflowen: github.token)
#   TORRKJORING    1 = vis hva som ville blitt gjort, uten å røre GitHub (for testing)
#   GITHUB_*       settes av GitHub Actions
set -euo pipefail

FIL="${1:?Bruk: rapporter-avvik.sh avviksfil}"
TORRKJORING="${TORRKJORING:-0}"
TITTEL="Avvik i Grep-dataene"
KJORING="${GITHUB_SERVER_URL:-https://github.com}/${GITHUB_REPOSITORY:-lokal}/actions/runs/${GITHUB_RUN_ID:-0}"
SAMMENDRAG="${GITHUB_STEP_SUMMARY:-/dev/null}"

if [ ! -f "$FIL" ]; then
  echo "Ingen avviksfil. Innlastingen ble hoppet over, så det er ingenting å rapportere."
  exit 0
fi

gh_() {  # kjører gh, eller viser kommandoen ved tørrkjøring
  if [ "$TORRKJORING" = "1" ]; then echo "[tørrkjøring] gh $*" >&2; else gh "$@"; fi
}

# Beskrivelsen inneholder ikke lenke til kjøringen, slik at den er lik fra natt til natt når avvikene er like
BESKRIVELSE="$(mktemp)"
trap 'rm -f "$BESKRIVELSE"' EXIT
{
  echo "Den nattlige innlastingen til Grep-sandkassen fant data som bør sjekkes i Grep."
  echo "Innlastingen er ikke stoppet. Issuen oppdateres når avvikene endrer seg, og lukkes når alt er rettet."
  echo
  cat "$FIL"
} > "$BESKRIVELSE"

if [ "$TORRKJORING" = "1" ]; then
  NR=""
else
  NR=$(gh issue list --state open --limit 100 --json number,title \
         --jq ".[] | select(.title == \"$TITTEL\") | .number" | head -n 1)
fi

if [ -s "$FIL" ]; then
  { echo "## $TITTEL"; echo; cat "$FIL"; } >> "$SAMMENDRAG"
  echo "::warning title=$TITTEL::Innlastingen fant avvik i dataene. Se issuen «$TITTEL» og sammendraget for kjøringen."

  if [ -z "$NR" ]; then
    echo "Oppretter issuen «$TITTEL»."
    gh_ issue create --title "$TITTEL" --body-file "$BESKRIVELSE" --assignee "${GITHUB_REPOSITORY_OWNER:-@me}"
  elif [ "$(gh issue view "$NR" --json body --jq .body | tr -d '\r')" != "$(cat "$BESKRIVELSE")" ]; then
    echo "Avvikene har endret seg. Oppdaterer og kommenterer issue #$NR."
    gh_ issue edit "$NR" --body-file "$BESKRIVELSE"
    { echo "Avvikene har endret seg i [kjøringen]($KJORING):"; echo; cat "$FIL"; } \
      | gh_ issue comment "$NR" --body-file -
  else
    echo "Avvikene er de samme som i issue #$NR. Ingen ny kommentar."
  fi
  if [ "$TORRKJORING" = "1" ]; then echo "--- beskrivelse ---"; cat "$BESKRIVELSE"; fi
else
  { echo "## $TITTEL"; echo; echo "Ingen avvik."; } >> "$SAMMENDRAG"
  if [ -n "$NR" ]; then
    echo "Ingen avvik lenger. Lukker issue #$NR."
    gh_ issue close "$NR" --comment "Ingen avvik i [kjøringen]($KJORING). Lukker."
  else
    echo "Ingen avvik."
  fi
fi
