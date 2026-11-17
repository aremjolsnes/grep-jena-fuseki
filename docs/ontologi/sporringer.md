# Ontologien: bruke den i spørringer

Ontologien er data i samme endepunkt som Grep-dataene. Du kan derfor bruke den på to måter: **spørre i den**
for å finne ut hva som finnes og hva det betyr, og **spørre med den**, slik at spørringene mot dataene blir
kortere, lesbare og uavhengige av revisjon.

Eksemplene forutsetter prefiksene i [brukerveiledningen](../bruk.md#prefikser). SPARQL-workbenchen legger dem
til selv når Sandkassen er valgt.

| Oppskrift | Bruker |
|---|---|
| [Slå opp hva noe betyr](#slå-opp-hva-noe-betyr) | navn og forklaringer |
| [Finne riktig egenskap](#finne-riktig-egenskap) | søk i navn og forklaringer, domene og rekkevidde |
| [Lesbare navn i svaret](#lesbare-navn-i-svaret) | `rdfs:label` koblet på typer og egenskaper |
| [Spørre på tvers av revisjonene](#spørre-på-tvers-av-revisjonene) | overbegrepene og `udir:revisjon` |
| [Bruke kjente vokabularer](#bruke-kjente-vokabularer) | Dublin Core, schema.org og SKOS |
| [Kontrollere dataene mot ontologien](#kontrollere-dataene-mot-ontologien) | domene, rekkevidde og merker |
| [Skrive spørringer som også virker hos Udir](#skrive-spørringer-som-også-virker-hos-udir) | typene med liten forbokstav |

## Hvor ontologien ligger i spørringen

Spørringer uten `GRAPH` ser alle grafene samlet. Ontologien, dataene og det utledede er da i samme graf, og du
kan blande dem fritt. Bruk `GRAPH` når du vil si hvor noe skal hentes fra:

| Vil ha | Skriv |
|---|---|
| Bare definisjonene (klasser, egenskaper, navn) | `GRAPH <urn:graph:ontologi> { … }` |
| Bare Grep-dataene, slik de er hos Udir | `GRAPH <urn:graph:grep> { … }` |
| Bare det som er utledet fra ontologien | `GRAPH <urn:graph:utledet> { … }` |
| Alt samlet | ingen `GRAPH` |

Hvor en trippel kommer fra, ser du ved å spørre etter grafen. Her er typene til ett kompetansemål:

```sparql
SELECT ?graf ?type WHERE {
  GRAPH ?graf { d:KM8644 a ?type }
} ORDER BY ?graf
```

Typen med liten forbokstav står i `urn:graph:grep`. Klassen og overbegrepet står i `urn:graph:utledet`.

## Slå opp hva noe betyr

Alt ontologien sier om en klasse eller egenskap:

```sparql
SELECT ?egenskap ?verdi WHERE {
  GRAPH <urn:graph:ontologi> { u:bygger-paa ?egenskap ?verdi }
}
```

Svaret gir typen, navnene, forklaringene, domenet og rekkevidden. Rekkevidden vises som en navnløs node når
den er en union. `DESCRIBE` tar med innholdet i unionen:

```sparql
DESCRIBE u:bygger-paa
```

Bare navn og forklaring på bokmål, for flere på en gang:

```sparql
SELECT ?term ?navn ?forklaring WHERE {
  VALUES ?term { u:Opplaeringsfag u:Kompetansemaalsett_lk20 u:tilknyttede-kjerneelementer udir:Gyldighet }
  GRAPH <urn:graph:ontologi> {
    ?term rdfs:label ?navn ; rdfs:comment ?forklaring .
    FILTER(LANG(?navn) = "nb" && LANG(?forklaring) = "nb")
  }
}
```

## Finne riktig egenskap

Grep har 172 egenskaper, og navnene er ikke alltid til å gjette. Tre måter å finne den du trenger:

**Søk i navn og forklaringer.** Alt som handler om privatister:

```sparql
SELECT ?term ?navn ?forklaring WHERE {
  GRAPH <urn:graph:ontologi> {
    ?term rdfs:label ?navn ; rdfs:comment ?forklaring .
    FILTER(LANG(?navn) = "nb" && LANG(?forklaring) = "nb")
    FILTER(CONTAINS(LCASE(CONCAT(?navn, " ", ?forklaring)), "privatist"))
  }
} ORDER BY ?term
```

**Spør hva en klasse kan ha.** Egenskapene til en fagkode, med hva de peker på:

```sparql
SELECT ?egenskap ?navn ?rekkevidde WHERE {
  GRAPH <urn:graph:ontologi> {
    ?egenskap rdfs:domain ?d .
    ?d (owl:unionOf/rdf:rest*/rdf:first)? u:Fagkode .
    OPTIONAL { ?egenskap rdfs:label ?navn FILTER(LANG(?navn) = "nb") }
    OPTIONAL {
      ?egenskap rdfs:range ?r .
      ?r (owl:unionOf/rdf:rest*/rdf:first)? ?rekkevidde .
      FILTER(isIRI(?rekkevidde))
    }
  }
} ORDER BY ?egenskap ?rekkevidde
```

Stien `(owl:unionOf/rdf:rest*/rdf:first)?` treffer både en enkelt klasse og klassene i en union. De generelle
egenskapene (`u:tittel`, `u:kode` …) har ikke domene og kommer ikke med.

**Spør hva som peker på en klasse.** Hvem viser til et kjerneelement?

```sparql
SELECT ?fra ?egenskap WHERE {
  GRAPH <urn:graph:ontologi> {
    ?egenskap rdfs:range ?r ; rdfs:domain ?d .
    ?r (owl:unionOf/rdf:rest*/rdf:first)? u:Kjerneelement_lk20 .
    ?d (owl:unionOf/rdf:rest*/rdf:first)? ?fra .
    FILTER(isIRI(?fra))
  }
} ORDER BY ?fra ?egenskap
```

**Se hva dataene faktisk gjør.** Ontologien sier hva som er mulig. Dataene sier hva som er brukt. Egenskapene
som forbinder opplæringsfag og LK20-læreplaner, med navn fra ontologien:

```sparql
SELECT ?egenskap ?navn (COUNT(*) AS ?antall) WHERE {
  GRAPH <urn:graph:grep> {
    ?a a u:opplaeringsfag ; ?egenskap ?b .
    ?b a u:laereplan_lk20 .
  }
  OPTIONAL { GRAPH <urn:graph:ontologi> { ?egenskap rdfs:label ?navn FILTER(LANG(?navn) = "nb") } }
} GROUP BY ?egenskap ?navn ORDER BY DESC(?antall)
```

Bytt de to typene for å finne veien mellom andre klasser.

## Lesbare navn i svaret

Koble på `rdfs:label` fra ontologien, så viser svaret navn og ikke adresser.

**Typene i dataene, med navn:**

```sparql
SELECT ?navn (COUNT(?s) AS ?antall) WHERE {
  GRAPH <urn:graph:grep> { ?s a ?type }
  GRAPH <urn:graph:ontologi> {
    ?klasse owl:equivalentClass ?type ; rdfs:label ?navn .
    FILTER(LANG(?navn) = "nb")
  }
} GROUP BY ?navn ORDER BY DESC(?antall)
```

Typen i dataene har liten forbokstav og ikke noe navn. Navnet står på klassen, og `owl:equivalentClass` er
broen mellom dem.

**En ressurs, forklart.** Alt Grep har om læreplanen i norsk, med egenskapenes navn:

```sparql
SELECT ?navn ?verdi WHERE {
  GRAPH <urn:graph:grep> { d:NOR01-07 ?egenskap ?verdi }
  GRAPH <urn:graph:ontologi> { ?egenskap rdfs:label ?navn FILTER(LANG(?navn) = "nb") }
  FILTER(!isLiteral(?verdi) || LANG(?verdi) IN ("", "default"))
} ORDER BY ?navn
```

Det siste filteret tar med ressurser, verdier uten språk og tekster på fastsettelsesspråket, og hopper over
oversettelsene. Bytt `"nb"` med `"en"` for engelske navn.

## Spørre på tvers av revisjonene

Uten ontologien må du nevne begge utgavene av en type hver gang:

```sparql
SELECT (COUNT(?lp) AS ?antall) WHERE {
  VALUES ?type { u:laereplan u:laereplan_lk20 }
  ?lp a ?type
}
```

Med overbegrepet holder det med én:

```sparql
SELECT (COUNT(?lp) AS ?antall) WHERE { ?lp a udir:Laereplan }
```

Overbegrepene er `udir:Laereplan`, `udir:Kompetansemaal` og `udir:Kompetansemaalsett`. Se
[Overbegreper](klasser-og-egenskaper.md#overbegreper).

**Skille på revisjon.** `udir:revisjon` sier hvilken revisjon en ressurs hører til. Publiserte læreplaner per
revisjon:

```sparql
SELECT ?revisjon (COUNT(?lp) AS ?antall) WHERE {
  ?lp a udir:Laereplan ; udir:revisjon ?r ; u:status st:publisert .
  ?r rdfs:label ?revisjon FILTER(LANG(?revisjon) = "nb")
} GROUP BY ?revisjon
```

**Alt som hører til en revisjon**, uansett klasse:

```sparql
SELECT ?navn (COUNT(?s) AS ?antall) WHERE {
  ?s udir:revisjon udir:LK20 ; a ?klasse .
  GRAPH <urn:graph:ontologi> {
    ?klasse udir:gjelderRevisjon udir:LK20 ; rdfs:label ?navn .
    FILTER(LANG(?navn) = "nb")
  }
} GROUP BY ?navn ORDER BY DESC(?antall)
```

**Søk i begge revisjonene på en gang.** Kompetansemål om kildekritikk, med revisjonen de hører til:

```sparql
SELECT ?revisjon ?kode ?tekst WHERE {
  (?km ?score) text:query (udir:bokmaalTittel "kildekritikk" 20) .
  ?km a udir:Kompetansemaal ; udir:revisjon/skos:notation ?revisjon ;
      u:kode ?kode ; udir:bokmaalTittel ?tekst .
} ORDER BY ?revisjon ?kode
```

**Følge klassehierarkiet selv.** Utledningen er gjort på forhånd, men du kan også gå i hierarkiet når
spørringen kjøres. Alle klasser og typer under et overbegrep:

```sparql
SELECT ?klasse WHERE {
  GRAPH <urn:graph:ontologi> { ?klasse rdfs:subClassOf+ udir:Kompetansemaal }
}
```

## Bruke kjente vokabularer

Noen Grep-egenskaper er underegenskaper av egenskaper i vokabularer som mange verktøy kjenner. Verdiene finnes
da under begge navnene:

| Grep | Kjent vokabular |
|---|---|
| `u:erstatter` / `u:erstattes-av` | `dcterms:replaces` / `dcterms:isReplacedBy` |
| `u:tilhoerer-laereplan` | `dcterms:isPartOf` |
| `u:fastsatt-dato` | `dcterms:dateAccepted` |
| `u:fastsatt-spraak` | `dcterms:language` |
| `udir:gyldigFra` / `udir:gyldigTil` | `schema:validFrom` / `schema:validThrough` |
| `u:fagkategori` | `skos:broader` |

Tabellen står også i ontologien:

```sparql
SELECT ?egenskap ?kjent WHERE {
  GRAPH <urn:graph:ontologi> { ?egenskap rdfs:subPropertyOf ?kjent }
} ORDER BY ?kjent
```

En spørring skrevet bare med Dublin Core, uten ett Grep-navn. Den gir alle læreplanene som læreplanen i norsk
har erstattet, hele kjeden bakover:

```sparql
SELECT ?tidligere WHERE {
  d:NOR01-07 dcterms:replaces+ ?tidligere .
}
```

Kjeden går over revisjonsskillet, fra LK20 (NOR01-06) tilbake til den første LK06-planen (NOR1-01).

Nytten er størst når Grep skal brukes sammen med andre data, eller av et verktøy som ikke kjenner Grep.
Kodelistene som er gjort om til SKOS, står under [Begrepssystemer](begrepssystemer.md).

## Kontrollere dataene mot ontologien

Sandkassen håndhever ikke ontologien. Ingenting stopper en trippel som bryter med den. Til gjengjeld kan du
spørre etter bruddene. Da blir ontologien en kvalitetskontroll av dataene, og dataene en kontroll av
ontologien.

**Egenskaper som brukes i dataene, men mangler i ontologien:**

```sparql
# forventer tomt
SELECT ?egenskap (COUNT(*) AS ?antall) WHERE {
  GRAPH <urn:graph:grep> { ?s ?egenskap ?o }
  FILTER(?egenskap != rdf:type && !CONTAINS(STR(?egenskap), "gyldighet-"))
  FILTER NOT EXISTS { GRAPH <urn:graph:ontologi> { ?egenskap a ?slag } }
} GROUP BY ?egenskap ORDER BY DESC(?antall)
```

Svaret skal være tomt. Kommer det rader, har Grep tatt i bruk en ny egenskap, og den bør legges til i
`ontologi/grep.ttl`. Filteret tar bort de genererte gyldighetsegenskapene, se «Egenheter i dataene» i
[brukerveiledningen](../bruk.md#egenheter-i-dataene).

**Egenskaper som står i ontologien, men ikke brukes:**

```sparql
# forventer tomt
SELECT ?egenskap WHERE {
  GRAPH <urn:graph:ontologi> {
    ?egenskap a ?slag .
    VALUES ?slag { owl:ObjectProperty owl:DatatypeProperty }
  }
  FILTER NOT EXISTS { ?s ?egenskap ?o }
} ORDER BY ?egenskap
```

Også her skal svaret være tomt. En egenskap som ikke lenger brukes, tas ut av ontologien.

**Verdier som bryter med rekkevidden.** For hver objektegenskap med rekkevidde: finnes det verdier av en annen
type?

```sparql
# forventer tomt
SELECT ?egenskap ?typen (COUNT(*) AS ?antall) WHERE {
  GRAPH <urn:graph:ontologi> { ?egenskap a owl:ObjectProperty ; rdfs:range ?r }
  GRAPH <urn:graph:grep> { ?s ?egenskap ?o . ?o a ?typen }
  FILTER NOT EXISTS {
    GRAPH <urn:graph:ontologi> {
      ?typen rdfs:subClassOf ?klasse .
      ?r (owl:unionOf/rdf:rest*/rdf:first)? ?klasse .
    }
  }
} GROUP BY ?egenskap ?typen ORDER BY DESC(?antall)
```

Svaret er tomt, og slik skal det være: rekkevidden følger dataene. Kommer det rader en dag, har Grep
begynt å bruke en egenskap på en ny måte. Bytt `rdfs:range` med `rdfs:domain`, og `?o a ?typen` med
`?s a ?typen`, for å kontrollere domenet på samme måte. Spørringen bruker 10–15 sekunder.

**Ressurser som peker på seg selv** med en egenskap som er merket irrefleksiv:

```sparql
# forventer tomt
SELECT ?egenskap ?s WHERE {
  GRAPH <urn:graph:ontologi> { ?egenskap a owl:IrreflexiveProperty }
  ?s ?egenskap ?s .
}
```

**Ressurser med to revisjoner.** Ingen ressurs skal høre til både LK06 og LK20:

```sparql
# forventer tomt
SELECT ?s WHERE {
  ?s udir:revisjon udir:LK06 , udir:LK20 .
}
```

Mønsteret er det samme i alle kontrollene: hent regelen fra ontologien, og let etter data som bryter den. Den
nattlige innlastingen kjører noen slike kontroller selv og melder avvik. Se
[Drift og oppsett](../../README.md#nattlig-innlasting).

## Skrive spørringer som også virker hos Udir

Ontologien, `udir:`-laget og det utledede finnes bare i sandkassen. Skal en spørring kunne kjøres mot Udirs
endepunkt også, gjelder dette:

| I sandkassen | Hos Udir |
|---|---|
| `?s a u:Kompetansemaal_lk20` (stor forbokstav) | `?s a u:kompetansemaal_lk20` (liten) |
| `?s a udir:Kompetansemaal` | `VALUES ?t { u:kompetansemaal u:kompetansemaal_lk20 } ?s a ?t` |
| `udir:revisjon` | velg typen med eller uten `_lk20` |
| `dcterms:isPartOf`, `dcterms:replaces` … | `u:tilhoerer-laereplan`, `u:erstatter` … |
| `rdfs:label` på klasser og egenskaper | finnes ikke |
| `udir:gyldighet`, `udir:bokmaalTittel` … | se «Egenheter i dataene» i [brukerveiledningen](../bruk.md#egenheter-i-dataene) |

Typene med liten forbokstav og egenskapene i `u:` virker begge steder. En spørring som bare bruker dem, og
som ikke teller alt i grafen, gir samme svar i sandkassen og hos Udir.
