"""Retter rdfs:domain / rdfs:range i Grep-ontologien slik at den står seg under resonnering.

Problemet i originalen (ontologi_kl06_20240523.ttl):
  * Flere rdfs:domain/rdfs:range på samme egenskap er brukt som en liste over "hvor
    egenskapen brukes". I RDFS/OWL betyr flere domener SNITT, ikke union: med resonnering
    blir f.eks. alt som har u:tittel utledet til å være 29 klasser samtidig.
  * Noen egenskaper er deklarert som owl:DatatypeProperty men har IRI-er som verdi i data.
  * Noen rekkevidder stemmer ikke med datatypene som faktisk forekommer.

Regler (data fra den nattlige dumpen er fasit, deklarert intensjon beholdes der den er forenlig):
  1. Domene  = union av deklarerte klasser og klassene egenskapen faktisk brukes på.
     - 1 klasse          -> rdfs:domain C
     - 2..GENERELL       -> rdfs:domain [ owl:unionOf (...) ]
     - > GENERELL        -> ingen domene (generell metadata-egenskap, f.eks. u:tittel)
     - brukt på subjekter uten type -> ingen domene
  2. Objektegenskap, rekkevidde: samme regel basert på typen til objektene.
     Objekter uten type i data -> ingen rekkevidde.
  3. Datatypeegenskap med IRI-verdier i data -> owl:ObjectProperty, rekkevidden fjernes.
  4. Datatypeegenskap, rekkevidde: beholdes hvis alle observerte datatyper dekkes,
     ellers settes den til den observerte datatypen (eller rdfs:Literal ved flere).
     Unntak: egenskapene i TYPEDE får datatypen derfra (beslutning B4). Verdiene gjøres om
     hver natt av sparql/normalisering/03-datatyper.ru, som leser rekkevidden fra ontologien.
  5. Egenskaper som ikke brukes i data: flere domener/rekkevidder slås sammen til union.

Klassene i data har liten forbokstav (u:kompetansemaal); de knyttes til ontologiens
klasser (u:Kompetansemaal) via grep_type_mapping.ttl. Her brukes klassene med stor forbokstav.

Bruk:  python scripts/rett_ontologi.py [endepunkt]
"""
import collections
import csv
import datetime
import io
import sys
import urllib.parse
import urllib.request
from pathlib import Path

import rdflib
from rdflib import BNode, Literal, URIRef
from rdflib.collection import Collection
from rdflib.namespace import OWL, RDF, RDFS, XSD

ROOT = Path(__file__).resolve().parent.parent
INN = ROOT / "ontologi" / "ontologi_kl06_20240523.ttl"
UT = ROOT / "ontologi" / "ontologi_kl06_rettet.ttl"
LOGG = ROOT / "ontologi" / "ontologi_kl06_rettet_endringslogg.md"
ENDEPUNKT = sys.argv[1] if len(sys.argv) > 1 else "https://grep-fuseki-v3.fly.dev/ds/query"
U = "http://psi.udir.no/ontologi/kl06/"
GENERELL = 10  # brukt på flere enn så mange klasser -> generell egenskap uten domene

# Bruksstatistikken hentes bare fra rådataene, ikke fra ontologien eller normaliserte/utledede grafer
G = "GRAPH <urn:graph:grep>"
SPORRINGER = {
    "subjekttyper": f"SELECT ?p ?t (COUNT(*) AS ?n) WHERE {{ {G} {{ ?s ?p ?o . ?s a ?t }} }} GROUP BY ?p ?t",
    "objekttyper": f"SELECT ?p ?t (COUNT(*) AS ?n) WHERE {{ {G} {{ ?s ?p ?o . ?o a ?t }} }} GROUP BY ?p ?t",
    "objektart": f'SELECT ?p ?art ?dt (COUNT(*) AS ?n) WHERE {{ {G} {{ ?s ?p ?o }} '
                 'BIND(IF(isLiteral(?o),"lit",IF(isBlank(?o),"bnode","iri")) AS ?art) '
                 'BIND(IF(isLiteral(?o),STR(DATATYPE(?o)),"") AS ?dt) } GROUP BY ?p ?art ?dt',
    "typede_subjekter": f"SELECT ?p (COUNT(*) AS ?n) WHERE {{ {G} {{ ?s ?p ?o . FILTER EXISTS {{ ?s a ?t }} }} }} GROUP BY ?p",
    "typede_objekter": f"SELECT ?p (COUNT(*) AS ?n) WHERE {{ {G} {{ ?s ?p ?o . FILTER EXISTS {{ ?o a ?t }} }} }} GROUP BY ?p",
}

