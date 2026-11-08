# N1: Gyldighet som kvalifisert relasjon (urn:graph:normalisert)
#
# Dumpen har gyldighet for en kobling som en blank node bak en generert egenskap:
#   d:ADI2001 u:opplaeringsfag d:ADI2Z01 ;
#             u:gyldighet-opplaeringsfag-ADI2Z01 [ u:gyldig-til "2021-07-31T00:00:00" ] .
# Regelen lager én navngitt ressurs per kobling:
#   d:ADI2001 udir:gyldighet <http://psi.udir.no/kl06/gyldighet/ADI2001/opplaeringsfag/ADI2Z01> .
#   <…/gyldighet/ADI2001/opplaeringsfag/ADI2Z01> a udir:Gyldighet ;
#       udir:relasjon u:opplaeringsfag ; udir:objekt d:ADI2Z01 ;
#       udir:gyldigFra "1970-01-01"^^xsd:date ; udir:gyldigTil "2021-07-31"^^xsd:date .
#
# Koblingen finnes med eksakt sammenligning:
#   gyldighet-<lokalnavn(egenskap)>-<siste del av objekt-IRI>
# En kobling kan ha flere gyldighetsperioder. Periode nummer 2 og videre heter i dumpen
#   gyldighet-<N>-<lokalnavn(egenskap)>-<siste del av objekt-IRI>
# og får /<N> bak IRI-en, for eksempel <…/gyldighet/DTDGH2----/bygger-paa-programomraade/TPTIP1----/2>.
# IRI-ene (B3) bygges av subjekt, relasjon, objekt og eventuelt periodenummer, og er stabile fra natt til natt.
# Egenskaper som ikke matcher noen kobling, hoppes over og rapporteres av nattlig-innlasting.sh.
# Datoene lagres som xsd:date uten klokkeslett og tidssone. Klokkeslettet i dumpen er redaksjonelt støy
# (for eksempel T02:00:00); det er datoen som gjelder, og til-datoen er siste gyldige dag. Mangler en ende,
# brukes 1970-01-01 eller 2100-12-31, slik at det synes at datoen er satt av sandkassen og ikke av Udir.
# Datoer som ikke lar seg gjøre om, beholdes som streng og fanges av avvikskontrollen.

PREFIX u:    <http://psi.udir.no/ontologi/kl06/>
PREFIX udir: <http://psi.udir.no/ontologi/>
PREFIX xsd:  <http://www.w3.org/2001/XMLSchema#>

INSERT {
  GRAPH <urn:graph:normalisert> {
    ?s udir:gyldighet ?g .
    ?g a udir:Gyldighet ;
       udir:relasjon ?p ;
       udir:objekt ?o ;
       udir:gyldigFra ?fra ;
       udir:gyldigTil ?til .
  }
}
WHERE {
  GRAPH <urn:graph:grep> {
    ?s ?gp ?b .
    FILTER(STRSTARTS(STR(?gp), "http://psi.udir.no/ontologi/kl06/gyldighet-"))
    # "2-bygger-paa-programomraade-TPTIP1----" gir ?nr "2" og ?nokkel "bygger-paa-programomraade-TPTIP1----"
    BIND(STRAFTER(STR(?gp), "http://psi.udir.no/ontologi/kl06/gyldighet-") AS ?rest)
    BIND(IF(REGEX(?rest, "^[0-9]+-"), STRBEFORE(?rest, "-"), "") AS ?nr)
    BIND(IF(?nr = "", ?rest, STRAFTER(?rest, "-")) AS ?nokkel)
    ?s ?p ?o .
    FILTER(isIRI(?o) && STRSTARTS(STR(?p), "http://psi.udir.no/ontologi/kl06/"))
    BIND(STRAFTER(STR(?p), "http://psi.udir.no/ontologi/kl06/") AS ?rel)
    BIND(REPLACE(STR(?o), "^.*/", "") AS ?objekt)
    FILTER(?nokkel = CONCAT(?rel, "-", ?objekt))
    OPTIONAL { ?b u:gyldig-fra ?fraTekst }
    OPTIONAL { ?b u:gyldig-til ?tilTekst }
  }
  BIND(IF(BOUND(?fraTekst), COALESCE(xsd:date(SUBSTR(STR(?fraTekst), 1, 10)), ?fraTekst), "1970-01-01"^^xsd:date) AS ?fra)
  BIND(IF(BOUND(?tilTekst), COALESCE(xsd:date(SUBSTR(STR(?tilTekst), 1, 10)), ?tilTekst), "2100-12-31"^^xsd:date) AS ?til)
  BIND(IRI(CONCAT("http://psi.udir.no/kl06/gyldighet/", REPLACE(STR(?s), "^.*/", ""), "/", ?rel, "/", ?objekt,
                  IF(?nr = "", "", CONCAT("/", ?nr)))) AS ?g)
}
