# Hostamar Platform Setup Script
$ErrorActionPreference = 'Stop'
$BasePath = 'G:\My Drive\Automations'
$projectPath = Join-Path $BasePath 'hostamar-platform'

Write-Host '========================================' -ForegroundColor Cyan
Write-Host 'Hostamar Platform Setup' -ForegroundColor Cyan
Write-Host '========================================' -ForegroundColor Cyan
Write-Host ''

# Navigate
Write-Host '[1/5] Navigating...' -ForegroundColor Yellow
Set-Location $projectPath
Write-Host 'OK' -ForegroundColor Green
Write-Host ''

# Clean
Write-Host '[2/5] Cleaning...' -ForegroundColor Yellow
if (Test-Path '.\node_modules') { Remove-Item -Recurse -Force '.\node_modules' }
if (Test-Path '.\package-lock.json') { Remove-Item -Force '.\package-lock.json' }
if (Test-Path '.\.next') { Remove-Item -Recurse -Force '.\.next' }
Write-Host 'OK' -ForegroundColor Green
Write-Host ''

# Install
Write-Host '[3/5] Installing...' -ForegroundColor Yellow
npm install --legacy-peer-deps
if ($LASTEXITCODE -ne 0) { exit 1 }
Write-Host 'OK' -ForegroundColor Green
Write-Host ''

# Env
Write-Host '[4/5] Creating env...' -ForegroundColor Yellow
$envContent = @'
DATABASE_URL="postgresql://user:password@localhost:5432/hostamar"
GITHUB_TOKEN="your-token-here"
NEXTAUTH_SECRET="change-me"
NEXTAUTH_URL="http://localhost:3000"
'@
if (-not (Test-Path '.\.env.local')) {
    Set-Content -Path '.\.env.local' -Value $envContent
}
Write-Host 'OK' -ForegroundColor Green
Write-Host ''

# Build
Write-Host '[5/5] Building...' -ForegroundColor Yellow
$env:NODE_ENV = 'production'
npm run build
if ($LASTEXITCODE -ne 0) { exit 1 }
Write-Host 'OK' -ForegroundColor Green
Write-Host ''

Write-Host 'Setup Complete!' -ForegroundColor Green
Write-Host 'Run: npm run dev' -ForegroundColor Cyan
Write-Host "Project path: $projectPath" -ForegroundColor Yellow
