# Idéer: Grep som kunnskapsgraf

Forslag til hvordan sandkassen kan bli en rikere kunnskapsgraf. Fasene 0–4 i
[plan-nattlig-normalisering.md](plan-nattlig-normalisering.md) er ferdige. Dette er neste runde.

Status: 🔜 påbegynt · 💡 idé · ✅ gjort

| # | Idé | Status |
|---|---|---|
| 1 | [Læreplanutsnitt for KI](#1-læreplanutsnitt-for-ki) | ✅ |
| 2 | [Fritekstsøk med jena-text](#2-fritekstsøk-med-jena-text) | 🔜 testet lokalt |
| 3 | [Historikk: hva endret seg?](#3-historikk-hva-endret-seg) | 💡 |
| 4 | [Koblinger til andre kunnskapsgrafer](#4-koblinger-til-andre-kunnskapsgrafer) | 💡 |
| 5 | [SHACL-former](#5-shacl-former) | 💡 |
| 6 | [Beskrivelse av datasettet med DCAT og VoID](#6-beskrivelse-av-datasettet-med-dcat-og-void) | 💡 |
| 7 | [Test eksemplene i bruk.md](#7-test-eksemplene-i-brukmd) | 💡 |
| 8 | [Inverse egenskaper (R6)](#8-inverse-egenskaper-r6) | 💡 |

## 1. Læreplanutsnitt for KI

En løsning som bruker KI på vurderingsdata, trenger «relevant del av læreplanen» i prompten.
Spørringen skal gi et lite og komplett utsnitt for én fagkode og ett trinn:

- læreplanen og versjonen som gjelder (LK06/LK20), med gyldighet;
- kompetansemålene for trinnet;
- kjerneelementene;
- vurderingsteksten;
- gjerne også hva som kom på trinnet før.

Det er GraphRAG i praksis. Grafen sørger for at utsnittet er riktig, og språkmodellen får bare det som
trengs.

✅ 2026-11-09: [eksempler/laereplanutsnitt.rq](eksempler/laereplanutsnitt.rq), dokumentert i bruk.md under
«Læreplanutsnitt for KI». Bare LK20. Kjeden velges ut fra gyldigheten på datoen. Svaret er en graf
(Turtle/JSON-LD) på ca. 16 kB per fagkode, og spørringen tar under ett sekund. Spørringene ligger under
`docs/`, ikke `sparql/`, fordi en push til `sparql/**` starter en innlasting.

Husk: Ikke alle fagkoder har en læreplan. Privatskolekoder, UPF og forsøk mangler det, så utsnittet må
tåle at læreplanen mangler.

## 2. Fritekstsøk med jena-text

Fuseki har en innebygd Lucene-indeks (`text:query`). Med den kan man søke etter tekst i kompetansemål
og andre tekster, i stedet for å bruke `CONTAINS`, som er tregt og ikke tar hensyn til bøyningsformer:

```sparql
?km text:query (u:tittel "kildekritikk") .
```

Det er nyttig for alle som utforsker dataene. For KI er det et første steg mot å finne relevante mål
ut fra fri tekst. Krever endringer i `fuseki/config.ttl`, og indeksen må holdes oppdatert når
rådatagrafen byttes ut hver natt.

🔜 2026-11-09, testet lokalt med to hele innlastinger:
- `text:TextDataset` rundt TDB2 i `fuseki/config.ttl`.
- Feltene er `udir:bokmaalTittel` og `udir:nynorskTittel` (begge med `NorwegianAnalyzer`) og `u:tittel` (med `StandardAnalyzer`).
- `uidField` sørger for at slettede tripler også forsvinner fra indeksen.
- Indeksen er 43 MB, og den var den samme etter andre innlasting, uten duplikater. MOVE tok 85 s lokalt.
- Indeksen fylles først ved neste innlasting etter deploy.
- Dokumentert i bruk.md under «Fritekstsøk».

## 3. Historikk: hva endret seg?

Hver natt erstattes rådataene i sin helhet, så endringene går tapt. Endringsloggen hos Udir
(`/endringer`) kan lagres som tripler i en egen graf, for eksempel med PROV-O. Da kan man spørre om
hvilke læreplaner som er endret siste måned, eller om alt som har skjedd med en bestemt fagkode. Dette
bygger videre på `endret-hos-udir` i metagrafen (2026-11-09).

## 4. Koblinger til andre kunnskapsgrafer

Vi har gjort det for språk med EUs språktabell (R5). De neste kandidatene er:

- **ESCO** (ferdigheter og yrker) for lærefag og yrkesfaglige kompetansemål.
- **SSBs standarder**: STYRK for yrker og NUS for utdanninger.
- **Nasjonalt kvalifikasjonsrammeverk (NKR)** for kompetansenivå.

Dette er det som gjør Grep til en *lenket* graf. Det krever fagavklaring, slik vi gjorde for språk.

## 5. SHACL-former

Formene beskriver hvordan dataene *skal* se ut, for eksempel at en publisert fagkode skal ha et
opplæringsfag med mindre den er en privatskolekode. Avvikssjekkene kan da bygge på formene i stedet for
på egne spørringer. Formene fungerer også som lesbar dokumentasjon av skjemaet, for både mennesker og
språkmodeller. Fuseki kan validere mot SHACL.

## 6. Beskrivelse av datasettet med DCAT og VoID

Metagrafen viser i dag bare noen tall. Med en beskrivelse etter DCAT-AP-NO (som brukes på
data.norge.no) og VoID kunne den også vise lisens, utgiver, hvilke grafer som finnes, hvor mange tripler
det er og hvilke vokabularer som brukes. Det er lite arbeid, og det gjør datasettet lettere å finne.
Hvis Udir senere vil publisere grafen offisielt, er det dette formatet de trenger.

## 7. Test eksemplene i bruk.md

Kjør spørringene i bruk.md mot endepunktet i CI, så eksemplene ikke slutter å virke uten at noen
merker det.

## 8. Inverse egenskaper (R6)

Lag inverse egenskaper som en ny regel via `owl:inverseOf`, slik at man kan gå begge veier i grafen,
for eksempel fra læreplan ned til fagkode, uten å skrive `^u:…`.
