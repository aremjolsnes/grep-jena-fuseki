# Kompetansemål som bygger på læreplaner som ikke gjelder lenger

*Oversikt fra Grep-sandkassen, 12. november 2026. Tallene gjelder Grep-dataene per denne datoen.*

## Kort fortalt

- 15 læreplaner som gjelder i dag, har kompetansemål som **bygger på** mål i en læreplan som **ikke gjelder lenger**. Det gjelder til sammen 333 koblinger.
- Den sannsynlige årsaken er at flere grunnskoleplaner fikk nye versjoner 1. august 2026 (matematikk, samfunnsfag, KRLE og engelsk), uten at koblingene fra videregående ble oppdatert.
- For samfunnsfag, KRLE og engelsk finnes nesten alle de gamle målene med **samme tekst** i den nye versjonen, så koblingene kan trolig flyttes uten faglig vurdering. For matematikk er målene endret, og der trengs en faglig vurdering.

## Hva «bygger på» er

I Grep kan et kompetansemål ha koblingen *bygger på* (`bygger-paa`) til mål på et tidligere trinn eller nivå. Koblingen viser progresjon, for eksempel at et mål i matematikk 1T bygger på et mål om ligningssett fra 10. trinn. Den kan brukes i verktøy for lærere og elever, blant annet for å foreslå hva en elev bør repetere.

Koblingen peker på et bestemt mål i en bestemt versjon av en læreplan. Når en læreplan får en ny versjon, får målene nye koder. Koblinger fra andre læreplaner peker da fortsatt på de gamle målene, til noen oppdaterer dem.

## Hva vi fant

| Læreplan som gjelder i dag | Bygger på (gjelder ikke lenger) | Koblinger | Gjeldende versjon | Delvis oppdatert? |
|---|---|---:|---|---|
| Historie fellesfag (HIS01-03) | Samfunnsfag (SAF01-04) | 67 | SAF01-05 | Nei |
| Historie fellesfag, samisk plan (HIS02-03) | Samfunnsfag samisk (SAF02-04) | 41 | SAF02-05 | Nei |
| Samfunnskunnskap vg1/vg2 (SAK01-01) | Samfunnsfag (SAF01-04) | 23 | SAF01-05 | Nei |
| Samfunnskunnskap, samisk plan (SAK02-01) | Samfunnsfag samisk (SAF02-04) | 24 | SAF02-05 | Nei |
| Geografi fellesfag (GEO01-02) | Samfunnsfag (SAF01-04) | 7 | SAF01-05 | Nei |
| Geografi fellesfag, samisk plan (GEO02-02) | Samfunnsfag samisk (SAF02-04) | 7 | SAF02-05 | Nei |
| Religion og etikk (REL01-02) | KRLE (RLE01-03) | 17 | RLE01-04 | Nei |
| Religion og etikk, samisk plan (REL02-02) | KRLE, samisk plan (RLE02-03) | 19 | RLE02-04 | Nei |
| Matematikk P, vg1 (MAT08-01) | Matematikk 1.–10. (MAT01-05) | 90 | MAT01-06 | Ja, 21 koblinger går til MAT01-06 |
| Matematikk T, vg1 (MAT09-02) | Matematikk 1.–10. (MAT01-05) | 25 | MAT01-06 | Nei |
| Matematikk 2P (MAT05-04) | Matematikk 1.–10. (MAT01-05) | 5 | MAT01-06 | Nei |
| Vg3 blomsterdekoratørfaget, voksne (BLD05-01) | Matematikk 1.–10. (MAT01-05) | 3 | MAT01-06 | Nei |
| Vg3 blomsterdekoratørfaget, voksne (BLD05-01) | Engelsk (ENG01-04) | 3 | ENG01-06 | Nei |
| Engelsk (ENG01-06) | Matematikk 1.–10. (MAT01-05) | 1 | MAT01-06 | Se under |
| Engelsk for elever med tegnspråk (ENG02-06) | Matematikk 1.–10. (MAT01-05) | 1 | MAT01-06 | Se under |

Alle de gjeldende versjonene i kolonnen «Gjeldende versjon» gjelder fra 1. august 2026. MAT09-02 (matematikk T) gjelder også fra 1. august 2026, men peker likevel på MAT01-05.

## Feil eller tilsiktet?

Koblingene kan leses på to måter:

1. **Riktig for overgangskullene.** Elever som går vg1 høsten 2026, hadde MAT01-05 og SAF01-04 på 10. trinn. For dem bygger målene faktisk på de gamle målene.
2. **Feil for alle senere kull.** Fra høsten 2027 kommer elevene fra MAT01-06 og SAF01-05. Da peker koblingene på mål de aldri har hatt.

Grep har én kobling per mål, ikke én per kull. Derfor må det velges hvilken versjon koblingen skal peke på. Vi tror den gjeldende versjonen er det naturlige valget, men det er de fagansvarlige som må avgjøre det.

## Forslag til oppfølging

**A. Samme tekst i ny versjon: kan trolig flyttes uten faglig vurdering**

Vi sammenlignet teksten i de gamle målene med målene i den gjeldende versjonen av samme læreplan:

