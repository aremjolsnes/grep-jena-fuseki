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
PREFIX st:   <https://data.udir.no/kl06/v201906/status/status_>   # statusverdier, se «Egenheter»
PREFIX rdf:  <http://www.w3.org/1999/02/22-rdf-syntax-ns#>
PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX owl:  <http://www.w3.org/2002/07/owl#>
```

Eksemplene under forutsetter disse prefiksene.

## Hvordan dataene er organisert

Dataene ligger i tre navngitte grafer. **Spørringer uten `GRAPH` ser alle samlet**, så de fleste spørringer
trenger ikke å bry seg om grafene.

| Graf | Innhold |
|---|---|
| `urn:graph:grep` | Grep-dataene, slik de kommer fra Udir (omtrent 1,2 millioner tripler) |
| `urn:graph:ontologi` | Ontologien: klasser, egenskaper og koblinger til typene i dataene |
| `urn:graph:meta` | Når dataene sist ble oppdatert |

Vil du ha *bare* Grep-dataene, for eksempel for å sammenligne med Udirs offisielle endepunkt, pakker du
spørringen inn i `GRAPH <urn:graph:grep> { … }`. Det gjelder særlig spørringer som teller eller lister *alt*
(alle tripler, alle typer, alle egenskaper). Uten `GRAPH` er ontologien også med i tallene.

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

**Bruke ontologien i spørringer.** Sandkassen kjører ikke resonnering ennå, så `?s a u:Kompetansemaal` gir
ingen treff. Gå via koblingen i stedet:

```sparql
SELECT ?klasse (COUNT(?s) AS ?antall) WHERE {
  VALUES ?klasse { u:Kompetansemaal u:Kompetansemaal_lk20 }
  ?type rdfs:subClassOf ?klasse .
  ?s a ?type
} GROUP BY ?klasse
```

### Det som kommer

Under arbeid, og ikke tilgjengelig ennå:

- **Overordnede begreper** som ikke er knyttet til én reform (`udir:Laereplan`, `udir:Kompetansemaal`, …). Da
  kan man spørre etter alle læreplaner på tvers av LK06 og LK20.
- **Reform og revisjon** som egne ressurser: Kunnskapsløftet med revisjonene LK06 og LK20.
- **Utledninger beregnet på forhånd**, slik at `?s a u:Kompetansemaal` fungerer direkte.
- **Gyldighet** modellert som egne ressurser (se «Egenheter»), og datoer og tall med riktige datatyper.
- **Koblinger til felles vokabularer**: SKOS-begrepssystemer, EUs språktabell (ISO 639) og Dublin Core.

## Egenheter i dataene

Dette gjelder Grep-dataene generelt, ikke bare sandkassen.

- **Status** peker til REST-API-adresser og ikke til PSI-ressurser. Bruk prefikset `st:`:
  ```sparql
  SELECT ?status (COUNT(*) AS ?antall) WHERE {
    ?lp a u:laereplan_lk20 ; u:status ?status
  } GROUP BY ?status
  ```
  Statusen er for eksempel `st:publisert` eller `st:utgaatt`.
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
  `FILTER(!CONTAINS(STR(?p), "gyldighet-"))`.
- **Datoer og tall** (`u:sist-endret`, `u:gyldig-fra`, `u:aarstimer`, …) er foreløpig tekststrenger. Sortering
  fungerer fordi datoene har ISO-format, men datofunksjoner krever omgjøring, for eksempel
  `xsd:dateTime(?d)`.

## Mer om Grep og SPARQL

- [Samling av SPARQL-spørringer (Grep-wikien)](https://github.com/Utdanningsdirektoratet/Grep_SPARQL/wiki/Samling-av-SPARQL-sp%C3%B8rringer).
  De fleste fungerer også her, med samme svar. Unntak: spørringer som teller eller lister alt i grafen, gir
  andre tall. Udirs endepunkt (GraphDB) har RDFS-inferens slått på, og her er ontologien med i unionen. Bruk
  `GRAPH <urn:graph:grep>` for å få bare dataene. Spørringen som tvinger `@sme` til `@nob` (xb10g54U), avvises av
  Fuseki fordi den binder samme variabel to ganger.
- [Grep_SPARQL-wikien](https://github.com/Utdanningsdirektoratet/Grep_SPARQL/wiki)
