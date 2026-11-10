"""Sjekker koblingene i ontologi/koblinger/*.csv mot SSBs KLASS og mot Grep-dataene. Brukes av den nattlige jobben.

Skriver CSV-rader (uten overskrift) for én sjekk til standard output, slik avvik() i nattlig-innlasting.sh vil ha dem:

    python3 scripts/sjekk-koblinger.py utgaatte-koder          # Kode,Klassifikasjon,Programområde
    python3 scripts/sjekk-koblinger.py nye-programomraader     # Programområde,Tittel,Mangler i

utgaatte-koder:      STYRK- og NUS-koder i CSV-filene som ikke finnes i versjonen av klassifikasjonen som gjelder i dag.
nye-programomraader: programområder i Grep som ikke står i nus.csv, og programområder med yrkestittel som ikke står i
                     styrk.csv. De må vurderes av et menneske (legg til en rad, eventuelt med metoden «ingen»).

Svarer ikke KLASS eller Fuseki, skrives en advarsel til standard error, og sjekken gir ingen rader.
Det skal ikke stoppe innlastingen.
"""
import csv, datetime, json, os, sys, urllib.parse, urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KLASS = 'https://data.ssb.no/api/klass/v1/classifications/%s/codesAt?date=%s'
KLASSIFIKASJONER = {'styrk': ('7', 'STYRK-08'), 'nus': ('36', 'NUS')}


def csv_rader(navn):
    return list(csv.DictReader(open(os.path.join(REPO, 'ontologi/koblinger/%s.csv' % navn), encoding='utf-8')))


def utgaatte_koder(w):
    idag = datetime.date.today().isoformat()
    for navn, (kid, tekst) in KLASSIFIKASJONER.items():
        req = urllib.request.Request(KLASS % (kid, idag), headers={'Accept': 'application/json'})
        gyldige = {k['code'] for k in json.load(urllib.request.urlopen(req, timeout=120))['codes']}
        for r in csv_rader(navn):
            if r[navn] and r[navn] not in gyldige:
                w.writerow([r[navn], tekst, r['programomraade']])


def nye_programomraader(w):
    url = os.environ.get('FUSEKI_URL', 'https://grep-fuseki-v3.fly.dev').rstrip('/') + '/' + os.environ.get('DATASET', 'ds') + '/query'
    q = '''PREFIX u: <http://psi.udir.no/ontologi/kl06/>
SELECT ?kode ?tittel ?yrke WHERE { GRAPH <urn:graph:grep> {
  ?p a u:programomraade ; u:kode ?kode . OPTIONAL { ?p u:tittel ?tittel FILTER(lang(?tittel) = "default") }
  OPTIONAL { ?p u:yrkestittel ?yrke } } }'''
    req = urllib.request.Request(url, data=urllib.parse.urlencode({'query': q}).encode(),
                                 headers={'Accept': 'application/sparql-results+json'})
    po = {}
    for b in json.load(urllib.request.urlopen(req, timeout=120))['results']['bindings']:
        k = b['kode']['value']
        po.setdefault(k, {'tittel': b.get('tittel', {}).get('value', ''), 'yrke': False})
        po[k]['yrke'] |= 'yrke' in b
    i_nus = {r['programomraade'] for r in csv_rader('nus')}
    i_styrk = {r['programomraade'] for r in csv_rader('styrk')}
    for k in sorted(po):
        mangler = [f for f, ok in (('nus.csv', k in i_nus), ('styrk.csv', k in i_styrk or not po[k]['yrke'])) if not ok]
        if mangler:
            w.writerow([k, po[k]['tittel'], ' og '.join(mangler)])


def main():
    sjekk = {'utgaatte-koder': utgaatte_koder, 'nye-programomraader': nye_programomraader}.get(sys.argv[1] if len(sys.argv) > 1 else '')
    if not sjekk:
        sys.exit('Bruk: sjekk-koblinger.py utgaatte-koder | nye-programomraader')
    class Rader:  # avvik() deler på komma, så komma inne i et felt blir semikolon
        def writerow(self, felt):
            print(','.join(str(f).replace(',', ';') for f in felt))
    w = Rader()
    try:
        sjekk(w)
    except Exception as e:  # nett eller tjeneste nede: ikke stopp innlastingen
        print('Advarsel: %s kunne ikke kjøres: %s' % (sys.argv[1], e), file=sys.stderr)


if __name__ == '__main__':
    main()
