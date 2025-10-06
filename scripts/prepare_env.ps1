# Initialize local environment after reboot
# Usage:  powershell -ExecutionPolicy Bypass -File scripts/prepare_env.ps1

Write-Host "[prepare_env] Loading .env if present"
if (Test-Path .env) {
  Get-Content .env | ForEach-Object {
    if ($_ -match '^[A-Za-z_][A-Za-z0-9_]*=') {
      $kv = $_.Split('=',2)
      $key=$kv[0]; $val=$kv[1]
      if (-not $env:$key) { $env:$key = $val }
    }
  }
}

if (-not (Test-Path artifacts)) { New-Item -ItemType Directory artifacts | Out-Null }

Write-Host "[prepare_env] BENCH_ARTIFACT_DIR=$env:BENCH_ARTIFACT_DIR"
Write-Host "[prepare_env] Done. Example run: python scripts/benchmark_metrics_quantiles.py --json-out artifacts/quantile_bench_$(Get-Date -Format yyyyMMdd_HHmmss).json"
