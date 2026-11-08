# N5: Tittel på bokmål og nynorsk med reserve, til urn:graph:normalisert
#
# u:tittel med språket "default" er tittelen på fastsettelsesspråket. For de 19 LK20-læreplanene som er fastsatt
# på samisk, er den samisk, og det samme gjelder kompetansemålene og kjerneelementene i dem. Mange ressurser i
# nynorsk-fastsatte læreplaner har ingen bokmålstittel, og de fleste i bokmåls-fastsatte har ingen nynorsktittel.
# To speilvendte egenskaper gir én tittel for hver målform, med fast rekkefølge av reserver:
#
#   udir:bokmaalTittel   bokmål (nob)  → nynorsk (nno) → fastsettelsesspråket (default)
#   udir:nynorskTittel   nynorsk (nno) → bokmål (nob)  → fastsettelsesspråket (default)
#
# Verdien merkes med språket den faktisk er på (nb, nn, se ...), så LANG() viser om en reserve er brukt.
# Reserven fra default merkes med fastsettelsesspråket til læreplanen, eller får ingen språkkode hvis ressursen
# hører til læreplaner med ulike språk eller ikke har noe fastsatt språk.
#
# Gjelder læreplanene og alt som hører til dem (u:tilhoerer-laereplan). Avklart med fagansvarlig 2026-11-08.

PREFIX u:    <http://psi.udir.no/ontologi/kl06/>
PREFIX udir: <http://psi.udir.no/ontologi/>

INSERT { GRAPH <urn:graph:normalisert> { ?s ?egenskap ?tittel } }
WHERE {
  VALUES (?egenskap ?forst ?forstTag ?saa ?saaTag) {
    (udir:bokmaalTittel "nob" "nb" "nno" "nn")
    (udir:nynorskTittel "nno" "nn" "nob" "nb")
  }
  {
    SELECT DISTINCT ?s WHERE {
      GRAPH <urn:graph:grep> {
        { ?s a u:laereplan } UNION { ?s a u:laereplan_lk20 } UNION { ?s u:tilhoerer-laereplan ?lp }
      }
    }
  }
  # Filteret må stå på OPTIONAL-nivå (ikke inne i GRAPH) for å se ?forst og ?saa fra VALUES
  OPTIONAL { GRAPH <urn:graph:grep> { ?s u:tittel ?t1 } FILTER(LANG(?t1) = ?forst) }
  OPTIONAL { GRAPH <urn:graph:grep> { ?s u:tittel ?t2 } FILTER(LANG(?t2) = ?saa) }
  OPTIONAL { GRAPH <urn:graph:grep> { ?s u:tittel ?def FILTER(LANG(?def) = "default") } }
  OPTIONAL {
    # Fastsettelsesspråket: fra læreplanen selv, eller fra læreplanene ressursen hører til
    SELECT ?s (COUNT(DISTINCT ?sp) AS ?antallSpraak) (SAMPLE(?sp) AS ?spraak) WHERE {
      GRAPH <urn:graph:grep> { { ?s u:fastsatt-spraak ?sp } UNION { ?s u:tilhoerer-laereplan/u:fastsatt-spraak ?sp } }
    } GROUP BY ?s
  }
  BIND(STRAFTER(STR(?spraak), "http://psi.udir.no/kl06/") AS ?kode)
  BIND(IF(?kode = "nob", "nb", IF(?kode = "nno", "nn", IF(?kode = "sme", "se", IF(?kode = "eng", "en", ?kode))))
       AS ?tag)
  BIND(COALESCE(
         STRLANG(STR(?t1), ?forstTag),
         STRLANG(STR(?t2), ?saaTag),
         IF(?antallSpraak = 1 && STRLEN(?tag) > 0, STRLANG(STR(?def), ?tag), STR(?def)),
         STR(?def)  # uten opplysning om fastsettelsesspråk
       ) AS ?tittel)
  FILTER(BOUND(?tittel))
}
