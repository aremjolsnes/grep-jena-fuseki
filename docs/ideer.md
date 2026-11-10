# Idéer: Grep som kunnskapsgraf

Forslag til hvordan sandkassen kan bli en rikere kunnskapsgraf. Fasene 0–4 i
[plan-nattlig-normalisering.md](plan-nattlig-normalisering.md) er ferdige. Dette er neste runde.

Status: 🔜 påbegynt · 💡 idé · ✅ gjort

| # | Idé | Status |
|---|---|---|
| 1 | [Læreplanutsnitt for KI](#1-læreplanutsnitt-for-ki) | ✅ |
| 2 | [Fritekstsøk med jena-text](#2-fritekstsøk-med-jena-text) | ✅ |
| 3 | [Historikk: hva endret seg?](#3-historikk-hva-endret-seg) | 💡 satt på vent |
| 4 | [Koblinger til andre kunnskapsgrafer](#4-koblinger-til-andre-kunnskapsgrafer) | 🔜 STYRK ✅, ESCO-yrker ✅, NUS og ISCED ✅, ESCO-ferdigheter 💡, NKR/ELM venter |
| 5 | [SHACL-former](#5-shacl-former) | 💡 |
| 6 | [Beskrivelse av datasettet med DCAT og VoID](#6-beskrivelse-av-datasettet-med-dcat-og-void) | ✅ |
| 7 | [Test eksemplene i bruk.md](#7-test-eksemplene-i-brukmd) | ✅ |
| 8 | [Inverse egenskaper (R6)](#8-inverse-egenskaper-r6) | 💡 |
| 9 | [Demo for KI: fra fagkode til prompt](#9-demo-for-ki-fra-fagkode-til-prompt) | 💡 |
| 10 | [Grunnlag for en veiledning om koblinger](#10-grunnlag-for-en-veiledning-om-koblinger) | 💡 |

Prioritert 2026-11-10: NUS (under 4, ✅ samme dag), så 9, så 10, så SHACL (5). Småting: R6 (8) og de 9 programområdene uten STYRK-kobling.

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

✅ 2026-11-09, i drift fra versjon 32 (0d7d6b0). Testet først lokalt med to hele innlastinger:
- `text:TextDataset` rundt TDB2 i `fuseki/config.ttl`.
- Feltene er `udir:bokmaalTittel` og `udir:nynorskTittel` (begge med `NorwegianAnalyzer`) og `u:tittel` (med `StandardAnalyzer`).
- `uidField` sørger for at slettede tripler også forsvinner fra indeksen.
- Indeksen er 43 MB, og den var den samme etter andre innlasting, uten duplikater. MOVE tok 85 s lokalt.
- Indeksen fylles først ved neste innlasting etter deploy.
- Dokumentert i bruk.md under «Fritekstsøk».
- I prod etter innlastingen: indeksen er 43 MB (databasen 686 MB). «kildekritikk» gir 16 treff, uten duplikater, og søkene svarer på under 0,5 s.

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

✅ 2026-11-09, STYRK-08:
- `udir:yrkesklassifisering` går fra 300 av 309 programområder (Vg3 med `u:yrkestittel`) til STYRK-08, i
  `urn:graph:koblinger`.
- Kilden er `ontologi/koblinger/styrk.csv`. 194 koblinger kommer fra SSBs Yrkeskatalog (KLASS-tabell 426), og
  106 er vurdert manuelt, med ESCO som støtte for 15 av dem.
- 9 programområder er bevisst uten kobling, blant annet fordi riktig gruppe er i hovedgruppe 2.
- Hovedgruppe 1 og 2 brukes aldri, fordi de krever høyere utdanning. Utgåtte programområder er med.
- STYRK-08 har `skos:exactMatch` til ISCO-08 i ESCO for alle koder unntatt de seks norske særkodene. Gruppene vi
  bruker, har 519 ESCO-yrker under seg.
- `scripts/lag-styrk-ttl.py` lager `styrk.ttl`.

✅ 2026-11-10, NUS og ISCED:
- `udir:utdanningsklassifisering` går fra 491 av 497 programområder (alle trinn) til NUS, i `urn:graph:koblinger`.
- Kilden er `ontologi/koblinger/nus.csv`:
  - 421 har samme navn og trinn som i NUS;
  - 29 er privatskolevarianter med samme kode som den vanlige utgaven;
  - 41 er forslag, og 21 av dem er usikre;
  - 6 er uten kobling, for eksempel Reform 94-plassholdere.
- Finnes både ny og gammel ordning i NUS, får utgåtte programområder gammel ordning.
- NUS-kodene har `skos:broadMatch` til ISCED-F 2013 i ESCO (44 fagfelt, alle sjekket) og ISCED 2011 (5 nivåer,
  egne begreper fordi EUs adresser ga tomme svar).
- `scripts/lag-nus-ttl.py` bruker NUS-versjonen som gjelder når skriptet kjøres.
- `scripts/sjekk-koblinger.py` melder hver natt avvik for koder SSB har tatt ut, og for programområder som ikke er
  vurdert. Neste steg kan være at skriptet foreslår koder for nye programområder automatisk.

✅ 2026-11-10, ESCO-yrker:
- ESCO-yrkene under de ISCO-gruppene programområdene er koblet til, også underyrkene, ligger i
  `ontologi/koblinger/esco-yrker.ttl` og i `urn:graph:koblinger`.
- Hvert yrke har norsk navn (`@nb`; ESCO kaller det `no`), norsk beskrivelse, ESCO-kode og `skos:broader`.
- ESCO har ikke noe SPARQL-endepunkt, så yrkene hentes fra API-et med `scripts/lag-esco-ttl.py`. Skriptet kjøres for hånd
  og tar flere minutter.
- `SERVICE` står på i Fuseki, fordi det kan bli nyttig for ELM.

Gjenstår:
- ESCO-ferdigheter. I snitt har hvert yrke 18,5 essensielle og 17 valgfrie, til sammen rundt 26 000 koblinger.
  Først ferdighetene til yrkene, så eventuelt kobling til kompetansemål. Det er et større arbeid.
- Gå gjennom de 21 usikre NUS-forslagene.
- NKR- og EQF-nivå for sluttkompetanse.
- ELM.

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

✅ 2026-11-10:
- Den faste beskrivelsen ligger i `ontologi/datasett.ttl` og lastes inn i `urn:graph:meta`.
- `dcterms:modified` og `void:triples` per graf skrives av innlastingen.
- Utgiveren er Are Mjølsnes, med GitHub-repoet som kontaktpunkt, fordi sandkassen er privat. Udir er oppgitt som kilde.
- Lisensen er NLOD 2.0.

## 7. Test eksemplene i bruk.md

Kjør spørringene i bruk.md mot endepunktet i CI, så eksemplene ikke slutter å virke uten at noen
merker det.

✅ 2026-11-10:
- `scripts/test-eksempler.py` kjører hver ```` ```sparql ````-blokk i bruk.md og hver fil i `docs/eksempler/*.rq`.
- Den feiler ved feil fra endepunktet eller tomt svar.
- Merkene `# forventer tomt` og `# ikke test` endrer hva som testes.
- Kjører som jobben `test-eksempler` i `ingest-data.yml` etter hver innlasting, også de nettene som hoppes over.

## 8. Inverse egenskaper (R6)

Lag inverse egenskaper som en ny regel via `owl:inverseOf`, slik at man kan gå begge veier i grafen,
for eksempel fra læreplan ned til fagkode, uten å skrive `^u:…`.

## 9. Demo for KI: fra fagkode til prompt

Et lite, konkret eksempel på hele kjeden for én elev: fagkode → læreplanutsnitt (LK20, idé 1) →
kompetansemål med kjerneelementer, og eventuelt programområde → STYRK-08 → ESCO-yrker (idé 4). Spørringen finnes
allerede. Det som mangler, er å vise hvordan svaret blir til en prompt. Nyttig til samtaler med folk som jobber med
KI på vurderingsdata.

## 10. Grunnlag for en veiledning om koblinger

Et utkast til en dypere veiledning om koblingene til andre kunnskapsgrafer:

- hva STYRK-08, ISCO-08, ESCO og NUS er;
- hvordan koblingene ble laget: SSBs Yrkeskatalog, manuell vurdering og ESCO som støtte;
- beslutningene: aldri hovedgruppe 1–2, gruppe 3 er greit, utgåtte programområder er med;
- eksempelspørringer.

Med i veiledningen: at «Høyskoleyrker» (hovedgruppe 3 i STYRK-08) beskriver arbeidsoppgavene i yrket, ikke at
yrket krever høyskole.

