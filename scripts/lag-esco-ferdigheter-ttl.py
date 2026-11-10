"""Lager ontologi/koblinger/esco-ferdigheter.ttl: ESCO-ferdighetene til ESCO-yrkene i esco-yrker.ttl, pluss alle
tverrgående ferdigheter (gjenbruksnivå transversal) utenom språkferdighetene.

ESCO har ikke noe SPARQL-endepunkt, og ferdighetene er for mange til API-et (over 6 000). Last derfor ned ESCO
som Turtle (https://esco.ec.europa.eu/en/use-esco/download: «classification», «ttl»; krever navn og e-post),
gjør den om til N-Triples med Jena RIOT og kjør skriptet med N-Triples-filen og versjonen:

    riot --output=nt esco-v1.2.1.ttl > esco.nt     # RIOT på Windows: rens med  grep -E '^(<|_:)'
    python -I -X utf8 scripts/lag-esco-ferdigheter-ttl.py esco.nt v1.2.1

Filen leses linje for linje, så den kan være stor (v1.2.1 er 1,7 GB som N-Triples). Ut kommer:
- esco:isEssentialSkillFor og esco:isOptionalSkillFor fra ferdighet til yrke, for yrkene i esco-yrker.ttl.
- Hver ferdighet med skos:prefLabel, skos:altLabel og skos:definition på norsk, esco:skillType,
  esco:skillReuseLevel og skos:broader (ferdighetsgrupper og ISCED-F-fagfelt).
- Ferdighetsgruppene over ferdighetene (skos:broader hele veien opp), med norsk navn, og navn på typer og nivåer.

Norsk er «no» i ESCO, men det er bokmål, så her er det @nb. Skriptet skriver ut hva som er endret siden forrige
gang (nye og fjernede ferdigheter og koblinger, endrede navn).
"""
import os, re, sys, collections

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
UT = os.path.join(REPO, 'ontologi/koblinger/esco-ferdigheter.ttl')
SKOS = 'http://www.w3.org/2004/02/skos/core#'
ESCO = 'http://data.europa.eu/esco/model#'
LINJE = re.compile(r'^<([^>]+)> <([^>]+)> (<[^>]+>|"(?:[^"\\]|\\.)*"(?:@[\w-]+|\^\^<[^>]+>)?) \.$')
RELASJONER = {ESCO + 'isEssentialSkillFor', ESCO + 'isOptionalSkillFor'}
TVERRGAAENDE = 'http://data.europa.eu/esco/skill-reuse-level/transversal'
SPRAAKGRUPPER = {  # språkferdighetene (70 språk × 4) og de klassiske språkene tas ikke med som tverrgående
    'http://data.europa.eu/esco/skill/9adca63b-9c75-4804-8dab-d62872540a10',  # beherske språk
    'http://data.europa.eu/esco/skill/43f425aa-f45d-4bb4-a200-6f82fa211b66',  # Språk
    'http://data.europa.eu/esco/skill/e434e71a-f068-44ed-8059-d1af9eb592d7',  # klassiske språk
}


def les(nt, filter_):
    with open(nt, encoding='utf-8') as f:
        for linje in f:
            m = LINJE.match(linje.rstrip('\n'))
            if m and filter_(m.group(1), m.group(2), m.group(3)):
                yield m.group(1), m.group(2), m.group(3)


