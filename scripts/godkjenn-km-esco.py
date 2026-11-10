"""Fører vurderingene fra utfylte arbeidslister (CSV) inn i SSSOM-filene for kompetansemål ↔ ESCO.

    python -I -X utf8 scripts/godkjenn-km-esco.py forslag/km-esco-bkf03-02.csv [flere.csv ...]
    python -I -X utf8 scripts/godkjenn-km-esco.py --kontrollor "Navn Navnesen" liste.csv
    python -I -X utf8 scripts/godkjenn-km-esco.py --toerrkjoering liste.csv     # vis hva som ville skjedd

Arbeidslistene er de som scripts/foreslaa-km-esco.py lager. Kolonnen «vurdert» styrer hva som skjer med raden:
- Ja (ja, j, x, 1, yes): kontrolløren settes som reviewer_label. Har du endret «relasjon», brukes den nye. Da får
  koblingen en direkte SKOS-trippel i grafen.
- Nei (nei, n, 0, no): raden flyttes fra <læreplan>.sssom.tsv til <læreplan>.avvist.tsv i samme mappe. Den filen
  lastes ikke inn, men avvisningene er nyttige som moteksempler for nye forslag.
- Tom eller noe annet (for eksempel «usikker»): raden står urørt og kan vurderes senere.
En utfylt «kommentar» legges til i SSSOM-kommentaren. Til slutt lages ontologi/koblinger/km-esco.ttl på nytt.

Lagret du fra Excel som vanlig CSV i stedet for «CSV UTF-8», leses filen som Windows-1252.
"""
import argparse, csv, glob, io, os, subprocess, sys
from collections import Counter

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KM_ESCO = os.path.join(REPO, 'ontologi/koblinger/km-esco')
RELASJONER = {'closematch': 'closeMatch', 'narrowmatch': 'narrowMatch', 'broadmatch': 'broadMatch',
              'relatedmatch': 'relatedMatch'}
JA = {'ja', 'j', 'x', '1', 'yes', 'y', 'ok'}
NEI = {'nei', 'n', '0', 'no'}


def les_csv(sti):
    data = open(sti, 'rb').read()
    try:
        tekst = data.decode('utf-8-sig')
    except UnicodeDecodeError:
        tekst = data.decode('cp1252')
    skille = ';' if tekst.split('\n', 1)[0].count(';') >= tekst.split('\n', 1)[0].count(',') else ','
    rader = list(csv.DictReader(io.StringIO(tekst), delimiter=skille))
    mangler = {'kompetansemaal', 'relasjon', 'esco_ferdighet', 'vurdert'} - set(rader[0] if rader else {})
    if mangler:
        sys.exit('%s mangler kolonnene %s' % (sti, ', '.join(sorted(mangler))))
    return rader


class Sssom:
    def __init__(self, fil):
        self.fil = fil
        linjer = open(fil, encoding='utf-8').read().rstrip('\n').split('\n')
        self.hode = [l for l in linjer if l.startswith('#')]
        tabell = [l for l in linjer if l and not l.startswith('#')]
        self.kol = tabell[0].split('\t')
        self.rader = [dict(zip(self.kol, l.split('\t'))) for l in tabell[1:]]
        self.endret = False

    def skriv(self):
        with open(self.fil, 'w', encoding='utf-8', newline='\n') as f:
            f.write('\n'.join(self.hode + ['\t'.join(self.kol)] +
                              ['\t'.join(r.get(k, '') for k in self.kol) for r in self.rader]) + '\n')


def legg_til_avvist(sssom, rad):
    fil = sssom.fil.replace('.sssom.tsv', '.avvist.tsv')
    ny = not os.path.exists(fil)
    with open(fil, 'a', encoding='utf-8', newline='\n') as f:
        if ny:
            f.write('# Forslag som en kontrollør har avvist. Lastes ikke inn i grafen; brukes som moteksempler.\n'
                    '# Kolonnene er de samme som i %s.\n' % os.path.basename(sssom.fil))
            f.write('\t'.join(sssom.kol) + '\n')
        f.write('\t'.join(rad.get(k, '') for k in sssom.kol) + '\n')


