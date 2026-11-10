"""Lager ontologi/koblinger/esco-yrker.ttl: ESCO-yrkene under ISCO-gruppene som programområdene er koblet til.

Kjør på nytt når ontologi/koblinger/styrk.csv får nye STYRK-koder, eller når ESCO har en ny versjon:

    python -I -X utf8 scripts/lag-esco-ttl.py

Henter fra ESCO-API-et (https://ec.europa.eu/esco/api). Det tar et par minutter. Ut kommer hvert ESCO-yrke under de
ISCO-08-gruppene STYRK-kodene i styrk.csv svarer til, også underyrkene, med ESCOs egne URI-er:
- skos:prefLabel og skos:definition på norsk. ESCO merker språket «no», men det er bokmål, så her er det @nb.
- skos:notation (ESCO-koden, for eksempel 7231.8).
- skos:broader til ISCO-gruppen (http://data.europa.eu/esco/isco/C<kode>) eller til yrket over.

Ferdighetene (hasEssentialSkill, hasOptionalSkill) er ikke med ennå (idé 4 i docs/ideer.md).
ESCO kan brukes fritt med kildehenvisning: © Den europeiske union, https://esco.ec.europa.eu.
"""
import csv, datetime, json, os, sys, time, urllib.parse, urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
API = 'https://ec.europa.eu/esco/api/resource/'


def hent(type_, uri):
    url = API + type_ + '?' + urllib.parse.urlencode({'uri': uri, 'language': 'no'})
    for forsok in range(5):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers={'User-Agent': 'grep-sandkasse'}), timeout=60) as r:
                return json.load(r)
        except Exception as e:
            feil = e
            time.sleep(2 + 3 * forsok)
    raise SystemExit('ESCO-API-et svarer ikke for %s: %s' % (uri, feil))


def lit(s):
    s = ' '.join(s.split())
    return '"' + s.replace('\\', '\\\\').replace('"', '\\"') + '"'


def main():
    koder = sorted({r['styrk'] for r in csv.DictReader(open(os.path.join(REPO, 'ontologi/koblinger/styrk.csv'),
                                                             encoding='utf-8')) if r['styrk']})
    ko, yrker = [], {}
    for k in koder:
        g = hent('concept', 'http://data.europa.eu/esco/isco/C' + k)
        ko += [(o['uri'], '<http://data.europa.eu/esco/isco/C%s>' % k) for o in g['_links'].get('narrowerOccupation', [])]
        time.sleep(0.1)
    while ko:
        uri, over = ko.pop()
        if uri in yrker:
            continue
        o = hent('occupation', uri)
        navn = (o.get('preferredLabel') or {}).get('no')
        beskrivelse = ((o.get('description') or {}).get('no') or {}).get('literal')
        yrker[uri] = (o.get('code'), navn, beskrivelse, over)
        ko += [(x['uri'], '<%s>' % uri) for x in o.get('_links', {}).get('narrowerOccupation', [])]
        time.sleep(0.1)
        if len(yrker) % 100 == 0:
            print('  %d yrker ...' % len(yrker), file=sys.stderr)

    ut = ['''# GENERERT av scripts/lag-esco-ttl.py fra ESCO-API-et %s. Ikke rediger for hånd.
# ESCO-yrkene under ISCO-08-gruppene som programområdene er koblet til (ontologi/koblinger/styrk.csv).
# Kilde: ESCO, © Den europeiske union, https://esco.ec.europa.eu (fri gjenbruk med kildehenvisning).
#
# Lastes inn i urn:graph:koblinger av scripts/nattlig-innlasting.sh.

@prefix skos:  <http://www.w3.org/2004/02/skos/core#> .
@prefix esco:  <http://data.europa.eu/esco/model#> .
@prefix dcterms: <http://purl.org/dc/terms/> .
''' % datetime.date.today().isoformat()]
    for uri, (kode, navn, beskrivelse, over) in sorted(yrker.items(), key=lambda x: (x[1][0] or '', x[0])):
        linjer = ['<%s> a skos:Concept, esco:Occupation' % uri,
                  'skos:inScheme <http://data.europa.eu/esco/concept-scheme/occupations>']
        if kode:
            linjer.append('skos:notation %s' % lit(kode))
        if navn:
            linjer.append('skos:prefLabel %s@nb' % lit(navn))
        if beskrivelse:
            linjer.append('skos:definition %s@nb' % lit(beskrivelse))
        linjer.append('skos:broader %s' % over)
        linjer.append('dcterms:source <https://esco.ec.europa.eu>')
        ut.append(' ;\n    '.join(linjer) + ' .\n')
    with open(os.path.join(REPO, 'ontologi/koblinger/esco-yrker.ttl'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(ut))
    print('ISCO-grupper: %d, ESCO-yrker: %d (uten norsk navn: %d)' % (
        len(koder), len(yrker), sum(1 for y in yrker.values() if not y[1])))


if __name__ == '__main__':
    main()
