# N4: Perioder som datoer (urn:graph:normalisert)
#
# Grep uttrykker tid på to måter:
#   - redaksjonelle datoer, u:gyldig-fra / u:gyldig-til (fagkoder, læreplaner, merknader m.fl.)
#   - semestre, d:semester_vaar_2021 / d:semester_hoest_2021 (fagkoder, programområder, utdanningsprogram)
# Regelen gjør begge om til datoer (xsd:date, uten klokkeslett og tidssone), slik at én og samme
# sammenligning virker overalt:
#
#   udir:gyldigFra / udir:gyldigTil              gyldighet (fra u:gyldig-fra/til, eller fra semestrene for
#                                                 programområder og utdanningsprogram)
#   udir:undervisningFra / udir:undervisningTil  når det gis undervisning i en fagkode
#   udir:eksamenFra / udir:eksamenTil            når man kan ta eksamen i en fagkode
#   udir:startdato / udir:sluttdato              på semestrene: vår 01.01–31.07, høst 01.08–31.12
#
# Fra-datoen er første dag og til-datoen siste dag i perioden. Mangler en ende, betyr det «fra tidenes morgen»
# eller «inntil videre», og da brukes 1970-01-01 og 2100-12-31. De datoene viser at verdien er satt av
# sandkassen, ikke av Udir.
#
# Undervisning og eksamen er egne perioder: en fagkode kan ha begge, bare den ene eller ingen av dem. En periode
# lages bare når minst én av de to semesteregenskapene finnes. Gyldighetsdatoene settes redaksjonelt og kan
# avvike litt fra semestrene; begge beholdes.

PREFIX u:    <http://psi.udir.no/ontologi/kl06/>
PREFIX udir: <http://psi.udir.no/ontologi/>
PREFIX xsd:  <http://www.w3.org/2001/XMLSchema#>

# 1. Start- og sluttdato på semestrene, ut fra koden (semester_vaar_2021, semester_hoest_2021)
INSERT {
  GRAPH <urn:graph:normalisert> { ?sem udir:startdato ?start ; udir:sluttdato ?slutt }
}
WHERE {
  GRAPH <urn:graph:grep> { ?sem a u:semester }
  BIND(REPLACE(STR(?sem), "^.*/", "") AS ?kode)
  FILTER(REGEX(?kode, "^semester_(vaar|hoest)_[0-9]{4}$"))
  BIND(SUBSTR(?kode, STRLEN(?kode) - 3) AS ?aar)
  BIND(CONTAINS(?kode, "_vaar_") AS ?vaar)
  BIND(xsd:date(CONCAT(?aar, IF(?vaar, "-01-01", "-08-01"))) AS ?start)
  BIND(xsd:date(CONCAT(?aar, IF(?vaar, "-07-31", "-12-31"))) AS ?slutt)
} ;

# 2. Perioder fra semestrene: undervisning og eksamen (fagkoder), gyldighet (programområder, utdanningsprogram)
INSERT {
  GRAPH <urn:graph:normalisert> { ?r ?pFra ?fra ; ?pTil ?til }
}
WHERE {
  VALUES (?pFoerste ?pSiste ?pFra ?pTil) {
    (u:naar-gis-det-undervisning-foerste-semester u:naar-gis-det-undervisning-siste-semester
     udir:undervisningFra udir:undervisningTil)
    (u:naar-kan-man-ta-eksamen-foerste-semester u:naar-kan-man-ta-eksamen-siste-semester
     udir:eksamenFra udir:eksamenTil)
    (u:foerste-semester u:siste-semester udir:gyldigFra udir:gyldigTil)
  }
  GRAPH <urn:graph:grep> { { ?r ?pFoerste ?x } UNION { ?r ?pSiste ?x } FILTER(!isBlank(?r)) }
  OPTIONAL { GRAPH <urn:graph:grep> { ?r ?pFoerste ?s1 } GRAPH <urn:graph:normalisert> { ?s1 udir:startdato ?f } }
  OPTIONAL { GRAPH <urn:graph:grep> { ?r ?pSiste ?s2 } GRAPH <urn:graph:normalisert> { ?s2 udir:sluttdato ?t } }
  BIND(COALESCE(?f, "1970-01-01"^^xsd:date) AS ?fra)
  BIND(COALESCE(?t, "2100-12-31"^^xsd:date) AS ?til)
} ;

# 3. Gyldighet fra de redaksjonelle datoene. Alle fagkoder og læreplaner får en periode, også uten datoer
#    (da 1970-01-01–2100-12-31). Andre ressurser får en periode når de har minst én av datoene.
INSERT {
  GRAPH <urn:graph:normalisert> { ?r udir:gyldigFra ?fra ; udir:gyldigTil ?til }
}
WHERE {
  {
    GRAPH <urn:graph:grep> { ?r a ?type VALUES ?type { u:fagkode u:laereplan u:laereplan_lk20 } }
  } UNION {
    GRAPH <urn:graph:grep> { ?r u:gyldig-fra|u:gyldig-til ?x FILTER(!isBlank(?r)) }
  }
  OPTIONAL { GRAPH <urn:graph:grep> { ?r u:gyldig-fra ?f } }
  OPTIONAL { GRAPH <urn:graph:grep> { ?r u:gyldig-til ?t } }
  BIND(IF(BOUND(?f), COALESCE(xsd:date(SUBSTR(STR(?f), 1, 10)), ?f), "1970-01-01"^^xsd:date) AS ?fra)
  BIND(IF(BOUND(?t), COALESCE(xsd:date(SUBSTR(STR(?t), 1, 10)), ?t), "2100-12-31"^^xsd:date) AS ?til)
}
