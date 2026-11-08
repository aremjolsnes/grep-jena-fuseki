# Endringslogg: ontologi_kl06_rettet.ttl

Generert 2026-11-06 av `scripts/rett_ontologi.py` fra `ontologi_kl06_20240523.ttl`, med bruksstatistikk fra `https://grep-fuseki-v3.fly.dev/ds/query`.

Se docstringen i skriptet for reglene. Egenskaper som ikke er nevnt her, er uendret.

50 egenskaper endret.

## u:aarstimer
- rdfs:range: xsd:string (observert i data: xsd:string). Var: xsd:integer
- rdfs:range: xsd:integer (B4: verdiene gjøres om av sparql/normalisering/02-datatyper.ru). Var: xsd:string

## u:aarstimer-doeve-og-tunghoerte
- rdfs:range: xsd:string (observert i data: xsd:string). Var: xsd:integer
- rdfs:range: xsd:integer (B4: verdiene gjøres om av sparql/normalisering/02-datatyper.ru). Var: xsd:string

## u:aarstimer-formgivningsfag
- rdfs:range: xsd:string (observert i data: xsd:string). Var: xsd:integer
- rdfs:range: xsd:integer (B4: verdiene gjøres om av sparql/normalisering/02-datatyper.ru). Var: xsd:string

## u:aarstimer-samisk
- rdfs:range: xsd:string (observert i data: xsd:string). Var: xsd:integer
- rdfs:range: xsd:integer (B4: verdiene gjøres om av sparql/normalisering/02-datatyper.ru). Var: xsd:string

## u:bygger-paa
- rdfs:range: unionOf(u:Kompetansemaal_lk20, u:Kompetansemaalsett_lk20) (lagt til fra data: u:Kompetansemaal_lk20). Var: u:Kompetansemaalsett_lk20

## u:bygger-paa-fag
- rdfs:range: unionOf(u:Fagkode, u:Opplaeringsfag) (lagt til fra data: u:Opplaeringsfag). Var: u:Fagkode

## u:fastsatt-dato
- rdfs:range: xsd:string (observert i data: xsd:string). Var: xsd:dateTime
- rdfs:range: xsd:dateTime (B4: verdiene gjøres om av sparql/normalisering/02-datatyper.ru). Var: xsd:string

## u:grep-type
- rdfs:domain: fjernet (generell egenskap, brukt på/deklarert for 44 klasser). Var: u:Aarstrinn, u:Fagkategori, u:Fagkode, u:Fagomraade, u:Fagtype, u:Grunnleggende_ferdighet_lk20, u:Hovedomraade, u:Karakter, u:Kjerneelement_lk20, u:Kompetansemaal, u:Kompetansemaal_lk20, u:Kompetansemaalsett, u:Kompetansemaalsett_lk20, u:Laereplan, u:Laereplan_lk20, u:Merkelapp, u:Merknad, u:Opplaeringsfag, u:Opplaeringsnivaa, u:Ordforklaring_lk20, u:Programfag, u:Programomraade, u:Semester, u:Spraak, u:Spraaknivaa, u:Status, u:Tidligere_navn, u:Tverrfaglig_tema_lk20, u:Utdanningsprogram, u:Verb_lk20
- endret fra owl:DatatypeProperty til owl:ObjectProperty (49642 IRI-verdier, 0 literaler i data)
- rdfs:range: fjernet datatype-rekkevidde xsd:anyURI (objektene er IRI-er)
- rdfs:range: fjernet (49642 av 49642 forekomster mangler type i data). Var: –

## u:grunnleggende-ferdigheter-digitale
- rdfs:domain: unionOf(u:Laereplan, u:Laereplan_lk20) (lagt til fra data: u:Laereplan_lk20). Var: u:Laereplan

## u:grunnleggende-ferdigheter-lese
- rdfs:domain: unionOf(u:Laereplan, u:Laereplan_lk20) (lagt til fra data: u:Laereplan_lk20). Var: u:Laereplan

