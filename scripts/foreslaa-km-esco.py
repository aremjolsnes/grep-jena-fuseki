"""Foreslår koblinger fra kompetansemål til ESCO-ferdigheter med en språkmodell (Claude) og skriver dem som SSSOM.

    python -I -X utf8 scripts/foreslaa-km-esco.py --antall 8              # 8 læreplaner som ikke har koblinger ennå
    python -I -X utf8 scripts/foreslaa-km-esco.py --laereplaner AKT03-03,ALU03-02
    python -I -X utf8 scripts/foreslaa-km-esco.py --antall 3 --toerrkjoering   # bygger ledetekstene, kaller ikke API-et

Hver læreplan blir ett kall til Claude. Kandidatene er de samme som i pilotene:
- ferdighetene til ESCO-yrkene under ISCO-gruppene programområdet er koblet til (via STYRK-08);
- ESCOs tverrgående ferdigheter (utenom språk).
Eksemplene er alle godkjente koblinger i ontologi/koblinger/km-esco/*.sssom.tsv (fasit fra pilotene).

Ut kommer ontologi/koblinger/km-esco/<læreplan>.sssom.tsv med forslag UTEN kontrollør (reviewer_label). Da blir de
bare sssom:Mapping-noder i grafen, ikke SKOS-tripler, til et menneske har vurdert dem. Skriptet skriver også en
arbeidsliste (CSV, semikolon, UTF-8 med BOM) per læreplan i --arbeidsliste-mappen, til vurdering i Excel.

Krever ANTHROPIC_API_KEY (ikke ved --toerrkjoering). Dataene hentes fra det åpne SPARQL-endepunktet (FUSEKI_QUERY_URL).
"""
import argparse, csv, datetime, glob, json, os, re, sys, urllib.parse, urllib.request
from collections import defaultdict

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KM_ESCO = os.path.join(REPO, 'ontologi/koblinger/km-esco')
ENDEPUNKT = os.environ.get('FUSEKI_QUERY_URL', 'https://grep-fuseki-v3.fly.dev/ds/query')
MODELL = 'claude-opus-5-5'
PRIS = {'input': 4.00, 'output': 20.00, 'cache_write_1h': 8.00, 'cache_read': 0.20}  # USD per million tokens
RELASJONER = ['closeMatch', 'narrowMatch', 'broadMatch', 'relatedMatch']
SPRAAKGRUPPER = [  # samme som i lag-esco-ferdigheter-ttl.py
    'http://data.europa.eu/esco/skill/9adca63b-9c75-4804-8dab-d62872540a10',
    'http://data.europa.eu/esco/skill/43f425aa-f45d-4bb4-a200-6f82fa211b66',
    'http://data.europa.eu/esco/skill/e434e71a-f068-44ed-8059-d1af9eb592d7',
]
PREFIKS = '''PREFIX u: <http://psi.udir.no/ontologi/kl06/>
PREFIX d: <http://psi.udir.no/kl06/>
PREFIX udir: <http://psi.udir.no/ontologi/>
PREFIX skos: <http://www.w3.org/2004/02/skos/core#>
PREFIX esco: <http://data.europa.eu/esco/model#>
'''
PUBLISERT = '<https://data.udir.no/kl06/v201906/status/status_publisert>'


def sporr(q):
    req = urllib.request.Request(ENDEPUNKT, data=urllib.parse.urlencode({'query': PREFIKS + q}).encode(),
                                 headers={'Accept': 'application/sparql-results+json'})
    with urllib.request.urlopen(req, timeout=300) as r:
        return [{k: v['value'] for k, v in b.items()} for b in json.load(r)['results']['bindings']]


def laereplaner():
    """Gjeldende læreplaner for Vg3-programområder med STYRK-kobling, med ISCO-gruppene."""
    rader = sporr('''
SELECT ?lpKode ?lpTittel ?poKode ?poTittel ?isco WHERE {
  ?po a u:Programomraade ; u:aarstrinn d:vg3 ; u:kode ?poKode ; u:status %s ;
      udir:yrkesklassifisering/skos:exactMatch ?isco .
  OPTIONAL { ?po u:tittel ?poTittel FILTER(LANG(?poTittel) IN ("nb", "nob", "")) }
  ?of u:programomraader-referanse ?po ; u:laereplan-referanse ?lp .
  ?lp u:kode ?lpKode ; u:status %s .
  OPTIONAL { ?lp udir:bokmaalTittel ?lpTittel }
}''' % (PUBLISERT, PUBLISERT))
    lp = {}
    for r in rader:
        x = lp.setdefault(r['lpKode'], {'kode': r['lpKode'], 'tittel': r.get('lpTittel', ''), 'programomraader': {},
                                         'isco': set()})
        x['programomraader'][r['poKode']] = r.get('poTittel', '')
        x['isco'].add(r['isco'])
    return lp