def main():
    ap = argparse.ArgumentParser(description=__doc__.split('\n')[0])
    ap.add_argument('lister', nargs='+', help='utfylte arbeidslister (CSV)')
    ap.add_argument('--kontrollor', default='Are Mjølsnes', help='navnet som settes som reviewer_label')
    ap.add_argument('--toerrkjoering', action='store_true', help='vis hva som ville skjedd, uten å skrive')
    a = ap.parse_args()

    filer = {os.path.basename(f): Sssom(f) for f in sorted(glob.glob(os.path.join(KM_ESCO, '*.sssom.tsv')))}
    indeks = {}
    for navn, s in filer.items():
        for r in s.rader:
            indeks[(r['subject_id'], r['object_id'])] = (s, r)

    teller = Counter()
    for sti in a.lister:
        for x in les_csv(sti):
            nokkel = ('grep:' + x['kompetansemaal'].strip(),
                      'escoskill:' + x['esco_ferdighet'].strip().rsplit('/', 1)[-1])
            vurdert = (x.get('vurdert') or '').strip().lower()
            if vurdert not in JA | NEI:
                teller['urørt' if not vurdert else 'urørt (%s)' % vurdert] += 1
                continue
            if nokkel not in indeks:
                print('  finnes ikke i SSSOM (allerede behandlet?): %s ↔ %s' % nokkel)
                teller['ikke funnet'] += 1
                continue
            s, r = indeks[nokkel]
            kommentar = ' '.join((x.get('kommentar') or '').split())
            if vurdert in NEI:
                if kommentar:
                    r['comment'] = (r.get('comment', '') + ' Avvist: ' + kommentar).strip()
                if not a.toerrkjoering:
                    legg_til_avvist(s, r)
                s.rader.remove(r)
                del indeks[nokkel]
                s.endret = True
                teller['avvist'] += 1
                continue
            rel = RELASJONER.get((x.get('relasjon') or '').strip().lower())
            if not rel:
                print('  ukjent relasjon «%s» for %s ↔ %s; hoppet over' % (x.get('relasjon'), *nokkel))
                teller['ukjent relasjon'] += 1
                continue
            if 'skos:' + rel != r['predicate_id']:
                print('  relasjon endret: %s ↔ %s: %s → %s' % (nokkel[0], r['object_label'], r['predicate_id'], 'skos:' + rel))
                r['predicate_id'] = 'skos:' + rel
                teller['relasjon endret'] += 1
            if r.get('reviewer_label') and r['reviewer_label'] != a.kontrollor:
                print('  hadde allerede kontrollør %s: %s ↔ %s' % (r['reviewer_label'], *nokkel))
            r['reviewer_label'] = a.kontrollor
            if kommentar and kommentar not in r.get('comment', ''):
                r['comment'] = (r.get('comment', '') + ' Kontrollør: ' + kommentar).strip()
            s.endret = True
            teller['godkjent'] += 1

    print('Resultat: ' + ', '.join('%s %d' % (k, v) for k, v in sorted(teller.items())))
    endret = [s for s in filer.values() if s.endret]
    if a.toerrkjoering:
        print('Tørrkjøring: ingenting er skrevet (%d filer ville blitt endret).' % len(endret))
        return
    for s in endret:
        s.skriv()
        uvurdert = sum(1 for r in s.rader if not r.get('reviewer_label'))
        print('  %s: %d rader, %d ikke vurdert ennå' % (os.path.basename(s.fil), len(s.rader), uvurdert))
    if endret:
        subprocess.run([sys.executable, '-I', '-X', 'utf8', os.path.join(REPO, 'scripts/lag-km-esco-ttl.py')], check=True)


if __name__ == '__main__':
    main()
