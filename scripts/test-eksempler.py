"""Tester eksempelspørringene i dokumentasjonen mot sandkassen (idé 7 i docs/ideer.md).

Kjører hver ```sparql-blokk i docs/bruk.md og hver fil i docs/eksempler/*.rq. Prefiksene fra den første
blokken i bruk.md (avsnittet «Prefikser») legges til der spørringen ikke selv har dem, slik sparql-appen gjør.
En spørring feiler hvis endepunktet gir feil, eller hvis den ikke gir noen rader eller tripler.

Merk en blokk med en kommentarlinje for å endre hva som testes:
    # forventer tomt   spørringen skal gi tomt svar
    # ikke test        hopp over blokken

Blokker som bare er utdrag (uten SELECT, CONSTRUCT, ASK eller DESCRIBE), hoppes over.

    FUSEKI_URL=https://grep-fuseki-v3.fly.dev python3 scripts/test-eksempler.py
"""
import glob, json, os, re, sys, textwrap, time, urllib.error, urllib.parse, urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = os.environ.get('FUSEKI_URL', 'https://grep-fuseki-v3.fly.dev').rstrip('/') + '/' + os.environ.get('DATASET', 'ds') + '/query'
SKJEMA = re.compile(r'^\s*(SELECT|CONSTRUCT|ASK|DESCRIBE)\b', re.I | re.M)
PREFIKS = re.compile(r'^\s*PREFIX\s+([\w-]*):\s*<([^>]*)>', re.I | re.M)


def blokker(md):
    """(linjenummer, tekst) for hver ```sparql-blokk, også innrykkede blokker i lister."""
    ut, i, linjer = [], 0, md.split('\n')
    while i < len(linjer):
        m = re.match(r'^(\s*)```sparql\s*$', linjer[i])
        if m:
            start, inn = i + 1, []
            i += 1
            while i < len(linjer) and not re.match(r'^\s*```\s*$', linjer[i]):
                inn.append(linjer[i]); i += 1
            ut.append((start, textwrap.dedent('\n'.join(inn))))
        i += 1
    return ut


def kjor(sporring, form):
    accept = 'text/turtle' if form in ('CONSTRUCT', 'DESCRIBE') else 'application/sparql-results+json'
    data = urllib.parse.urlencode({'query': sporring}).encode()
    req = urllib.request.Request(URL, data=data, headers={'Accept': accept, 'User-Agent': 'grep-sandkasse-test'})
    with urllib.request.urlopen(req, timeout=120) as r:
        tekst = r.read().decode('utf-8')
    if form == 'ASK':
        return 1 if json.loads(tekst)['boolean'] else 0
    if form == 'SELECT':
        return len(json.loads(tekst)['results']['bindings'])
    # Turtle: tell linjer som avslutter en trippel eller en blokk (godt nok til å se om svaret er tomt)
    return sum(1 for l in tekst.split('\n') if l.strip() and not l.lstrip().upper().startswith(('PREFIX', '@PREFIX')))


def vekk():
    for _ in range(30):
        try:
            urllib.request.urlopen(URL.rsplit('/', 2)[0] + '/$/ping', timeout=20); return
        except Exception:
            time.sleep(5)
    sys.exit('Fuseki svarer ikke på %s' % URL)


def main():
    md = open(os.path.join(REPO, 'docs/bruk.md'), encoding='utf-8').read()
    alle = [('docs/bruk.md:%d' % n, b) for n, b in blokker(md)]
    prefikser = dict(PREFIKS.findall(alle[0][1])) if alle and not SKJEMA.search(alle[0][1]) else {}
    for f in sorted(glob.glob(os.path.join(REPO, 'docs/eksempler/*.rq'))):
        alle.append((os.path.relpath(f, REPO).replace('\\', '/'), open(f, encoding='utf-8').read()))
    vekk()
    feil, testet, hoppet = [], 0, 0
    for sted, b in alle:
        m = SKJEMA.search(b)
        if not m or re.search(r'^\s*#\s*ikke test', b, re.M):
            hoppet += 1; continue
        form = m.group(1).upper()
        egne = {p for p, _ in PREFIKS.findall(b)}
        sporring = ''.join('PREFIX %s: <%s>\n' % (p, u) for p, u in prefikser.items() if p not in egne) + b
        tomt_ok = bool(re.search(r'^\s*#\s*forventer tomt', b, re.M))
        t0 = time.time()
        try:
            n = kjor(sporring, form)
        except urllib.error.HTTPError as e:
            feil.append((sted, 'HTTP %d: %s' % (e.code, e.read().decode('utf-8', 'replace')[:300].strip())))
            print('FEIL  %-32s HTTP %d' % (sted, e.code)); continue
        except Exception as e:
            feil.append((sted, str(e))); print('FEIL  %-32s %s' % (sted, e)); continue
        testet += 1
        ok = (n == 0) if tomt_ok else (n > 0)
        print('%-5s %-32s %s %6d  %.1f s' % ('OK' if ok else 'FEIL', sted, form.ljust(9), n, time.time() - t0))
        if not ok:
            feil.append((sted, 'forventet tomt svar, fikk %d' % n if tomt_ok else 'tomt svar'))
    print('\n%d testet, %d hoppet over (utdrag eller merket), %d feil.' % (testet, hoppet, len(feil)))
    for sted, grunn in feil:
        print('  %s: %s' % (sted, grunn))
    sys.exit(1 if feil else 0)


if __name__ == '__main__':
    main()
