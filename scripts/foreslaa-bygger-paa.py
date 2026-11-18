"""Foreslår hvor «bygger på»-koblinger som peker på en utgått læreplan, bør flyttes (se docs/avvik-bygger-paa.md).

    python -I -X utf8 scripts/foreslaa-bygger-paa.py                   # alle filene i docs/avvik-bygger-paa
    python -I -X utf8 scripts/foreslaa-bygger-paa.py --filer HIS01-03_SAF01-04.csv
    python -I -X utf8 scripts/foreslaa-bygger-paa.py --toerrkjoering   # uten API-kall; mål som trenger Claude, står tomme

Filene heter <gjeldende læreplan>_<utgått læreplan>.csv og har kolonnene mal, tekst, byggerPaa, gammelTekst (fra
spørringen i docs/avvik-bygger-paa.md). Skriptet legger til kolonnene lpKode, km, nyTekst og grunnlag:
- lpKode: den gjeldende versjonen av den utgåtte læreplanen (følger u:erstattes-av til en publisert læreplan);
- km og nyTekst: målet i den gjeldende versjonen som koblingen bør flyttes til;
- grunnlag: hvordan forslaget er funnet, i prioritert rekkefølge:
    «gjenbruk-av»  det nye målet er merket som gjenbruk av det gamle i Grep (u:gjenbruk-av), ev. gjennom flere versjoner;
    «samme tekst»  et mål i den nye versjonen har identisk tekst;
    «Claude: …»    forslag fra en språkmodell med begrunnelse; må vurderes faglig.
Et gammelt mål som er delt i to nye, gir to rader. Finnes ikke noe passende mål, står km og nyTekst tomme.
Kolonnen tekst (teksten til målet som bygger på) fylles alltid fra endepunktet.

Målene som trenger Claude, samles i ett kall per utgått læreplan. Svarene lagres i forslag/bygger-paa-<utgått
læreplan>.json og brukes om igjen ved neste kjøring (slett filen for å spørre på nytt). Krever ANTHROPIC_API_KEY når
noe må spørres om. Dataene hentes fra det åpne SPARQL-endepunktet (FUSEKI_QUERY_URL).
"""
import argparse, csv, glob, json, os, re, urllib.parse, urllib.request

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MAPPE = os.path.join(REPO, 'docs/avvik-bygger-paa')
FORSLAG = os.path.join(REPO, 'forslag')
ENDEPUNKT = os.environ.get('FUSEKI_QUERY_URL', 'https://grep-fuseki-v3.fly.dev/ds/query')
MODELL = 'claude-opus-5-5'
PRIS = {'input': 4.00, 'output': 20.00, 'cache_write_1h': 8.00, 'cache_read': 0.20}  # USD per million tokens
PREFIKS = '''PREFIX u: <http://psi.udir.no/ontologi/kl06/>
PREFIX d: <http://psi.udir.no/kl06/>
PREFIX udir: <http://psi.udir.no/ontologi/>
'''
PUBLISERT = 'https://data.udir.no/kl06/v201906/status/status_publisert'
KOLONNER = ['mal', 'tekst', 'byggerPaa', 'gammelTekst', 'lpKode', 'km', 'nyTekst', 'grunnlag']
NYE = KOLONNER[4:]


def sporr(q):
    req = urllib.request.Request(ENDEPUNKT, data=urllib.parse.urlencode({'query': PREFIKS + q}).encode(),
                                 headers={'Accept': 'application/sparql-results+json'})
    with urllib.request.urlopen(req, timeout=300) as r:
        return [{k: v['value'] for k, v in b.items()} for b in json.load(r)['results']['bindings']]


def versjonskjede(gammel):
    """Følger u:erstattes-av fra den utgåtte læreplanen til en publisert: [ENG01-04, ENG01-05, ENG01-06]."""
    kjede = [gammel]
    while True:
        r = sporr('SELECT ?ny ?status WHERE { d:%s u:erstattes-av ?n . ?n u:kode ?ny ; u:status ?status }' % kjede[-1])
        if not r:
            raise RuntimeError('%s erstattes ikke av noen; kjeden så langt: %s' % (kjede[-1], ' → '.join(kjede)))
        if len(r) > 1:
            raise RuntimeError('%s erstattes av flere: %s' % (kjede[-1], ', '.join(x['ny'] for x in r)))
        kjede.append(r[0]['ny'])
        if r[0]['status'] == PUBLISERT:
            return kjede
        if len(kjede) > 6:
            raise RuntimeError('for lang kjede: ' + ' → '.join(kjede))


