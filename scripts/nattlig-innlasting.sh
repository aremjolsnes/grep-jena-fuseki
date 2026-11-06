#!/usr/bin/env bash
# Nattlig innlasting av Grep-data til Fuseki-sandkassen.
#
# Grafstruktur (Fuseki kjører med tdb2:unionDefaultGraph, så spørringer uten GRAPH ser alt):
#   urn:graph:grep      rådata fra dumpen (erstattes i sin helhet hver gang)
#   urn:graph:ontologi  ontologi_kl06_rettet.ttl + grep_type_mapping.ttl fra repoet
#   urn:graph:meta      siste endrings-id og tidspunkt (skrives sist)
#
# Miljøvariabler:
#   FUSEKI_URL, FUSEKI_USER, FUSEKI_PASSWORD   påkrevd
#   DATASET        datasettnavn (standard: ds)
#   TVING          1 = last inn selv om endrings-id er uendret (standard: 0)
#   NT_FIL         ferdig N-Triples-fil; hopper over nedlasting og konvertering (for testing)
#   RIOT           kommando for Jena RIOT (standard: riot)
#   MIN_TRIPLER    røyktest: minste antall tripler i urn:graph:grep (standard: 1000000)
set -euo pipefail

: "${FUSEKI_URL:?FUSEKI_URL mangler}" "${FUSEKI_USER:?FUSEKI_USER mangler}" "${FUSEKI_PASSWORD:?FUSEKI_PASSWORD mangler}"
DATASET="${DATASET:-ds}"
TVING="${TVING:-0}"
NT_FIL="${NT_FIL:-}"
RIOT="${RIOT:-riot}"
MIN_TRIPLER="${MIN_TRIPLER:-1000000}"

REPO="$(cd "$(dirname "$0")/.." && pwd)"
ARBEID="$(mktemp -d)"
trap 'rm -rf "$ARBEID"' EXIT

BASE="${FUSEKI_URL%/}"
QUERY="$BASE/$DATASET/query"
UPDATE="$BASE/$DATASET/update"
GSP="$BASE/$DATASET/data"
AUTH=(-u "$FUSEKI_USER:$FUSEKI_PASSWORD")

G_GREP="urn:graph:grep"
G_ONTOLOGI="urn:graph:ontologi"
G_META="urn:graph:meta"
META="https://grep.udir.no/meta"
SCHEMA="https://grep.udir.no/schema"

logg() { echo "[$(date -u +%H:%M:%S)] $*"; }

# Første verdi i første rad av et SELECT-svar (CSV), tom streng hvis ingen treff
sporr() {
  curl -sS --fail-with-body -H 'Accept: text/csv' --data-urlencode "query=$1" "$QUERY" \
    | tr -d '\r' | sed -n '2p' | cut -d, -f1
}

oppdater() {
  curl -sS --fail-with-body "${AUTH[@]}" --data-urlencode "update=$1" "$UPDATE" > /dev/null
}

# Erstatter (PUT) eller legger til (POST) innhold i en named graph
last_graf() {  # metode graf filtype fil
  curl -sS --fail-with-body "${AUTH[@]}" -X "$1" -H "Content-Type: $3" \
       --data-binary "@$4" "$GSP?graph=$2" > /dev/null
}

tell_graf() { sporr "SELECT (COUNT(*) AS ?n) WHERE { GRAPH <$1> { ?s ?p ?o } }"; }

# 1. Sørg for at Fuseki er våken (Fly stopper maskinen ved inaktivitet)
logg "Vekker Fuseki ..."
for i in $(seq 1 30); do
  curl -s -o /dev/null --fail "$BASE/\$/ping" && break
  [ "$i" = 30 ] && { echo "Fuseki svarer ikke"; exit 1; }
  sleep 5
done

# 2. Sammenlign siste endrings-id hos Udir med den lagrede
SISTE_ID=$(curl -sS --fail "https://data.udir.no/kl06/v201906/endringer?antall=1" \
  | grep -oE '"endrings-id":\s*"[^"]+"' | head -n 1 | cut -d'"' -f4)
LAGRET_ID=$(sporr "SELECT ?id WHERE { GRAPH <$G_META> { <$META> <$SCHEMA/last-id> ?id } }" || true)
logg "Siste endrings-id hos Udir: $SISTE_ID"
logg "Lagret endrings-id:         ${LAGRET_ID:-(ingen)}"
if [ "$SISTE_ID" = "$LAGRET_ID" ] && [ "$TVING" != "1" ]; then
  logg "Ingen nye endringer. Avslutter."
  exit 0
fi

# 3. Last ned dumpen og konverter til N-Triples (med mindre NT_FIL er gitt)
if [ -z "$NT_FIL" ]; then
  logg "Laster ned JSON-LD-dump ..."
  curl -sS --fail -L "https://data.udir.no/kl06/v201906/dump/jsonld" -o "$ARBEID/dump.zip"
  unzip -q "$ARBEID/dump.zip" -d "$ARBEID/dump"
  logg "Konverterer til N-Triples ..."
  find "$ARBEID/dump" -name '*.jsonld' -print0 | xargs -0 $RIOT --output=nt > "$ARBEID/grep.nt"
  NT_FIL="$ARBEID/grep.nt"
fi
logg "N-Triples: $(wc -l < "$NT_FIL") linjer"

# 4. Rådata: erstatt hele urn:graph:grep i ett kall
logg "Laster rådata til <$G_GREP> ..."
last_graf PUT "$G_GREP" application/n-triples "$NT_FIL"

# 5. Ontologi fra repoet
logg "Laster ontologi til <$G_ONTOLOGI> ..."
last_graf PUT  "$G_ONTOLOGI" text/turtle "$REPO/ontologi/ontologi_kl06_rettet.ttl"
last_graf POST "$G_ONTOLOGI" text/turtle "$REPO/ontologi/grep_type_mapping.ttl"

# 6. Rydd bort data i den lagrede default graph (før B2 lå rådata der).
#    Med unionDefaultGraph er den usynlig for spørringer; DROP DEFAULT rører ikke named graphs.
oppdater "DROP SILENT DEFAULT"

# 7. Røyktest
N_GREP=$(tell_graf "$G_GREP")
N_ONT=$(tell_graf "$G_ONTOLOGI")
logg "Tripler: $G_GREP=$N_GREP, $G_ONTOLOGI=$N_ONT"
if [ "${N_GREP:-0}" -lt "$MIN_TRIPLER" ] || [ "${N_ONT:-0}" -lt 1 ]; then
  echo "Røyktest feilet (forventet minst $MIN_TRIPLER tripler i $G_GREP og >0 i $G_ONTOLOGI)"
  exit 1
fi

# 8. Lagre endrings-id sist, slik at en kjøring som feiler, blir forsøkt på nytt neste gang
NAA=$(date -u +%Y-%m-%dT%H:%M:%SZ)
cat > "$ARBEID/meta.nt" <<EOF
<$META> <$SCHEMA/last-id> "$SISTE_ID" .
<$META> <$SCHEMA/lastet> "$NAA"^^<http://www.w3.org/2001/XMLSchema#dateTime> .
<$META> <$SCHEMA/antall-tripler> "$N_GREP"^^<http://www.w3.org/2001/XMLSchema#integer> .
EOF
last_graf PUT "$G_META" application/n-triples "$ARBEID/meta.nt"
logg "Ferdig. Oppdatert til endrings-id $SISTE_ID."
