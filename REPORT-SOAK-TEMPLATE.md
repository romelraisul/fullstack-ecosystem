# Soak Test Report (Template)

- Duration: 60 minutes
- Pace: 1 call / 5s (12/min)
- Systems: 81

## Results

- Calls: [total]
- OK: [ok_calls]
- Errors: [errors]
- Error rate: [error_rate_pct]%
- p95 duration: [p95_duration_ms] ms
- Tasks/min window: ~100–105 during activity (from /orchestrator/throughput)

## Alerts

- HighLatencyP95: [none/fired]
- LowSuccessRatio: [none/fired]
- Quantum guardrails: [none/fired]
- Alert delivery (Teams sink): [received/not received]

## Notes

- Gateway Live Snapshot updated throughout and banner behavior observed.
- No server-side rate-limit hits (bypass header applied).

## Follow-ups

- [ ] Keep ASSUME_HEALTH_READY in demo; evaluate strict probing in staging.
- [ ] Optional banner tuning via query params (?tpm=5&consec=6).
- [ ] Tag v1 checkpoint.
