# R4: SKOS-begreper, til urn:graph:utledet
#
# Grep-ressurser av en klasse med udir:begrepssystem (ontologi/udir.ttl) blir SKOS-begreper i det
# begrepssystemet: fagtyper, opplæringsnivåer, fagkategorier og fagområder. Nye verdier i Grep kommer med
# automatisk. Hierarkiet (skos:broader) kommer fra R2 via u:fagkategori rdfs:subPropertyOf skos:broader,
# så denne regelen må kjøres etter 02-egenskaper.ru.
#
# Fem operasjoner: begrep og begrepssystem, navn, kode, skos:narrower og toppbegreper.

PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX u:    <http://psi.udir.no/ontologi/kl06/>
PREFIX udir: <http://psi.udir.no/ontologi/>

# 1. Begrep i begrepssystemet
INSERT { GRAPH <urn:graph:utledet> { ?s a skos:Concept ; skos:inScheme ?ks } }
WHERE {
  SELECT DISTINCT ?s ?ks WHERE {
    GRAPH <urn:graph:ontologi> { ?c udir:begrepssystem ?ks . ?t rdfs:subClassOf* ?c }
    GRAPH <urn:graph:grep> { ?s a ?t }
  }
} ;

# 2. Navn fra u:tittel. Grep bruker ISO 639-2/3-koder (nob, nno, eng, sme ...), SKOS-navnene får de vanlige
#    språkkodene (nb, nn, en, se ...). Tittelen med språket "default" tas ikke med: den er en kopi av en av de andre.
INSERT { GRAPH <urn:graph:utledet> { ?s skos:prefLabel ?navn } }
WHERE {
  SELECT DISTINCT ?s ?navn WHERE {
    VALUES (?fra ?til) { ("nob" "nb") ("nno" "nn") ("eng" "en") ("sme" "se") ("sma" "sma") ("smj" "smj") }
    GRAPH <urn:graph:ontologi> { ?c udir:begrepssystem ?ks . ?t rdfs:subClassOf* ?c }
    GRAPH <urn:graph:grep> { ?s a ?t ; u:tittel ?tittel }
    FILTER(LANG(?tittel) = ?fra)
    BIND(STRLANG(STR(?tittel), ?til) AS ?navn)
  }
} ;

# 3. Koden som skos:notation
INSERT { GRAPH <urn:graph:utledet> { ?s skos:notation ?kode } }
WHERE {
  SELECT DISTINCT ?s ?kode WHERE {
    GRAPH <urn:graph:ontologi> { ?c udir:begrepssystem ?ks . ?t rdfs:subClassOf* ?c }
    GRAPH <urn:graph:grep> { ?s a ?t ; u:kode ?kode }
  }
} ;

# 4. skos:narrower som motsatt retning av skos:broader (fra R2)
INSERT { GRAPH <urn:graph:utledet> { ?over skos:narrower ?under } }
WHERE {
  GRAPH <urn:graph:utledet> { ?under skos:broader ?over . ?under a skos:Concept . ?over a skos:Concept }
} ;

# 5. Toppbegreper: begreper uten overbegrep i samme begrepssystem
INSERT { GRAPH <urn:graph:utledet> { ?s skos:topConceptOf ?ks . ?ks skos:hasTopConcept ?s } }
WHERE {
  GRAPH <urn:graph:utledet> { ?s a skos:Concept ; skos:inScheme ?ks }
  FILTER NOT EXISTS { GRAPH <urn:graph:utledet> { ?s skos:broader ?over . ?over skos:inScheme ?ks } }
}
