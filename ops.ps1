<#!
.PowerShell operational helpers mirroring Makefile targets.
#>
param(
    [Parameter(Position = 0)][string]$Target = 'help'
)

function Invoke-Up { docker compose up -d }
function Invoke-Down { docker compose down }
function Invoke-Restart { docker compose restart prometheus alertmanager grafana gateway summary }
function Invoke-Logs { docker compose logs -f gateway summary }
function Invoke-PromRules { promtool check rules docker/prometheus_rules.yml }
function Invoke-Tldr { python scripts/generate_runbook_tldr.py }
function Invoke-SeedFleet { python scripts/synthetic_seed.py }

switch ($Target) {
    'up' { Invoke-Up }
    'down' { Invoke-Down }
    'restart' { Invoke-Restart }
    'logs' { Invoke-Logs }
    'prom-rules' { Invoke-PromRules }
    'tldr' { Invoke-Tldr }
    'seed-fleet' { Invoke-SeedFleet }
    default {
        Write-Host 'Targets:'
        '  up           Start stack (docker compose up -d)'
        '  down         Stop & remove containers'
        '  restart      Restart core observability services'
        '  logs         Tail gateway + summary'
        '  prom-rules   Validate Prometheus rules (promtool)'
        '  tldr         Regenerate runbook TL;DR'
        '  seed-fleet   Run synthetic seeder once'
    }
}