def kompetansemaal(lp):
    """Målene i en læreplan: kode → {tekst, trinn, gjenbrukAv (koder)}."""
    rader = sporr('''
SELECT ?kode ?tekst ?sett ?gjenbruk WHERE {
  ?km u:tilhoerer-laereplan d:%s ; a u:kompetansemaal_lk20 ; u:kode ?kode ; udir:bokmaalTittel ?tekst .
  OPTIONAL { ?km u:tilhoerer-kompetansemaalsett/udir:bokmaalTittel ?sett }
  OPTIONAL { ?km u:gjenbruk-av/u:kode ?gjenbruk }
}''' % lp)
    km = {}
    for r in rader:
        x = km.setdefault(r['kode'], {'tekst': r['tekst'].strip(), 'trinn': trinn(r.get('sett', '')), 'gjenbrukAv': set()})
        if r.get('gjenbruk'):
            x['gjenbrukAv'].add(r['gjenbruk'])
    return km


def trinn(sett):
    return re.sub(r'^Kompetansemål og vurdering\s*', '', sett).strip()


def gjenbrukskart(kjede, km):
    """Gammelt mål → nye mål i siste versjon, via u:gjenbruk-av gjennom alle versjonene i kjeden."""
    kart = {k: {k} for k in km[kjede[0]]}
    for lp in kjede[1:]:
        neste = {}
        for ny, x in km[lp].items():
            for forrige in x['gjenbrukAv']:
                for gammel, mellom in kart.items():
                    if forrige in mellom:
                        neste.setdefault(gammel, set()).add(ny)
        kart = neste
    return kart


INSTRUKS = '''Du hjelper Utdanningsdirektoratet med å vedlikeholde koblinger mellom kompetansemål i Grep, det norske
læreplanverket. Koblingen «bygger på» går fra et mål i en læreplan på videregående til et mål på et lavere trinn.
En grunnskoleplan har fått ny versjon, og koblingene peker fortsatt på målene i den gamle versjonen. Målene i den
nye versjonen er skrevet om, delt eller slått sammen. Du får de gamle målene det pekes på, og alle målene i den nye
versjonen, begge med trinn.

For hvert gammelt mål: finn det eller de (høyst to) målene i den nye versjonen som dekker det samme faglige
innholdet, slik at en kobling som pekte på det gamle målet, kan flyttes dit. Det nye målet vil som regel stå på
samme trinn, men innhold kan ha blitt flyttet mellom trinn, så se også på nabotrinnene. Velg bare mål som faktisk
dekker innholdet; finnes det ikke, skal listen over nye mål være tom. Gi en kort begrunnelse på bokmål (én setning)
som viser hva som er likt, og hva som eventuelt mangler. Svar for alle de gamle målene.'''

SKJEMA = {
    'type': 'object',
    'properties': {'koblinger': {'type': 'array', 'items': {
        'type': 'object',
        'properties': {'gammel': {'type': 'string'},
                       'nye': {'type': 'array', 'items': {'type': 'string'}},
                       'begrunnelse': {'type': 'string'}},
        'required': ['gammel', 'nye', 'begrunnelse'], 'additionalProperties': False}}},
    'required': ['koblinger'], 'additionalProperties': False,
}


def linjer(km, koder):
    return '\n'.join('%s | %s | %s' % (k, km[k]['trinn'] or '?', km[k]['tekst']) for k in koder)


