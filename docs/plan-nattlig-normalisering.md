# Plan: nattlig normalisering og utledning i Grep-sandkassen

Status 2026-11-06: fase 0 og fase 1 er gjennomført og i drift. Fase 2–4 gjenstår.

## Mål

Etter hver nattlige innlasting av Grep-dumpen skal Fuseki-sandkassen inneholde:

1. **Rådataene** uendret, slik at eksisterende spørringer og eksemplene i Grep-wikien fungerer som før.
2. **Ontologien** (rettet Grep-ontologi, typekoblinger og etter hvert `udir:`-laget).
3. **Normaliserte data** som retter strukturelle svakheter i dumpen: gyldighet som kvalifiserte relasjoner, en kobling fra status til PSI-ressursene og typede datoer.
4. **Utledninger** fra ontologien, beregnet på forhånd, slik at `?s a u:Kompetansemaal` og `?s a udir:Laereplan` gir treff uten resonnering når spørringen kjøres.

Beslutninger som ligger til grunn (tatt 2026-11-06):

- Utledninger beregnes **hver natt** med SPARQL Update-regler som vi skriver selv, ikke med OWL-resonnering når spørringen kjøres.
- Gyldighet modelleres som en **kvalifisert relasjon** (alternativ A).
- Status kobles til PSI-ressursene med en **regel**, ikke med `owl:sameAs`.
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

## Fase 2: Normalisering (`urn:graph:normalisert`)

Reglene ligger som `.ru`-filer i `sparql/normalisering/` og kjøres i nummerert rekkefølge.

### N1: Gyldighet som kvalifisert relasjon

```turtle
d:ADI2001 udir:gyldighet <…/gyldighet/ADI2001/opplaeringsfag/ADI2Z01> .
<…/gyldighet/ADI2001/opplaeringsfag/ADI2Z01>
    a udir:Gyldighet ;
    udir:relasjon u:opplaeringsfag ;
    udir:objekt   d:ADI2Z01 ;
    udir:gyldigFra "…"^^xsd:dateTime ;
    udir:gyldigTil "2021-07-31T00:00:00"^^xsd:dateTime .
```

- Koblingen gjøres med eksakt strengsammenligning: `gyldighet-<lokalnavn(egenskap)>-<siste del av objekt-IRI>`. Testet 2026-11-06: 36 207 av 36 210 treff.
- De tre med prefikset `gyldighet-2-…` (DTDGH2----, HSPOR3---- ×2) logges og hoppes over inntil videre.
- IRI-ene bygges av subjekt, relasjon og objekt. Da er de stabile fra natt til natt og kan refereres direkte.

### N2: Status til PSI

`?s u:status st:publisert` gir `?s udir:status d:status_publisert` (fem verdier). Da kan man gå videre til tittelen og de andre egenskapene til statusressursen.

### N3: Typede datoer og tall

Datoer og tall ligger i dumpen som `xsd:string`. Gjelder blant annet `sist-endret`, `gyldig-fra`, `gyldig-til`, `fastsatt-dato`, `siste-eksamen`, `aarstimer*` og `omfang-*`. Verdiene valideres med regex før de gjøres om. Verdier som ikke passer, beholdes som streng og telles i loggen. Se beslutning B4 for hvor de typede verdiene skal ligge.

## Fase 3: Utledning (`urn:graph:utledet`)

Reglene ligger i `sparql/utledning/`. Siden SPARQL property paths (`+`) gir den transitive lukningen i én spørring, trengs ingen iterasjon.

| Regel | Mønster | Eksempel |
|---|---|---|
| R1 Typer via subklasser | `?s a ?c . ?c rdfs:subClassOf+ ?d` gir `?s a ?d` | `u:kompetansemaal_lk20` → `u:Kompetansemaal_lk20` → `udir:Kompetansemaal` |
| R2 Egenskaper via subegenskaper | `?s ?p ?o . ?p rdfs:subPropertyOf+ ?q` gir `?s ?q ?o` | `u:erstatter` → `dcterms:replaces` |
| R3 Revisjonstilhørighet | `?s a ?c . ?c udir:gjelderRevisjon ?r` gir `?s udir:revisjon ?r` | Alle `kompetansemaal_lk20` får `udir:revisjon udir:LK20` |
| R4 SKOS-koblinger | Verdier med `skos:exactMatch` gjøres tilgjengelige via `udir:`-begrepene | `d:fagtype_fellesfag` → `udir:Fellesfag` |

Bevisst **ikke** med: utledning fra domene og rekkevidde, transitiv `erstatter` og `owl:sameAs`.

Regel R1 kjøres etter fase 2, slik at også `udir:Gyldighet`-nodene får sine typer.

## Fase 4: `udir:`-laget i ontologien

Dette er et eget arbeid som gjøres stegvis i dialog og legges i `ontologi/udir.ttl`. Fasene 1–3 kan bygges og testes uten det, med den rettede ontologien og typekoblingene vi allerede har.

Innhold: overbegreper (gruppe 1), `udir:Reform` og `udir:Revisjon` med individene KL06, LK06 (1) og LK20 (2), SKOS-begrepssystemer (fagtype, opplæringsnivå, fagkategori og fagområde), språkkobling til EUs autoritetstabell, gyldighetsvokabularet (`udir:Gyldighet` med egenskaper) og koblinger til Dublin Core.

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

- **Minne:** den deployede containeren har `-Xmx1g` på en maskin med 4 GB. `INSERT`-regler over 1,2 millioner tripler kan bli tunge. Vi måler N1 og R1 først, og øker eventuelt til `-Xmx2g`/`3g`.
- **Tid:** dagens jobb tar omtrent 2 minutter. Normalisering og utledning legger trolig til noen minutter. Det er godt innenfor grensene til GitHub Actions.
- **Avvik fra prod:** sandkassen er ikke lenger en ren kopi av prod. Rådatagrafen er det fortsatt, så sammenligninger må bruke `GRAPH <urn:graph:grep>`.
- **Den lokale `Dockerfile`-endringen** (offisielt image, `shiro.ini`, `-Xmx2g`) er ikke committet. Vi må avklare om den skal tas med i fase 0 eller forkastes.

## Beslutninger (2026-11-06)

- **B1:** Skrivetilgangen sikres nå, før alt annet. ✅ Gjennomført: `fuseki/config.ttl`, `fuseki/shiro.ini`, `fuseki/entrypoint.sh` og et nytt passord som Fly- og GitHub-secret.
- **B2:** Default graph blir unionen av alle grafer, og rådataene flyttes til `urn:graph:grep`. Rådatagrafen erstattes i sin helhet hver natt med én `PUT` (ingen inkrementell fletting).
- **B3:** Genererte IRI-er får navnerommet `http://psi.udir.no/kl06/gyldighet/…`.
- **B4:** Datoer og tall gjøres om til riktige datatyper direkte i `urn:graph:grep`. Rekkeviddene i `ontologi_kl06_rettet.ttl` må da tilbake til `xsd:dateTime`/`xsd:integer` for de egenskapene som gjøres om.
- **B5:** Den lokale `Dockerfile`-endringen forkastes. Vi bygger videre på den committede versjonen.