def kompetansemaal(lp):
    return sporr('''
SELECT ?kode ?tekst WHERE {
  d:%s u:kompetansemaalsett/u:kompetansemaal ?km . ?km u:kode ?kode ; udir:bokmaalTittel ?tekst .
} ORDER BY ?kode''' % lp)


def ferdigheter_til_yrker(isco):
    verdier = ' '.join('<%s>' % i for i in sorted(isco))
    return sporr('''
SELECT ?f ?navn ?type ?def (COUNT(DISTINCT ?y) AS ?yrker) WHERE {
  VALUES ?isco { %s }
  ?y a esco:Occupation ; skos:broader+ ?isco .
  ?f esco:isEssentialSkillFor|esco:isOptionalSkillFor ?y ; skos:prefLabel ?navn .
  OPTIONAL { ?f skos:definition ?def }
  OPTIONAL { ?f esco:skillType/skos:prefLabel ?type FILTER(LANG(?type) = "nb") }
} GROUP BY ?f ?navn ?type ?def ORDER BY ?f''' % verdier)


def tverrgaaende():
    return sporr('''
SELECT ?f ?navn ?type ?def WHERE {
  ?f a esco:Skill ; esco:skillReuseLevel <http://data.europa.eu/esco/skill-reuse-level/transversal> ; skos:prefLabel ?navn .
  FILTER NOT EXISTS { VALUES ?g { %s } ?f skos:broader+ ?g }
  OPTIONAL { ?f skos:definition ?def }
  OPTIONAL { ?f esco:skillType/skos:prefLabel ?type FILTER(LANG(?type) = "nb") }
} ORDER BY ?f''' % ' '.join('<%s>' % g for g in SPRAAKGRUPPER))


def kort(tekst, n=220):
    tekst = ' '.join((tekst or '').split())
    return tekst if len(tekst) <= n else tekst[:n].rsplit(' ', 1)[0] + ' …'


def typ(t):
    return 'kunnskap' if t and 'kunnskap' in t.lower() else 'ferdighet'


def les_sssom():
    """Alle eksisterende koblinger: {læreplan: [rad]}, og de godkjente som eksempler."""
    alle = {}
    for fil in sorted(glob.glob(os.path.join(KM_ESCO, '*.sssom.tsv'))):
        linjer = [l for l in open(fil, encoding='utf-8').read().split('\n') if l and not l.startswith('#')]
        kol = linjer[0].split('\t')
        alle[os.path.basename(fil).split('.')[0]] = [dict(zip(kol, l.split('\t'))) for l in linjer[1:]]
    return alle


