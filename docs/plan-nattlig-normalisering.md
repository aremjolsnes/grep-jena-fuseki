# Plan: nattlig normalisering og utledning i Grep-sandkassen

Status 2026-11-08: fase 0, 1 og 2 er gjennomført og i drift. I fase 2 er N2 (status) fjernet og N4 (perioder) lagt
til 2026-11-08. I fase 3 er R1 og R2 bygget 2026-11-08. Fase 4 er påbegynt 2026-11-08 (steg 1: overbegreper). R3–R4 og resten
av fase 4 gjenstår.

## Mål

Etter hver nattlige innlasting av Grep-dumpen skal Fuseki-sandkassen inneholde:

1. **Rådataene** uendret, slik at eksisterende spørringer og eksemplene i Grep-wikien fungerer som før.
2. **Ontologien** (rettet Grep-ontologi, typekoblinger og etter hvert `udir:`-laget).
3. **Normaliserte data** som retter strukturelle svakheter i dumpen: gyldighet som kvalifiserte relasjoner, typede datoer og tall, og perioder (gyldighet, undervisning, eksamen) som datoer.
4. **Utledninger** fra ontologien, beregnet på forhånd, slik at `?s a u:Kompetansemaal` og `?s a udir:Laereplan` gir treff uten resonnering når spørringen kjøres.

Beslutninger som ligger til grunn (tatt 2026-11-06):

- Utledninger beregnes **hver natt** med SPARQL Update-regler som vi skriver selv, ikke med OWL-resonnering når spørringen kjøres.
- Gyldighet modelleres som en **kvalifisert relasjon** (alternativ A).
- Status kobles til PSI-ressursene med en **regel**, ikke med `owl:sameAs`. (Regelen, N2, ble fjernet 2026-11-08: status er Grep-teknisk.)
- `rdfs:domain`/`rdfs:range` brukes **ikke** til utledning. De står i ontologien som dokumentasjon.
- `u:erstatter` gjøres **ikke** transitiv.

## Fase 0: Sikre skrivetilgangen ✅ (i drift 2026-11-06)

**Problem:** Den deployede containeren kjører `fuseki-server --update /ds` uten tilgangskontroll. Både `/ds/update` og `/ds/data` (Graph Store Protocol) tar imot skriving anonymt.

**Tiltak:** Kjør Fuseki med en konfigurasjonsfil (`config.ttl`) og `shiro.ini`:

| Endepunkt | Tilgang |
|---|---|
| `/ds/query`, `/ds/sparql` (bare spørringer) | Åpent |
| `/ds/get` (bare lesing via GSP) | Åpent |
| `/ds/update`, `/ds/data` (skriving) | Krever innlogging (`authcBasic`) |
| Roten `/ds` (tar imot alle operasjoner) | Krever innlogging |
| `/$/**` (administrasjon) | Krever innlogging |

Workflowen sender allerede `-u $FUSEKI_USER:$FUSEKI_PASSWORD`, så den trenger ingen endring. Passordet hentes fra Fly-secret og ikke fra `fly.toml`.

**Verifisering:** En anonym `POST` til `/ds/update` og `/ds/data` skal gi 401. Spørringer skal fortsatt fungere uten innlogging.

## Fase 1: Grafstruktur ✅ (i drift 2026-11-06, `scripts/nattlig-innlasting.sh`)

| Graf | Innhold | Hvordan den oppdateres |
|---|---|---|
| `urn:graph:grep` | Rådata fra dumpen | `PUT` (erstattes hver natt) |
| `urn:graph:meta` | Siste `endrings-id` og tidspunkt | Skrives **sist** i jobben |
| `urn:graph:ontologi` | `ontologi_kl06_rettet.ttl`, `grep_type_mapping.ttl` og senere `udir.ttl` | `PUT` fra filene i repoet hver natt |
| `urn:graph:normalisert` | Resultatet av fase 2 | Tømmes og bygges på nytt |
| `urn:graph:utledet` | Resultatet av fase 3 | Tømmes og bygges på nytt |

**Default graph som union av alle grafer** (`tdb2:unionDefaultGraph true`): spørringer uten `GRAPH`/`FROM` ser alt samlet. De som bare vil ha rådata, bruker `GRAPH <urn:graph:grep> { … }`.

Merk: i TDB2 betyr union at default graph er *bare* unionen av named graphs. Den lagrede default graph blir usynlig. Derfor må rådataene flyttes fra default graph til `urn:graph:grep`. Det er den største endringen i den eksisterende workflowen. Steget `DELETE ?default` + `POST` erstattes av én `PUT` til `?graph=urn:graph:grep`, som også gir kortere tid med tomt datasett.

