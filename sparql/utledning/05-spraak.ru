# R5: Språk koblet til EUs språktabell, til urn:graph:utledet
#
# ?s a u:spraak ; u:kode ?kode  gir  ?s skos:exactMatch <http://publications.europa.eu/resource/authority/language/KODE>
#
# Grep bruker de samme ISO 639-kodene som EU, med små bokstaver (nob, sme, eng ...). EU-tabellen har dem med
# store. Alle ti språkene i Grep fantes i EU-tabellen 2026-11-08. Nye språk i Grep kommer med automatisk.
# Begrepene selv (skos:Concept i udir:Spraak) kommer fra R4.

PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX u:    <http://psi.udir.no/ontologi/kl06/>

INSERT { GRAPH <urn:graph:utledet> { ?s skos:exactMatch ?eu } }
WHERE {
  GRAPH <urn:graph:grep> { ?s a u:spraak ; u:kode ?kode }
  FILTER(REGEX(STR(?kode), "^[a-z]{3}$"))
  BIND(IRI(CONCAT("http://publications.europa.eu/resource/authority/language/", UCASE(STR(?kode)))) AS ?eu)
}
