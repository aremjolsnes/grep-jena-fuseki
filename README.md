# Grep SPARQL-sandkasse (Apache Jena Fuseki på Fly.io)

Driftsdokumentasjon. Brukerveiledning for endepunktet ligger i [docs/bruk.md](docs/bruk.md).

En uoffisiell kopi av Grep-dataene (læreplandata fra Udir) i Apache Jena Fuseki, med en Grep-ontologi
lagt ved. Formålet er å eksperimentere med ontologi og kunnskapsgraf uten å røre Udirs produksjonsendepunkt
(`https://sparql-data.udir.no/repositories/201906`, GraphDB).

- **Spørringer:** `https://grep-fuseki-v3.fly.dev/ds/query` (åpent)
- **Nettgrensesnitt:** `https://grep-fuseki-v3.fly.dev/#/dataset/ds/query`
- **Repo:** `github.com/aremjolsnes/grep-jena-fuseki` (offentlig)
- **Videre plan:** [docs/plan-nattlig-normalisering.md](docs/plan-nattlig-normalisering.md)

## Oversikt

```
data.udir.no (nattlig JSON-LD-dump)
        │
        ▼
GitHub Actions: ingest-data.yml ──► scripts/nattlig-innlasting.sh
        │  (riot: JSON-LD → N-Triples, PUT til mellomgraf, MOVE til Fuseki)
        ▼
Fly.io: app grep-fuseki-v3 (Udir-kontoen), region arn
        Fuseki 5.3.0, TDB2 på volumet fuseki_storage_v4 (/fuseki)
        ▲
GitHub Actions: deploy.yml (bygger Dockerfile, flyctl deploy)
```

## Tilgang

| Endepunkt | Tilgang |
|---|---|
| `/ds/query`, `/ds/sparql` (SPARQL-spørringer) | Åpent |
| `/ds/get` (lesing via Graph Store Protocol) | Åpent |
| `/ds/update` (SPARQL Update), `/ds/data` (skriving via Graph Store Protocol) | Brukeren `admin` med passord |
| `/$/...` (administrasjons-API) | Bare fra localhost, altså via `fly ssh console` |
| `/$/ping`, `/$/server` | Åpent |

Oppsettet ligger i [fuseki/config.ttl](fuseki/config.ttl) (endepunkter og `fuseki:allowedUsers`) og
[fuseki/shiro.ini](fuseki/shiro.ini) (administrasjons-API). [fuseki/entrypoint.sh](fuseki/entrypoint.sh)
skriver passordfilen fra miljøvariabelen `FUSEKI_PASSWORD` ved oppstart, og **nekter å starte uten den**.

## Grafer

Datasettet `ds` kjører med `tdb2:unionDefaultGraph true`: spørringer uten `GRAPH`/`FROM` ser unionen av alle
named graphs. Den lagrede default graph er usynlig og skal være tom.