## Fase 2: Normalisering (`urn:graph:normalisert`) ✅ (i drift 2026-11-06)

Reglene ligger som `.ru`-filer i `sparql/normalisering/` og kjøres i nummerert rekkefølge:
`01-gyldighet.ru` (N1), `02-datatyper.ru` (N3) og `03-perioder.ru` (N4). N2 er fjernet (se under).

**Resultat ved lokal test** (rådata fra 2026-11-06, Fuseki 5.3.0, `-Xmx2g`): 36 210 `udir:Gyldighet`,
46 383 `udir:status` og 244 052 tripler i `urn:graph:normalisert`. Alle 118 905 dato- og tallverdier ble gjort
om, og ingen ble stående som streng. Tid: N1 29 s, N2 5 s, N3 33 s. Hele jobben tok 2 min 10 s. En ny kjøring
av N3 endrer ingenting. Anonym `POST` til `/ds/update` gir fortsatt 401.

### N1: Gyldighet som kvalifisert relasjon

```turtle
d:ADI2001 udir:gyldighet <…/gyldighet/ADI2001/opplaeringsfag/ADI2Z01> .
<…/gyldighet/ADI2001/opplaeringsfag/ADI2Z01>
    a udir:Gyldighet ;
    udir:relasjon u:opplaeringsfag ;
    udir:objekt   d:ADI2Z01 ;
    udir:gyldigFra "1970-01-01"^^xsd:date ;
    udir:gyldigTil "2021-07-31"^^xsd:date .
```

- Koblingen gjøres med eksakt strengsammenligning: `gyldighet-<lokalnavn(egenskap)>-<siste del av objekt-IRI>`. Testet 2026-11-06: 36 207 av 36 210 treff.
- De tre med prefikset `gyldighet-2-…` er en **andre gyldighetsperiode** for den samme koblingen, ikke feil. Først ble de hoppet over, men nå tas de med (avgjort 2026-11-06), med `/2` bak IRI-en. Alle 36 210 kommer med.
  - DTDGH2---- → TPTIP1----: 2021-08-01 til 2022-07-31, så igjen fra 2023-08-01. En reell andre periode.
  - HSPOR3---- → HSAMB2---- og → HSHEA2----: to perioder uten opphold (til 2021-07-31 og fra 2021-08-01). Sjekket med fagansvarlig 2026-11-08: «sært, men greit».
- IRI-ene bygges av subjekt, relasjon, objekt og eventuelt periodenummer. Da er de stabile fra natt til natt og kan refereres direkte.
  Kontrollert: alle er unike, og alle subjekter ligger i `http://psi.udir.no/kl06/`.
- Datoene på `udir:Gyldighet` er `xsd:date` (endret 2026-11-08, se N4). Mangler en ende, brukes 1970-01-01 eller
  2100-12-31. Verdier som ikke lar seg gjøre om, beholdes som streng.
- Funn: to koblinger har feil årstall i `gyldig-fra` i dumpen, MAT1106–MAT1Z10 (`0209-08-01`) og
  PSP6092–PSP1Z04 (`2626-01-01`). Feilen står på begge sider av koblingen, altså fire verdier. Rettet i prod
  2026-11-06, og rettelsen kommer med i dumpen natt til 2026-11-07.
- Avvik i dataene (urimelige årstall, gyldighet uten kobling, verdier med feil format) rapporteres i issuen
  «Avvik i Grep-dataene» via `scripts/rapporter-avvik.sh`. Se README-filen.

### N2: Status til PSI ❌ (fjernet 2026-11-08)

N2 ga `?s udir:status d:status_publisert`. Fjernet fordi status er et Grep-teknisk begrep (hvor posten er i det
redaksjonelle løpet), ikke et begrep fra fagområdet, og fordi brukerne allerede har det innarbeidede mønsteret
`PREFIX st: <https://data.udir.no/kl06/v201906/status/status_>` med `?s u:status st:publisert`. Bare
`st:publisert` og `st:utgaatt` er i bruk.

**Prinsipp for `udir:`:** bare begreper fra fagområdet (gyldighet, revisjon, fagtype, kompetansemål …).
Grep-tekniske ting blir i Greps eget vokabular. Status kan eventuelt tas inn i fase 4 som et SKOS-begrepssystem
og `adms:status`.

### N3: Typede datoer og tall

