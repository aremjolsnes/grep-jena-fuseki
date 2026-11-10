#!/usr/bin/env bash
# Nattlig innlasting av Grep-data til Fuseki-sandkassen.
#
# Grafstruktur (Fuseki kjører med tdb2:unionDefaultGraph, så spørringer uten GRAPH ser alt):
#   urn:graph:grep         rådata fra dumpen (erstattes i sin helhet hver gang)
#   urn:graph:ontologi     ontologi_kl06_rettet.ttl + grep_type_mapping.ttl + udir.ttl fra repoet
#   urn:graph:normalisert  resultatet av sparql/normalisering/*.ru (bygges på nytt hver gang)
#   urn:graph:utledet      resultatet av sparql/utledning/*.ru (bygges på nytt hver gang)
#   urn:graph:koblinger    koblinger til andre kunnskapsgrafer fra ontologi/koblinger/*.ttl (STYRK-08, NUS, ESCO-yrker)
#   urn:graph:meta         siste endrings-id og tidspunkt, og DCAT/VoID fra ontologi/datasett.ttl (skrives sist)
#   urn:graph:grep-ny      mellomgraf under innlasting; flyttes til urn:graph:grep med MOVE
#
# Miljøvariabler:
#   FUSEKI_URL, FUSEKI_USER, FUSEKI_PASSWORD   påkrevd
#   DATASET        datasettnavn (standard: ds)
#   TVING          1 = last inn selv om endrings-id er uendret (standard: 0)
#   NT_FIL         ferdig N-Triples-fil; hopper over nedlasting og konvertering (for testing)
#   RIOT           kommando for Jena RIOT (standard: riot)
#   PYTHON         Python 3 for scripts/sjekk-koblinger.py (standard: python3)
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
# Nye forsøk ved forbigående feil (tidsavbrudd, 5xx). Fly-proxyen har gitt 502 midt i en PUT (2026-11-06).
# Trygt fordi alle kallene kan gjentas: PUT erstatter grafen, og reglene gir samme resultat to ganger.
RETRY=(--retry 3 --retry-delay 15 --retry-connrefused)

G_GREP="urn:graph:grep"
G_GREP_NY="urn:graph:grep-ny"   # mellomgraf under innlasting (se steg 4)
G_ONTOLOGI="urn:graph:ontologi"
G_NORM="urn:graph:normalisert"
G_UTLEDET="urn:graph:utledet"
G_KOBLINGER="urn:graph:koblinger"
G_META="urn:graph:meta"
META="https://grep.udir.no/meta"
SCHEMA="https://grep.udir.no/schema"

logg() { echo "[$(date -u +%H:%M:%S)] $*"; }

# Første verdi i første rad av et SELECT-svar (CSV), tom streng hvis ingen treff
sporr() {
  curl -sS "${RETRY[@]}" --fail-with-body -H 'Accept: text/csv' --data-urlencode "query=$1" "$QUERY" \
    | tr -d '\r' | sed -n '2p' | cut -d, -f1
}

oppdater() {
  curl -sS "${RETRY[@]}" --fail-with-body "${AUTH[@]}" --data-urlencode "update=$1" "$UPDATE" > /dev/null
}

# Erstatter (PUT) eller legger til (POST) innhold i en named graph
last_graf() {  # metode graf filtype fil
  curl -sS "${RETRY[@]}" --fail-with-body "${AUTH[@]}" -X "$1" -H "Content-Type: $3" \
       --data-binary "@$4" "$GSP?graph=$2" > /dev/null
}

tell_graf() { sporr "SELECT (COUNT(*) AS ?n) WHERE { GRAPH <$1> { ?s ?p ?o } }"; }

