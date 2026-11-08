# R3: Revisjonstilhørighet, til urn:graph:utledet
#
# ?s a ?t . ?t rdfs:subClassOf* ?c . ?c udir:gjelderRevisjon ?r  gir  ?s udir:revisjon ?r
#
# udir:gjelderRevisjon står på Grep-klassene i ontologi/udir.ttl (for eksempel u:Kompetansemaal_lk20 → udir:LK20).
# Typene i dataene har liten forbokstav, så regelen går via koblingene i ontologien (rdfs:subClassOf*).
# Klasser som gjelder begge revisjonene (fagkode, opplæringsfag, programområde ...) får ingen revisjon.

PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>
PREFIX udir: <http://psi.udir.no/ontologi/>

INSERT { GRAPH <urn:graph:utledet> { ?s udir:revisjon ?r } }
WHERE {
  SELECT DISTINCT ?s ?r WHERE {
    GRAPH <urn:graph:ontologi> { ?c udir:gjelderRevisjon ?r . ?t rdfs:subClassOf* ?c }
    GRAPH <urn:graph:grep> { ?s a ?t }
  }
}