Datoer og tall ligger i dumpen som `xsd:string`. Gjelder blant annet `sist-endret`, `gyldig-fra`, `gyldig-til`, `fastsatt-dato`, `siste-eksamen`, `aarstimer*` og `omfang-*`. Verdiene valideres med regex før de gjøres om. Verdier som ikke passer, beholdes som streng og telles i loggen. Se beslutning B4 for hvor de typede verdiene skal ligge.

Gjennomføring:

- Ontologien styrer hvilke egenskaper som gjøres om. `TYPEDE` i `scripts/rett_ontologi.py` setter `rdfs:range`, og `02-datatyper.ru` gjør om strengverdiene til egenskaper med rekkevidde `xsd:dateTime`, `xsd:integer` eller `xsd:decimal` i `urn:graph:ontologi`. Listen finnes bare ett sted.
- 14 egenskaper: fem datoer, sju heltall og to desimaltall (`opplaeringstid` og `verdiskapingstid`, som har desimalkomma i dumpen, «1,00»).
- `u:omfang-vitnemaal` manglet i originalontologien, der den heter `u:omfang-vitnemål`. Skriptet legger den til.
- Kartlagt 2026-11-06: ingen andre strengegenskaper har verdier som ligner datoer eller tall. Sannhetsverdier er allerede `xsd:boolean` i dumpen.
- Konsekvens av B4: spørringer som sammenligner med en tekststreng, for eksempel `FILTER(?d >= "2026-01-01")`, gir ingen treff her, men gjør det hos Udir. Dette står i `docs/bruk.md`.

### N4: Perioder som datoer ✅ (lagt til 2026-11-08)

Grep uttrykker tid både med redaksjonelle datoer (`u:gyldig-fra`/`u:gyldig-til`) og med semestre. N4 gjør begge
om til `xsd:date` i `urn:graph:normalisert`:

| Egenskap | Hvor | Kilde |
|---|---|---|
| `udir:gyldigFra` / `udir:gyldigTil` | fagkoder, læreplaner (alle), andre ressurser med datoer | `u:gyldig-fra` / `u:gyldig-til` |
| `udir:gyldigFra` / `udir:gyldigTil` | programområder (497), utdanningsprogram (18) | `u:foerste-semester` / `u:siste-semester` |
| `udir:undervisningFra` / `udir:undervisningTil` | fagkoder med undervisning (4 483) | `u:naar-gis-det-undervisning-…-semester` |
| `udir:eksamenFra` / `udir:eksamenTil` | fagkoder med eksamen (4 474) | `u:naar-kan-man-ta-eksamen-…-semester` |
| `udir:startdato` / `udir:sluttdato` | semestre (49) | koden: vår 01.01–31.07, høst 01.08–31.12 |

Beslutninger sammen med fagansvarlig 2026-11-08:

- **Åpne ender:** ett par overalt, `1970-01-01` og `2100-12-31`, slik at det synes hva sandkassen har satt og
  hva Udir har satt. Gjelder også N1. Avvikskontrollen for årstall unntar disse to.
- **Undervisning og eksamen hver for seg.** Fagkoder kan ha begge (2 702), bare eksamen (1 772), bare
  undervisning (1 781) eller ingen (365). En periode lages bare når minst én av de to semesteregenskapene finnes.
- **De 365 uten semestre** er stort sett privatskolekoder (se `u:merkelapper`) og noen `uspesifisert_programfag`.
  De får bare gyldighet 1970-01-01–2100-12-31.
- **Gyldighetsdatoene settes redaksjonelt** og kan avvike litt fra semestrene. Begge beholdes, og det er ingen
  avvikskontroll på sammenhengen.
- **`xsd:date`, ikke `xsd:dateTime`.** Grep-datoene har ingen tidssone, men `NOW()` har det. Sammenligning av
  verdier med og uten tidssone er ubestemt i XSD når de ligger under 14 timer fra hverandre, og Fuseki gir da
  feil. Mønsteret er `BIND(xsd:date(SUBSTR(STR(NOW()), 1, 10)) AS ?idag)`. Klokkeslett i Grep-datoene (40 av
  64 000, for eksempel `T02:00:00`) er redaksjonell støy og kuttes bort.

**Resultat ved lokal test** (rådata fra 2026-11-06): N4 tok 9 s. 107 112 datoer, alle `xsd:date`, ingen ressurs
med to verdier for samme egenskap. Til-datoen er siste gyldige dag (testet: AGR3001 eksamen til 2026-07-31 gir
ja 31.07 og nei 01.08). I dag: 3 275 fagkoder gyldige, 2 344 med undervisning, 1 855 med eksamen.