def kall_claude(gammelLp, nyLp, kmGammel, kmNy, mangler, effort):
    import anthropic
    bruker = ('## Gamle mål i %s som det pekes på (kode | trinn | tekst), %d stykker\n%s\n\n'
              '## Alle mål i den nye versjonen %s (kode | trinn | tekst), %d stykker\n%s\n\n'
              'Foreslå for hvert av de gamle målene hvilke mål i %s koblingene bør flyttes til.'
              % (gammelLp, len(mangler), linjer(kmGammel, mangler), nyLp, len(kmNy), linjer(kmNy, sorted(kmNy)), nyLp))
    with anthropic.Anthropic().beta.messages.stream(
        model=MODELL, max_tokens=32000,
        betas=['server-side-fallback-2026-07-01'], fallbacks='default',
        system=[{'type': 'text', 'text': INSTRUKS}],
        messages=[{'role': 'user', 'content': bruker}],
        output_config={'effort': effort, 'format': {'type': 'json_schema', 'schema': SKJEMA}},
    ) as stream:
        svar = stream.get_final_message()
    if svar.stop_reason != 'end_turn':
        raise RuntimeError('uventet stopp: %s' % svar.stop_reason)
    u = svar.usage
    kostnad = (u.input_tokens * PRIS['input'] + u.output_tokens * PRIS['output'] +
               (u.cache_creation_input_tokens or 0) * PRIS['cache_write_1h'] +
               (u.cache_read_input_tokens or 0) * PRIS['cache_read']) / 1e6
    tekst = next(b.text for b in svar.content if b.type == 'text')
    return {'modell': svar.model, 'gammelLp': gammelLp, 'nyLp': nyLp, 'kostnadUsd': round(kostnad, 4),
            'tokens': {'inn': u.input_tokens, 'ut': u.output_tokens},
            'koblinger': json.loads(tekst)['koblinger']}


def claude_forslag(gammelLp, nyLp, kmGammel, kmNy, mangler, a):
    """Forslag fra Claude for målene som verken gjenbruk-av eller identisk tekst dekker; lagres i forslag/."""
    sti = os.path.join(FORSLAG, 'bygger-paa-%s.json' % gammelLp)
    lagret = json.load(open(sti, encoding='utf-8')) if os.path.exists(sti) else None
    har = {k['gammel'] for k in lagret['koblinger']} if lagret else set()
    nye = sorted(k for k in mangler if k not in har)
    if nye and not a.toerrkjoering:
        print('%s: spør Claude om %d mål som ikke finnes igjen i %s ...' % (gammelLp, len(nye), nyLp))
        svar = kall_claude(gammelLp, nyLp, kmGammel, kmNy, nye, a.effort)
        svar['koblinger'] = (lagret['koblinger'] if lagret else []) + svar['koblinger']
        if lagret:
            svar['kostnadUsd'] = round(svar['kostnadUsd'] + lagret.get('kostnadUsd', 0), 4)
        lagret = svar
        os.makedirs(FORSLAG, exist_ok=True)
        with open(sti, 'w', encoding='utf-8') as f:
            json.dump(lagret, f, ensure_ascii=False, indent=1)
        print('  svar fra %s, kostnad %.3f USD, lagret i %s' % (svar['modell'], svar['kostnadUsd'], os.path.relpath(sti, REPO)))
    elif nye:
        print('%s: tørrkjøring, %d mål ville blitt sendt til Claude' % (gammelLp, len(nye)))
    ut = {}
    for k in (lagret['koblinger'] if lagret else []):
        ukjent = [n for n in k['nye'] if n not in kmNy]
        if ukjent:
            print('  ADVARSEL: Claude foreslo mål som ikke finnes i %s: %s' % (nyLp, ', '.join(ukjent)))
        ut[k['gammel']] = ([n for n in k['nye'] if n in kmNy][:2], k['begrunnelse'])
    return ut


def les(sti):
    with open(sti, encoding='utf-8-sig', newline='') as f:
        return list(csv.DictReader(f))