# Kjører alle .ru-filer i en mappe i alfabetisk rekkefølge
kjor_regler() {  # mappe
  local f t0
  for f in "$1"/*.ru; do
    t0=$(date +%s)
    curl -sS "${RETRY[@]}" --fail-with-body "${AUTH[@]}" -H 'Content-Type: application/sparql-update' \
         --data-binary "@$f" "$UPDATE" > /dev/null
    logg "  ${f#"$REPO"/}: $(( $(date +%s) - t0 )) s"
  done
}

# Skriver ut alle rader i et SELECT-svar (CSV) uten overskrift
sporr_alle() {
  curl -sS "${RETRY[@]}" --fail-with-body -H 'Accept: text/csv' --data-urlencode "query=$1" "$QUERY" | tr -d '\r' | sed '1d'
}

# 1. Sørg for at Fuseki er våken (Fly stopper maskinen ved inaktivitet)
logg "Vekker Fuseki ..."
for i in $(seq 1 30); do
  curl -s -o /dev/null --fail "$BASE/\$/ping" && break
  [ "$i" = 30 ] && { echo "Fuseki svarer ikke"; exit 1; }
  sleep 5
done

# 2. Sammenlign siste endrings-id hos Udir med den lagrede
last_ned_dump() {
  [ -f "$ARBEID/dump.zip" ] && return 0
  logg "Laster ned JSON-LD-dump ..."
  curl -sS "${RETRY[@]}" --fail -L "https://data.udir.no/kl06/v201906/dump/jsonld" -o "$ARBEID/dump.zip"
}
ENDRINGER=$(curl -sS "${RETRY[@]}" --fail "https://data.udir.no/kl06/v201906/endringer?antall=1")
SISTE_ID=$(printf '%s' "$ENDRINGER" | grep -oE '"endrings-id":\s*"[^"]+"' | head -n 1 | cut -d'"' -f4 || true)
# Udirs tidspunkt for siste endring, i norsk lokal tid uten tidssone (slik API-et gir det).
# Brøkdelen av sekundet kuttes. Tomt hvis API-et ikke ga noe gyldig.
UDIR_TIDSPUNKT=$(printf '%s' "$ENDRINGER" | grep -oE '"tidspunkt":\s*"[^"]+"' | head -n 1 | cut -d'"' -f4 | cut -d. -f1 || true)
if ! printf '%s' "$UDIR_TIDSPUNKT" | grep -qE '^[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}$'; then
  UDIR_TIDSPUNKT=""
fi
if [ -z "$SISTE_ID" ]; then
  # Endrings-API-et har svart med en tom liste ([], 2026-11-07). Uten reserve døde skriptet
  # stille her. Dumpen har verken ETag eller Last-Modified, så sjekksummen brukes som id.
  echo "::warning::Endrings-API-et hos Udir ga ingen endrings-id (svar: ${ENDRINGER:0:100}). Bruker sjekksummen til dumpen i stedet."
  if [ -z "$NT_FIL" ]; then
    last_ned_dump
    SISTE_ID="sha256:$(sha256sum "$ARBEID/dump.zip" | cut -c1-64)"
  else
    SISTE_ID="lokal:$(basename "$NT_FIL")"
  fi
fi
LAGRET_ID=$(sporr "SELECT ?id WHERE { GRAPH <$G_META> { <$META> <$SCHEMA/last-id> ?id } }" || true)
logg "Siste endrings-id hos Udir: $SISTE_ID"
logg "Lagret endrings-id:         ${LAGRET_ID:-(ingen)}"
if [ "$SISTE_ID" = "$LAGRET_ID" ] && [ "$TVING" != "1" ]; then
  logg "Ingen nye endringer. Avslutter."
  exit 0
fi

# 3. Last ned dumpen og konverter til N-Triples (med mindre NT_FIL er gitt)
if [ -z "$NT_FIL" ]; then
  last_ned_dump
  unzip -q "$ARBEID/dump.zip" -d "$ARBEID/dump"
  logg "Konverterer til N-Triples ..."
  find "$ARBEID/dump" -name '*.jsonld' -print0 | xargs -0 $RIOT --output=nt > "$ARBEID/grep.nt"
  NT_FIL="$ARBEID/grep.nt"
fi
logg "N-Triples: $(wc -l < "$NT_FIL") linjer"

# 4. Rådata: last opp til en tom mellomgraf, og bytt den inn med MOVE.
#    En PUT rett til urn:graph:grep stopper opp: Fuseki leser den første bufferen og sletter
#    så den gamle grafen (1,2 mill. tripler) før den leser mer. På en nystartet maskin tar det
#    over 30 s, og da bryter Fly-proxyen forbindelsen (502, 2026-11-07). Mot en tom graf er det
#    ingenting å slette, og slettingen skjer i stedet i MOVE, et kall uten innhold å sende.
logg "Laster rådata til <$G_GREP_NY> ..."
oppdater "DROP SILENT GRAPH <$G_GREP_NY>"
last_graf PUT "$G_GREP_NY" application/n-triples "$NT_FIL"
N_NY=$(tell_graf "$G_GREP_NY")
logg "<$G_GREP_NY>: $N_NY tripler"
# Mellomgrafen er synlig i union default graph, så den skal ikke bli liggende hvis noe feiler
rydd_ny() { oppdater "DROP SILENT GRAPH <$G_GREP_NY>" || true; }
if [ "${N_NY:-0}" -lt "$MIN_TRIPLER" ]; then
  echo "FEIL: <$G_GREP_NY> har bare ${N_NY:-0} tripler (minst $MIN_TRIPLER). <$G_GREP> er ikke rørt." >&2
  rydd_ny
  exit 1
fi
logg "Bytter inn <$G_GREP> ..."
t0=$(date +%s)
# Ikke RETRY her: kjøres MOVE to ganger, er mellomgrafen tom andre gang og ville tømt urn:graph:grep.
if ! curl -sS --fail-with-body "${AUTH[@]}" --data-urlencode "update=MOVE <$G_GREP_NY> TO <$G_GREP>" "$UPDATE" > /dev/null; then
  # MOVE er én transaksjon: grafen er enten uendret eller helt byttet (fikk bare proxyen 502,
  # kan Fuseki ha fullført). Meta er ikke skrevet, så neste kjøring laster uansett på nytt.
  echo "FEIL: MOVE feilet." >&2
  rydd_ny
  exit 1
fi
logg "  MOVE: $(( $(date +%s) - t0 )) s"

# 5. Ontologi fra repoet
logg "Laster ontologi til <$G_ONTOLOGI> ..."
last_graf PUT  "$G_ONTOLOGI" text/turtle "$REPO/ontologi/ontologi_kl06_rettet.ttl"
last_graf POST "$G_ONTOLOGI" text/turtle "$REPO/ontologi/grep_type_mapping.ttl"
last_graf POST "$G_ONTOLOGI" text/turtle "$REPO/ontologi/udir.ttl"

# 5b. Koblinger til andre kunnskapsgrafer (idé 4 i docs/ideer.md). styrk.ttl lages av scripts/lag-styrk-ttl.py.
logg "Laster koblinger til <$G_KOBLINGER> ..."
last_graf PUT "$G_KOBLINGER" text/turtle "$REPO/ontologi/koblinger/styrk.ttl"
last_graf POST "$G_KOBLINGER" text/turtle "$REPO/ontologi/koblinger/nus.ttl"   # lages av scripts/lag-nus-ttl.py
last_graf POST "$G_KOBLINGER" text/turtle "$REPO/ontologi/koblinger/esco-yrker.ttl"   # lages av scripts/lag-esco-ttl.py

# 6. Rydd bort data i den lagrede default graph (før B2 lå rådata der).
#    Med unionDefaultGraph er den usynlig for spørringer; DROP DEFAULT rører ikke named graphs.
oppdater "DROP SILENT DEFAULT"

# 7. Normalisering (fase 2): urn:graph:normalisert bygges på nytt, og datoer og tall
#    gjøres om til riktige datatyper direkte i urn:graph:grep (B4)
logg "Normaliserer ..."
oppdater "DROP SILENT GRAPH <$G_NORM>"
kjor_regler "$REPO/sparql/normalisering"

# 7b. Utledning (fase 3): typer og egenskaper fra ontologien, i urn:graph:utledet.
#     Kjøres etter normaliseringen, slik at også udir:Gyldighet-ressursene er med.
logg "Utleder ..."
oppdater "DROP SILENT GRAPH <$G_UTLEDET>"
kjor_regler "$REPO/sparql/utledning"

# 8. Røyktest og kontroller
N_GREP=$(tell_graf "$G_GREP")
N_ONT=$(tell_graf "$G_ONTOLOGI")
N_NORM=$(tell_graf "$G_NORM")
N_UTLEDET=$(tell_graf "$G_UTLEDET")
N_KOBLINGER=$(tell_graf "$G_KOBLINGER")
# STYRK-08: programområder med yrkesklassifisering
N_STYRK=$(sporr "PREFIX udir: <http://psi.udir.no/ontologi/>
  SELECT (COUNT(*) AS ?n) WHERE { GRAPH <$G_KOBLINGER> { ?p udir:yrkesklassifisering ?k } }")
# NUS: programområder med utdanningsklassifisering
N_NUS=$(sporr "PREFIX udir: <http://psi.udir.no/ontologi/>
  SELECT (COUNT(*) AS ?n) WHERE { GRAPH <$G_KOBLINGER> { ?p udir:utdanningsklassifisering ?k } }")
# ESCO: yrker under ISCO-gruppene programområdene er koblet til
N_ESCO=$(sporr "SELECT (COUNT(*) AS ?n) WHERE { GRAPH <$G_KOBLINGER> { ?y a <http://data.europa.eu/esco/model#Occupation> } }")
# R1: kompetansemål i LK20 skal ha typen fra Udirs ontologi
N_KM_TYPE=$(sporr "PREFIX u: <http://psi.udir.no/ontologi/kl06/>
  SELECT (COUNT(*) AS ?n) WHERE { GRAPH <$G_UTLEDET> { ?s a u:Kompetansemaal_lk20 } }")
# Fase 4: overbegrepene i ontologi/udir.ttl (på tvers av LK06 og LK20)
N_OVERBEGREP=$(sporr_alle "PREFIX udir: <http://psi.udir.no/ontologi/>
  SELECT ?k (COUNT(*) AS ?n) WHERE { GRAPH <$G_UTLEDET> { ?s a ?k
    VALUES ?k { udir:Laereplan udir:Kompetansemaal udir:Kompetansemaalsett } } } GROUP BY ?k ORDER BY ?k" \
  | sed 's#http://psi.udir.no/ontologi/#udir:#' | tr '\n' ' ')
# R3: revisjonstilhørighet, og ingen ressurs i begge revisjonene
N_REVISJON=$(sporr_alle "PREFIX udir: <http://psi.udir.no/ontologi/>
  SELECT ?r (COUNT(*) AS ?n) WHERE { GRAPH <$G_UTLEDET> { ?s udir:revisjon ?r } } GROUP BY ?r ORDER BY ?r" \
  | sed 's#http://psi.udir.no/ontologi/#udir:#' | tr '\n' ' ')
N_TO_REVISJONER=$(sporr "PREFIX udir: <http://psi.udir.no/ontologi/>
  SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE { GRAPH <$G_UTLEDET> { ?s udir:revisjon udir:LK06 , udir:LK20 } }")
# R4: SKOS-begreper per begrepssystem, og fagområder uten fagkategori (skal være 0)
N_SKOS=$(sporr_alle "PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
  SELECT ?ks (COUNT(*) AS ?n) WHERE { GRAPH <$G_UTLEDET> { ?s a skos:Concept ; skos:inScheme ?ks } }
  GROUP BY ?ks ORDER BY ?ks" \
  | sed 's#http://psi.udir.no/ontologi/#udir:#' | tr '\n' ' ')
N_FAGOMR_UTEN_KATEGORI=$(sporr "PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
  PREFIX udir: <http://psi.udir.no/ontologi/> PREFIX u: <http://psi.udir.no/ontologi/kl06/>
  SELECT (COUNT(*) AS ?n) WHERE { GRAPH <$G_GREP> { ?fo a u:fagomraade }
    FILTER NOT EXISTS { GRAPH <$G_UTLEDET> { ?fo skos:broader ?fk . ?fk skos:inScheme udir:Fagkategorier } } }")
# R5: alle språk skal ha kobling til EUs språktabell
N_SPRAAK_UTEN_EU=$(sporr "PREFIX skos: <http://www.w3.org/2004/02/skos/core#> PREFIX u: <http://psi.udir.no/ontologi/kl06/>
  SELECT (COUNT(*) AS ?n) WHERE { GRAPH <$G_GREP> { ?s a u:spraak }
    FILTER NOT EXISTS { GRAPH <$G_UTLEDET> { ?s skos:exactMatch ?eu
      FILTER(STRSTARTS(STR(?eu), \"http://publications.europa.eu/resource/authority/language/\")) } } }")
# N5: læreplaner og alt som hører til dem, skal ha udir:bokmaalTittel og udir:nynorskTittel
N_UTEN_BOKMAALTITTEL=$(sporr "PREFIX u: <http://psi.udir.no/ontologi/kl06/> PREFIX udir: <http://psi.udir.no/ontologi/>
  SELECT (COUNT(DISTINCT ?s) AS ?n) WHERE {
    GRAPH <$G_GREP> { { ?s a u:laereplan } UNION { ?s a u:laereplan_lk20 } UNION { ?s u:tilhoerer-laereplan ?lp } ?s u:tittel ?x }
    FILTER(NOT EXISTS { GRAPH <$G_NORM> { ?s udir:bokmaalTittel ?t } }
        || NOT EXISTS { GRAPH <$G_NORM> { ?s udir:nynorskTittel ?t } }) }")
# Dublin Core (fase 4 steg 5): relasjonene fra Grep-egenskapene via R2
N_DCTERMS=$(sporr_alle "SELECT ?p (COUNT(*) AS ?n) WHERE { GRAPH <$G_UTLEDET> { ?s ?p ?o
    FILTER(STRSTARTS(STR(?p), \"http://purl.org/dc/terms/\")) } } GROUP BY ?p ORDER BY ?p" \
  | sed 's#http://purl.org/dc/terms/#dcterms:#' | tr '\n' ' ')
# schema.org (fase 4 steg 6): udir:gyldigFra/gyldigTil som schema:validFrom/validThrough via R2
N_SCHEMA=$(sporr_alle "SELECT ?p (COUNT(*) AS ?n) WHERE { GRAPH <$G_UTLEDET> { ?s ?p ?o
    FILTER(STRSTARTS(STR(?p), \"https://schema.org/\")) } } GROUP BY ?p ORDER BY ?p" \
  | sed 's#https://schema.org/#schema:#' | tr '\n' ' ')
N_GYLDIGHET=$(sporr "PREFIX udir: <http://psi.udir.no/ontologi/>
  SELECT (COUNT(*) AS ?n) WHERE { GRAPH <$G_NORM> { ?g a udir:Gyldighet } }")
# N4: alle fagkoder skal ha en gyldighetsperiode (eventuelt 1970-01-01–2100-12-31)
N_FAGKODER_UTEN_PERIODE=$(sporr "PREFIX u: <http://psi.udir.no/ontologi/kl06/> PREFIX udir: <http://psi.udir.no/ontologi/>
  SELECT (COUNT(*) AS ?n) WHERE { GRAPH <$G_GREP> { ?fk a u:fagkode }
    FILTER NOT EXISTS { GRAPH <$G_NORM> { ?fk udir:gyldigFra ?fra ; udir:gyldigTil ?til } } }")
N_PERIODER=$(sporr_alle "PREFIX udir: <http://psi.udir.no/ontologi/>
  SELECT ?p (COUNT(*) AS ?n) WHERE { GRAPH <$G_NORM> { ?r ?p ?d
    VALUES ?p { udir:gyldigFra udir:undervisningFra udir:eksamenFra udir:startdato } } } GROUP BY ?p ORDER BY ?p" \
  | sed 's#http://psi.udir.no/ontologi/#udir:#' | tr '\n' ' ')
logg "Tripler: $G_GREP=$N_GREP, $G_ONTOLOGI=$N_ONT, $G_NORM=$N_NORM, $G_UTLEDET=$N_UTLEDET, $G_KOBLINGER=$N_KOBLINGER"
logg "Programområder med STYRK-08 (koblinger): $N_STYRK, med NUS: $N_NUS. ESCO-yrker: $N_ESCO"
logg "u:Kompetansemaal_lk20 (utledet): $N_KM_TYPE"
logg "Overbegreper (utledet): $N_OVERBEGREP"
logg "Revisjon (utledet): $N_REVISJON, i begge revisjonene: $N_TO_REVISJONER"
logg "SKOS-begreper (utledet): $N_SKOS, fagområder uten fagkategori: $N_FAGOMR_UTEN_KATEGORI"
logg "Språk uten kobling til EUs språktabell: $N_SPRAAK_UTEN_EU"
logg "Dublin Core (utledet): $N_DCTERMS"
logg "schema.org (utledet): $N_SCHEMA"
logg "Uten udir:bokmaalTittel eller udir:nynorskTittel (læreplaner og det som hører til dem): $N_UTEN_BOKMAALTITTEL"
logg "udir:Gyldighet: $N_GYLDIGHET, fagkoder uten periode: $N_FAGKODER_UTEN_PERIODE"
logg "Perioder: $N_PERIODER"

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
  "Årstall før 1990 eller etter 2100. Sannsynligvis en skrivefeil i Grep. 1970-01-01 og 2100-12-31 er sandkassens egne verdier for åpne ender og telles ikke." \
  "Ressurs,Egenskap,Dato" "$(sporr_alle "$(cat <<EOF
PREFIX xsd: <http://www.w3.org/2001/XMLSchema#>
SELECT ?s ?p ?d WHERE {
  { GRAPH <$G_GREP> { ?s ?p ?d FILTER(!isBlank(?s)) } } UNION { GRAPH <$G_NORM> { ?s ?p ?d } }
  FILTER(DATATYPE(?d) IN (xsd:dateTime, xsd:date) && (YEAR(?d) < 1990 || YEAR(?d) > 2100))
  FILTER(?d NOT IN ("1970-01-01"^^xsd:date, "2100-12-31"^^xsd:date))
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

# STYRK-08-koblinger (ontologi/koblinger/styrk.csv) til programområder som ikke lenger finnes i Grep
avvik "Kobling til ukjent programområde" \
  "Programområdet står i ontologi/koblinger/styrk.csv eller nus.csv, men finnes ikke i Grep-dataene. Fjern raden eller rett koden." \
  "Programområde,Egenskap,Kode" "$(sporr_alle "$(cat <<EOF
PREFIX udir: <http://psi.udir.no/ontologi/>
PREFIX u: <http://psi.udir.no/ontologi/kl06/>
SELECT ?p ?e ?k WHERE {
  GRAPH <$G_KOBLINGER> { ?p ?e ?k VALUES ?e { udir:yrkesklassifisering udir:utdanningsklassifisering } }
  FILTER NOT EXISTS { GRAPH <$G_GREP> { ?p a u:programomraade } }
} ORDER BY ?p
EOF
)")"

# Koblingene holdes oppdatert (scripts/sjekk-koblinger.py): koder SSB har tatt ut, og nye programområder i Grep
avvik "Kode tatt ut av klassifikasjonen hos SSB" \
  "Koden står i ontologi/koblinger/styrk.csv eller nus.csv, men finnes ikke i versjonen av STYRK-08 eller NUS som gjelder i dag. Velg en ny kode, og kjør scripts/lag-styrk-ttl.py eller lag-nus-ttl.py på nytt." \
  "Kode,Klassifikasjon,Programområde" "$("${PYTHON:-python3}" "$REPO/scripts/sjekk-koblinger.py" utgaatte-koder)"
avvik "Nye programområder som ikke er vurdert" \
  "Programområdet finnes i Grep, men står ikke i ontologi/koblinger/nus.csv (alle programområder) eller styrk.csv (programområder med yrkestittel). Legg til en rad, eventuelt med metoden «ingen»." \
  "Programområde,Tittel,Mangler i" "$(FUSEKI_URL="$BASE" DATASET="$DATASET" "${PYTHON:-python3}" "$REPO/scripts/sjekk-koblinger.py" nye-programomraader)"

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
   || [ "${N_GYLDIGHET:-0}" -lt "$MIN_GYLDIGHET" ] || [ "${N_FAGKODER_UTEN_PERIODE:-1}" -ne 0 ] \
   || [ "${N_KM_TYPE:-0}" -lt 1 ] || [ -z "${N_OVERBEGREP// /}" ] \
   || [ "$(printf '%s' "$N_REVISJON" | grep -o 'udir:LK' | wc -l)" -ne 2 ] || [ "${N_TO_REVISJONER:-1}" -ne 0 ] \
   || [ "$(printf '%s' "$N_SKOS" | grep -o 'udir:' | wc -l)" -ne 5 ] || [ "${N_FAGOMR_UTEN_KATEGORI:-1}" -ne 0 ] \
   || [ "${N_SPRAAK_UTEN_EU:-1}" -ne 0 ] || [ "$(printf '%s' "$N_DCTERMS" | grep -o 'dcterms:' | wc -l)" -ne 5 ] \
   || [ "${N_UTEN_BOKMAALTITTEL:-1}" -ne 0 ] || [ "$(printf '%s' "$N_SCHEMA" | grep -o 'schema:' | wc -l)" -ne 2 ] \n   || [ "${N_STYRK:-0}" -lt 1 ] || [ "${N_NUS:-0}" -lt 1 ] || [ "${N_ESCO:-0}" -lt 1 ]; then
  echo "Røyktest feilet (forventet minst $MIN_TRIPLER tripler i $G_GREP, >0 i $G_ONTOLOGI," \
       "minst $MIN_GYLDIGHET udir:Gyldighet og gyldighetsperiode på alle fagkoder i $G_NORM," \
       ">0 u:Kompetansemaal_lk20, overbegreper fra udir.ttl og udir:revisjon for LK06 og LK20" \
       "(ingen ressurs i begge), begreper i alle fem SKOS-begrepssystemene, fagkategori på alle" \
       "fagområder, EU-kobling på alle språk og alle fem Dublin Core-egenskapene i $G_UTLEDET," \
       "udir:bokmaalTittel og udir:nynorskTittel på alle læreplaner og det som hører til dem i $G_NORM," \
       "schema:validFrom og schema:validThrough i $G_UTLEDET, og STYRK-08- og NUS-koblinger og ESCO-yrker i $G_KOBLINGER)"
  exit 1
fi

# 9. Lagre endrings-id sist, slik at en kjøring som feiler, blir forsøkt på nytt neste gang
NAA=$(date -u +%Y-%m-%dT%H:%M:%SZ)
cat > "$ARBEID/meta.nt" <<EOF
<$META> <$SCHEMA/last-id> "$SISTE_ID" .
<$META> <$SCHEMA/lastet> "$NAA"^^<http://www.w3.org/2001/XMLSchema#dateTime> .
<$META> <$SCHEMA/antall-tripler> "$N_GREP"^^<http://www.w3.org/2001/XMLSchema#integer> .
<$META> <$SCHEMA/antall-tripler-normalisert> "$N_NORM"^^<http://www.w3.org/2001/XMLSchema#integer> .
<$META> <$SCHEMA/antall-tripler-utledet> "$N_UTLEDET"^^<http://www.w3.org/2001/XMLSchema#integer> .
EOF
if [ -n "$UDIR_TIDSPUNKT" ]; then
  echo "<$META> <$SCHEMA/endret-hos-udir> \"$UDIR_TIDSPUNKT\"^^<http://www.w3.org/2001/XMLSchema#dateTime> ." >> "$ARBEID/meta.nt"
fi
# DCAT og VoID (idé 6): ontologi/datasett.ttl beskriver datasettet; her kommer det som endrer seg ved hver innlasting
DS="https://grep-fuseki-v3.fly.dev/ds#"
XI="http://www.w3.org/2001/XMLSchema#integer"
VT="http://rdfs.org/ns/void#triples"
{
  echo "<${DS}datasett> <http://purl.org/dc/terms/modified> \"$NAA\"^^<http://www.w3.org/2001/XMLSchema#dateTime> ."
  echo "<${DS}datasett> <$VT> \"$(( N_GREP + N_ONT + N_NORM + N_UTLEDET + N_KOBLINGER ))\"^^<$XI> ."
  echo "<${DS}grep> <$VT> \"$N_GREP\"^^<$XI> ."
  echo "<${DS}ontologi> <$VT> \"$N_ONT\"^^<$XI> ."
  echo "<${DS}normalisert> <$VT> \"$N_NORM\"^^<$XI> ."
  echo "<${DS}utledet> <$VT> \"$N_UTLEDET\"^^<$XI> ."
  echo "<${DS}koblinger> <$VT> \"$N_KOBLINGER\"^^<$XI> ."
} >> "$ARBEID/meta.nt"
last_graf PUT "$G_META" application/n-triples "$ARBEID/meta.nt"
last_graf POST "$G_META" text/turtle "$REPO/ontologi/datasett.ttl"
logg "Avvik i dataene: $N_AVVIK"
if [ -n "$AVVIK_FIL" ]; then cp "$ARBEID/avvik.md" "$AVVIK_FIL"; fi
logg "Ferdig. Oppdatert til endrings-id $SISTE_ID."