# Beslutning B4: disse egenskapene gjøres om fra xsd:string til riktig datatype hver natt
# (sparql/normalisering/03-datatyper.ru). Regelen leser rekkevidden fra ontologien, så denne
# listen er det eneste stedet den bestemmes. Alle verdiene i dumpen passet formatet 2026-11-06.
TYPEDE = {
    "sist-endret": XSD.dateTime, "gyldig-fra": XSD.dateTime, "gyldig-til": XSD.dateTime,
    "fastsatt-dato": XSD.dateTime, "siste-eksamen": XSD.dateTime,
    "aarstimer": XSD.integer, "aarstimer-doeve-og-tunghoerte": XSD.integer,
    "aarstimer-formgivningsfag": XSD.integer, "aarstimer-samisk": XSD.integer,
    "omfang-totalt": XSD.integer, "omfang-vitnemaal": XSD.integer, "omfang-til-naa": XSD.integer,
    "opplaeringstid": XSD.decimal, "verdiskapingstid": XSD.decimal,  # "1,00": desimalkomma i dumpen
}


def sporr(q):
    data = urllib.parse.urlencode({"query": q}).encode()
    req = urllib.request.Request(ENDEPUNKT, data=data, headers={"Accept": "text/csv"})
    with urllib.request.urlopen(req, timeout=600) as r:
        return list(csv.DictReader(io.StringIO(r.read().decode("utf-8"))))


def kort(x):
    return (str(x).replace(U, "u:").replace(str(XSD), "xsd:")
            .replace(str(RDF), "rdf:").replace(str(RDFS), "rdfs:"))