def skriv(sti, rader):
    with open(sti, 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.DictWriter(f, fieldnames=KOLONNER, lineterminator='\n')
        w.writeheader()
        w.writerows(rader)


def analyser(sti, km_cache):
    """Leser en fil og finner forslag via gjenbruk-av og identisk tekst; returnerer det som gjenstår for Claude."""
    navn = os.path.basename(sti)
    lp, gammelLp = navn[:-4].split('_')
    kjede = versjonskjede(gammelLp)
    nyLp = kjede[-1]
    for x in [lp] + kjede:
        if x not in km_cache:
            km_cache[x] = kompetansemaal(x)
    kmGammel, kmNy = km_cache[gammelLp], km_cache[nyLp]
    gjenbruk = gjenbrukskart(kjede, km_cache)
    tekst_til_ny = {}
    for k, x in kmNy.items():
        tekst_til_ny.setdefault(x['tekst'], []).append(k)

    # Radene kan ha forslagskolonnene fra en tidligere kjøring: slå dem sammen til én rad per kobling.
    rader, sett = [], set()
    for r in les(sti):
        if (r['mal'], r['byggerPaa']) not in sett:
            sett.add((r['mal'], r['byggerPaa']))
            if r['mal'] in km_cache[lp]:  # kolonnen tekst hentes alltid fra endepunktet
                r['tekst'] = km_cache[lp][r['mal']]['tekst']
            rader.append(r)
    print('%s: %s (%d koblinger)' % (navn, ' → '.join(kjede), len(rader)))

    forslag, mangler = {}, []
    for g in dict.fromkeys(r['byggerPaa'] for r in rader):
        if g not in kmGammel:
            print('  ADVARSEL: %s finnes ikke i %s' % (g, gammelLp))
            forslag[g] = ([], 'målet finnes ikke i %s' % gammelLp)
        elif gjenbruk.get(g):
            forslag[g] = (sorted(gjenbruk[g]), 'gjenbruk-av')
        elif kmGammel[g]['tekst'] in tekst_til_ny:
            forslag[g] = (tekst_til_ny[kmGammel[g]['tekst']], 'samme tekst')
        else:
            mangler.append(g)
    return {'sti': sti, 'navn': navn, 'gammelLp': gammelLp, 'nyLp': nyLp, 'rader': rader, 'forslag': forslag,
            'mangler': mangler}


def skriv_fil(f, kmNy):
    ut, telling = [], {}
    for r in f['rader']:
        nye, grunn = f['forslag'].get(r['byggerPaa'], ([], ''))
        kategori = grunn.split(':')[0] if nye else ('uten forslag' if grunn else 'ikke spurt')
        telling[kategori] = telling.get(kategori, 0) + 1
        basis = {k: r.get(k, '') for k in KOLONNER[:4]}
        if not nye:
            ut.append({**basis, 'lpKode': f['nyLp'], 'km': '', 'nyTekst': '', 'grunnlag': grunn})
        for n in nye:
            ut.append({**basis, 'lpKode': f['nyLp'], 'km': n, 'nyTekst': kmNy[n]['tekst'], 'grunnlag': grunn})
    skriv(f['sti'], ut)
    print('%s: %d rader; koblinger etter grunnlag: %s'
          % (f['navn'], len(ut), ', '.join('%s %d' % kv for kv in sorted(telling.items()))))


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--filer', help='kommaseparert liste med filnavn i docs/avvik-bygger-paa (ellers alle)')
    ap.add_argument('--effort', default='high', choices=['low', 'medium', 'high', 'xhigh', 'max'])
    ap.add_argument('--toerrkjoering', action='store_true', help='ikke kall Claude; bruk bare lagrede svar')
    a = ap.parse_args()
    stier = ([os.path.join(MAPPE, f) for f in a.filer.split(',')] if a.filer
             else sorted(glob.glob(os.path.join(MAPPE, '*_*.csv'))))
    km_cache = {}
    filer = [analyser(s, km_cache) for s in stier]

    # Ett Claude-kall per utgått læreplan, for alle målene som gjenstår på tvers av filene.
    per_lp = {}
    for f in filer:
        if f['mangler']:
            x = per_lp.setdefault(f['gammelLp'], {'nyLp': f['nyLp'], 'mangler': set()})
            x['mangler'].update(f['mangler'])
    for gammelLp, x in per_lp.items():
        svar = claude_forslag(gammelLp, x['nyLp'], km_cache[gammelLp], km_cache[x['nyLp']], x['mangler'], a)
        for f in filer:
            if f['gammelLp'] == gammelLp:
                for g in f['mangler']:
                    if g in svar:
                        f['forslag'][g] = (svar[g][0], 'Claude: ' + svar[g][1])
    for f in filer:
        skriv_fil(f, km_cache[f['nyLp']])


if __name__ == '__main__':
    main()