| Gammel versjon | Ny versjon | Mål det pekes på | Med identisk tekst i ny versjon |
|---|---|---:|---:|
| Samfunnsfag (SAF01-04) | SAF01-05 | 62 | 61 |
| Samfunnsfag samisk (SAF02-04) | SAF02-05 | 62 | 62 |
| KRLE (RLE01-03) | RLE01-04 | 35 | 35 |
| KRLE samisk (RLE02-03) | RLE02-04 | 36 | 36 |
| Engelsk (ENG01-04) | ENG01-06 | 61 | 61 |

Her har målene i praktisk talt alle tilfeller bare fått ny kode. Koblingene kan flyttes til målet med samme tekst. Ett mål i SAF01-04 har endret tekst og må ses på for seg.

**B. Matematikk: krever faglig vurdering**

Bare 17 av 83 mål i MAT01-05 som det pekes på, finnes med samme tekst i MAT01-06. Koblingene fra matematikk P, matematikk T, 2P og blomsterdekoratørfaget må derfor vurderes faglig. Matematikk P (MAT08-01) er allerede delvis oppdatert, og 21 av koblingene peker på MAT01-06.

**C. Enkeltkoblinger som bør sjekkes**

Engelsk (ENG01-06 og ENG02-06) har én kobling hver til matematikk, fra et mål om å lytte til, lese og samtale om enkle tekster og billedbøker (KM13336, KM13431) til et mål om å utforske tall, mengder og telling i lek (KM266, MAT01-05). Det kan være en tilsiktet tverrfaglig kobling, men det kan også være feil kode. Alle de andre koblingene i engelsk peker innenfor engelskfaget.

## Spørsmål til de fagansvarlige

1. Skal «bygger på» peke på den versjonen som gjelder i dag?
2. Kan koblingene i gruppe A flyttes automatisk til målet med samme tekst, eller må hver kobling ses på?
3. Hvem tar den faglige vurderingen i matematikk (gruppe B)?
4. Er koblingen fra engelsk til matematikk (gruppe C) tilsiktet?
5. Bør dette bli en fast rutine når en læreplan får ny versjon? Andre læreplaner kan ha koblinger som peker på den.

## Eksempler

| Mål | Bygger på (gammel versjon) |
|---|---|
| **KM12755** (matematikk T): utforske strategier for å løse ligninger, ligningssystemer og ulikheter og argumentere for tenkemåtene sine | **KM224** (MAT01-05): lage, løse og forklare ligningssett knyttet til praktiske situasjoner |
| **KM348** (matematikk P): utforske og bruke egenskapene ved geometriske figurer, målestokk og trigonometri til å beregne lengder, vinkler og arealer i problemløsing innenfor bygg- og anleggsfag | **KM240** (MAT01-05): utforske, beskrive og argumentere for sammenhenger mellom sidelengdene i trekanter |
| **KM861** (historie): reflektere over hvordan fortiden former oss som mennesker, og hvordan våre fortolkninger av fortiden er preget av nåtidsforståelse og forventninger til framtiden | **KM1664** (SAF01-04): drøfte hvordan framstillinger av fortiden, hendelser og grupper har påvirket og påvirker folks holdninger og handlinger |
| **KM1903** (religion og etikk): presentere og sammenligne noen sentrale trekk ved østlige og vestlige religions- og livssynstradisjoner, inkludert kristendom og islam | **KM1963** (RLE01-03): utforske og presentere sentrale trekk ved kristendom og andre religions- og livssynstradisjoner og deres utbredelse i dag |
| **KM12780** (blomsterdekoratør, voksne): lytte til, forstå og bruke fagterminologi muntlig og skriftlig i arbeidssituasjoner | **KM76** (ENG01-04): lytte til og forstå ord og uttrykk i varianter av engelsk |

## Oppfølging i sandkassen

Sandkassen sjekker dette hver natt. Funnene står i issuen «Avvik i Grep-dataene» i GitHub-repoet grep-jena-fuseki under overskriften «Bygger på læreplan som ikke gjelder». Issuen oppdateres når tallene endrer seg, og avsnittet forsvinner når koblingene er rettet i Grep.

Slik kan du se på koblingene selv i SPARQL-endepunktet til sandkassen (https://grep-fuseki-v3.fly.dev/ds/query). Bytt læreplankode:

```sparql
PREFIX u: <http://psi.udir.no/ontologi/kl06/>
PREFIX udir: <http://psi.udir.no/ontologi/>
PREFIX d: <http://psi.udir.no/kl06/>
SELECT ?mal ?tekst ?byggerPaa ?gammelTekst WHERE {
  ?km u:tilhoerer-laereplan d:MAT09-02 ; u:kode ?mal ; udir:bokmaalTittel ?tekst ;
      u:bygger-paa ?f .
  ?f u:tilhoerer-laereplan d:MAT01-05 ; u:kode ?byggerPaa ; udir:bokmaalTittel ?gammelTekst .
} ORDER BY ?mal
```

Grep-sandkassen er et eksperiment og ikke en tjeneste fra Udir. Grunnlaget for alle tallene er de åpne Grep-dataene.
