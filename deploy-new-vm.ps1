$ErrorActionPreference = "Stop"
$IP = "34.131.107.91"
$User = "romel"
$Key = "C:\Users\romel\.ssh\google_compute_engine"
# Note: In PowerShell, call operators & require variables or paths, so we construct strings carefully for Invoke-Expression or just call directly.
# Simpler to just use the command string for complex SSH.

Write-Host "🚀 Deploying to NEW VM: $IP"

# 1. Archive Source
Write-Host "📦 Archiving Source Code..."
# Check if tar exists, otherwise use python zip? bsdtar is usually there.
tar -czf hostamar-source.tar.gz --exclude node_modules --exclude .next --exclude .git hostamar-platform

# 2. Upload
Write-Host "⬆️  Uploading files..."
scp -i $Key -o StrictHostKeyChecking=no hostamar-source.tar.gz hostamar-platform/deploy/provision-server.sh "$($User)@$($IP):~/"