# Idéer: Grep som kunnskapsgraf

Forslag til hvordan sandkassen kan bli en rikere kunnskapsgraf. Fasene 0–4 i
[plan-nattlig-normalisering.md](plan-nattlig-normalisering.md) er ferdige. Dette er neste runde.

Status: 🔜 påbegynt · 💡 idé · ✅ gjort

| # | Idé | Status |
|---|---|---|
| 1 | [Læreplanutsnitt for AI](#1-læreplanutsnitt-for-ai) | ✅ |
| 2 | [Fritekstsøk med jena-text](#2-fritekstsøk-med-jena-text) | ✅ |
| 3 | [Historikk: hva endret seg?](#3-historikk-hva-endret-seg) | 💡 satt på vent |
| 4 | [Koblinger til andre kunnskapsgrafer](#4-koblinger-til-andre-kunnskapsgrafer) | 🔜 STYRK ✅, ESCO-yrker ✅, NUS og ISCED ✅, ESCO-ferdigheter ✅, kompetansemål ↔ ferdigheter ✅ Vg3-yrkesfag, fellesfag/SF 💡, NKR/ELM venter |
| 5 | [SHACL-former](#5-shacl-former) | 💡 |
| 6 | [Beskrivelse av datasettet med DCAT og VoID](#6-beskrivelse-av-datasettet-med-dcat-og-void) | ✅ |
| 7 | [Test eksemplene i bruk.md](#7-test-eksemplene-i-brukmd) | ✅ |
| 8 | [Inverse egenskaper (R6)](#8-inverse-egenskaper-r6) | 💡 |
| 9 | [Demo for AI: fra fagkode til prompt](#9-demo-for-ai-fra-fagkode-til-prompt) | ✅ |
| 10 | [Grunnlag for en veiledning om koblinger](#10-grunnlag-for-en-veiledning-om-koblinger) | 💡 |

Prioritert 2026-11-10: NUS (under 4, ✅ samme dag), så 9, så 10, så SHACL (5). Småting: R6 (8) og de 9 programområdene uten STYRK-kobling.

## 1. Læreplanutsnitt for AI

En løsning som bruker AI på vurderingsdata, trenger «relevant del av læreplanen» i prompten.
Spørringen skal gi et lite og komplett utsnitt for én fagkode og ett trinn:

- læreplanen og versjonen som gjelder (LK06/LK20), med gyldighet;
- kompetansemålene for trinnet;
- kjerneelementene;
- vurderingsteksten;
- gjerne også hva som kom på trinnet før.

Det er GraphRAG i praksis. Grafen sørger for at utsnittet er riktig, og språkmodellen får bare det som
trengs.

✅ 2026-11-09: [eksempler/laereplanutsnitt.rq](eksempler/laereplanutsnitt.rq), dokumentert i bruk.md under
«Læreplanutsnitt for AI». Bare LK20. Kjeden velges ut fra gyldigheten på datoen. Svaret er en graf
(Turtle/JSON-LD) på ca. 16 kB per fagkode, og spørringen tar under ett sekund. Spørringene ligger under
`docs/`, ikke `sparql/`, fordi en push til `sparql/**` starter en innlasting.

✅ 2026-11-11, utvidet: vurderingsordningen, grunnleggende ferdigheter og tverrfaglige temaer (med læreplanens
tekst om hva de betyr i faget), verbene (lokale verb overstyrer globale med samme navn) og forklaringen av målet
(«didaktisk støtte»). Testet for grunnskolen (hvert årstrinn), fellesfag og SF-programfag: 42–70 kB som
N-Triples, ca. 29 kB som Turtle for MAT0015. Lærdom om ytelse i Jena: ingen OPTIONAL rundt hele kompetansemålet,
og ingen oppslag i egne OPTIONAL-blokker på variabler som kan være ubundet (se kommentaren øverst i spørringen).

Husk: Ikke alle fagkoder har en læreplan. Privatskolekoder, UPF og forsøk mangler det, så utsnittet må
tåle at læreplanen mangler.

## 2. Fritekstsøk med jena-text

Fuseki har en innebygd Lucene-indeks (`text:query`). Med den kan man søke etter tekst i kompetansemål
og andre tekster, i stedet for å bruke `CONTAINS`, som er tregt og ikke tar hensyn til bøyningsformer:

```sparql
?km text:query (u:tittel "kildekritikk") .
```

Det er nyttig for alle som utforsker dataene. For AI er det et første steg mot å finne relevante mål
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
  - 41 er forslag; de 21 usikre er vurdert av et menneske 2026-11-11 (metoden «manuell»);
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

✅ 2026-11-10, ESCO-ferdigheter:
- ESCO v1.2.1 er lastet ned (classification, ttl; nedlastingen krever navn og e-post). Den ligger ikke i repoet.
- `scripts/lag-esco-ferdigheter-ttl.py` leser N-Triples-filen linje for linje og henter ut ferdighetene til yrkene våre.
  Resultatet er 26 650 koblinger fra 6 486 ferdigheter, med 932 ferdighetsgrupper og fagfelt, til sammen 82 234 tripler.
  10.11: Alle 120 tverrgående ferdigheter (utenom språk) er lagt til, også de uten yrke: 6 606 ferdigheter og
  82 663 tripler.
  Alle har norsk navn og beskrivelse.
- Filen har én trippel per linje og er sortert, så `git diff` viser endringene mellom ESCO-versjonene. Skriptet skriver
  også en oppsummering av endringene.
- `sjekk-koblinger.py esco-versjon` melder hver natt et avvik når ESCO har en nyere versjon.
- Vilkårene for gjenbruk er oppfylt: kildesetningen står der den skal, og den endrede utgaven er merket.

✅ 2026-11-10, pilot: kompetansemål ↔ ESCO-ferdigheter for BMK03-03 (Vg3 bilfaget, lette kjøretøy):
- 22 kompetansemål og 185 kandidater (ferdighetene til de 10 ESCO-yrkene under ISCO 7231).
- En språkmodell (Claude) foreslo 95 koblinger, og et menneske godkjente alle.
- Relasjonene er 5 closeMatch, 53 narrowMatch, 1 broadMatch og 36 relatedMatch. Ett mål, KM8657 om partssamarbeid,
  har ingen kandidat.
- Kilden er SSSOM (`ontologi/koblinger/km-esco/BMK03-03.sssom.tsv`). `scripts/lag-km-esco-ttl.py` lager
  `sssom:Mapping`-noder og direkte SKOS-tripler.
- bruk.md har spørringer for hull i begge retninger:
  - kompetansemål uten ESCO-ferdighet;
  - essensielle ESCO-ferdigheter uten kompetansemål.
- Plan for automatiske forslag i andre fag: kandidatene er ferdighetene til ESCO-yrkene til programområdet, pluss
  tverrgående ferdigheter. Vurderingene fra piloten brukes som fasit og som eksempler. Først 2–3 piloter fra andre
  utdanningsprogram (for eksempel helsefag og elektro), og så skalering med menneskelig kontroll.

✅ 2026-11-10, pilot 2 og 3 med samme metode og uten tilpasning: HEA03-03 (helsearbeiderfaget, 82 koblinger) og
ELE03-04 (elektrikerfaget, 85 koblinger). Et menneske godkjente alle 262 forslagene i de tre pilotene, så
presisjonen er høy. Dekningen er ikke målt. Arbeidslivsmålene, som partssamarbeid og bedriftsdemokrati, står uten
kandidat i alle tre læreplanene. De trenger tverrgående ESCO-ferdigheter, og de er ikke med blant kandidatene ennå.

✅ 2026-11-10, dekning: en stikkprøve på 199 kandidater som ikke ble valgt, fra 25 kompetansemål i de tre
læreplanene. Et menneske vurderte alle og mente at 23 burde vært med (12 %):
- 14 relatedMatch, 5 broadMatch, 4 narrowMatch og ingen closeMatch. Det som manglet, var kanttilfeller, ikke
  ferdigheter som er det samme som målet.
- De 23 er lagt til i SSSOM-filene med en kommentar om at de kommer fra stikkprøven.
- Arbeidslivsmålene fikk heller ikke noe treff i stikkprøven.
- Metoden har et hull: kandidatene er bare ferdighetene til yrkene. KM5469 (ergonomi i helsearbeiderfaget) hadde
  derfor ingen kobling, selv om ESCO har *arbeide ergonomisk*. Den ferdigheten står ikke på yrkene til
  helsearbeideren. Den er nå lagt inn for hånd som closeMatch, sammen med én til for KM12873 (relatedMatch,
  *oppgi informasjon om solcellepaneler*).
- Til sammen er det nå 287 godkjente koblinger.

✅ 2026-11-10, tverrgående ferdigheter: ESCOs 120 tverrgående ferdigheter (utenom språk) er lagt til i grafen og som
kandidater for alle kompetansemål. En språkmodell foreslo 54 koblinger i de tre læreplanene (28 relatedMatch,
22 narrowMatch, 2 closeMatch og 2 broadMatch), og et menneske godkjente alle. Nå har alle arbeidslivsmålene en
kobling, for eksempel KM8657 og KM5451 ↔ *utøve rettigheter og ansvar* og KM5470 ↔ *løse konflikter* (closeMatch).
Til sammen er det 341 koblinger.

✅ 2026-11-11, alle Vg3-læreplanene: de 223 gjeldende Vg3-læreplanene med STYRK-kobling har koblinger, til sammen
23 940 (454 vurdert av et menneske, 23 486 automatiske).
- `scripts/foreslaa-km-esco.py` og workflowen «Foreslå koblinger kompetansemål ↔ ESCO» (startes manuelt) laget
  forslagene, med de vurderte koblingene som eksempler. Workflowen committer rett på main som SSSOM uten kontrollør.
  Den deler kø (concurrency-gruppe) med innlastingen, fordi kompetansemålene leses fra endepunktet.
- Prøven 10.11: 963 forslag for 8 læreplaner (PR #2), 3,48 USD. Deretter seks puljer 11.11. Til sammen kostet det
  om lag 82 USD, eller 0,37–0,46 USD per læreplan.
- Stikkprøve: 50 tilfeldige automatiske koblinger fra 50 ulike læreplaner. Alle var riktige, så minst 93 % av de
  automatiske koblingene er riktige (95 % konfidensintervall).
- ESCO har ingen yrker under ISCO 7549 (blomsterdekoratør). Det nærmeste, 5223.7.18 *spesialisert selger, blomster og
  hage*, er et salgsyrke og ble valgt bort. BLD03-03 og BLD05-01 er derfor koblet bare til de tverrgående
  ferdighetene (`--bare-tverrgaaende`).
- `scripts/godkjenn-km-esco.py` fører vurderingene fra utfylte arbeidslister inn: Ja gir kontrollør, Nei flytter
  raden til `<læreplan>.avvist.tsv`. Godkjente rader blir nye eksempler, og avviste blir moteksempler i neste kjøring.

Gjenstår:
- Fellesfag og studieforberedende fag ↔ ESCO. Så langt er bare Vg3-yrkesfag koblet, fordi kandidatene kommer fra
  yrkene (programområde → STYRK → ESCO-yrke). Studieforberedende programområder har ingen yrker (aldri hovedgruppe
  1–2), så kandidatene må komme fra andre steder i ESCO:
  - kunnskapsbegreper (`skill-type/knowledge`), som *matematikk*, *fysikk*, *historie* og *samfunnsfag*, gjerne
    valgt via fagfeltet (programområde → NUS → ISCED-F, eller fagets eget fagfelt);
  - de tverrgående ferdighetene, som vi allerede har;
  - språkferdighetene, som er holdt utenfor så langt, for norsk, engelsk og fremmedspråk.

  ESCO har ingen nivåer, så «matematikk» er det samme på 1. trinn og på master. Vent derfor mest `relatedMatch` og
  `broadMatch`. Utdraget vårt må utvides med kunnskapsbegrepene som ikke henger på noe yrke. Start med en pilot på
  noen få fellesfag (for eksempel matematikk, norsk og naturfag), vurdert av et menneske, slik vi gjorde for
  yrkesfagene.
- Eventuelt fritekstsøk (jena-text) i ferdighetsnavnene.
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

## 9. Demo for AI: fra fagkode til prompt

Et lite, konkret eksempel på hele kjeden for én elev: fagkode → læreplanutsnitt (LK20, idé 1) →
kompetansemål med kjerneelementer, og eventuelt programområde → STYRK-08 → ESCO-yrker (idé 4). Spørringen finnes
allerede. Det som mangler, er å vise hvordan svaret blir til en prompt. Nyttig til samtaler med folk som jobber med
AI på vurderingsdata.

✅ 2026-11-12: skriptet `lag_prompt.py` i et eget, privat søskenprosjekt (`laereplan-prompt`). Skriptet gjør dette:
- henter [eksempler/laereplanutsnitt.rq](eksempler/laereplanutsnitt.rq) herfra og setter inn fagkode og
  vurderingsdato;
- gjør Turtle om til Markdown;
- setter sammen en prompt av systemprompt, utsnitt og oppdiktede vurderingsdata for én elev;
- viser prompten, eller sender den til Claude med `--kall`.

Testet med elever i matematikk 10. trinn og 1T: ca. 10 000 tokens inn og rundt 0,15 USD per kall. Svarene viser
til kompetansemål med kode, leser verbene slik Udir forklarer dem, skiller mellom det dataene viser og det modellen
tolker, peker på hull i vurderingsgrunnlaget og foreslår mål fra tidligere trinn via `u:bygger-paa`.

Datoen avgjør hvilken læreplanversjon som brukes. Da kommer også avviket der `bygger-paa` peker på læreplaner som
ikke gjelder, til syne: forslagene for 1T peker på mål i MAT01-05, se [avvik-bygger-paa.md](avvik-bygger-paa.md).

ESCO-delen er ikke med, fordi demoen gjelder fellesfag og studieforberedende.

## 10. Grunnlag for en veiledning om koblinger

Et utkast til en dypere veiledning om koblingene til andre kunnskapsgrafer:

- hva STYRK-08, ISCO-08, ESCO og NUS er;
- hvordan koblingene ble laget: SSBs Yrkeskatalog, manuell vurdering og ESCO som støtte;
- beslutningene: aldri hovedgruppe 1–2, gruppe 3 er greit, utgåtte programområder er med;
- eksempelspørringer.

Med i veiledningen: at «Høyskoleyrker» (hovedgruppe 3 i STYRK-08) beskriver arbeidsoppgavene i yrket, ikke at
yrket krever høyskole.

