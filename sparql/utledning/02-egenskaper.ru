# R2: Egenskaper via subegenskaper, til urn:graph:utledet
#
# ?s ?p ?o . ?p rdfs:subPropertyOf+ ?q  gir  ?s ?q ?o
#
# Underegenskapene står i ontologi/udir.ttl: Grep-egenskaper koblet til Dublin Core, SKOS og schema.org
# (for eksempel u:erstatter → dcterms:replaces). Nye rdfs:subPropertyOf i ontologien følger med.
#
# Utledning fra domene og rekkevidde er bevisst ikke med (se docs/plan-nattlig-normalisering.md).

PREFIX rdfs: <http://www.w3.org/2000/01/rdf-schema#>

INSERT { GRAPH <urn:graph:utledet> { ?s ?q ?o } }
WHERE {
  {
    SELECT DISTINCT ?s ?q ?o WHERE {
      GRAPH <urn:graph:ontologi> { ?p rdfs:subPropertyOf+ ?q FILTER(isIRI(?q) && ?q != ?p) }
      VALUES ?kilde { <urn:graph:grep> <urn:graph:normalisert> }
      GRAPH ?kilde { ?s ?p ?o }
    }
  }
  FILTER NOT EXISTS { VALUES ?k { <urn:graph:grep> <urn:graph:normalisert> } GRAPH ?k { ?s ?q ?o } }
}
