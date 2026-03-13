# ingest.ps1 - Henter Grep-data og laster det inn i Fuseki

$datasetName = "201906"
$fusekiUrl = "http://localhost:3030/$datasetName/data"
$zipUrl = "https://data.udir.no/kl06/v201906/dump/jsonld"
$tempDir = "./temp_data"
$zipFile = "$tempDir/grep_dump.zip"

# 1. Opprett temp-mappe
if (!(Test-Path $tempDir)) { New-Item -ItemType Directory -Path $tempDir }

# 2. Last ned data
Write-Host "Laster ned data fra $zipUrl..."
Invoke-WebRequest -Uri $zipUrl -OutFile $zipFile

# 3. Pakk ut
Write-Host "Pakker ut..."
Expand-Archive -Path $zipFile -DestinationPath $tempDir -Force

# 4. Last opp til Fuseki
# Vi antar at datasettet er opprettet på forhånd.
$files = Get-ChildItem "$tempDir/*.jsonld" -Recurse
foreach ($file in $files) {
    Write-Host "Laster opp $($file.Name)..."
    $content = Get-Content $file.FullName -Raw
    Invoke-RestMethod -Uri $fusekiUrl -Method Post -Body $content -ContentType "application/ld+json"
}

Write-Host "Ferdig!"