def main():
    if len(sys.argv) != 3:
        sys.exit('Bruk: lag-esco-ferdigheter-ttl.py <esco.nt> <versjon, for eksempel v1.2.1>')
    nt, versjon = sys.argv[1], sys.argv[2]
    yrker = set(re.findall(r'^<(http://data\.europa\.eu/esco/occupation/[^>]+)>',
                           open(os.path.join(REPO, 'ontologi/koblinger/esco-yrker.ttl'), encoding='utf-8').read(), re.M))

    # 1. Koblingene fra ferdighet til yrkene våre
    koblinger = [(s, p, o[1:-1]) for s, p, o in les(nt, lambda s, p, o: p in RELASJONER and o[1:-1] in yrker)]
    ferdigheter = {s for s, _, _ in koblinger}

    # 1b. Alle tverrgående ferdigheter (gjenbruksnivå transversal), uansett yrke, men uten språkferdighetene.
    #     De er kandidater for kompetansemål som ikke hører til ett yrke (arbeidsliv, etikk, HMS, bærekraft).
    tverr = {s for s, _, _ in les(nt, lambda s, p, o: p == ESCO + 'skillReuseLevel' and o == '<%s>' % TVERRGAAENDE)}
    over = collections.defaultdict(set)
    behov = set(tverr)
    while behov:
        nye = set()
        for s, _, o in les(nt, lambda s, p, o: s in behov and p == SKOS + 'broader'):
            over[s].add(o[1:-1])
            nye.add(o[1:-1])
        behov = nye - set(over) - SPRAAKGRUPPER

    def er_spraak(s, sett=()):
        return any(g in SPRAAKGRUPPER or (g not in sett and er_spraak(g, sett + (s,))) for g in over.get(s, ()))
    tverr = {s for s in tverr if not er_spraak(s)}
    print('tverrgående ferdigheter utenom språk: %d, av dem %d nye' % (len(tverr), len(tverr - ferdigheter)))
    ferdigheter |= tverr

    # 2. Egenskapene til ferdighetene og gruppene over dem. Gruppene finnes ved å følge skos:broader til ingen nye kommer.
    egenskaper = {SKOS + 'prefLabel', SKOS + 'altLabel', SKOS + 'broader', ESCO + 'skillType', ESCO + 'skillReuseLevel',
                  'http://purl.org/dc/terms/description'}
    data = collections.defaultdict(list)
    behov = set(ferdigheter)
    while behov:
        nye = set()
        for s, p, o in les(nt, lambda s, p, o: s in behov and p in egenskaper):
            data[s].append((p, o))
            if p == SKOS + 'broader' and o.startswith('<') and o[1:-1] not in data and o[1:-1] not in behov:
                nye.add(o[1:-1])
        behov = nye - set(data)

    # 3. Norske beskrivelser (egne noder per språk) og navn på typer, nivåer og ISCED-F-fagfelt
    noder = {o[1:-1] for v in data.values() for p, o in v if p.endswith('/description')}
    norsk = set()
    for s, p, o in les(nt, lambda s, p, o: s in noder and p == ESCO + 'language' and o.startswith('"no"')):
        norsk.add(s)
    tekst = {s: o for s, p, o in les(nt, lambda s, p, o: s in norsk and p == ESCO + 'nodeLiteral')}
    andre = {o[1:-1] for v in data.values() for p, o in v if o.startswith('<') and p != 'http://purl.org/dc/terms/description'} - set(data)
    navn = {s: o for s, p, o in les(nt, lambda s, p, o: s in andre and p == SKOS + 'prefLabel' and o.endswith('"@no'))}

    def nb(o):
        return o[:-3] + '@nb' if o.endswith('"@no') else o

    def ren(o):  # fjerner innrykk og linjeskift i ESCO-tekstene
        return '"' + ' '.join(re.sub(r'\\[ntr]', ' ', o[1:o.rindex('"')]).split()) + '"'

    trip = set()
    for s, p, o in koblinger:
        trip.add('<%s> <%s> <%s> .' % (s, p, o))
    for s, v in data.items():
        type_ = '<%s#Skill>' % ESCO[:-1] if '/skill/' in s and s in ferdigheter else '<%sConcept>' % SKOS
        trip.add('<%s> a %s .' % (s, type_))
        trip.add('<%s> a <%sConcept> .' % (s, SKOS))
        for p, o in v:
            if p.endswith('/description'):
                n = o[1:-1]
                if n in tekst:
                    trip.add('<%s> <%sdefinition> %s@nb .' % (s, SKOS, ren(tekst[n])))
            elif p in (SKOS + 'prefLabel', SKOS + 'altLabel'):
                if o.endswith('"@no'):
                    trip.add('<%s> <%s> %s .' % (s, p, nb(o)))
            else:
                trip.add('<%s> <%s> %s .' % (s, p, o))
    for s, o in navn.items():
        trip.add('<%s> <%sprefLabel> %s .' % (s, SKOS, nb(o)))

    gamle = set()
    if os.path.exists(UT):
        gamle = {l for l in open(UT, encoding='utf-8').read().split('\n') if l.startswith('<')}
    linjer = sorted(trip)
    hode = '''# GENERERT av scripts/lag-esco-ferdigheter-ttl.py fra den nedlastede ESCO-klassifikasjonen. Ikke rediger for hånd.
# ESCO-versjon: %s
# Ferdighetene til ESCO-yrkene i esco-yrker.ttl og de tverrgående ferdighetene (utenom språk), med gruppene over dem.
# This service uses the ESCO classification of the European Commission. https://esco.ec.europa.eu
# ENDRET UTGAVE: bare et utdrag av ESCO, og språkkoden er endret fra «no» til «nb». Vilkår: Kommisjonens beslutning
# 2011/833/EU om gjenbruk.
#
# Lastes inn i urn:graph:koblinger av scripts/nattlig-innlasting.sh. Én trippel per linje, sortert, så git diff viser
# nøyaktig hva som er endret mellom ESCO-versjonene.
''' % versjon
    with open(UT, 'w', encoding='utf-8', newline='\n') as f:
        f.write(hode + '\n'.join(linjer) + '\n')

    ferd = lambda ls: {re.match(r'<([^>]+)>', l).group(1) for l in ls if '#Skill>' in l and ' a ' in l}
    print('ESCO %s: %d koblinger fra %d ferdigheter til %d yrker, %d ferdighetsgrupper og fagfelt, %d tripler'
          % (versjon, len(koblinger), len(ferdigheter), len({o for _, _, o in koblinger}),
             len(data) - len(ferdigheter), len(linjer)))
    print('  uten norsk navn: %d, uten norsk beskrivelse: %d' % (
        sum(1 for s in ferdigheter if not any(p == SKOS + 'prefLabel' and o.endswith('"@no') for p, o in data[s])),
        sum(1 for s in ferdigheter if not any(p.endswith('/description') and o[1:-1] in tekst for p, o in data[s]))))
    if gamle:
        ny = set(linjer)
        print('Endringer siden forrige gang: %d tripler lagt til, %d fjernet; %d nye ferdigheter, %d fjernet' % (
            len(ny - gamle), len(gamle - ny), len(ferd(ny) - ferd(gamle)), len(ferd(gamle) - ferd(ny))))


if __name__ == '__main__':
    main()