def main():
    g = rdflib.Graph().parse(INN)
    klasser = {str(c) for c in g.subjects(RDF.type, OWL.Class) if isinstance(c, URIRef)}
    til_klasse = {c.lower(): URIRef(c) for c in klasser}  # u:kompetansemaal -> u:Kompetansemaal

    print("Henter bruksstatistikk fra", ENDEPUNKT, "...", file=sys.stderr)
    r = {k: sporr(q) for k, q in SPORRINGER.items()}

    subj = collections.defaultdict(set)
    for x in r["subjekttyper"]:
        if x["t"].lower() in til_klasse:
            subj[x["p"]].add(til_klasse[x["t"].lower()])
    obj = collections.defaultdict(set)
    for x in r["objekttyper"]:
        if x["t"].lower() in til_klasse:
            obj[x["p"]].add(til_klasse[x["t"].lower()])
    art = collections.defaultdict(collections.Counter)
    for x in r["objektart"]:
        art[x["p"]][(x["art"], x["dt"])] += int(x["n"])
    typede_s = {x["p"]: int(x["n"]) for x in r["typede_subjekter"]}
    typede_o = {x["p"]: int(x["n"]) for x in r["typede_objekter"]}

    logg = collections.defaultdict(list)

    def sett(p, rel, mengde, grunn):
        """Erstatter alle p rel ... med én verdi (klasse eller union)."""
        gamle = sorted(kort(o) for o in g.objects(p, rel) if not isinstance(o, BNode))
        g.remove((p, rel, None))
        if not mengde:
            logg[kort(p)].append(f"{kort(rel)}: fjernet ({grunn}). Var: {', '.join(gamle) or '–'}")
            return
        mengde = sorted(mengde, key=str)
        if len(mengde) == 1:
            g.add((p, rel, mengde[0]))
            ny = kort(mengde[0])
        else:
            b, liste = BNode(), BNode()
            Collection(g, liste, mengde)
            g.add((b, RDF.type, OWL.Class))
            g.add((b, OWL.unionOf, liste))
            g.add((p, rel, b))
            ny = "unionOf(" + ", ".join(kort(m) for m in mengde) + ")"
        if gamle != [kort(m) for m in mengde]:
            logg[kort(p)].append(f"{kort(rel)}: {ny} ({grunn}). Var: {', '.join(gamle) or '–'}")

    def klasse_regel(p, rel, observert, totalt, typede):
        deklarert = {o for o in g.objects(p, rel) if isinstance(o, URIRef) and str(o) in klasser}
        if totalt and typede < totalt:
            return sett(p, rel, set(), f"{totalt - typede} av {totalt} forekomster mangler type i data")
        alle = deklarert | observert
        if len(alle) > GENERELL:
            return sett(p, rel, set(), f"generell egenskap, brukt på/deklarert for {len(alle)} klasser")
        nye = observert - deklarert
        grunn = ("lagt til fra data: " + ", ".join(kort(c) for c in sorted(nye, key=str))) if nye else \
                ("slått sammen til union" if len(alle) > 1 else "uendret")
        sett(p, rel, alle, grunn)

    # Egenskaper i TYPEDE som brukes i data, men mangler i originalen, deklareres
    # (u:omfang-vitnemaal heter u:omfang-vitnemål i originalen)
    for navn in TYPEDE:
        p = URIRef(U + navn)
        if (p, RDF.type, None) not in g and art.get(str(p)):
            g.add((p, RDF.type, OWL.DatatypeProperty))
            g.add((p, RDFS.comment, Literal("Brukes i Grep-dataene, men mangler i ontologi_kl06_20240523.ttl. "
                                            "Lagt til av scripts/rett_ontologi.py.", lang="nb")))
            logg[kort(p)].append("lagt til som owl:DatatypeProperty (brukes i data, mangler i originalen)")

    obj_props = set(g.subjects(RDF.type, OWL.ObjectProperty))
    dt_props = set(g.subjects(RDF.type, OWL.DatatypeProperty))

    for p in sorted(obj_props | dt_props, key=str):
        ps = str(p)
        a = art.get(ps, collections.Counter())
        totalt = sum(a.values())
        n_lit = sum(n for (k, _), n in a.items() if k == "lit")
        n_iri = sum(n for (k, _), n in a.items() if k in ("iri", "bnode"))
        ubrukt = totalt == 0
        if ubrukt:
            logg[kort(p)].append("brukes ikke i data (beholdt, eventuelle flere domener/rekkevidder slått sammen til union)")

        # 1. Domene
        klasse_regel(p, RDFS.domain, subj.get(ps, set()), totalt, typede_s.get(ps, 0))

        # 3. DatatypeProperty med IRI-verdier -> ObjectProperty
        if p in dt_props and n_iri:
            g.remove((p, RDF.type, OWL.DatatypeProperty))
            g.add((p, RDF.type, OWL.ObjectProperty))
            dt_props.discard(p)
            obj_props.add(p)
            logg[kort(p)].append(f"endret fra owl:DatatypeProperty til owl:ObjectProperty ({n_iri} IRI-verdier, {n_lit} literaler i data)")

        # 2./4. Rekkevidde
        if p in obj_props:
            ikke_klasse = [o for o in g.objects(p, RDFS.range) if isinstance(o, URIRef) and str(o) not in klasser]
            if ikke_klasse:
                g.remove((p, RDFS.range, None))
                logg[kort(p)].append(f"rdfs:range: fjernet datatype-rekkevidde {', '.join(kort(o) for o in ikke_klasse)} (objektene er IRI-er)")
            if n_lit:
                logg[kort(p)].append(f"ADVARSEL: objektegenskap med {n_lit} literal-verdier i data")
            klasse_regel(p, RDFS.range, obj.get(ps, set()), n_iri, typede_o.get(ps, 0))
        elif p in dt_props and not ubrukt:
            observert = {URIRef(dt) for (k, dt), n in a.items() if k == "lit" and dt}
            deklarert = set(g.objects(p, RDFS.range))
            if not observert <= deklarert:
                ny = observert.pop() if len(observert) == 1 else RDFS.Literal
                gamle = ", ".join(sorted(kort(o) for o in deklarert))
                g.remove((p, RDFS.range, None))
                g.add((p, RDFS.range, ny))
                logg[kort(p)].append(f"rdfs:range: {kort(ny)} (observert i data: "
                                     f"{', '.join(sorted(kort(dt) for (k, dt) in a if k == 'lit'))}). Var: {gamle}")

        # B4: datatypen bestemmes her, og verdiene gjøres om av sparql/normalisering/03-datatyper.ru
        navn = ps[len(U):] if ps.startswith(U) else None
        if p in dt_props and navn in TYPEDE and set(g.objects(p, RDFS.range)) != {TYPEDE[navn]}:
            gamle = ", ".join(sorted(kort(o) for o in g.objects(p, RDFS.range))) or "–"
            g.remove((p, RDFS.range, None))
            g.add((p, RDFS.range, TYPEDE[navn]))
            logg[kort(p)].append(f"rdfs:range: {kort(TYPEDE[navn])} (B4: verdiene gjøres om av "
                                 f"sparql/normalisering/03-datatyper.ru). Var: {gamle}")

    # Versjonsinformasjon i ontologihodet
    ont = URIRef(U)
    idag = datetime.date.today().isoformat()
    g.set((ont, OWL.versionInfo, Literal(f"{idag}: rettet rdfs:domain/rdfs:range (se ontologi_kl06_rettet_endringslogg.md)")))
    g.add((ont, RDFS.comment, Literal(
        "Rettet versjon av ontologi_kl06_20240523.ttl: flere domener/rekkevidder (som i RDFS/OWL betyr snitt) "
        "er erstattet med owl:unionOf, generelle metadata-egenskaper har ikke lenger domene, og egenskapstyper "
        "og rekkevidder er justert etter faktisk bruk i Grep-dataene. Generert av scripts/rett_ontologi.py.", lang="nb")))

    g.bind("u", U, replace=True)
    g.bind("udir", "http://psi.udir.no/ontologi/")
    UT.write_text(g.serialize(format="turtle"), encoding="utf-8", newline="\n")

    linjer = [f"# Endringslogg: ontologi_kl06_rettet.ttl",
              "",
              f"Generert {idag} av `scripts/rett_ontologi.py` fra `ontologi_kl06_20240523.ttl`, "
              f"med bruksstatistikk fra `{ENDEPUNKT}`.",
              "",
              "Se docstringen i skriptet for reglene. Egenskaper som ikke er nevnt her, er uendret.",
              "",
              f"{len(logg)} egenskaper endret.",
              ""]
    for p in sorted(logg):
        linjer.append(f"## {p}")
        linjer += [f"- {x}" for x in logg[p]]
        linjer.append("")
    LOGG.write_text("\n".join(linjer), encoding="utf-8", newline="\n")
    print(f"Skrev {UT.name} ({len(g)} tripler) og {LOGG.name} ({len(logg)} egenskaper endret)", file=sys.stderr)


if __name__ == "__main__":
    main()