## Fase 3: Utledning (`urn:graph:utledet`)

Reglene ligger i `sparql/utledning/`. Siden SPARQL property paths (`+`) gir den transitive lukningen i én spørring, trengs ingen iterasjon.

| Regel | Mønster | Eksempel |
|---|---|---|
| R1 Typer via subklasser ✅ | `?s a ?c . ?c rdfs:subClassOf+ ?d` gir `?s a ?d` | `u:kompetansemaal_lk20` → `u:Kompetansemaal_lk20` → `udir:Kompetansemaal` |
| R2 Egenskaper via subegenskaper ✅ | `?s ?p ?o . ?p rdfs:subPropertyOf+ ?q` gir `?s ?q ?o` | `u:erstatter` → `dcterms:replaces` |
| R3 Revisjonstilhørighet | `?s a ?c . ?c udir:gjelderRevisjon ?r` gir `?s udir:revisjon ?r` | Alle `kompetansemaal_lk20` får `udir:revisjon udir:LK20` |
| R4 SKOS-koblinger | Verdier med `skos:exactMatch` gjøres tilgjengelige via `udir:`-begrepene | `d:fagtype_fellesfag` → `udir:Fellesfag` |

Bevisst **ikke** med: utledning fra domene og rekkevidde, transitiv `erstatter` og `owl:sameAs`.

Regel R1 kjøres etter fase 2, slik at også `udir:Gyldighet`-nodene får sine typer.

### R1 og R2 ✅ (bygget 2026-11-08)

`sparql/utledning/01-typer.ru` og `02-egenskaper.ru`. Begge leser fra `urn:graph:grep` og `urn:graph:normalisert`
og skriver bare tripler som ikke står der fra før.

- **R1 i dag:** ontologien har ennå ikke noe hierarki. De 88 `rdfs:subClassOf` er 44 par begge veier mellom
  typene i dataene og klassene i ontologien (`u:kompetansemaal ⇄ u:Kompetansemaal`). R1 gir derfor hver ressurs
  klassen med stor forbokstav: 49 642 tripler, for eksempel 17 021 `u:Kompetansemaal` og 15 189
  `u:Kompetansemaal_lk20`. Syklene håndteres av `+` og `FILTER(?d != ?c)`. Overbegrepene fra fase 4
  (`udir:Kompetansemaal` osv.) følger med uten regelendringer.
- **R2 i dag: ingen tripler.** Originalen har bare to subegenskaper, `u:vurderingsordning-hoeyeste-nivaa-elev`
  og `-privatist` under `u:hoeyeste-nivaa`. Alle tre er ja/nei-verdier, og 606 fagkoder (for eksempel DAN2011)
  har forskjellig verdi for elev og privatist. Sammenslått ville de fått `u:hoeyeste-nivaa` både `true` og
  `false`. Fjernet i den rettede ontologien etter avtale med fagansvarlig 2026-11-08 (regel 6,
  `FJERN_SUBEGENSKAP` i `scripts/rett_ontologi.py`). R2 blir stående som generell regel for fase 4
  (`u:erstatter` → `dcterms:replaces`).
- **Røyktest:** minst én utledet `u:Kompetansemaal_lk20`.
- **Lokal test** (rådata fra 2026-11-06): R1 7–9 s, R2 1–2 s. Prod-kjøringen 2026-11-08 brukte omtrent like lang
  tid som lokalt på normaliseringen, så utledningen bør legge til under et halvt minutt.

## Fase 4: `udir:`-laget i ontologien

Dette er et eget arbeid som gjøres stegvis i dialog og legges i `ontologi/udir.ttl`. Fasene 1–3 kan bygges og testes uten det, med den rettede ontologien og typekoblingene vi allerede har.

Innhold: overbegreper (gruppe 1) ✅, `udir:Reform` og `udir:Revisjon` med individene KL06, LK06 (1) og LK20 (2), SKOS-begrepssystemer (fagtype, opplæringsnivå, fagkategori og fagområde), språkkobling til EUs autoritetstabell, gyldighetsvokabularet (`udir:Gyldighet` med egenskaper) og koblinger til Dublin Core.

### Steg 1: overbegreper ✅ (2026-11-08)

Avklart med fagansvarlig:

- **Tre overbegreper:** `udir:Laereplan`, `udir:Kompetansemaal` og `udir:Kompetansemaalsett`. Læreplan,
  kompetansemål og kompetansemålsett er samme begrep i LK06 og LK20, i hver sin utgave. Begge Grep-klassene kobles
  til overbegrepet med `rdfs:subClassOf`, og R1 gir typene uten regelendringer: 1 109 læreplaner, 32 210
  kompetansemål og 2 517 kompetansemålsett. `urn:graph:utledet` vokser fra 49 642 til 85 478 tripler.
- **Hovedområde (LK06) og kjerneelement (LK20) holdes adskilt.** De ligner, men en mapping mellom dem ville blitt en
  redaksjonell utfordring. `udir.ttl` sier `owl:disjointWith` (ingenting er begge deler) og `rdfs:seeAlso` med en
  forklaring, uten at noe utledes.
- **Ingen `udir:`-utgave av klasser som allerede gjelder begge reformene** (`u:Fagkode`, `u:Opplaeringsfag`,
  `u:Programomraade` osv.). `udir:` brukes bare der det tilfører noe.
- Navn og forklaringer på bokmål, nynorsk og engelsk.
- Røyktest: overbegrepene skal ha utledede typer.

## Den nattlige jobben, ny rekkefølge

1. Sjekk `endrings-id` (som i dag). Hopp over hvis ingenting er endret. Unntak: manuell kjøring, eller endringer i `ontologi/` eller `sparql/`.
2. Last ned dumpen og konverter til N-Triples (som i dag).
3. `PUT` rådata til `urn:graph:grep`.
4. `PUT` ontologifilene til `urn:graph:ontologi`.
5. Kjør `sparql/normalisering/*.ru`.
6. Kjør `sparql/utledning/*.ru`.
7. Røyktest: tellinger per graf, og et par kontrollspørringer (for eksempel at antall `udir:Gyldighet` er over 36 000). Jobben feiler hvis noe er tomt.
8. Skriv `endrings-id` til `urn:graph:meta`. Dette skjer sist, så en kjøring som feiler, blir forsøkt på nytt neste natt.

**Endringer i ontologi og regler skal slå gjennom uten å vente på Udir.** Workflowen bør i tillegg kunne startes av `push` til `ontologi/**` og `sparql/**`. Samtidig får `deploy.yml` `paths-ignore` for de samme stiene og `docs/**`, slik at vi slipper `[skip ci]` for slike endringer.

## Risiko

- **Minne:** containeren kjører med `-Xmx2g` på en maskin med 4 GB. Fase 2 og R1–R2 gikk fint med `-Xmx2g` lokalt.
- **Tid:** dagens jobb tar omtrent 2 minutter. Normalisering og utledning legger trolig til noen minutter. Det er godt innenfor grensene til GitHub Actions.
- **Avvik fra prod:** sandkassen er ikke lenger en ren kopi av prod. Rådatagrafen er det fortsatt, så sammenligninger må bruke `GRAPH <urn:graph:grep>`.
- **Den lokale `Dockerfile`-endringen** (offisielt image, `shiro.ini`, `-Xmx2g`) er ikke committet. Vi må avklare om den skal tas med i fase 0 eller forkastes.

## Beslutninger (2026-11-06)

- **B1:** Skrivetilgangen sikres nå, før alt annet. ✅ Gjennomført: `fuseki/config.ttl`, `fuseki/shiro.ini`, `fuseki/entrypoint.sh` og et nytt passord som Fly- og GitHub-secret.
- **B2:** Default graph blir unionen av alle grafer, og rådataene flyttes til `urn:graph:grep`. Rådatagrafen erstattes i sin helhet hver natt med én `PUT` (ingen inkrementell fletting).
- **B3:** Genererte IRI-er får navnerommet `http://psi.udir.no/kl06/gyldighet/…`.
- **B4:** Datoer og tall gjøres om til riktige datatyper direkte i `urn:graph:grep`. Rekkeviddene i `ontologi_kl06_rettet.ttl` må da tilbake til `xsd:dateTime`/`xsd:integer` for de egenskapene som gjøres om.
- **B5:** Den lokale `Dockerfile`-endringen forkastes. Vi bygger videre på den committede versjonen.
- **B6 (2026-11-08):** Nye begreper legges direkte i `udir:` (`http://psi.udir.no/ontologi/`), ikke i et eget
  navnerom for sandkassen. De er et forslag til Udir, og de brukes bare i sandkassen. Navnerommet viser hvor
  begrepet hører hjemme: `udir:` er fagområdet uavhengig av reform, og `u:` er Greps eget vokabular (se
  prinsippet under N2). Gjelder også `ontologi/udir.ttl` i fase 4.
