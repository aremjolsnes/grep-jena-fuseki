# Grep SPARQL Sandbox

Dette prosjektet er satt opp for å teste ut Apache Jena Fuseki som en triple-store for Grep-data.

## Kom i gang (Lokalt)

1. **Start Fuseki**:
   Sørg for at du har Docker installert, og kjør:
   ```bash
   docker-compose up -d
   ```
   Fuseki vil da være tilgjengelig på [http://localhost:3030](http://localhost:3030).

2. **Opprett et Datasett**:
   - Gå til web-grensesnittet.
   - Klikk på "Manage datasets" -> "add new dataset".
   - Gi det navnet `201906`.
   - Velg "Persistent (TDB2)".

3. **Last inn data**:
   Du kan bruke scriptet `ingest.ps1` (for Windows) eller manuelt laste opp JSON-LD filene via UI-et.

## Arkitektur for Sky (SaaS)

For å kjøre dette i produksjon uten å drifte egen server:

- **Hosting**: Bruk [Fly.io](https://fly.io) til å kjøre det samme Docker-imaget. Det støtter "Volumes" slik at dataene dine ikke forsvinner.
- **Automatisering**: Bruk GitHub Actions for å hente data fra Udir og dytte det inn i Fuseki via HTTP API.

## Eksempel på spørring (Machine-to-Machine)

Når datasettet er opprettet, kan du bruke `curl` som i dag, men mot din nye URL:

```bash
curl -H "Accept:application/json" \
     "http://localhost:3030/201906/query?query=..."
```
