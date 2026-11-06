#!/usr/bin/env bash
# Nattlig innlasting av Grep-data til Fuseki-sandkassen.
#
# Grafstruktur (Fuseki kjører med tdb2:unionDefaultGraph, så spørringer uten GRAPH ser alt):
#   urn:graph:grep         rådata fra dumpen (erstattes i sin helhet hver gang)
#   urn:graph:ontologi     ontologi_kl06_rettet.ttl + grep_type_mapping.ttl fra repoet
#   urn:graph:normalisert  resultatet av sparql/normalisering/*.ru (bygges på nytt hver gang)
#   urn:graph:meta         siste endrings-id og tidspunkt (skrives sist)
#
# Miljøvariabler:
#   FUSEKI_URL, FUSEKI_USER, FUSEKI_PASSWORD   påkrevd
#   DATASET        datasettnavn (standard: ds)
#   TVING          1 = last inn selv om endrings-id er uendret (standard: 0)
#   NT_FIL         ferdig N-Triples-fil; hopper over nedlasting og konvertering (for testing)
#   RIOT           kommando for Jena RIOT (standard: riot)
#   MIN_TRIPLER    røyktest: minste antall tripler i urn:graph:grep (standard: 1000000)
#   MIN_GYLDIGHET  røyktest: minste antall udir:Gyldighet i urn:graph:normalisert (standard: 36000)
#   AVVIK_FIL      skriv avvik i dataene som Markdown hit (tom fil = ingen avvik). Brukes av
#                  scripts/rapporter-avvik.sh. Filen skrives ikke når innlastingen hoppes over.
set -euo pipefail

: "${FUSEKI_URL:?FUSEKI_URL mangler}" "${FUSEKI_USER:?FUSEKI_USER mangler}" "${FUSEKI_PASSWORD:?FUSEKI_PASSWORD mangler}"
DATASET="${DATASET:-ds}"
TVING="${TVING:-0}"
NT_FIL="${NT_FIL:-}"
RIOT="${RIOT:-riot}"
MIN_TRIPLER="${MIN_TRIPLER:-1000000}"
MIN_GYLDIGHET="${MIN_GYLDIGHET:-36000}"
AVVIK_FIL="${AVVIK_FIL:-}"

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
G_NORM="urn:graph:normalisert"
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

# Kjører alle .ru-filer i en mappe i alfabetisk rekkefølge
kjor_regler() {  # mappe
  local f t0
  for f in "$1"/*.ru; do
    t0=$(date +%s)
    curl -sS --fail-with-body "${AUTH[@]}" -H 'Content-Type: application/sparql-update' \
         --data-binary "@$f" "$UPDATE" > /dev/null
    logg "  ${f#"$REPO"/}: $(( $(date +%s) - t0 )) s"
  done
}

# Skriver ut alle rader i et SELECT-svar (CSV) uten overskrift
sporr_alle() {
  curl -sS --fail-with-body -H 'Accept: text/csv' --data-urlencode "query=$1" "$QUERY" | tr -d '\r' | sed '1d'
}

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

# 7. Normalisering (fase 2): urn:graph:normalisert bygges på nytt, og datoer og tall
#    gjøres om til riktige datatyper direkte i urn:graph:grep (B4)
logg "Normaliserer ..."
oppdater "DROP SILENT GRAPH <$G_NORM>"
kjor_regler "$REPO/sparql/normalisering"

# 8. Røyktest og kontroller
N_GREP=$(tell_graf "$G_GREP")
N_ONT=$(tell_graf "$G_ONTOLOGI")
N_NORM=$(tell_graf "$G_NORM")
N_GYLDIGHET=$(sporr "PREFIX udir: <http://psi.udir.no/ontologi/>
  SELECT (COUNT(*) AS ?n) WHERE { GRAPH <$G_NORM> { ?g a udir:Gyldighet } }")
N_STATUS=$(sporr "PREFIX udir: <http://psi.udir.no/ontologi/>
  SELECT (COUNT(*) AS ?n) WHERE { GRAPH <$G_NORM> { ?s udir:status ?st } }")
logg "Tripler: $G_GREP=$N_GREP, $G_ONTOLOGI=$N_ONT, $G_NORM=$N_NORM"
logg "udir:Gyldighet: $N_GYLDIGHET, udir:status: $N_STATUS"

# Avvik i dataene: noe et menneske bør se på, men som ikke stopper innlastingen.
# Hvert funn logges og samles i $ARBEID/avvik.md, som scripts/rapporter-avvik.sh gjør om til en GitHub-issue.
: > "$ARBEID/avvik.md"
N_AVVIK=0
kort_iri() {
  sed -e 's#http://psi.udir.no/ontologi/kl06/#u:#g' -e 's#http://psi.udir.no/ontologi/#udir:#g' \
      -e 's#http://psi.udir.no/kl06/#d:#g' -e 's#http://www.w3.org/2001/XMLSchema\##xsd:#g'
}
avvik() {  # overskrift forklaring kolonner(kommaseparert) csv-rader
  local n skille
  n=$(printf '%s' "$4" | grep -c . || true)
  logg "$1: $n"
  printf '%s\n' "$4" | sed '/^$/d; s/^/    /'
  [ "$n" -eq 0 ] && return 0
  N_AVVIK=$((N_AVVIK + n))
  skille=$(printf '%s' "$3" | sed 's/[^,]*/---/g')   # "A,B,C" -> "---,---,---"
  {
    printf '### %s (%s)\n\n%s\n\n' "$1" "$n" "$2"
    printf '%s\n%s\n' "$3" "$skille" | sed 's/,/ | /g; s/^/| /; s/$/ |/'
    printf '%s\n' "$4" | sed '/^$/d' | kort_iri | sed 's/,/ | /g; s/^/| /; s/$/ |/'
    printf '\n'
  } >> "$ARBEID/avvik.md"
}