## u:grunnleggende-ferdigheter-muntlig
- rdfs:domain: unionOf(u:Laereplan, u:Laereplan_lk20) (lagt til fra data: u:Laereplan_lk20). Var: u:Laereplan

## u:grunnleggende-ferdigheter-regne
- rdfs:domain: unionOf(u:Laereplan, u:Laereplan_lk20) (lagt til fra data: u:Laereplan_lk20). Var: u:Laereplan

## u:gyldig-fra
- rdfs:domain: fjernet (30825 av 38110 forekomster mangler type i data). Var: u:Fagkode, u:Laereplan, u:Laereplan_lk20, u:Merknad
- rdfs:range: xsd:string (observert i data: xsd:string). Var: xsd:dateTime
- rdfs:range: xsd:dateTime (B4: verdiene gjøres om av sparql/normalisering/02-datatyper.ru). Var: xsd:string

## u:gyldig-til
- rdfs:domain: fjernet (22004 av 26062 forekomster mangler type i data). Var: u:Fagkode, u:Laereplan, u:Laereplan_lk20, u:Merknad
- rdfs:range: xsd:string (observert i data: xsd:string). Var: xsd:dateTime
- rdfs:range: xsd:dateTime (B4: verdiene gjøres om av sparql/normalisering/02-datatyper.ru). Var: xsd:string

## u:hoeyeste-nivaa
- brukes ikke i data (beholdt, eventuelle flere domener/rekkevidder slått sammen til union)

## u:id
- rdfs:domain: fjernet (generell egenskap, brukt på/deklarert for 44 klasser). Var: u:Aarstrinn, u:Fagkategori, u:Fagkode, u:Fagomraade, u:Fagtype, u:Grunnleggende_ferdighet_lk20, u:Hovedomraade, u:Karakter, u:Kjerneelement_lk20, u:Kompetansemaal, u:Kompetansemaal_lk20, u:Kompetansemaalsett, u:Kompetansemaalsett_lk20, u:Laereplan, u:Laereplan_lk20, u:Merkelapp, u:Merknad, u:Opplaeringsfag, u:Opplaeringsnivaa, u:Ordforklaring_lk20, u:Programfag, u:Programomraade, u:Semester, u:Spraak, u:Spraaknivaa, u:Status, u:Tidligere_navn, u:Tverrfaglig_tema_lk20, u:Utdanningsprogram, u:Verb_lk20

## u:iso-639-2-kode
- rdfs:range: xsd:string (observert i data: xsd:string). Var: xsd:anyURI

## u:kode
- rdfs:domain: fjernet (generell egenskap, brukt på/deklarert for 44 klasser). Var: u:Aarstrinn, u:Fagkategori, u:Fagkode, u:Fagomraade, u:Fagtype, u:Grunnleggende_ferdighet_lk20, u:Hovedomraade, u:Karakter, u:Kjerneelement_lk20, u:Kompetansemaal, u:Kompetansemaal_lk20, u:Kompetansemaalsett, u:Kompetansemaalsett_lk20, u:Laereplan, u:Laereplan_lk20, u:Merkelapp, u:Merknad, u:Opplaeringsfag, u:Opplaeringsnivaa, u:Ordforklaring_lk20, u:Programfag, u:Programomraade, u:Semester, u:Spraak, u:Spraaknivaa, u:Status, u:Tidligere_navn, u:Tverrfaglig_tema_lk20, u:Utdanningsprogram, u:Verb_lk20

## u:kortform
- rdfs:domain: fjernet (generell egenskap, brukt på/deklarert for 20 klasser). Var: u:Aarstrinn, u:Fagkategori, u:Fagkode, u:Fagtype, u:Kompetansemaalsett_lk20, u:Laereplan_lk20, u:Merknad, u:Opplaeringsfag, u:Programomraade, u:Semester, u:Spraaknivaa, u:Utdanningsprogram

