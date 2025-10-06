# Alert Taxonomy

| Alert | Group | Severity | SLO | Scope | Category | For | Windows | Description |
|---|---|---|---|---|---|---|---|---|
| HighLatencyP95 | api-health | warning |  | service | latency | 10m | 5m eval / 10m hold | Deprecated: superseded by AgentP95Latency* SLO-based alerts. High API latency (p95) above 700ms for 10 minutes |
| LowSuccessRatio | api-health | warning |  | service | error-rate | 10m | 10m | Deprecated: superseded by refined error budget alerts. Success ratio below 99% for 10 minutes |
| NoExperimentsIn1h | bridge-health | info |  | system | throughput |  | 1h | No approved experiments in the last hour |
| HighRejectedShare | bridge-health | warning |  | system | quality | 15m | 15m | More than 50% of inputs rejected over 15m |
| UltraHighLatencyP95 | ultra-services | warning |  | multi-service | latency | 10m | 5m eval / 10m hold | One or more ultra services p95 latency >1s for 10m |
| UltraErrorRateHigh | ultra-services | warning |  | multi-service | error-rate | 10m | 5m eval / 10m hold | Error ratio >1% over last 10m for ultra services |
| QCAEGuardrailViolations | quantum-guardrails | warning |  | service | guardrail | 5m | 5m | QCAE guardrail violations detected in last 5m |
| QCAEQuantumJobsP99High | quantum-guardrails | warning |  | service | latency | 10m | 5m eval / 10m hold | QCAE p99 job duration >1s for 10m |
| QCAEQuantumJobsP99HighByKind | quantum-guardrails | warning |  | dimension | latency | 10m | 5m eval / 10m hold | QCAE p99 job duration by kind >1s for 10m |
| QCAEInstanceDown | quantum-health | critical |  | service | availability | 5m | 5m | QCAE target down for 5m |
| QDCInstanceDown | quantum-health | warning |  | service | availability | 5m | 5m | QDC target down for 5m |
| QCMSInstanceDown | quantum-health | warning |  | service | availability | 5m | 5m | QCMS target down for 5m |
| OrchestrateQuantumP95High | quantum-health | warning |  | route | latency | 10m | 10m | Route /orchestrate/quantum p95 >700ms for 10m |
| NoQuantumJobsIn10m | quantum-health | info |  | service | throughput | 0m | 10m | No quantum jobs completed in 10m |
| AgentTargetDown | agents-health | critical |  | agent | availability | 2m | 2m | Agent target down (up==0) for 2m |
| AcademicAgentNoRequests10m | agents-health | warning |  | agent | throughput | 0m | 10m | Academic agent received no requests in 10m (while up) |
| DeveloperEcosystemAgentNoRequests10m | agents-health | warning |  | agent | throughput | 0m | 10m | Developer ecosystem agent received no requests in 10m |
| WebSecurityAgentNoRequests10m | agents-health | warning |  | agent | throughput | 0m | 10m | Web security agent received no requests in 10m |
| TopicsDiscoveryAgentNoRequests10m | agents-health | warning |  | agent | throughput | 0m | 10m | Topics discovery agent received no requests in 10m |
| AgentP95LatencyHigh | agents-slo-latency | warning | latency | agent | latency | 5m | 5m | Agent p95 latency above warning threshold for 5m |
| AgentP95LatencyCritical | agents-slo-latency | critical | latency | agent | latency | 10m | 10m | Agent p95 latency above critical threshold for 10m |
| AgentLatencyBurnFast | agents-slo-burn | warning | latency-burn | agent | latency-acceleration | 5m | 5m vs 30m | Latency accelerating: 5m avg >1.2x warning threshold and >30% over 30m baseline |
| AgentErrorRateHigh | agents-slo-error | warning | error-rate | agent | error-rate | 10m | 5m / 10m | 5m error rate exceeds 2x agent budget for 10m |
| AgentErrorRateCritical | agents-slo-error | critical | error-rate | agent | error-rate | 5m | 5m | 5m error rate exceeds 5x agent budget for 5m |
| AgentErrorBurnFast | agents-slo-error | warning | error-burn | agent | error-acceleration | 5m | 5m vs 30m | 5m error rate > budget and >2x 30m baseline for 5m |
| AgentFleetErrorRateHigh | agents-slo-error | critical | error-rate | fleet | error-rate | 10m | 5m / 10m | Fleet 5m error rate >3x fleet budget for 10m |
| AgentErrorBudgetBurnFast | agents-slo-error-burn-multiwindow | critical | error-burn-fast | agent | error-budget-burn | 5m | 5m / 1h | Burn rate >14x budget on 5m & 1h windows |
| AgentErrorBudgetBurnSlow | agents-slo-error-burn-multiwindow | warning | error-burn-slow | agent | error-budget-burn | 30m | 30m / 6h | Burn rate >6x budget on 30m & 6h windows |
| AgentFleetErrorBudgetBurnFast | agents-slo-error-burn-multiwindow | critical | error-burn-fast | fleet | error-budget-burn | 5m | 5m / 1h | Fleet burn rate >14x budget on 5m & 1h windows |
| AgentFleetErrorBudgetBurnSlow | agents-slo-error-burn-multiwindow | warning | error-burn-slow | fleet | error-budget-burn | 30m | 30m / 6h | Fleet burn rate >6x budget on 30m & 6h windows |