| Graf | Innhold | Kilde |
|---|---|---|
| `urn:graph:grep` | Rådata fra dumpen (omtrent 1,2 millioner tripler). Datoer og tall gjøres om til riktige datatyper (N3, B4), ellers uendret. | Erstattes i sin helhet hver natt (`PUT` til `urn:graph:grep-ny`, så `MOVE`) |
| `urn:graph:ontologi` | `ontologi/ontologi_kl06_rettet.ttl`, `ontologi/grep_type_mapping.ttl` og `ontologi/udir.ttl` | Lastes fra repoet ved hver innlasting |
| `urn:graph:normalisert` | `udir:Gyldighet`-ressurser (N1), perioder som datoer (N4) og tittel per målform (N5), omtrent 328 000 tripler | Tømmes og bygges på nytt av `sparql/normalisering/*.ru` |
| `urn:graph:utledet` | Typer fra ontologien via `rdfs:subClassOf+` (R1), også overbegrepene i `udir.ttl`, revisjon (R3), SKOS-begreper (R4), språk koblet til EUs språktabell (R5) og Dublin Core- og schema.org-egenskaper (R2), omtrent 270 000 tripler | Tømmes og bygges på nytt av `sparql/utledning/*.ru` |
| `urn:graph:koblinger` | `ontologi/koblinger/styrk.ttl`: STYRK-08 som SKOS-begrepssystem (582 grupper, `skos:exactMatch` til ISCO-08 i ESCO) og `udir:yrkesklassifisering` fra 300 programområder. Lages av `scripts/lag-styrk-ttl.py` fra `ontologi/koblinger/styrk.csv`. `ontologi/koblinger/nus.ttl`: NUS-kodene i bruk med grupper (`skos:broadMatch` til ISCED-F 2013 i ESCO og ISCED 2011) og `udir:utdanningsklassifisering` fra 491 programområder. Lages av `scripts/lag-nus-ttl.py` fra `ontologi/koblinger/nus.csv`. `ontologi/koblinger/esco-yrker.ttl`: ESCO-yrkene under ISCO-gruppene, med norsk navn og beskrivelse og ESCOs egne URI-er. Lages av `scripts/lag-esco-ttl.py` fra ESCO-API-et. `ontologi/koblinger/esco-ferdigheter.ttl`: ferdighetene til yrkene (ESCO v1.2.1, rundt 6 500 ferdigheter og 26 000 koblinger, med gruppene over dem). Lages av `scripts/lag-esco-ferdigheter-ttl.py` fra den nedlastede ESCO-klassifikasjonen. `scripts/sjekk-koblinger.py` melder avvik for utgåtte koder og nye programområder | Lastes fra repoet ved hver innlasting |
| `urn:graph:meta` | `last-id` (endrings-id), `lastet` (vårt tidspunkt, UTC), `endret-hos-udir` (Udirs tidspunkt for siste endring, når det finnes), `antall-tripler`, `antall-tripler-normalisert`, `antall-tripler-utledet`, og beskrivelsen av datasettet etter DCAT-AP-NO og VoID (`ontologi/datasett.ttl`, med `dcterms:modified` og `void:triples` per graf) | Skrives sist i hver innlasting |

## Filer

| Fil | Hva |
|---|---|
| `Dockerfile` | Bygger Fuseki 5.3.0 fra Maven Central (fast SHA-512), og kopierer inn `fuseki/` |
| `fuseki/config.ttl`, `fuseki/shiro.ini`, `fuseki/entrypoint.sh` | Fuseki-konfigurasjon og oppstart |
| `fly.toml` | Fly-app: volum, VM (shared-cpu-2x, 4 GB), stopp ved inaktivitet. **Ingen hemmeligheter her.** |
| `scripts/nattlig-innlasting.sh` | Innlastingen, som kan testes lokalt (se under) |
| `scripts/komprimer.sh` | Komprimerer TDB2-databasen i prod via `flyctl ssh` (admin-API-et er bare åpent fra localhost) |
| `scripts/rapporter-avvik.sh` | Gjør avvik i dataene om til en GitHub-issue og et sammendrag for kjøringen |
| `scripts/rett_ontologi.py` | Lager `ontologi_kl06_rettet.ttl` og endringsloggen fra originalen og bruksstatistikk. `TYPEDE` bestemmer hvilke egenskaper N3 gjør om. |
| `sparql/normalisering/*.ru` | Normaliseringsreglene (fase 2), kjøres i alfabetisk rekkefølge: `01-gyldighet` (N1), `02-datatyper` (N3), `03-perioder` (N4), `04-titler` (N5) |
| `sparql/utledning/*.ru` | Utledningsreglene (fase 3), kjøres etter normaliseringen: `01-typer` (R1), `02-egenskaper` (R2), `03-revisjon` (R3), `04-skos` (R4), `05-spraak` (R5) |
| `ontologi/ontologi_kl06_20240523.ttl` | Original Grep-ontologi (klasser med stor forbokstav). Rør ikke. |
| `ontologi/ontologi_kl06_rettet.ttl` (+ `_endringslogg.md`) | Ontologi med rettet domene og rekkevidde. Den som lastes inn. |
| `ontologi/udir.ttl` | `udir:`-laget (fase 4): overbegreper på tvers av revisjonene, reform og revisjon, SKOS-begrepssystemer, språk og språknivå, Dublin Core, gyldighetsvokabularet og titler per målform. Skrives for hånd, stegvis. |
| `ontologi/grep_type_mapping.ttl` | 44 koblinger, f.eks. `u:Kompetansemaal ≡ u:kompetansemaal`, med `owl:equivalentClass` og `rdfs:subClassOf` begge veier |
| `.github/workflows/ingest-data.yml` | Nattlig innlasting, komprimering og keepalive |
| `.github/workflows/komprimer.yml` | Komprimering for hånd |
| `.github/workflows/deploy.yml` | Deploy til Fly |
| `docs/` | Plan og brukerveiledning |

