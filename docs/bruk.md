# Grep-data som kunnskapsgraf: SPARQL-sandkasse

Dette er et åpent SPARQL-endepunkt med Grep-dataene (læreplaner, kompetansemål, fag, fagkoder m.m.) fra
Utdanningsdirektoratet, med en ontologi lagt ved. Det er en **eksperimentell sandkasse**, ikke en offisiell
Udir-tjeneste.

> **Til produksjonsbruk** bruker du Udirs offisielle endepunkt `https://sparql-data.udir.no/repositories/201906`
> eller REST-API-et på `https://data.udir.no/kl06/v201906/`. Sandkassen kan endres, være nede eller forsvinne 
> uten varsel.

## Kom i gang

| | |
|---|---|
| **SPARQL-endepunkt** | `https://grep-fuseki-v3.fly.dev/ds/query` |
| **Nettgrensesnitt** | [grep-fuseki-v3.fly.dev/#/dataset/ds/query](https://grep-fuseki-v3.fly.dev/#/dataset/ds/query) |
| **Tilgang** | Åpent for lesing. Ingen innlogging. |
| **Oppdatering** | Hver natt fra Udirs JSON-LD-dump, omtrent kl. 02:30 (03:30 sommertid). Bare når det er endringer. |

Første spørring etter en periode uten bruk kan ta 5–10 sekunder, fordi tjenesten starter opp ved behov.
Spørringene etterpå går raskt.

Fra kommandolinjen:

```bash
curl -H "Accept: application/sparql-results+json" \
     --data-urlencode "query=SELECT * WHERE { ?s ?p ?o } LIMIT 5" \
     https://grep-fuseki-v3.fly.dev/ds/query
```

Endepunktet følger SPARQL 1.1-protokollen, så alle SPARQL-klienter fungerer, for eksempel rdflib, Apache Jena,
SPARQLWrapper og YASGUI. Bruk `Accept: text/csv` hvis du vil ha CSV.

## Prefikser

```sparql
PREFIX u:    <http://psi.udir.no/ontologi/kl06/>   # egenskaper og typer i Grep
PREFIX d:    <http://psi.udir.no/kl06/>            # Grep-ressurser (læreplaner, kompetansemål, ...)
PREFIX udir: <http://psi.udir.no/ontologi/>        # sandkassens egne begreper, se «Normaliserte data»
PREFIX st:   <https://data.udir.no/kl06/v201906/status/status_>   # statusverdier, se «Egenheter»
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl:  <http://www.w3.org/2002/07/owl#>
PREFIX xsd:  <http://www.w3.org/2001/XMLSchema#>
```

Eksemplene under forutsetter disse prefiksene.

## Hvordan dataene er organisert

Dataene ligger i fem navngitte grafer. **Spørringer uten `GRAPH` ser alle samlet**, så de fleste spørringer
trenger ikke å bry seg om grafene.

| Graf | Innhold |
|---|---|
| `urn:graph:grep` | Grep-dataene fra Udir (omtrent 1,2 millioner tripler). Datoer og tall har riktige datatyper, ellers uendret. |
| `urn:graph:ontologi` | Ontologien: klasser, egenskaper og koblinger til typene i dataene |
| `urn:graph:normalisert` | Gyldighet som egne ressurser og perioder som datoer (omtrent 250 000 tripler) |
| `urn:graph:utledet` | Typene fra ontologien, utledet fra typene i dataene (omtrent 50 000 tripler) |
| `urn:graph:meta` | Når dataene sist ble oppdatert |

Vil du ha *bare* Grep-dataene, for eksempel for å sammenligne med Udirs offisielle endepunkt, pakker du
spørringen inn i `GRAPH <urn:graph:grep> { … }`. Det gjelder særlig spørringer som teller eller lister *alt*
(alle tripler, alle typer, alle egenskaper). Uten `GRAPH` er ontologien og de normaliserte og utledede dataene
også med i tallene. For eksempel får hver ressurs to typer, `u:kompetansemaal` og `u:Kompetansemaal`.

**Hvor ferske er dataene?**

```sparql
SELECT ?lastet ?endringsId WHERE {
  GRAPH <urn:graph:meta> {
    ?m <https://grep.udir.no/schema/lastet> ?lastet ;
       <https://grep.udir.no/schema/last-id> ?endringsId
  }
}
```

`endringsId` tilsvarer siste innslag i Udirs endringslogg (`https://data.udir.no/kl06/v201906/endringer`).

## Eksempler

**Hvilke typer finnes, og hvor mange av hver?**

```sparql
SELECT ?type (COUNT(?s) AS ?antall) WHERE {
  GRAPH <urn:graph:grep> { ?s a ?type }
} GROUP BY ?type ORDER BY DESC(?antall)
```

De største er `u:kompetansemaal` (LK06, omtrent 17 000), `u:kompetansemaal_lk20` (omtrent 15 000) og `u:fagkode`.

**Kompetansemålene i en læreplan** (her LK20-læreplanen i norsk, NOR01-07):

```sparql
SELECT ?kode ?tittel WHERE {
  ?km a u:kompetansemaal_lk20 ;
      u:tilhoerer-laereplan d:NOR01-07 ;
      u:kode ?kode ;
      u:tittel ?tittel .
  FILTER(LANG(?tittel) = "default")
} ORDER BY ?kode
```

Titler finnes på flere språk: `default`, `nob`, `nno`, `eng`, `sme`, `sma` og `smj`.
`default` er fastsettelsesspråket.

**Hvilken læreplan erstatter hvilken?**

```sparql
SELECT ?kode ?erstatter ?erstattesAv WHERE {
  ?lp u:kode ?kode .
  FILTER(?kode IN ("NOR1-05", "NOR01-06"))
  OPTIONAL { ?lp u:erstatter ?erstatter }
  OPTIONAL { ?lp u:erstattes-av ?erstattesAv }
}
```

Kjeden går på tvers av reformene: NOR1-04 → NOR1-05 (LK06) → NOR01-06 (LK20) → NOR01-07. «Erstatter» er en
faglig vurdering. Når en plan splittes i flere, eller bare en liten del av innholdet videreføres, finnes det
ikke nødvendigvis en erstatter-kobling.

## Ontologien

Grep-dataene i seg selv har typer og egenskaper, men ingen ontologi som beskriver dem. Sandkassen har en
Grep-ontologi (OWL) med 44 klasser, for eksempel `u:Laereplan`, `u:Laereplan_lk20`, `u:Kompetansemaal` og
`u:Kompetansemaal_lk20`, med norske og engelske navn og beskrivelser.

Klassene i ontologien skrives med **stor forbokstav**. Typene i dataene skrives med **liten**
(`u:kompetansemaal`). Grunnen er at mange av navnene med liten forbokstav også brukes som egenskaper. For
eksempel er `u:kompetansemaalsett` både en type og en egenskap. Ontologien kobler hver klasse til typen i
dataene med `owl:equivalentClass` og `rdfs:subClassOf`.

**Hvilke klasser finnes?**

```sparql
SELECT ?klasse ?navn ?beskrivelse WHERE {
  GRAPH <urn:graph:ontologi> {
    ?klasse a owl:Class ; rdfs:label ?navn .
    FILTER(isIRI(?klasse) && LANG(?navn) = "nb")
    OPTIONAL { ?klasse rdfs:comment ?beskrivelse FILTER(LANG(?beskrivelse) = "nb") }
  }
} ORDER BY ?klasse
```

**Hvilke egenskaper har en LK20-læreplan?**

```sparql
SELECT ?egenskap ?navn WHERE {
  GRAPH <urn:graph:ontologi> {
    ?egenskap rdfs:domain ?d .
    { FILTER(?d = u:Laereplan_lk20) }
    UNION
    { ?d owl:unionOf/rdf:rest*/rdf:first u:Laereplan_lk20 }
    OPTIONAL { ?egenskap rdfs:label ?navn FILTER(LANG(?navn) = "nb") }
  }
} ORDER BY ?egenskap
```

Domene og rekkevidde i ontologien er justert etter hvordan dataene faktisk ser ut. Generelle egenskaper som
`u:tittel`, `u:kode` og `u:status` brukes på nesten alle typer og har derfor ikke noe domene.

**Bruke ontologien i spørringer.** Hver natt utleder sandkassen typene fra ontologien (`urn:graph:utledet`),
så klassene med stor forbokstav kan brukes direkte:

```sparql
SELECT ?klasse (COUNT(?s) AS ?antall) WHERE {
  VALUES ?klasse { u:Kompetansemaal u:Kompetansemaal_lk20 }
  ?s a ?klasse
} GROUP BY ?klasse
```

Sandkassen kjører ikke en resonnerer. Utledningen er egne SPARQL-regler (`sparql/utledning/` i repoet) som
følger `rdfs:subClassOf` og `rdfs:subPropertyOf` i ontologien. Domene og rekkevidde brukes bevisst ikke til å
utlede typer. Hos Udir gir `?s a u:Kompetansemaal` ingen treff.

## Normaliserte data

Hver natt, etter innlastingen, retter sandkassen svakheter i dumpen: gyldighet som egne ressurser,
perioder som datoer, og datoer og tall med riktige datatyper. Reglene ligger som SPARQL Update i
`sparql/normalisering/` i repoet.

**Gyldighet som egne ressurser.** Hver kobling med fra–til-dato får en ressurs av typen `udir:Gyldighet` med
egenskapene `udir:relasjon`, `udir:objekt`, `udir:gyldigFra` og `udir:gyldigTil`. Ressursen henger på subjektet
med `udir:gyldighet`. IRI-en er satt sammen av subjekt, relasjon og objekt, for eksempel
`http://psi.udir.no/kl06/gyldighet/ADI2001/opplaeringsfag/ADI2Z01`, og er den samme fra natt til natt.
Datoene er `xsd:date`, og begge ender er alltid satt (se «Perioder» under om 1970-01-01 og 2100-12-31).

```sparql
SELECT ?fag ?fra ?til WHERE {
  d:ADI2001 udir:gyldighet ?g .
  ?g udir:relasjon u:opplaeringsfag ;
     udir:objekt ?fag ;
     udir:gyldigFra ?fra ;
     udir:gyldigTil ?til .
}
```

Alle koblinger som var gyldige på en bestemt dato:

```sparql
SELECT ?s ?relasjon ?objekt WHERE {
  ?s udir:gyldighet ?g .
  ?g udir:relasjon ?relasjon ; udir:objekt ?objekt ;
     udir:gyldigFra ?fra ; udir:gyldigTil ?til .
  FILTER(?fra <= "2020-08-01"^^xsd:date && ?til >= "2020-08-01"^^xsd:date)
} LIMIT 100
```

En kobling kan ha flere gyldighetsperioder. Periode nummer 2 og videre får nummeret bak IRI-en, for eksempel
`…/gyldighet/DTDGH2----/bygger-paa-programomraade/TPTIP1----/2` (gyldig fra 2023-08-01, etter at den første
perioden sluttet 2022-07-31). I dumpen heter slike egenskaper `u:gyldighet-2-…`.

**Perioder: gyldighet, undervisning og eksamen.** Grep uttrykker tid både med redaksjonelle datoer
(`u:gyldig-fra`/`u:gyldig-til`) og med semestre (`d:semester_hoest_2021`). Sandkassen gjør begge om til datoer
(`xsd:date`), slik at samme sammenligning virker overalt:

| Egenskap | Hvor | Kilde |
|---|---|---|
| `udir:gyldigFra` / `udir:gyldigTil` | fagkoder, læreplaner, merknader m.fl. | `u:gyldig-fra` / `u:gyldig-til` (satt redaksjonelt) |
| `udir:gyldigFra` / `udir:gyldigTil` | programområder, utdanningsprogram | `u:foerste-semester` / `u:siste-semester` |
| `udir:undervisningFra` / `udir:undervisningTil` | fagkoder med undervisning | `u:naar-gis-det-undervisning-…-semester` |
| `udir:eksamenFra` / `udir:eksamenTil` | fagkoder med eksamen | `u:naar-kan-man-ta-eksamen-…-semester` |
| `udir:startdato` / `udir:sluttdato` | semestre | vår 01.01–31.07, høst 01.08–31.12 |

- Fra-datoen er første og til-datoen **siste** dag i perioden. Klokkeslett i Grep-dataene er kuttet bort.
- **1970-01-01 og 2100-12-31** betyr at Grep ikke har satt noen dato i den enden («fra starten» eller
  «inntil videre»). Det er sandkassens egne verdier, ikke Udirs.
- **Undervisning og eksamen er egne perioder.** En fagkode kan ha begge, bare én av dem eller ingen. Har den ikke
  eksamen, har den ingen `udir:eksamenFra`. Spør derfor alltid: undervisning eller eksamen? Gyldighetsdatoene
  settes redaksjonelt og kan avvike litt fra semestrene.
- **Status er noe annet.** `st:publisert` betyr at posten er i bruk i Grep, ikke at den gjelder i dag. En
  fagkode er ofte publisert etter siste undervisningssemester, så lenge man kan ta eksamen.

Fagkoder det gis undervisning i i dag:

```sparql
SELECT ?fk ?fra ?til WHERE {
  BIND(xsd:date(SUBSTR(STR(NOW()), 1, 10)) AS ?idag)
  ?fk udir:undervisningFra ?fra ; udir:undervisningTil ?til .
  FILTER(?fra <= ?idag && ?til >= ?idag)
} ORDER BY ?fk
```

Bytt `undervisning` med `eksamen` eller `gyldig` for de andre periodene. `?idag` lages uten tidssone med vilje:
Grep-datoene har ingen tidssone, og en direkte sammenligning med `NOW()` kan da gi feil svar rundt midnatt.

Kunne man ta eksamen i AGR3001 våren 2026?

```sparql
SELECT ?fra ?til ?kanTaEksamen WHERE {
  d:semester_vaar_2026 udir:startdato ?start ; udir:sluttdato ?slutt .
  d:AGR3001 udir:eksamenFra ?fra ; udir:eksamenTil ?til .
  BIND(?fra <= ?slutt && ?til >= ?start AS ?kanTaEksamen)
}
```

**Datoer og tall med riktige datatyper.** Disse egenskapene er gjort om fra tekst direkte i
`urn:graph:grep`:

| Datatype | Egenskaper |
|---|---|
| `xsd:dateTime` | `u:sist-endret`, `u:gyldig-fra`, `u:gyldig-til`, `u:fastsatt-dato`, `u:siste-eksamen` |
| `xsd:integer` | `u:aarstimer`, `u:aarstimer-doeve-og-tunghoerte`, `u:aarstimer-formgivningsfag`, `u:aarstimer-samisk`, `u:omfang-totalt`, `u:omfang-vitnemaal`, `u:omfang-til-naa` |
| `xsd:decimal` | `u:opplaeringstid`, `u:verdiskapingstid` (desimalkomma i dumpen, «1,00» blir 1.00) |

Datofunksjoner og sammenligninger virker direkte:

```sparql
SELECT ?s ?endret WHERE {
  ?s u:sist-endret ?endret .
  FILTER(?endret >= "2026-01-01T00:00:00"^^xsd:dateTime)
} ORDER BY DESC(?endret) LIMIT 20
```

**Dette fungerer annerledes enn hos Udir.** Sammenligner du med en tekststreng, for eksempel
`FILTER(?d >= "2026-01-01")`, gir det ingen treff her. Bruk en typet verdi som over, eller `STR(?d)`.

### Det som kommer

Under arbeid, og ikke tilgjengelig ennå:

- **Overordnede begreper** som ikke er knyttet til én reform (`udir:Laereplan`, `udir:Kompetansemaal`, …). Da
  kan man spørre etter alle læreplaner på tvers av LK06 og LK20.
- **Reform og revisjon** som egne ressurser: Kunnskapsløftet med revisjonene LK06 og LK20.
- **Utledninger beregnet på forhånd**, slik at `?s a u:Kompetansemaal` fungerer direkte.
- **Koblinger til felles vokabularer**: SKOS-begrepssystemer, EUs språktabell (ISO 639) og Dublin Core.

## Egenheter i dataene

Dette gjelder Grep-dataene generelt, ikke bare sandkassen.

- **Status** peker til REST-API-adresser og ikke til PSI-ressurser. Bruk prefikset `st:`:
  ```sparql
  SELECT ?status (COUNT(*) AS ?antall) WHERE {
    ?lp a u:laereplan_lk20 ; u:status ?status
  } GROUP BY ?status
  ```
  Statusen er `st:publisert` eller `st:utgaatt`. Status sier om posten er i bruk i Grep, ikke om den gjelder
  i dag. Til det brukes periodene under «Normaliserte data».
- **Gyldighet på koblinger** (fra–til-dato for en relasjon) ligger i blanke noder bak genererte egenskaper med
  navn som `u:gyldighet-opplaeringsfag-ADI2Z01`. Se Grep-wikien: [Blanke noder for gyldighetsinformasjon i
  referanseobjekter](https://github.com/Utdanningsdirektoratet/Grep_SPARQL/wiki/Blanke-noder-for-gyldighetsinformasjon-i-referanseobjekter).
  ```sparql
  SELECT ?fag ?gyldigTil WHERE {
    d:ADI2001 u:opplaeringsfag ?fag ; ?g ?b .
    ?b u:gyldig-til ?gyldigTil .
    FILTER(STRSTARTS(STR(?g), CONCAT(STR(u:), "gyldighet-opplaeringsfag-")))
  }
  ```
  Ved listing av alle egenskaper dukker det opp nesten 13 000 slike. Filtrer dem bort med
  `FILTER(!CONTAINS(STR(?p), "gyldighet-"))`. Enklere: bruk `udir:gyldighet` (se «Normaliserte data»).
- **Datoer og tall** (`u:sist-endret`, `u:gyldig-fra`, `u:aarstimer`, …) er tekststrenger i dumpen og hos Udir.
  Her er de gjort om til riktige datatyper (se «Normaliserte data»).

## Mer om Grep og SPARQL

- [Samling av SPARQL-spørringer (Grep-wikien)](https://github.com/Utdanningsdirektoratet/Grep_SPARQL/wiki/Samling-av-SPARQL-sp%C3%B8rringer).
  De fleste fungerer også her, med samme svar. Unntak: spørringer som teller eller lister alt i grafen, gir
  andre tall. Udirs endepunkt (GraphDB) har RDFS-inferens slått på, og her er ontologien med i unionen. Bruk
  `GRAPH <urn:graph:grep>` for å få bare dataene. Spørringen som tvinger `@sme` til `@nob` (xb10g54U), avvises av
  Fuseki fordi den binder samme variabel to ganger.
- [Grep_SPARQL-wikien](https://github.com/Utdanningsdirektoratet/Grep_SPARQL/wiki)