## u:laaereplanstruktur
- brukes ikke i data (beholdt, eventuelle flere domener/rekkevidder slått sammen til union)

## u:merknad-bruksomraade
- rdfs:range: xsd:string (observert i data: xsd:string). Var: rdf:langString

## u:numerisk-verdi
- rdfs:domain: unionOf(u:Aarstrinn, u:Fagkode) (lagt til fra data: u:Aarstrinn). Var: u:Fagkode

## u:omfang-til-naa
- rdfs:range: xsd:string (observert i data: xsd:string). Var: xsd:integer
- rdfs:range: xsd:integer (B4: verdiene gjøres om av sparql/normalisering/02-datatyper.ru). Var: xsd:string

## u:omfang-totalt
- rdfs:range: xsd:string (observert i data: xsd:string). Var: xsd:integer
- rdfs:range: xsd:integer (B4: verdiene gjøres om av sparql/normalisering/02-datatyper.ru). Var: xsd:string

## u:omfang-vitnemaal
- lagt til som owl:DatatypeProperty (brukes i data, mangler i originalen)
- rdfs:domain: u:Fagkode (lagt til fra data: u:Fagkode). Var: –
- rdfs:range: xsd:string (observert i data: xsd:string). Var: 
- rdfs:range: xsd:integer (B4: verdiene gjøres om av sparql/normalisering/02-datatyper.ru). Var: xsd:string

## u:omfang-vitnemål
- brukes ikke i data (beholdt, eventuelle flere domener/rekkevidder slått sammen til union)

## u:opplaaeringssted
- brukes ikke i data (beholdt, eventuelle flere domener/rekkevidder slått sammen til union)

## u:opplaeringstid
- rdfs:range: xsd:string (observert i data: xsd:string). Var: xsd:float
- rdfs:range: xsd:decimal (B4: verdiene gjøres om av sparql/normalisering/02-datatyper.ru). Var: xsd:string

## u:rekkefoelge
- rdfs:domain: fjernet (generell egenskap, brukt på/deklarert for 30 klasser). Var: u:Aarstrinn, u:Fagtype, u:Grunnleggende_ferdighet_lk20, u:Kjerneelement_lk20, u:Kompetansemaal_lk20, u:Kompetansemaalsett_lk20, u:Opplaeringsnivaa, u:Ordforklaring_lk20, u:Semester, u:Spraak, u:Spraaknivaa, u:Tverrfaglig_tema_lk20, u:Verb_lk20

## u:sist-endret
- rdfs:domain: fjernet (generell egenskap, brukt på/deklarert for 41 klasser). Var: u:Fagkategori, u:Fagkode, u:Fagomraade, u:Grunnleggende_ferdighet_lk20, u:Kjerneelement_lk20, u:Kompetansemaal, u:Kompetansemaal_lk20, u:Kompetansemaalsett_lk20, u:Laereplan, u:Laereplan_lk20, u:Merkelapp, u:Opplaeringsfag, u:Ordforklaring_lk20, u:Programomraade, u:Tidligere_navn, u:Tverrfaglig_tema_lk20, u:Utdanningsprogram, u:Verb_lk20
- rdfs:range: xsd:string (observert i data: xsd:string). Var: xsd:dateTime
- rdfs:range: xsd:dateTime (B4: verdiene gjøres om av sparql/normalisering/02-datatyper.ru). Var: xsd:string

## u:siste-eksamen
- rdfs:range: xsd:string (observert i data: xsd:string). Var: xsd:dateTime
- rdfs:range: xsd:dateTime (B4: verdiene gjøres om av sparql/normalisering/02-datatyper.ru). Var: xsd:string

## u:soekehjelp-navn-motsatt-maalform
- rdfs:range: xsd:string (observert i data: xsd:string). Var: rdf:langString