## Nattlig innlasting

- **Når:** `cron: '30 1 * * *'`, det vil si 02:30 vintertid og 03:30 sommertid. Udirs eksport er ferdig omtrent kl. 01:20.
  GitHub starter ofte planlagte jobber 5–30 minutter for sent.
- **Hopper over** når Udirs siste `endrings-id` er lik den i `urn:graph:meta`. Gjelder bare planlagt kjøring.
  Manuell start og `push` laster alltid inn. Svarer endrings-API-et med en tom liste (skjedde 07.11.2026),
  brukes `sha256:` av dump-filen som id, med en gul advarsel i Actions.
- **Starter også ved push** til `ontologi/**`, `sparql/**`, `scripts/nattlig-innlasting.sh` eller `ingest-data.yml`.
- **Rekkefølge:** vekk Fuseki → sammenlign endrings-id → last ned og konverter → `PUT` rådata til den tomme
  mellomgrafen `urn:graph:grep-ny` → `MOVE` til `urn:graph:grep` → last inn ontologi
  → `DROP SILENT DEFAULT` → normalisering (`DROP` av `urn:graph:normalisert`, så `sparql/normalisering/*.ru`)
  → utledning (`DROP` av `urn:graph:utledet`, så `sparql/utledning/*.ru`)
  → røyktest og kontroller → skriv metadata → rapporter avvik → komprimer databasen.
  Metadata skrives sist, så en kjøring som feiler, blir forsøkt på nytt neste natt.
- **Røyktest:** minst 1 000 000 tripler i rådata (`MIN_TRIPLER`), minst 36 000 `udir:Gyldighet` (`MIN_GYLDIGHET`),
  en gyldighetsperiode (`udir:gyldigFra`/`udir:gyldigTil`) på alle fagkoder, minst én utledet
  `u:Kompetansemaal_lk20`, utledede overbegreper fra `udir.ttl` og `udir:revisjon` for både LK06 og LK20,
  uten at noen ressurs har begge, begreper i alle fem SKOS-begrepssystemene, fagkategori på alle fagområder og kobling til EUs
  språktabell på alle språk, alle fem Dublin Core-egenskapene, `udir:bokmaalTittel` og `udir:nynorskTittel` på
  alle læreplaner og det som hører til dem, og `schema:validFrom`/`schema:validThrough`.
- **Avvik i dataene** stopper ikke jobben, men skal ses av et menneske. Kontrollene er datoer med årstall før 1990
  eller etter 2100, gyldighet uten kobling og verdier N3 ikke kunne gjøre om. `nattlig-innlasting.sh` skriver dem
  til `AVVIK_FIL`, og `scripts/rapporter-avvik.sh` lager issuen **«Avvik i Grep-dataene»**. Den tildeles
  repo-eieren, som får varsel. Issuen kommenteres bare når avvikene endrer seg og lukkes når de er borte.
  Avvikene står også i sammendraget for kjøringen i Actions, med en gul advarsel. Avvik rettes i Grep (prod)
  og forsvinner da etter neste innlasting. Test lokalt med `TORRKJORING=1 bash scripts/rapporter-avvik.sh avvik.md`.
- **Hvorfor mellomgraf:** en `PUT` rett til `urn:graph:grep` leser den første bufferen og sletter så den gamle
  grafen før den leser mer. På en nystartet maskin tar det over 30 sekunder, og da bryter Fly-proxyen forbindelsen
  (502, 07.11.2026). `MOVE` er ett kall uten innhold å sende, og én transaksjon. Det prøves ikke på nytt
  automatisk, for et nytt forsøk ville flyttet en tom graf over den riktige.
- **Komprimering:** TDB2 beholder gamle versjoner av dataene, og volumet var fylt til 8,1 av 10 GB etter
  noen måneders innlastinger. Gjeldende data tar rundt 0,7 GB. `scripts/komprimer.sh` kjører
  `/$/compact/ds?deleteOld=true` etter hver innlasting som faktisk lastet noe.
- Tar rundt 30 minutter i prod når noe lastes inn (opplasting ca. 5 min, `MOVE` ca. 15 min, normalisering ca. 5 min,
  komprimering ca. 4 min), og under ett minutt når ingenting er endret. Lokalt tar hele jobben ca. 3 minutter. `concurrency: ingest` hindrer at to innlastinger kjører samtidig.
