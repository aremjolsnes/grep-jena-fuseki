"""Lager ontologi/koblinger/styrk.ttl fra ontologi/koblinger/styrk.csv og STYRK-08 i SSBs KLASS.

Kjør på nytt når styrk.csv endres:

    python -I -X utf8 scripts/lag-styrk-ttl.py

Ut kommer:
- STYRK-08 som begrepssystem (udir:Styrk08). Alle grupper på alle fire nivåer, med kode, navn og
  skos:broader, slik SSB publiserer dem (KLASS, klassifikasjon 7).
- skos:exactMatch til samme ISCO-08-gruppe i ESCO (http://data.europa.eu/esco/isco/C<kode>). STYRK-08 har
  samme koder som ISCO-08, bortsett fra noen norske særkoder som ESCO ikke har (sjekket 2026-11-09).
- udir:yrkesklassifisering fra hvert programområde til STYRK-gruppen, der styrk.csv har en kode.

Metoden i styrk.csv (ssb-yrkeskatalog, manuell, forslag) blir ikke med i grafen. CSV-filen er kilden.
"""
import csv, json, os, urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KLASS = 'https://data.ssb.no/api/klass/v1/classifications/7'
# Koder i STYRK-08 som ikke finnes som ISCO-08-grupper i ESCO (sjekket mot ESCO-API-et 2026-11-09)
IKKE_I_ESCO = {'0000', '00', '000', '2223', '2224', '3439'}
# Hovedgruppe 1 (ledere) og 2 (akademiske yrker) krever høyere utdanning og kobles aldri til programområder
FORBUDT = ('1', '2')


def lit(s):
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


def main():
    req = urllib.request.Request(KLASS + '/codesAt?date=2026-11-09', headers={'Accept': 'application/json'})
    koder = json.load(urllib.request.urlopen(req, timeout=60))['codes']
    navn = {k['code']: k['name'] for k in koder}
    rader = list(csv.DictReader(open(os.path.join(REPO, 'ontologi/koblinger/styrk.csv'), encoding='utf-8')))
    for r in rader:
        k = r['styrk']
        if k and (k not in navn or len(k) != 4 or k.startswith(FORBUDT)):
            raise SystemExit('Ugyldig STYRK-kode for %s: %s' % (r['programomraade'], k))

    ut = ['''# GENERERT av scripts/lag-styrk-ttl.py fra ontologi/koblinger/styrk.csv og SSBs KLASS. Ikke rediger for hånd.
#
# Lastes inn i urn:graph:koblinger av scripts/nattlig-innlasting.sh.

@prefix udir:  <http://psi.udir.no/ontologi/> .
@prefix styrk: <http://psi.udir.no/ontologi/styrk08/> .
@prefix d:     <http://psi.udir.no/kl06/> .
@prefix skos:  <http://www.w3.org/2004/02/skos/core#> .
@prefix rdfs:  <http://www.w3.org/2000/01/rdf-schema#> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix isco:  <http://data.europa.eu/esco/isco/> .

udir:Styrk08 a skos:ConceptScheme ;
    skos:prefLabel "STYRK-08 Standard for yrkesklassifisering"@nb, "STYRK-08 Standard for yrkesklassifisering"@nn,
                   "STYRK-08 Norwegian Standard Classification of Occupations"@en ;
    rdfs:comment "SSBs yrkesklassifisering, basert på ISCO-08. SSB har ingen faste URI-er for kodene, så sandkassen lager dem selv."@nb ;
    dcterms:publisher <https://www.ssb.no/> ;
    rdfs:seeAlso <%s> ;
    skos:hasTopConcept %s .
''' % (KLASS, ', '.join('styrk:' + k['code'] for k in koder if k['level'] == '1'))]

    for k in sorted(koder, key=lambda k: k['code']):
        linjer = ['styrk:%s a skos:Concept' % k['code'],
                  'skos:inScheme udir:Styrk08',
                  'skos:notation %s' % lit(k['code']),
                  'skos:prefLabel %s@nb' % lit(k['name'])]
        if k.get('parentCode'):
            linjer.append('skos:broader styrk:%s' % k['parentCode'])
        else:
            linjer.append('skos:topConceptOf udir:Styrk08')
        if k['code'] not in IKKE_I_ESCO:
            linjer.append('skos:exactMatch isco:C%s' % k['code'])
        linjer.append('rdfs:seeAlso <%s/codesAt?date=2026-11-09&selectCodes=%s>' % (KLASS, k['code']))
        ut.append(' ;\n    '.join(linjer) + ' .\n')

    ut.append('# Programområder koblet til yrke (u:yrkestittel) i STYRK-08\n')
    n = 0
    for r in rader:
        if r['styrk']:
            ut.append('d:%s udir:yrkesklassifisering styrk:%s .' % (r['programomraade'], r['styrk']))
            n += 1
    with open(os.path.join(REPO, 'ontologi/koblinger/styrk.ttl'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(ut) + '\n')
    print('STYRK-grupper: %d, programområder med kobling: %d av %d' % (len(koder), n, len(rader)))


if __name__ == '__main__':
    main()
