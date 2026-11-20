"""Sammenligner Udirs liste over verneverdige tradisjonshåndverksfag på udir.no med merkelappen i Grep.

Udir avgjør hvilke fag som er verneverdige tradisjonshåndverksfag (ekstra lærlingtilskudd). Lista publiseres som
en tabell på udir.no, og i Grep skal de samme programområdene ha merkelappen d:verneverdig_tradisjonshaandverk.
De to har sklidd fra hverandre (oppdaget 2026-11-20: fire fag på udir.no uten merkelapp, to med merkelapp som
ikke står på udir.no). Brukes av den nattlige jobben.

Skriver CSV-rader (uten overskrift) til standard output, slik avvik() i nattlig-innlasting.sh vil ha dem
(avvik() deler på komma, så teksten i siste kolonne er uten komma):

    python3 scripts/sjekk-verneverdige.py          # Fag,Programområde,Avvik

Fagene sammenlignes på tittel (bokmål) blant publiserte programområder. Et fag på udir.no som ikke finnes som
programområde i Grep i det hele tatt, meldes også.

Miljøvariabler: FUSEKI_URL (standard: sandkassen i prod), DATASET (standard: ds).
Svarer ikke udir.no eller Fuseki, eller finnes ikke tabellen på siden lenger, skrives en advarsel til standard error,
og sjekken gir ingen rader. Det skal ikke stoppe innlastingen.
"""
import csv, html, json, os, re, sys, urllib.parse, urllib.request
from html.parser import HTMLParser

UDIR_URL = 'https://www.udir.no/om-udir/tilskudd-og-prosjektmidler/retningslinjer-tilskudd-larebedrifter/sma-verneverdige-fag-vgo/'
MERKELAPP = 'http://psi.udir.no/kl06/verneverdig_tradisjonshaandverk'
UA = 'grep-sandkasse (github.com/aremjolsnes/grep-jena-fuseki)'


def normaliser(t):
    """Nøkkel for sammenligning: små bokstaver, ett mellomrom, uten hardt mellomrom og bindestrekvarianter."""
    return re.sub(r'\s+', ' ', html.unescape(t).replace('\xa0', ' ').replace('‑', '-').replace('–', '-')).strip().lower()


class Tabell(HTMLParser):
    """Plukker ut cellene i tabellen med «verneverdige tradisjonshåndverksfag» i <caption>."""
    def __init__(self):
        super().__init__()
        self.i_tabell = self.i_caption = self.i_celle = False
        self.caption = self.celle = ''
        self.celler = []
        self.funnet = None  # cellene i riktig tabell

    def handle_starttag(self, tag, attrs):
        if tag == 'table':
            self.i_tabell, self.caption, self.celler = True, '', []
        elif self.i_tabell and tag == 'caption':
            self.i_caption = True
        elif self.i_tabell and tag == 'td':
            self.i_celle, self.celle = True, ''

    def handle_endtag(self, tag):
        if tag == 'caption':
            self.i_caption = False
        elif tag == 'td' and self.i_celle:
            self.i_celle = False
            if self.celle.strip():
                self.celler.append(self.celle)
        elif tag == 'table' and self.i_tabell:
            self.i_tabell = False
            if 'verneverdige tradisjonsh' in normaliser(self.caption) and self.funnet is None:
                self.funnet = self.celler

    def handle_data(self, data):
        if self.i_caption:
            self.caption += data
        elif self.i_celle:
            self.celle += data


def fag_paa_udir_no():
    """{normalisert tittel: tittel slik den står på udir.no}"""
    req = urllib.request.Request(UDIR_URL, headers={'User-Agent': UA})
    p = Tabell()
    p.feed(urllib.request.urlopen(req, timeout=120).read().decode('utf-8'))
    if not p.funnet:
        raise RuntimeError('fant ingen tabell med «verneverdige tradisjonshåndverksfag» i <caption> på ' + UDIR_URL)
    return {normaliser(c): html.unescape(c).replace('\xa0', ' ').strip() for c in p.funnet}


def programomraader_i_grep():
    """{normalisert tittel: [(kode, tittel, har merkelappen)]} for publiserte programområder"""
    url = os.environ.get('FUSEKI_URL', 'https://grep-fuseki-v3.fly.dev').rstrip('/') + '/' + os.environ.get('DATASET', 'ds') + '/query'
    q = '''PREFIX u: <http://psi.udir.no/ontologi/kl06/>
PREFIX st: <https://data.udir.no/kl06/v201906/status/status_>
SELECT ?kode ?tittel ?merket WHERE { GRAPH <urn:graph:grep> {
  ?p a u:programomraade ; u:kode ?kode ; u:status st:publisert ; u:tittel ?tittel . FILTER(lang(?tittel) = "nob")
  BIND(EXISTS { <%s> u:tilknyttede-programomraader ?p } AS ?merket) } }''' % MERKELAPP
    req = urllib.request.Request(url, data=urllib.parse.urlencode({'query': q}).encode(),
                                 headers={'Accept': 'application/sparql-results+json', 'User-Agent': UA})
    po = {}
    for b in json.load(urllib.request.urlopen(req, timeout=120))['results']['bindings']:
        t = b['tittel']['value']
        po.setdefault(normaliser(t), []).append((b['kode']['value'], t, b['merket']['value'] == 'true'))
    return po


def main():
    w = csv.writer(sys.stdout, lineterminator='\n')
    try:
        udir = fag_paa_udir_no()
        grep = programomraader_i_grep()
    except Exception as e:  # nettverk, endret side, Fuseki nede: meld fra, men ikke stopp innlastingen
        print('sjekk-verneverdige: hoppet over: %s' % e, file=sys.stderr)
        return
    for n, tittel in sorted(udir.items()):
        if n not in grep:
            w.writerow([tittel, '', 'Står på udir.no uten å finnes som publisert programområde i Grep'])
        elif not any(m for _, _, m in grep[n]):
            w.writerow([tittel, ' / '.join(k for k, _, _ in grep[n]), 'Står på udir.no uten merkelappen i Grep'])
    for n in sorted(grep):
        for kode, tittel, m in grep[n]:
            if m and n not in udir:
                w.writerow([tittel, kode, 'Har merkelappen i Grep uten å stå på udir.no'])


if __name__ == '__main__':
    main()