- **Keepalive:** GitHub slår av planlagte workflows etter 60 dager uten aktivitet i repoet. Det skjedde
  16.05.2026. Jobben `keepalive` lager derfor en tom commit (`[skip ci]`) når siste commit er eldre enn 50 dager.

## Deploy

`deploy.yml` kjører ved push til `main`, men **ikke** når bare `ontologi/`, `scripts/`, `docs/`, `sparql/`,
`ingest-data.yml` eller `*.md` er endret (`paths-ignore`). Den kan også startes manuelt.

**Når deploy og innlasting må skje i rekkefølge**, for eksempel ved endringer i `fuseki/config.ttl` som påvirker
hvor data ligger:

1. Commit med `[skip ci]` i meldingen, slik at ingenting starter automatisk.
2. Actions → **PLAN-E-DEPLOY** → *Run workflow*. Vent til den er grønn.
3. Actions → **Ingest Grep Data** → *Run workflow*.

Meldingen «Name has already been taken» i deploy-loggen er ufarlig. Den kommer fra `flyctl apps create || true`.

## Hemmeligheter

| Hvor | Navn | Merknad |
|---|---|---|
| Fly, app `grep-fuseki-v3` | `FUSEKI_PASSWORD` | Appen ligger på **Udir-kontoen** (are.mjolsnes@udir.no), ikke Gmail-kontoen |
| GitHub, repo → Settings → Secrets and variables → Actions | `FUSEKI_PASSWORD`, `FUSEKI_USER` (= `admin`), `FUSEKI_PROD_URL`, `FLY_API_TOKEN` | Passordet må være likt i Fly og GitHub |

**Bytte passord.** Bruk Git Bash. PowerShell på maskinen kjører i Constrained Language Mode og kan ikke lage
passord med .NET. Kjør én linje om gangen, fra repo-mappen:

```bash
pw=$(openssl rand -base64 48 | tr -dc 'A-Za-z0-9' | head -c 32)
echo ${#pw}                                   # skal gi 32
./flyctl.exe auth whoami                      # skal vise Udir-kontoen
printf 'FUSEKI_PASSWORD=%s\n' "$pw" | ./flyctl.exe secrets import --stage -a grep-fuseki-v3
printf '%s' "$pw" | clip                      # lim inn i GitHub-secreten FUSEKI_PASSWORD
printf ' ' | clip; unset pw
```

Deretter: kjør PLAN-E-DEPLOY (`--stage` gjør at passordet først tas i bruk ved deploy), og så Ingest Grep Data
for å bekrefte.

Merk: eldre passord ligger i git-historikken til `fly.toml`, og repoet er offentlig. De gir ikke tilgang lenger.

## Lokal testing

Docker finnes ikke på maskinen. Test med Java og den samme Fuseki-distribusjonen:

```bash
M=https://repo1.maven.org/maven2/org/apache/jena
curl -sSfO $M/apache-jena-fuseki/5.3.0/apache-jena-fuseki-5.3.0.tar.gz && tar -xzf apache-jena-fuseki-5.3.0.tar.gz
sed 's#"/fuseki/databases"#"'"$PWD"'/testdb"#' fuseki/config.ttl > /tmp/config.ttl
printf 'admin: testpass\n' > /tmp/passwd
java -Xmx2g -jar apache-jena-fuseki-5.3.0/fuseki-server.jar --port=3399 \
     --config=/tmp/config.ttl --passwd=/tmp/passwd --auth=basic &

FUSEKI_URL=http://localhost:3399 FUSEKI_USER=admin FUSEKI_PASSWORD=testpass TVING=1 \
  NT_FIL=grep.nt bash scripts/nattlig-innlasting.sh
```

`NT_FIL` hopper over nedlasting og konvertering. **Fallgruve:** RIOT kjørt som
`java -cp fuseki-server.jar riotcmd.riot` på Windows skriver logglinjer (`… INFO riot :: File: …`) til
standard output, altså rett inn i N-Triples-filen. Rens med
`tr -d '\r' < grep.nt | grep -E '^(<|_:)' > grep-ren.nt`. Det offisielle `riot`-skriptet på GitHub-runneren
har ikke dette problemet.

## Ontologien

