"""Lager ontologi/koblinger/nus.ttl fra ontologi/koblinger/nus.csv og NUS i SSBs KLASS.

Kjør på nytt når nus.csv endres, eller når SSB har publisert en ny NUS-versjon:

    python -I -X utf8 scripts/lag-nus-ttl.py

Ut kommer:
- NUS som begrepssystem (udir:Nus): kodene programområdene bruker, og gruppene over dem (nivå, fagfelt,
  faggruppe, utdanningsgruppe), med navn og skos:broader slik SSB publiserer dem (KLASS, klassifikasjon 36).
  Versjonen som gjelder i dag, brukes.
- skos:broadMatch fra hver NUS-kode til fagfeltet i ISCED-F 2013, slik ESCO publiserer det
  (http://data.europa.eu/esco/isced-f/<kode>), etter SSBs korrespondansetabell.
- skos:broadMatch fra hver NUS-kode til nivået i ISCED 2011 (Attainment), etter SSBs korrespondansetabell.
  EU har ingen ISCED 2011-adresser som virker (sjekket 2026-11-10), så nivåene er egne begreper (udir:Isced2011).
- udir:utdanningsklassifisering fra hvert programområde til NUS-koden, der nus.csv har en kode.

Metoden i nus.csv (ssb-navn, som-vanlig-utgave, forslag, manuell) blir ikke med i grafen. CSV-filen er kilden.
"""
import csv, datetime, json, os, urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KLASS = 'https://data.ssb.no/api/klass/v1'


def hent(sti):
    req = urllib.request.Request(KLASS + sti, headers={'Accept': 'application/json'})
    return json.load(urllib.request.urlopen(req, timeout=120))


def lit(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


def main():
    idag = datetime.date.today().isoformat()
    koder = {k['code']: k for k in hent('/classifications/36/codesAt?date=' + idag)['codes']}
    versjon = next(v for v in hent('/classifications/36')['versions']
                   if v['validFrom'] <= idag and (not v.get('validTo') or v['validTo'] > idag))
    tabeller = hent('/versions/' + versjon['_links']['self']['href'].rsplit('/', 1)[1])['correspondenceTables']

    def korrespondanse(del_av_navn):
        t = next(t for t in tabeller if del_av_navn in t['name'])
        return {m['sourceCode']: (m['targetCode'], m['targetName']) for m in
                hent('/correspondencetables/' + t['_links']['self']['href'].rsplit('/', 1)[1])['correspondenceMaps']}

    iscedf, isced11 = korrespondanse('ISCED-F 2013'), korrespondanse('ISCED 2011 Attainment')

    rader = list(csv.DictReader(open(os.path.join(REPO, 'ontologi/koblinger/nus.csv'), encoding='utf-8')))
    brukt = set()
    for r in rader:
        if r['nus']:
            if r['nus'] not in koder:
                raise SystemExit('NUS-koden %s (%s) finnes ikke i %s' % (r['nus'], r['programomraade'], versjon['name']))
            brukt.add(r['nus'])
    med_over = set()
    for k in brukt:
        while k:
            med_over.add(k)
            k = koder[k].get('parentCode')

    ut = ['''# GENERERT av scripts/lag-nus-ttl.py fra ontologi/koblinger/nus.csv og SSBs KLASS. Ikke rediger for hånd.
# NUS-versjon: %s
#
# Lastes inn i urn:graph:koblinger av scripts/nattlig-innlasting.sh.

@prefix udir:  <http://psi.udir.no/ontologi/> .
@prefix nus:   <http://psi.udir.no/ontologi/nus/> .
@prefix isced2011: <http://psi.udir.no/ontologi/isced2011/> .
@prefix iscedf: <http://data.europa.eu/esco/isced-f/> .
@prefix d:     <http://psi.udir.no/kl06/> .
@prefix skos:  <http://www.w3.org/2004/02/skos/core#> .
@prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .
@prefix dcterms: <http://purl.org/dc/terms/> .

udir:Nus a skos:ConceptScheme ;
    skos:prefLabel "NUS Norsk standard for utdanningsgruppering"@nb, "NUS Norsk standard for utdanningsgruppering"@nn,
                   "NUS Norwegian Standard Classification of Education"@en ;
    rdfs:comment "SSBs utdanningsgruppering. Bare kodene programområdene bruker, og gruppene over dem, er med. SSB har ingen faste URI-er for kodene, så sandkassen lager dem selv."@nb ;
    dcterms:publisher <https://www.ssb.no/> ;
    owl:versionInfo %s ;
    rdfs:seeAlso <%s/classifications/36> .

udir:Isced2011 a skos:ConceptScheme ;
    skos:prefLabel "ISCED 2011 (nivå, fullført utdanning)"@nb, "ISCED 2011 Attainment"@en ;
    rdfs:comment "Nivåene i ISCED 2011 som NUS-kodene er koblet til i SSBs korrespondansetabell. Egne begreper fordi EU ikke har adresser for dem som virker (sjekket 2026-11-10)."@nb .
''' % (versjon['name'], lit(versjon['name']), KLASS)]
    ut[0] = ut[0].replace('@prefix dcterms:', '@prefix owl:   <http://www.w3.org/2002/07/owl#> .\n@prefix dcterms:')

    nivaaer = {}
    for k in sorted(med_over, key=lambda k: (len(k), k)):
        c = koder[k]
        linjer = ['nus:%s a skos:Concept' % k, 'skos:inScheme udir:Nus', 'skos:notation %s' % lit(k),
                  'skos:prefLabel %s@nb' % lit(c['name'])]
        linjer.append('skos:broader nus:%s' % c['parentCode'] if c.get('parentCode') else 'skos:topConceptOf udir:Nus')
        if k in iscedf:
            linjer.append('skos:broadMatch iscedf:%s' % iscedf[k][0])
        if k in isced11:
            linjer.append('skos:broadMatch isced2011:%s' % isced11[k][0])
            nivaaer[isced11[k][0]] = isced11[k][1]
        ut.append(' ;\n    '.join(linjer) + ' .\n')
    for k, navn in sorted(nivaaer.items()):
        ut.append('isced2011:%s a skos:Concept ;\n    skos:inScheme udir:Isced2011 ;\n    skos:notation %s ;\n'
                  '    skos:prefLabel %s@en .\n' % (k, lit(k), lit(navn)))

    ut.append('# Programområder koblet til utdanning i NUS\n')
    n = 0
    for r in rader:
        if r['nus']:
            ut.append('d:%s udir:utdanningsklassifisering nus:%s .' % (r['programomraade'], r['nus']))
            n += 1
    with open(os.path.join(REPO, 'ontologi/koblinger/nus.ttl'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(ut) + '\n')
    print('%s: %d NUS-begreper (%d i bruk), %d ISCED 2011-nivåer, programområder med kobling: %d av %d'
          % (versjon['name'], len(med_over), len(brukt), len(nivaaer), n, len(rader)))


if __name__ == '__main__':
    main()