INSTRUKS = '''Du hjelper Utdanningsdirektoratets Grep-sandkasse med å koble kompetansemål i norske læreplaner for
yrkesfag (Vg3) til ferdigheter i ESCO, EUs klassifikasjon av yrker og ferdigheter. Koblingene skal brukes til å finne
hull i begge retninger: kompetansemål uten ESCO-ferdighet, og viktige ESCO-ferdigheter uten kompetansemål. Et menneske
vurderer hvert forslag før det godkjennes, men vurderingen tar tid, så forslagene bør være slike en fagperson ville
stå inne for.

Relasjonen leses fra kompetansemålet (SKOS):
- closeMatch: ferdigheten og målet er omtrent det samme.
- narrowMatch: ferdigheten er en del av målet (vanligst, fordi målene er sammensatte). Gjelder også generelle
  ferdigheter som står i målets ordlyd, for eksempel «feilsøke» på et mål om å feilsøke, «planlegge» på et mål om å
  planlegge arbeidsoppdrag, eller «overholde forskrifter» på et mål om å arbeide i tråd med lovverk.
- broadMatch: ferdigheten er bredere enn målet; målet er et særtilfelle av den (for eksempel «utføre reparasjoner av
  kjøretøy» for et mål om å reparere bremser).
- relatedMatch: ferdigheten er beslektet med målet og nyttig å se sammen med det, men ikke en del av det.

Erfaringer fra vurderingen av pilotene:
- Det som manglet i pilotene, var kanttilfeller (relatedMatch og broadMatch), ikke ferdigheter som er det samme som
  målet. Ta derfor med beslektede ferdigheter når en fagperson ville sett sammenhengen.
- Ikke koble på felles ord alene (for eksempel «montere fremføringsutstyr» til et mål om å montere elanlegg, eller
  «utvikle faglig nettverk» til et mål om datanettverk).
- Hold riktig yrke og objekt: motorsykkel er ikke bil, dekk er ikke bremser, klimaanlegg er ikke bremser.
- «Gjøre rede for» er ikke det samme som å utføre eller diagnostisere. Å føre dokumentasjon er ikke det samme som å
  bruke dokumentasjon.
- Lederoppgaver (planlegge andres arbeid, administrere medarbeidere) hører ikke til mål om eget arbeid.
- Generelle HMS-ferdigheter (renhold, helsefarlige stoffer, lovbestemte kontroller) kan være relatedMatch eller
  narrowMatch på HMS-mål, men ikke på rent tekniske mål.
- Svært generelle ferdigheter (løse problemer, arbeide selvstendig, tenke analytisk) kobles bare når målet handler om
  akkurat det.
- Mål om arbeidsliv, rettigheter, etikk, inkludering, miljø og refleksjon finner ofte sin match blant de tverrgående
  ferdighetene.
- Et mål kan godt stå uten forslag hvis ingen kandidat passer.

Svar bare med kandidater fra listene (bruk id-en, for eksempel F12 eller T7) og koder for kompetansemål fra
læreplanen. Begrunnelsen er én kort setning på bokmål som viser hvorfor relasjonen passer, gjerne med målets egne ord
i «». Ikke foreslå samme par to ganger.'''


def eksempler(alle):
    linjer = []
    for lp, rader in sorted(alle.items()):
        for r in rader:
            if r.get('reviewer_label'):
                linjer.append('%s | %s | %s | %s | %s' % (r['subject_label'], r['predicate_id'].split(':')[1],
                                                           r['object_label'], r['comment'] or '', lp))
    return linjer


def moteksempler():
    """Forslag som en kontrollør har avvist (<læreplan>.avvist.tsv, skrevet av godkjenn-km-esco.py)."""
    linjer = []
    for fil in sorted(glob.glob(os.path.join(KM_ESCO, '*.avvist.tsv'))):
        tabell = [l for l in open(fil, encoding='utf-8').read().split('\n') if l and not l.startswith('#')]
        kol = tabell[0].split('\t')
        for l in tabell[1:]:
            r = dict(zip(kol, l.split('\t')))
            linjer.append('%s | %s | %s | %s' % (r['subject_label'], r['predicate_id'].split(':')[1], r['object_label'],
                                                 r.get('comment', '')))
    return linjer


def system_blokk(alle, tverr):
    """Lik for alle læreplanene i en kjøring, så den kan caches: instruks, eksempler og de tverrgående ferdighetene."""
    eks = eksempler(alle)
    mot = moteksempler()
    tv = ['%s | %s (%s) | %s' % (t['id'], t['navn'], typ(t.get('type')), kort(t.get('def'))) for t in tverr]
    return (INSTRUKS + '\n\n## Godkjente koblinger fra pilotene (kompetansemål | relasjon | ferdighet | kommentar | '
            'læreplan), %d stykker\n' % len(eks) + '\n'.join(eks) +
            ('\n\n## Avviste forslag (kompetansemål | foreslått relasjon | ferdighet | kommentar), %d stykker. Slike '
             'forslag skal du ikke gjenta\n' % len(mot) + '\n'.join(mot) if mot else '') +
            '\n\n## Tverrgående ESCO-ferdigheter (kandidater for alle læreplaner), %d stykker\n' % len(tv) +
            '\n'.join(tv))


def bruker_blokk(lp, km, kand):
    po = '; '.join('%s %s' % (k, t) for k, t in sorted(lp['programomraader'].items()))
    return ('## Læreplan %s %s\nProgramområde: %s. ISCO-grupper: %s.\n\n## Kompetansemål (%d)\n%s\n\n'
            '## ESCO-ferdighetene til yrkene (%d), med antall yrker i gruppen som har ferdigheten\n%s\n\n'
            'Foreslå koblinger fra kompetansemålene til kandidatene (både F- og T-ferdigheter).'
            % (lp['kode'], lp['tittel'], po, ', '.join(sorted(i.rsplit('/', 1)[1] for i in lp['isco'])), len(km),
               '\n'.join('%s | %s' % (k['kode'], k['tekst']) for k in km), len(kand),
               '\n'.join('%s | %s (%s, %s yrker) | %s' % (f['id'], f['navn'], typ(f.get('type')), f['yrker'],
                                                          kort(f.get('def'))) for f in kand)))