- Tre lag (avtalt 06.11.2026): `udir:` (`http://psi.udir.no/ontologi/`) for begreper som ikke er knyttet til
  én revisjon, `u:` med stor forbokstav for Grep-klasser, og `u:` med liten forbokstav for typene i dataene.
  `udir:`-laget ligger i `ontologi/udir.ttl` og bygges stegvis (fase 4). Nye begreper legges direkte i `udir:`,
  som et forslag til Udir (B6). `udir:` brukes bare der det tilfører noe, for eksempel et overbegrep på tvers av
  revisjonene. Klasser som allerede gjelder begge revisjonene, som `u:Fagkode`, får ingen `udir:`-utgave.
- **Domene og rekkevidde** i originalen var skrevet som lister over hvor egenskapen brukes. I RDFS/OWL betyr flere
  domener *snitt*, så resonnering ville gitt feil typer. `scripts/rett_ontologi.py` retter dette. Kjør det på
  nytt hvis dataene endrer seg: `python scripts/rett_ontologi.py`.
- **Datatyper (B4):** `TYPEDE` i `scripts/rett_ontologi.py` setter `rdfs:range` til `xsd:dateTime`, `xsd:integer`
  eller `xsd:decimal`. Regelen `02-datatyper.ru` leser rekkevidden fra `urn:graph:ontologi` og gjør om verdiene.
  Skal en ny egenskap få datatype, legger du den i `TYPEDE` og kjører skriptet. Skriptet henter statistikk bare
  fra `urn:graph:grep`.
- Domene og rekkevidde brukes **ikke** til utledning. Utledningene beregnes hver natt med egne SPARQL-regler
  (fase 3, `sparql/utledning/`): R1 følger `rdfs:subClassOf`, R2 følger `rdfs:subPropertyOf`. Begge følger det
  som står i `urn:graph:ontologi`, så nye klasser og egenskaper i ontologien slår gjennom uten regelendringer.
- **Subegenskaper (regel 6):** `FJERN_SUBEGENSKAP` i `scripts/rett_ontologi.py` fjerner `rdfs:subPropertyOf` som
  gir feil resultat når R2 følger dem. Foreløpig de to ja/nei-egenskapene for høyeste nivå (elev og privatist)
  under `u:hoeyeste-nivaa` (2026-11-08). R2 gir derfor ingen tripler i dag.
- Klassene med stor forbokstav ble valgt fordi mange URI-er med liten forbokstav også brukes som egenskaper,
  f.eks. `u:kompetansemaalsett` og `u:opplaeringsfag`.

## Feilsøking

| Symptom | Årsak og tiltak |
|---|---|
| Data er gamle, ingen nattlige kjøringer | Workflowen er slått av etter 60 dager uten aktivitet. Actions → Ingest Grep Data → *Enable workflow* (krever innlogging på GitHub). |
| Deploy feiler ved nedlasting av Fuseki | Nettverksproblem. Vi bruker Maven Central; `archive.apache.org` har vært utilgjengelig. |
| Innlasting feiler med 502 midt i en `PUT` | Fly-proxyen mistet forbindelsen til maskinen. Se Fuseki-loggen i Grafana (fly.io → Monitoring), og se etter «Broken token» og `[PU02] … Operation timed out`. Skjedde før mellomgrafen ble innført, fordi Fuseki slettet den gamle grafen midt i opplastingen. De gamle dataene står, fordi transaksjonen avbrytes. |
| Volumet fylles opp | Kjør «Komprimer databasen» under Actions. |
| Innlasting feiler med 401 | Passordet er ulikt i Fly og GitHub. Bytt det begge steder (se over). |
| Første spørring tar 5–10 sekunder | Maskinen var stoppet ved inaktivitet (`auto_stop_machines`). Den neste går raskt. |
| Spørringer gir 0 treff etter en endring i konfigurasjonen | Data ligger i lagret default graph, som er usynlig med union. Kjør Ingest Grep Data. |
| `flyctl`: «Could not find App» | Feil konto. `./flyctl.exe auth logout` og logg inn med Udir-kontoen. |

## Løse tråder

- Utdaterte filer i repo-mappen som ikke er i bruk: `ingest.ps1` (laster til default graph), `docker-compose.yml`
  (annet image, ingen konfigurasjon) og `shiro.ini` i roten. Den som brukes, ligger i `fuseki/`.
- `Rapport_Fuseki_Azure*.docx` og `generate_report.py` er ikke committet.