# Datoer med urimelige årstall. Blanke noder vises via gyldighetsressursen i urn:graph:normalisert.
avvik "Datoer med urimelig årstall" \
  "Årstall før 1990 eller etter 2100. Sannsynligvis en skrivefeil i Grep." \
  "Ressurs,Egenskap,Dato" "$(sporr_alle "$(cat <<EOF
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT ?s ?p ?d WHERE {
  { GRAPH <$G_GREP> { ?s ?p ?d FILTER(!isBlank(?s)) } } UNION { GRAPH <$G_NORM> { ?s ?p ?d } }
  FILTER(DATATYPE(?d) = xsd:dateTime && (YEAR(?d) < 1990 || YEAR(?d) > 2100))
} ORDER BY ?s ?p
EOF
)")"

# Gyldighetsegenskaper i dumpen som N1 ikke fant koblingen til (skal være 0).
# IRI-en <…/gyldighet/S/REL/OBJ> svarer til u:gyldighet-REL-OBJ på S, og <…/S/REL/OBJ/N> til u:gyldighet-N-REL-OBJ.
avvik "Gyldighet uten kobling" \
  "Gyldighetsinformasjon for en kobling som ikke finnes på ressursen. Ikke med i urn:graph:normalisert." \
  "Ressurs,Gyldighetsegenskap" "$(sporr_alle "$(cat <<EOF
PREFIX udir: <http://psi.udir.no/ontologi/>
SELECT ?s ?gp WHERE {
  GRAPH <$G_GREP> { ?s ?gp ?b FILTER(STRSTARTS(STR(?gp), "http://psi.udir.no/ontologi/kl06/gyldighet-")) }
  FILTER NOT EXISTS {
    GRAPH <$G_NORM> { ?s udir:gyldighet ?g }
    BIND(REPLACE(STR(?g), "^http://psi.udir.no/kl06/gyldighet/[^/]*/", "") AS ?sti)
    FILTER(STR(?gp) = CONCAT("http://psi.udir.no/ontologi/kl06/gyldighet-",
      REPLACE(REPLACE(?sti, "^([^/]*)/([^/]*)/([0-9]+)\$", "\$3-\$1-\$2"), "^([^/]*)/([^/]*)\$", "\$1-\$2")))
  }
}
EOF
)")"

# Verdier som N3 ikke kunne gjøre om (rekkevidden er typet, men verdien passer ikke formatet)
avvik "Verdier med feil format" \
  "Egenskapen skal være dato eller tall, men verdien passer ikke formatet. Står som tekst." \
  "Ressurs,Egenskap,Verdi" "$(sporr_alle "$(cat <<EOF
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT ?r ?p ?v WHERE {
  GRAPH <$G_ONTOLOGI> { ?p rdfs:range ?dt VALUES ?dt { xsd:dateTime xsd:integer xsd:decimal } }
  GRAPH <$G_GREP> { ?s ?p ?v FILTER(DATATYPE(?v) = xsd:string) }
  OPTIONAL { GRAPH <$G_GREP> { ?eier ?gp ?s } FILTER(isBlank(?s)) }  # blank node: vis eieren
  BIND(COALESCE(?eier, ?s) AS ?r)
} ORDER BY ?r ?p LIMIT 200
EOF
)")"

if [ "${N_GREP:-0}" -lt "$MIN_TRIPLER" ] || [ "${N_ONT:-0}" -lt 1 ] \
   || [ "${N_GYLDIGHET:-0}" -lt "$MIN_GYLDIGHET" ] || [ "${N_STATUS:-0}" -lt 1 ]; then
  echo "Røyktest feilet (forventet minst $MIN_TRIPLER tripler i $G_GREP, >0 i $G_ONTOLOGI," \
       "minst $MIN_GYLDIGHET udir:Gyldighet og >0 udir:status i $G_NORM)"
  exit 1
fi

# 9. Lagre endrings-id sist, slik at en kjøring som feiler, blir forsøkt på nytt neste gang
NAA=$(date -u +%Y-%m-%dT%H:%M:%SZ)
cat > "$ARBEID/meta.nt" <<EOF
<$META> <$SCHEMA/last-id> "$SISTE_ID" .
<$META> <$SCHEMA/lastet> "$NAA"^^<http://www.w3.org/2001/XMLSchema#dateTime> .
<$META> <$SCHEMA/antall-tripler> "$N_GREP"^^<http://www.w3.org/2001/XMLSchema#integer> .
<$META> <$SCHEMA/antall-tripler-normalisert> "$N_NORM"^^<http://www.w3.org/2001/XMLSchema#integer> .
EOF
last_graf PUT "$G_META" application/n-triples "$ARBEID/meta.nt"
logg "Avvik i dataene: $N_AVVIK"
if [ -n "$AVVIK_FIL" ]; then cp "$ARBEID/avvik.md" "$AVVIK_FIL"; fi
logg "Ferdig. Oppdatert til endrings-id $SISTE_ID."