## u:status
- rdfs:domain: fjernet (generell egenskap, brukt på/deklarert for 42 klasser). Var: u:Aarstrinn, u:Dokumenttype, u:Eksamensform, u:Eksamensordning, u:Fagkategori, u:Fagkode, u:Fagomraade, u:Fagtype, u:Grunnleggende_ferdighet_lk20, u:Karakter, u:Kjerneelement_lk20, u:Kompetansemaal, u:Kompetansemaal_lk20, u:Kompetansemaalsett_lk20, u:Laereplan, u:Laereplan_lk20, u:Laereplanstruktur, u:Loepstype, u:Merkelapp, u:Merknad, u:Merknadstype, u:Oppgave, u:Opplaeringsfag, u:Opplaeringsnivaa, u:Opplaeringssted, u:Ordforklaring_lk20, u:Programfag, u:Programomraade, u:Programomraadetype, u:Semester, u:Sensur, u:Sluttkompetanse, u:Spraak, u:Spraaknivaa, u:Status, u:Tidligere_navn, u:Trekkordning, u:Tverrfaglig_tema_lk20, u:Utdanningsprogram, u:Utdanningsprogramtype, u:Verb_lk20, u:Vurderingsuttrykk
- rdfs:range: fjernet (46383 av 46383 forekomster mangler type i data). Var: u:Status

## u:tilhoerer-laereplan
- rdfs:domain: unionOf(u:Kjerneelement_lk20, u:Kompetansemaal, u:Kompetansemaal_lk20, u:Kompetansemaalsett, u:Kompetansemaalsett_lk20, u:Ordforklaring_lk20, u:Verb_lk20) (lagt til fra data: u:Kjerneelement_lk20). Var: u:Kompetansemaal, u:Kompetansemaal_lk20, u:Kompetansemaalsett, u:Kompetansemaalsett_lk20, u:Ordforklaring_lk20, u:Verb_lk20

## u:tilknyttede-fag
- rdfs:range: unionOf(u:Fagkode, u:Opplaeringsfag) (lagt til fra data: u:Opplaeringsfag). Var: u:Fagkode

## u:tilleggsopplysninger
- rdfs:range: rdfs:Literal (observert i data: rdf:langString, xsd:string). Var: rdf:langString

## u:tittel
- rdfs:domain: fjernet (generell egenskap, brukt på/deklarert for 35 klasser). Var: u:Aarstrinn, u:Fagkategori, u:Fagkode, u:Fagomraade, u:Fagtype, u:Grunnleggende_ferdighet_lk20, u:Hovedomraade, u:Karakter, u:Kjerneelement_lk20, u:Kompetansemaal, u:Kompetansemaal_lk20, u:Kompetansemaalsett, u:Kompetansemaalsett_lk20, u:Laereplan, u:Laereplan_lk20, u:Merkelapp, u:Merknad, u:Opplaeringsfag, u:Ordforklaring_lk20, u:Programfag, u:Programomraade, u:Semester, u:Spraak, u:Spraaknivaa, u:Status, u:Tidligere_navn, u:Tverrfaglig_tema_lk20, u:Utdanningsprogram, u:Verb_lk20

## u:tverrfaglige-temaer
- rdfs:domain: unionOf(u:Kompetansemaal_lk20, u:Laereplan_lk20) (lagt til fra data: u:Laereplan_lk20). Var: u:Kompetansemaal_lk20

## u:underliggende-hovedomraader
- rdfs:domain: unionOf(u:Hovedomraade, u:Programfag) (lagt til fra data: u:Hovedomraade). Var: u:Programfag