SKJEMA = {
    'type': 'object',
    'properties': {'koblinger': {'type': 'array', 'items': {
        'type': 'object',
        'properties': {'kompetansemaal': {'type': 'string'}, 'ferdighet': {'type': 'string'},
                       'relasjon': {'type': 'string', 'enum': RELASJONER}, 'begrunnelse': {'type': 'string'}},
        'required': ['kompetansemaal', 'ferdighet', 'relasjon', 'begrunnelse'], 'additionalProperties': False}}},
    'required': ['koblinger'], 'additionalProperties': False,
}


def kall_claude(klient, system, bruker, effort):
    with klient.beta.messages.stream(
        model=MODELL,
        max_tokens=64000,
        betas=['server-side-fallback-2026-07-01'],
        fallbacks='default',  # avslår sikkerhetsfilteret, prøver API-et en annen modell i samme kall
        system=[{'type': 'text', 'text': system, 'cache_control': {'type': 'ephemeral', 'ttl': '1h'}}],
        messages=[{'role': 'user', 'content': bruker}],
        output_config={'effort': effort, 'format': {'type': 'json_schema', 'schema': SKJEMA}},
    ) as stream:
        svar = stream.get_final_message()
    if svar.stop_reason == 'refusal':
        raise RuntimeError('modellen avslo (%s)' % (svar.stop_details.category if svar.stop_details else '?'))
    if svar.stop_reason == 'max_tokens':
        raise RuntimeError('svaret ble kuttet (max_tokens)')
    tekst = next(b.text for b in svar.content if b.type == 'text')
    return json.loads(tekst)['koblinger'], svar.usage, svar.model


def kostnad(u):
    return ((u.input_tokens * PRIS['input'] + u.output_tokens * PRIS['output'] +
             (u.cache_creation_input_tokens or 0) * PRIS['cache_write_1h'] +
             (u.cache_read_input_tokens or 0) * PRIS['cache_read']) / 1e6)


def skriv_sssom(lp, km, forslag, kand_id, modell, dato):
    tekst = {k['kode']: k['tekst'] for k in km}
    isco = ', '.join(sorted(i.rsplit('/', 1)[1][1:] for i in lp['isco']))
    hode = '''# curie_map:
#   grep: http://psi.udir.no/kl06/
#   escoskill: http://data.europa.eu/esco/skill/
#   skos: http://www.w3.org/2004/02/skos/core#
#   semapv: https://w3id.org/semapv/vocab/
# mapping_set_id: http://psi.udir.no/kl06/kobling/km-esco/{kode}
# mapping_set_title: Kompetansemål i {kode} ({tittel}) koblet til ESCO-ferdigheter
# mapping_set_description: >-
#   Grep-sandkassens koblinger fra kompetansemålene i læreplanen {kode} til ESCO-ferdighetene (v1.2.1) til
#   yrkene under ISCO {isco}, og til ESCOs tverrgående ferdigheter (utenom språk). Forslagene er laget automatisk
#   av en språkmodell ({modell}) med pilotene BMK03-03, HEA03-03 og ELE03-04 som eksempler, med
#   scripts/foreslaa-km-esco.py. Rader uten reviewer_label er ikke vurdert av et menneske ennå. Relasjonen leses fra
#   kompetansemålet: narrowMatch betyr at ferdigheten er en del av målet, broadMatch at den er bredere,
#   relatedMatch at den er beslektet. Koblingene er ikke en del av ESCO. This service uses the ESCO classification
#   of the European Commission.
# license: https://data.norge.no/nlod/no/2.0
# subject_source: http://psi.udir.no/kl06/{kode}
# object_source: http://data.europa.eu/esco/
# object_source_version: v1.2.1
# mapping_date: {dato}
subject_id	subject_label	predicate_id	object_id	object_label	mapping_justification	author_label	reviewer_label	mapping_tool	comment
'''.format(kode=lp['kode'], tittel=lp['tittel'] or lp['kode'], isco=isco, modell=modell, dato=dato)
    rader = []
    for f in forslag:
        k = kand_id[f['ferdighet']]
        rad = ['grep:' + f['kompetansemaal'], tekst[f['kompetansemaal']], 'skos:' + f['relasjon'],
               'escoskill:' + k['f'].rsplit('/', 1)[1], k['navn'], 'semapv:ManualMappingCuration',
               'Claude (språkmodell, forslag)', '', 'Claude (Anthropic) ' + modell,
               'Automatisk forslag (%s). %s' % (dato, ' '.join(f['begrunnelse'].split()))]
        rader.append('\t'.join(c.replace('\t', ' ') for c in rad))
    with open(os.path.join(KM_ESCO, lp['kode'] + '.sssom.tsv'), 'w', encoding='utf-8', newline='\n') as fil:
        fil.write(hode + '\n'.join(rader) + '\n')


