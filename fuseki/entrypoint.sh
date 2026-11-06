#!/bin/sh
# Oppstart av Fuseki i Grep-sandkassen.
#  - Lesing (/ds/query, /ds/sparql, /ds/get) er åpen.
#  - Skriving (/ds/update, /ds/data) krever brukeren "admin" med passord fra
#    miljøvariabelen FUSEKI_PASSWORD (Fly-secret). Uten passord starter ikke serveren,
#    slik at vi aldri kjører med åpen eller tom skrivetilgang.
set -eu

: "${FUSEKI_PASSWORD:?FUSEKI_PASSWORD er ikke satt (fly secrets set FUSEKI_PASSWORD=...). Avbryter.}"

mkdir -p /fuseki/databases
cp /opt/fuseki/shiro.ini /fuseki/shiro.ini

# Passordfilen ligger utenfor volumet og lages på nytt ved hver oppstart.
umask 077
printf 'admin: %s\n' "$FUSEKI_PASSWORD" > /opt/fuseki/passwd

exec java $JAVA_OPTIONS -jar /opt/fuseki/fuseki-server.jar \
    --port=3030 \
    --config=/opt/fuseki/config.ttl \
    --passwd=/opt/fuseki/passwd \
    --auth=basic
