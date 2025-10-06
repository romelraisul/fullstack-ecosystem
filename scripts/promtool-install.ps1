param(
    [string]$Version = "2.55.1"
)

$ErrorActionPreference = 'Stop'
$binDir = Join-Path -Path $PSScriptRoot -ChildPath '..\bin'
$newExe = Join-Path $binDir 'promtool.exe'

Write-Host "Installing promtool version $Version (Windows)"
if (-Not (Test-Path $binDir)) { New-Item -ItemType Directory -Path $binDir | Out-Null }

if (Test-Path $newExe) {
    Write-Host "promtool.exe already exists at $newExe"
    Write-Host "Re-download? (y/N)"
    $resp = Read-Host
    if ($resp -notin @('y', 'Y')) { Write-Host 'Skipping'; exit 0 }
}

$zipName = "prometheus-$Version.windows-amd64.zip"
$downloadUrl = "https://github.com/prometheus/prometheus/releases/download/v$Version/$zipName"
$tmpZip = Join-Path $env:TEMP $zipName
$tmpExtract = Join-Path $env:TEMP "prometheus-$Version.windows-amd64"

Write-Host "Downloading $downloadUrl"
Invoke-WebRequest -Uri $downloadUrl -OutFile $tmpZip -UseBasicParsing

if (Test-Path $tmpExtract) { Remove-Item $tmpExtract -Recurse -Force }
Expand-Archive -Path $tmpZip -DestinationPath $env:TEMP -Force

Copy-Item (Join-Path $tmpExtract 'promtool.exe') $newExe -Force
Remove-Item $tmpZip -Force
Remove-Item $tmpExtract -Recurse -Force

Write-Host "promtool installed to $newExe"

# Add optional PATH guidance
if ($env:PATH -notlike "*\\bin*") {
    Write-Host 'Tip: Add the repo bin directory to PATH for easier usage.'
}
