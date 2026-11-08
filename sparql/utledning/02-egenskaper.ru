# R2: Egenskaper via subegenskaper, til urn:graph:utledet
#
# ?s ?p ?o . ?p rdfs:subPropertyOf+ ?q  gir  ?s ?q ?o
#
# I dag gjelder det u:vurderingsordning-hoeyeste-nivaa-elev og -privatist, som begge gir
# u:hoeyeste-nivaa. En ressurs kan da få to verdier for u:hoeyeste-nivaa, én fra hver.
# Nye rdfs:subPropertyOf i ontologien (for eksempel u:erstatter → dcterms:replaces i fase 4) følger med.
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
