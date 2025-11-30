# Upload monitoring files to VM via base64 chunks over IAP with verification
$BasePath = 'G:\My Drive\Automations'
param(
  [string]$RemoteDir = "~/deploy/monitoring/systemd",
  [string]$LocalDir  = (Join-Path $BasePath 'deploy/monitoring/systemd'),
  [int]$ChunkSize = 1000
)

$Files = @(
  "hostamar-uptime-check.service",
  "hostamar-uptime-check.timer",
  "hostamar-tls-expiry-check.service",
  "hostamar-tls-expiry-check.timer",
  "hostamar-uptime-check.sh",
  "hostamar-tls-expiry-check.sh",
  "install_systemd_timers.sh",
  "README.md"
)

function Upload-Base64Verified {
  param(
    [string]$LocalFile,
    [string]$RemoteFile,
    [int]$ChunkSize = 1000
  )
  if (!(Test-Path $LocalFile)) { Write-Warning "Missing: $LocalFile"; return $false }
  Write-Host "Uploading $LocalFile -> $RemoteFile (chunkSize=$ChunkSize)" -ForegroundColor Cyan
  $bytes = [IO.File]::ReadAllBytes($LocalFile)
  $b64   = [Convert]::ToBase64String($bytes)
  $chunks = @()
  for ($i=0; $i -lt $b64.Length; $i += $ChunkSize) {
    $chunks += $b64.Substring($i, [Math]::Min($ChunkSize, $b64.Length - $i))
  }
  ssh hostamar-iap "rm -f $RemoteFile.b64 $RemoteFile" | Out-Null
  $sent=0; $total=$chunks.Count
  foreach ($c in $chunks) {
    $escaped = $c -replace "`$", "`$"
    ssh hostamar-iap "echo $escaped >> $RemoteFile.b64" | Out-Null
    $sent++
    if ($sent % 25 -eq 0) { Write-Host "  Sent $sent/$total chunks" }
  }
  ssh hostamar-iap "base64 -d $RemoteFile.b64 > $RemoteFile && rm $RemoteFile.b64" | Out-Null
  # Verify size + sha256
  $localSize = $bytes.Length
  $localHash = (Get-FileHash -Algorithm SHA256 $LocalFile).Hash.ToLower()
  $remoteSize = (ssh hostamar-iap "wc -c <$RemoteFile").Trim()
  $remoteHash = (ssh hostamar-iap "sha256sum $RemoteFile | awk '{print tolower($1)}'").Trim()
  if ([int]$remoteSize -ne $localSize) {
    Write-Warning "Size mismatch: local=$localSize remote=$remoteSize file=$LocalFile"; return $false }
  if ($remoteHash -ne $localHash) {
    Write-Warning "Hash mismatch: local=$localHash remote=$remoteHash file=$LocalFile"; return $false }
  Write-Host "OK: Verified $LocalFile" -ForegroundColor Green
  return $true
}

Write-Host "[1/5] Ensure remote directory" -ForegroundColor Yellow
ssh hostamar-iap "mkdir -p $RemoteDir"

Write-Host "[2/5] Upload files with verification" -ForegroundColor Yellow
foreach ($f in $Files) {
  $localPath  = Join-Path $LocalDir $f
  $remotePath = "$RemoteDir/$f"
  $ok = Upload-Base64Verified -LocalFile $localPath -RemoteFile $remotePath -ChunkSize $ChunkSize
  if (-not $ok) {
    Write-Host "Retrying $f with smaller chunks (800)" -ForegroundColor Magenta
    $ok = Upload-Base64Verified -LocalFile $localPath -RemoteFile $remotePath -ChunkSize 800
    if (-not $ok) { Write-Error "Failed to upload $f after retry. Aborting."; break }
  }
}

Write-Host "[3/5] Set permissions & install units" -ForegroundColor Yellow
ssh hostamar-iap "cd $RemoteDir && chmod +x hostamar-uptime-check.sh hostamar-tls-expiry-check.sh install_systemd_timers.sh"
ssh hostamar-iap "sudo cp $RemoteDir/hostamar-*.service $RemoteDir/hostamar-*.timer /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable --now hostamar-uptime-check.timer hostamar-tls-expiry-check.timer"

Write-Host "[4/5] Trigger services & show logs" -ForegroundColor Yellow
ssh hostamar-iap "systemctl list-timers --all | grep hostamar || true"
ssh hostamar-iap "sudo systemctl start hostamar-uptime-check.service; sudo journalctl -u hostamar-uptime-check.service -n 20 --no-pager"
ssh hostamar-iap "sudo systemctl start hostamar-tls-expiry-check.service; sudo journalctl -u hostamar-tls-expiry-check.service -n 20 --no-pager"

Write-Host "[5/5] Done." -ForegroundColor Green
Write-Host "Use: ssh hostamar-iap 'journalctl -u hostamar-uptime-check.service -n 10 --no-pager' for follow-up."