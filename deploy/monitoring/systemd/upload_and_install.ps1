# Upload monitoring files to VM via base64 chunks over IAP and install systemd timers

$BasePath = 'G:\My Drive\Automations'
param(
    [string]$RemoteDir = "~/deploy/monitoring/systemd",
    [string]$LocalDir  = (Join-Path $BasePath 'deploy/monitoring/systemd')
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

function Upload-Base64Chunked {
    param(
        [string]$LocalFile,
        [string]$RemoteFile,
        [int]$ChunkSize = 3000
    )
    if (!(Test-Path $LocalFile)) { Write-Warning "Missing: $LocalFile"; return }
    Write-Host "Uploading $LocalFile -> $RemoteFile"
    $bytes = [IO.File]::ReadAllBytes($LocalFile)
    $b64   = [Convert]::ToBase64String($bytes)
    $chunks = @()
    for ($i=0; $i -lt $b64.Length; $i += $ChunkSize) {
        $chunks += $b64.Substring($i, [Math]::Min($ChunkSize, $b64.Length - $i))
    }
    ssh hostamar-iap "rm -f $RemoteFile.b64" | Out-Null
    $sent=0
    foreach ($c in $chunks) {
        $escaped = $c -replace "`$", "`$"
        ssh hostamar-iap "echo $escaped >> $RemoteFile.b64" | Out-Null
        $sent++
        if ($sent % 10 -eq 0) { Write-Host "  Chunks sent: $sent" }
    }
    ssh hostamar-iap "base64 -d $RemoteFile.b64 > $RemoteFile && rm $RemoteFile.b64"
}

Write-Host "[1/4] Ensure remote directory..."
ssh hostamar-iap "mkdir -p $RemoteDir"

Write-Host "[2/4] Upload files..."
foreach ($f in $Files) {
    $localPath  = Join-Path $LocalDir $f
    $remotePath = "$RemoteDir/$f"
    Upload-Base64Chunked -LocalFile $localPath -RemoteFile $remotePath
}

Write-Host "[3/4] Set permissions and install units..."
ssh hostamar-iap "cd $RemoteDir && chmod +x hostamar-uptime-check.sh hostamar-tls-expiry-check.sh install_systemd_timers.sh"
ssh hostamar-iap "sudo cp $RemoteDir/hostamar-*.service $RemoteDir/hostamar-*.timer /etc/systemd/system/ && sudo systemctl daemon-reload && sudo systemctl enable --now hostamar-uptime-check.timer hostamar-tls-expiry-check.timer"

Write-Host "[4/4] Verify and tail logs..."
ssh hostamar-iap "systemctl list-timers --all | grep hostamar || true"
ssh hostamar-iap "sudo systemctl start hostamar-uptime-check.service; sudo journalctl -u hostamar-uptime-check.service -n 20 --no-pager"
ssh hostamar-iap "sudo systemctl start hostamar-tls-expiry-check.service; sudo journalctl -u hostamar-tls-expiry-check.service -n 20 --no-pager"

Write-Host "Done."