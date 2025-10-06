# Tools quick guide

This folder contains helper scripts to validate and diagnose the orchestrator under different loads.

- tools/validate-10-cycles.ps1
  - Runs 10 sequential full-experiment calls and prints duration per call plus live tasks/min.
  - Expected: 10/10 ok, avg duration ~50–120ms, tasks/min ~100+ while active.

- tools/stress-60s.ps1
  - Tight loop for 60 seconds. Measures iterations ok/error and reports tasks/min snapshot.
  - Expected: >500 iterations; near-zero errors when internal rate-limit bypass is set.

- tools/soak-60min.ps1
  - Paced run every 5s for 60 minutes. Tracks ok/errors, p95 duration, and tasks/min snapshot.
  - Expected: 0 errors; stable p95; low-throughput banner appears only when idle.

Notes

- All scripts send `X-Orchestrator-Bypass: 1` to avoid demo rate limiting.
- API default base is <http://localhost:8010>. Adjust if you changed ports.
- Run with PowerShell:

```powershell
powershell -NoProfile -ExecutionPolicy Bypass -File ".\tools\validate-10-cycles.ps1"
powershell -NoProfile -ExecutionPolicy Bypass -File ".\tools\stress-60s.ps1"
powershell -NoProfile -ExecutionPolicy Bypass -File ".\tools\soak-60min.ps1"
```
