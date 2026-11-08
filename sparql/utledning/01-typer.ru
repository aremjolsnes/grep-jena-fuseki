# R1: Typer via subklasser, til urn:graph:utledet
#
# ?s a ?c . ?c rdfs:subClassOf+ ?d  gir  ?s a ?d
#
# I dag gir dette typene med stor forbokstav fra Udirs ontologi (u:kompetansemaal_lk20 i dataene gir
# u:Kompetansemaal_lk20), fordi grep_type_mapping.ttl kobler hvert par begge veier. Når overbegrepene
# i fase 4 (for eksempel udir:Kompetansemaal) kommer inn i urn:graph:ontologi, følger de med uten
# endringer her. Property paths gir hele den transitive lukningen i én spørring, også med sykler.
#
# Leser typer fra rådata og fra normaliseringen (udir:Gyldighet). Typer som allerede står der,
# skrives ikke på nytt. urn:graph:utledet tømmes av nattlig-innlasting.sh før reglene kjøres.

PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

INSERT { GRAPH <urn:graph:utledet> { ?s a ?d } }
WHERE {
  {
    SELECT DISTINCT ?s ?d WHERE {
      VALUES ?kilde { <urn:graph:grep> <urn:graph:normalisert> }
      GRAPH ?kilde { ?s a ?c }
      GRAPH <urn:graph:ontologi> { ?c rdfs:subClassOf+ ?d }
      FILTER(isIRI(?d) && ?d != ?c)
    }
  }
  FILTER NOT EXISTS { VALUES ?k { <urn:graph:grep> <urn:graph:normalisert> } GRAPH ?k { ?s a ?d } }
}
