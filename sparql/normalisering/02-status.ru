# N2: Status til PSI-ressursen (urn:graph:normalisert)
#
# I dumpen peker u:status til REST-adressen, for eksempel
#   <https://data.udir.no/kl06/v201906/status/status_publisert>.
# Statusressursen d:status_publisert har den samme adressen i u:url-data. Regelen kobler via den:
#   ?s u:status <https://…/status_publisert>  gir  ?s udir:status d:status_publisert
# Ingen owl:sameAs: REST-adressen og PSI-ressursen holdes fra hverandre.

PREFIX u:    <http://psi.udir.no/ontologi/kl06/>
PREFIX udir: <http://psi.udir.no/ontologi/>

INSERT {
  GRAPH <urn:graph:normalisert> { ?s udir:status ?status }
}
WHERE {
  GRAPH <urn:graph:grep> {
    ?status a u:status ;
            u:url-data ?adresse .
    ?s u:status ?adresse .
  }
}