def skriv_arbeidsliste(mappe, lp, km, forslag, kand_id):
    os.makedirs(mappe, exist_ok=True)
    tekst = {k['kode']: k['tekst'] for k in km}
    with open(os.path.join(mappe, 'km-esco-%s.csv' % lp['kode'].lower()), 'w', encoding='utf-8-sig', newline='') as f:
        w = csv.writer(f, delimiter=';', lineterminator='\r\n')
        w.writerow(['kompetansemaal', 'km_tekst', 'relasjon', 'ferdighet_navn', 'type', 'vurdert', 'kommentar',
                    'esco_ferdighet', 'forslag_begrunnelse', 'beskrivelse'])
        for x in forslag:
            k = kand_id[x['ferdighet']]
            w.writerow([x['kompetansemaal'], tekst[x['kompetansemaal']], x['relasjon'], k['navn'], typ(k.get('type')),
                        '', '', k['f'], x['begrunnelse'], kort(k.get('def'), 400)])


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('--laereplaner', help='kommaseparert liste med læreplankoder')
    ap.add_argument('--antall', type=int, default=0, help='velg så mange læreplaner uten koblinger, spredt på programområder')
    ap.add_argument('--effort', default='high', choices=['low', 'medium', 'high', 'xhigh', 'max'])
    ap.add_argument('--maks-dollar', type=float, default=10.0, help='stopp før neste læreplan når kostnaden er nådd')
    ap.add_argument('--arbeidsliste', default=os.path.join(REPO, 'forslag'), help='mappe for CSV-arbeidslister')
    ap.add_argument('--toerrkjoering', action='store_true', help='bygg ledetekstene og skriv størrelsen, uten API-kall')
    a = ap.parse_args()

    alle = les_sssom()
    lp_alle = laereplaner()
    if a.laereplaner:
        valgt = [k.strip() for k in a.laereplaner.split(',') if k.strip()]
        ukjent = [k for k in valgt if k not in lp_alle]
        if ukjent:
            sys.exit('Ukjent eller ikke gjeldende Vg3-læreplan med STYRK-kobling: ' + ', '.join(ukjent))
    elif a.antall:
        # Spre utvalget på utdanningsprogram (de to første bokstavene i programområdekoden), én om gangen
        grupper = defaultdict(list)
        for k in sorted(lp_alle):
            if k not in alle:
                grupper[sorted(lp_alle[k]['programomraader'])[0][:2]].append(k)
        valgt = []  # hele køen; løkken i main stopper når --antall læreplaner er behandlet
        while any(grupper.values()):
            for g in sorted(grupper):
                if grupper[g]:
                    valgt.append(grupper[g].pop(0))
    else:
        sys.exit('Oppgi --laereplaner eller --antall.')
    finnes = [k for k in valgt if k in alle]
    if finnes:
        sys.exit('Har allerede koblinger (slett filen først hvis du vil lage nye forslag): ' + ', '.join(finnes))

    tverr = tverrgaaende()
    for i, t in enumerate(tverr, 1):
        t['id'] = 'T%d' % i
    system = system_blokk(alle, tverr)
    kun_antall = a.antall and not a.laereplaner
    print('Læreplaner: %s%s' % (', '.join(valgt[:a.antall] if kun_antall else valgt),
                                ' (og flere i køen hvis noen hoppes over)' if kun_antall else ''))
    print('Systemblokk (caches): %d tegn, %d eksempler, %d tverrgående' % (len(system), len(eksempler(alle)), len(tverr)))

    klient = None
    if not a.toerrkjoering:
        global anthropic
        import anthropic
        klient = anthropic.Anthropic()
    dato = datetime.date.today().isoformat()
    total = 0.0
    oppsummering = []
    behandlet = 0
    tomme_paa_rad = 0  # læreplaner på rad uten kompetansemål; flere tyder på at Grep-dataene mangler (innlasting pågår?)
    for kode in valgt:
        if kun_antall and behandlet >= a.antall:
            break
        if total >= a.maks_dollar:
            print('Stopper: kostnaden (%.2f USD) har nådd grensen %.2f USD.' % (total, a.maks_dollar))
            break
        lp = lp_alle[kode]
        km = kompetansemaal(kode)
        if not km:  # ingen fil skrives, så læreplanen blir med i køen neste gang
            tomme_paa_rad += 1
            print('\n%s: hoppet over, fant ingen kompetansemål' % kode)
            oppsummering.append((kode, 'ingen kompetansemål', '-', 0.0))
            if tomme_paa_rad >= 3:
                print('::error::Stopper: %d læreplaner på rad uten kompetansemål. Grep-dataene ser ut til å mangle '
                      'i endepunktet (pågår innlastingen?). Kjør på nytt når den er ferdig.' % tomme_paa_rad)
                break
            continue
        tomme_paa_rad = 0
        kand = ferdigheter_til_yrker(lp['isco'])
        for i, f in enumerate(kand, 1):
            f['id'] = 'F%d' % i
        kand_id = {f['id']: f for f in kand + tverr}
        if not kand:  # ingen ESCO-yrker under ISCO-gruppen: bare tverrgående kandidater, det gir for lite
            print('\n%s: hoppet over, ingen ESCO-yrker under %s'
                  % (kode, ', '.join(sorted(i.rsplit('/', 1)[1] for i in lp['isco']))))
            oppsummering.append((kode, 'ingen ESCO-yrker', '-', 0.0))
            continue
        behandlet += 1
        bruker = bruker_blokk(lp, km, kand)
        print('\n%s: %d kompetansemål, %d yrkesferdigheter, brukerblokk %d tegn' % (kode, len(km), len(kand), len(bruker)))
        if a.toerrkjoering:
            continue
        try:
            forslag, usage, modell = kall_claude(klient, system, bruker, a.effort)
        except (anthropic.AuthenticationError, anthropic.PermissionDeniedError, anthropic.NotFoundError) as e:
            sys.exit('Stopper: %s: %s' % (type(e).__name__, e))  # nøkkel eller modell er feil; gjelder alle læreplanene
        except Exception as e:  # én læreplan som feiler, skal ikke stoppe resten
            print('  FEIL: %s: %s' % (type(e).__name__, e))
            oppsummering.append((kode, 'feil', 0, 0.0))
            continue
        kmkoder = {k['kode'] for k in km}
        gyldige, sett = [], set()
        for f in forslag:
            par = (f['kompetansemaal'], f['ferdighet'])
            if f['kompetansemaal'] not in kmkoder or f['ferdighet'] not in kand_id or par in sett:
                print('  forkastet ugyldig eller dobbelt forslag: %s' % json.dumps(f, ensure_ascii=False))
                continue
            sett.add(par)
            gyldige.append(f)
        gyldige.sort(key=lambda f: (f['kompetansemaal'], RELASJONER.index(f['relasjon']), kand_id[f['ferdighet']]['navn']))
        skriv_sssom(lp, km, gyldige, kand_id, modell, dato)
        skriv_arbeidsliste(a.arbeidsliste, lp, km, gyldige, kand_id)
        k = kostnad(usage)
        total += k
        uten = len(kmkoder - {f['kompetansemaal'] for f in gyldige})
        print('  %d forslag (%s), %d mål uten forslag; tokens inn %d, cache skrevet %d, cache lest %d, ut %d; %.3f USD'
              % (len(gyldige), ', '.join('%d %s' % (sum(1 for f in gyldige if f['relasjon'] == r), r) for r in RELASJONER),
                 uten, usage.input_tokens, usage.cache_creation_input_tokens or 0, usage.cache_read_input_tokens or 0,
                 usage.output_tokens, k))
        oppsummering.append((kode, len(gyldige), uten, k))
    if not a.toerrkjoering:
        print('\nTotalt: %.2f USD' % total)
        utfil = os.environ.get('GITHUB_STEP_SUMMARY')
        if utfil:
            with open(utfil, 'a', encoding='utf-8') as f:
                f.write('| Læreplan | Forslag | Mål uten forslag | USD |\n|---|---|---|---|\n')
                for kode, n, uten, k in oppsummering:
                    f.write('| %s | %s | %s | %.3f |\n' % (kode, n, uten, k))
                f.write('\nTotalt: %.2f USD\n' % total)
        if oppsummering and all(n == 'feil' for _, n, _, _ in oppsummering if n != 'ingen ESCO-yrker'):
            sys.exit('Alle kallene feilet.')


if __name__ == '__main__':
    main()
