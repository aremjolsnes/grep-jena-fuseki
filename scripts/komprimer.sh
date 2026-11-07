#!/usr/bin/env bash
# Komprimerer TDB2-databasen i prod.
#
# TDB2 sletter ikke gamle data når en graf erstattes: hver innlasting legger en ny
# versjon ved siden av den gamle, og volumet fylles opp (8,1 av 10 GB 2026-11-07).
# Komprimering skriver en ny Data-NNNN med bare gjeldende data og sletter den gamle.
#
# Admin-API-et (/$/...) er bare åpent fra localhost (fuseki/shiro.ini), så kallene
# går via flyctl ssh inne på maskinen. Krever flyctl og FLY_API_TOKEN.
#
# Bruk: FLY_API_TOKEN=... scripts/komprimer.sh
set -euo pipefail

APP="${FLY_APP:-grep-fuseki-v3}"
URL="${FUSEKI_URL:-https://$APP.fly.dev}"
URL="${URL%/}"
MAKS_MINUTTER="${MAKS_MINUTTER:-30}"

logg() { echo "[$(date -u +%H:%M:%S)] $*"; }

# Kjører en kommando inne på maskinen. Admin-URL-ene skrives med %24 i stedet for $,
# så de slipper å kvoteres gjennom ssh.
inne() { flyctl ssh console -a "$APP" -C "$1"; }
ADMIN="http://localhost:3030/%24"

# Fly stopper maskinen når det ikke er trafikk gjennom proxyen. Ping holder den våken,
# også mens komprimeringen går (ssh-trafikk teller ikke).
vekk() { curl -s -o /dev/null --max-time 30 --fail "$URL/\$/ping"; }

logg "Vekker Fuseki ..."
for i in $(seq 1 30); do vekk && break; sleep 5; done

logg "Diskbruk før:"
inne "sh -c 'df -h /fuseki; du -sh /fuseki/databases/*'"

logg "Starter komprimering ..."
SVAR=$(inne "curl -sS --fail -X POST $ADMIN/compact/ds?deleteOld=true")
echo "$SVAR"
TASK=$(echo "$SVAR" | tr -d ' \r\n' | sed -n 's/.*"taskId":"\{0,1\}\([0-9]*\).*/\1/p')
if [ -z "$TASK" ]; then
  echo "::error::Fant ikke taskId i svaret fra /\$/compact" >&2
  exit 1
fi
logg "Oppgave $TASK"

SLUTT=$(( $(date +%s) + MAKS_MINUTTER * 60 ))
while :; do
  sleep 20
  vekk || true
  STATUS=$(inne "curl -sS $ADMIN/tasks/$TASK" | tr -d ' \r\n')
  if echo "$STATUS" | grep -q '"finished"'; then
    logg "Ferdig: $STATUS"
    if echo "$STATUS" | grep -q '"success":false'; then
      echo "::error::Komprimeringen feilet" >&2
      exit 1
    fi
    break
  fi
  if [ "$(date +%s)" -gt "$SLUTT" ]; then
    echo "::error::Komprimeringen ble ikke ferdig på $MAKS_MINUTTER minutter" >&2
    exit 1
  fi
  logg "Pågår ..."
done

logg "Diskbruk etter:"
inne "sh -c 'df -h /fuseki; du -sh /fuseki/databases/*'"