## u:uri
- rdfs:domain: fjernet (generell egenskap, brukt på/deklarert for 44 klasser). Var: u:Aarstrinn, u:Fagkategori, u:Fagkode, u:Fagomraade, u:Fagtype, u:Grunnleggende_ferdighet_lk20, u:Hovedomraade, u:Karakter, u:Kjerneelement_lk20, u:Kompetansemaal, u:Kompetansemaal_lk20, u:Kompetansemaalsett, u:Kompetansemaalsett_lk20, u:Laereplan, u:Laereplan_lk20, u:Merkelapp, u:Merknad, u:Opplaeringsfag, u:Opplaeringsnivaa, u:Ordforklaring_lk20, u:Programfag, u:Programomraade, u:Semester, u:Spraak, u:Spraaknivaa, u:Status, u:Tidligere_navn, u:Tverrfaglig_tema_lk20, u:Utdanningsprogram, u:Verb_lk20
- endret fra owl:DatatypeProperty til owl:ObjectProperty (49642 IRI-verdier, 0 literaler i data)
- rdfs:range: fjernet datatype-rekkevidde xsd:anyURI (objektene er IRI-er)
- rdfs:range: fjernet (generell egenskap, brukt på/deklarert for 44 klasser). Var: –

## u:url-data
- rdfs:domain: fjernet (generell egenskap, brukt på/deklarert for 44 klasser). Var: u:Aarstrinn, u:Fagkategori, u:Fagkode, u:Fagomraade, u:Fagtype, u:Grunnleggende_ferdighet_lk20, u:Hovedomraade, u:Karakter, u:Kjerneelement_lk20, u:Kompetansemaal, u:Kompetansemaal_lk20, u:Kompetansemaalsett, u:Kompetansemaalsett_lk20, u:Laereplan, u:Laereplan_lk20, u:Merkelapp, u:Merknad, u:Opplaeringsfag, u:Opplaeringsnivaa, u:Ordforklaring_lk20, u:Programfag, u:Programomraade, u:Semester, u:Spraak, u:Spraaknivaa, u:Status, u:Tidligere_navn, u:Tverrfaglig_tema_lk20, u:Utdanningsprogram, u:Verb_lk20
- endret fra owl:DatatypeProperty til owl:ObjectProperty (49642 IRI-verdier, 0 literaler i data)
- rdfs:range: fjernet datatype-rekkevidde xsd:anyURI (objektene er IRI-er)
- rdfs:range: fjernet (49642 av 49642 forekomster mangler type i data). Var: –

## u:verdiskapingstid
- rdfs:range: xsd:string (observert i data: xsd:string). Var: xsd:float
- rdfs:range: xsd:decimal (B4: verdiene gjøres om av sparql/normalisering/02-datatyper.ru). Var: xsd:string

## u:vurderingsordning
- brukes ikke i data (beholdt, eventuelle flere domener/rekkevidder slått sammen til union)

## u:vurderingsordning-eksemen-for-elever
- brukes ikke i data (beholdt, eventuelle flere domener/rekkevidder slått sammen til union)

## u:vurderingsordning-eksemen-for-privatister
- brukes ikke i data (beholdt, eventuelle flere domener/rekkevidder slått sammen til union)

## u:vurderingsordning-halvaarsvurdering-2-benyttes-ved-inntak-til-hoeyere-trinn-VIGO-privatist
- rdfs:range: xsd:boolean (observert i data: xsd:boolean). Var: xsd:anyURI

## u:vurderingsordning-standpunktvurdering
- brukes ikke i data (beholdt, eventuelle flere domener/rekkevidder slått sammen til union)

## u:vurderingsordning-trekkordning-elev
- endret fra owl:DatatypeProperty til owl:ObjectProperty (5394 IRI-verdier, 0 literaler i data)
- rdfs:range: fjernet datatype-rekkevidde xsd:anyURI (objektene er IRI-er)
- rdfs:range: u:Trekkordning (lagt til fra data: u:Trekkordning). Var: –

## u:vurderingsordning-trekkordning-privatist
- endret fra owl:DatatypeProperty til owl:ObjectProperty (3960 IRI-verdier, 0 literaler i data)
- rdfs:range: fjernet datatype-rekkevidde xsd:anyURI (objektene er IRI-er)
- rdfs:range: u:Trekkordning (lagt til fra data: u:Trekkordning). Var: –

## u:vurderingsordninger-kapittel
- brukes ikke i data (beholdt, eventuelle flere domener/rekkevidder slått sammen til union)
