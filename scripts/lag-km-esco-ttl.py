"""Lager ontologi/koblinger/km-esco.ttl fra SSSOM-filene i ontologi/koblinger/km-esco/*.sssom.tsv.

    python -I -X utf8 scripts/lag-km-esco-ttl.py

Hver kobling fra kompetansemål til ESCO-ferdighet blir:
- en direkte SKOS-trippel (for eksempel d:KM8640 skos:narrowMatch <ESCO-ferdighet>), slik at det er lett å spørre;
- en egen node (sssom:Mapping) med det SSSOM sier om koblingen: relasjon, begrunnelse, forfatter, kontrollør, verktøy,
  dato, kommentar og hvilket koblingssett (læreplan) den hører til.
Bare koblinger med kontrollør (reviewer_label) får den direkte SKOS-trippelen. Forslag som ikke er vurdert, blir
bare noder.
"""
import glob, os, re

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
SSSOM = 'https://w3id.org/sssom/'


def lit(s):
    return '"' + ' '.join(s.split()).replace('\\', '\\\\').replace('"', '\\"') + '"'


def main():
    ut = ['''# GENERERT av scripts/lag-km-esco-ttl.py fra ontologi/koblinger/km-esco/*.sssom.tsv. Ikke rediger for hånd.
# Grep-sandkassens koblinger fra kompetansemål til ESCO-ferdigheter. Koblingene er ikke en del av ESCO.
# This service uses the ESCO classification of the European Commission. https://esco.ec.europa.eu
#
# Lastes inn i urn:graph:koblinger av scripts/nattlig-innlasting.sh.

@prefix skos:  <http://www.w3.org/2004/02/skos/core#> .
@prefix sssom: <https://w3id.org/sssom/> .
@prefix semapv: <https://w3id.org/semapv/vocab/> .
@prefix dcterms: <http://purl.org/dc/terms/> .
@prefix xsd:   <http://www.w3.org/2001/XMLSchema#> .
''']
    totalt = 0
    for fil in sorted(glob.glob(os.path.join(REPO, 'ontologi/koblinger/km-esco/*.sssom.tsv'))):
        linjer = open(fil, encoding='utf-8').read().split('\n')
        meta = {}
        curie = {}
        for l in linjer:
            m = re.match(r'^#\s+(\w+): (http\S+)$', l)
            if m:
                curie[m.group(1)] = m.group(2)
            m = re.match(r'^# (\w+): (.*)$', l)
            if m:
                meta[m.group(1)] = m.group(2).strip()
        tabell = [l for l in linjer if l and not l.startswith('#')]
        kol = tabell[0].split('\t')
        sett = meta['mapping_set_id']
        ut.append('<%s> a sssom:MappingSet ;\n    dcterms:title %s@nb ;\n    dcterms:license <%s> ;\n'
                  '    sssom:object_source_version %s ;\n    sssom:mapping_date "%s"^^xsd:date .\n'
                  % (sett, lit(meta.get('mapping_set_title', '')), meta['license'],
                     lit(meta.get('object_source_version', '')), meta['mapping_date']))

        def iri(c):
            p, l = c.split(':', 1)
            return '<%s%s>' % (curie[p], l)

        for l in tabell[1:]:
            r = dict(zip(kol, l.split('\t')))
            s_, p_, o_ = iri(r['subject_id']), iri(r['predicate_id']), iri(r['object_id'])
            node = '<%s/%s/%s>' % (sett, r['subject_id'].split(':', 1)[1], r['object_id'].split(':', 1)[1])
            felt = ['%s a sssom:Mapping' % node, 'sssom:mapping_set %s' % ('<%s>' % sett),
                    'sssom:subject_id %s' % s_, 'sssom:predicate_id %s' % p_, 'sssom:object_id %s' % o_,
                    'sssom:mapping_justification %s' % iri(r['mapping_justification'])]
            for k in ('author_label', 'reviewer_label', 'mapping_tool', 'comment'):
                if r.get(k):
                    felt.append('sssom:%s %s' % (k, lit(r[k])))
            ut.append(' ;\n    '.join(felt) + ' .')
            if r.get('reviewer_label'):
                ut.append('%s %s %s .\n' % (s_, p_, o_))
            totalt += 1
    with open(os.path.join(REPO, 'ontologi/koblinger/km-esco.ttl'), 'w', encoding='utf-8', newline='\n') as f:
        f.write('\n'.join(ut) + '\n')
    print('koblinger fra kompetansemål til ESCO-ferdigheter:', totalt)


if __name__ == '__main__':
    main()
