# N3: Typede datoer og tall, direkte i urn:graph:grep (beslutning B4)
#
# Dumpen har datoer og tall som xsd:string. Hvilke egenskaper som gjøres om, styres av ontologien:
# en egenskap med rdfs:range xsd:dateTime, xsd:integer eller xsd:decimal i urn:graph:ontologi får
# strengverdiene sine gjort om. Listen vedlikeholdes i TYPEDE i scripts/rett_ontologi.py.
#
# Verdiene valideres med regex og en cast. Verdier som ikke passer, beholdes som streng og telles
# av nattlig-innlasting.sh. Regelen rører bare xsd:string-verdier, så den kan kjøres flere ganger.

PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX xsd:  <http://www.w3.org/2001/XMLSchema#>

# Datoer med klokkeslett, for eksempel "2021-06-09T20:07:07.9262317"
DELETE { GRAPH <urn:graph:grep> { ?s ?p ?v } }
INSERT { GRAPH <urn:graph:grep> { ?s ?p ?t } }
WHERE {
  GRAPH <urn:graph:ontologi> { ?p rdfs:range xsd:dateTime }
  GRAPH <urn:graph:grep> { ?s ?p ?v }
  FILTER(DATATYPE(?v) = xsd:string
         && REGEX(?v, "^-?[0-9]{4}-[0-9]{2}-[0-9]{2}T[0-9]{2}:[0-9]{2}:[0-9]{2}([.][0-9]+)?(Z|[+-][0-9]{2}:[0-9]{2})?$"))
  BIND(xsd:dateTime(?v) AS ?t)
  FILTER(BOUND(?t))
} ;

# Heltall, for eksempel "253"
DELETE { GRAPH <urn:graph:grep> { ?s ?p ?v } }
INSERT { GRAPH <urn:graph:grep> { ?s ?p ?t } }
WHERE {
  GRAPH <urn:graph:ontologi> { ?p rdfs:range xsd:integer }
  GRAPH <urn:graph:grep> { ?s ?p ?v }
  FILTER(DATATYPE(?v) = xsd:string && REGEX(?v, "^[+-]?[0-9]+$"))
  BIND(xsd:integer(?v) AS ?t)
  FILTER(BOUND(?t))
} ;

# Desimaltall med komma eller punktum, for eksempel "1,00"
DELETE { GRAPH <urn:graph:grep> { ?s ?p ?v } }
INSERT { GRAPH <urn:graph:grep> { ?s ?p ?t } }
WHERE {
  GRAPH <urn:graph:ontologi> { ?p rdfs:range xsd:decimal }
  GRAPH <urn:graph:grep> { ?s ?p ?v }
  FILTER(DATATYPE(?v) = xsd:string && REGEX(?v, "^[+-]?[0-9]+([.,][0-9]+)?$"))
  BIND(xsd:decimal(REPLACE(?v, ",", ".")) AS ?t)
  FILTER(BOUND(?t))
}
