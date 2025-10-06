package policy

# Input is policy-evaluation.json parsed as JSON
# Expect structure: {"policy":..., "critical":N, "high":N, "medium":N, "decision":..., "reason":..., ...}

# Parameters (can be overridden via CONTEST_PARAMS in future)
DEFAULT_FAIL_ON := upper(input.policy)

# Deny if counts exceed threshold logic (replicates existing gate as policy-as-code)
# Provide explicit messages that can be surfaced in conftest output.

violation[msg] {
  DEFAULT_FAIL_ON == "CRITICAL"
  input.critical > 0
  msg := sprintf("critical vulnerabilities present: %v", [input.critical])
}

violation[msg] {
  DEFAULT_FAIL_ON == "HIGH"
  total := input.critical + input.high
  total > 0
  msg := sprintf("high/critical vulnerabilities present: %v", [total])
}

violation[msg] {
  DEFAULT_FAIL_ON == "MEDIUM"
  total := input.critical + input.high + input.medium
  total > 0
  msg := sprintf("medium/high/critical vulnerabilities present: %v", [total])
}

violation[msg] {
  DEFAULT_FAIL_ON == "ANY"
  total := input.critical + input.high
  total > 0
  msg := sprintf("any high/critical vulnerabilities present: %v", [total])
}

# License blocklist placeholder: expect license list maybe under input.licenses (future enrichment)
violation[msg] {
  block := split(lower(env.allow_licenses_blocklist), ",")
  some i
  lic := lower(input.licenses[i])
  lic != ""
  block[j] == lic
  msg := sprintf("blocked license detected: %s", [lic])
}

# Helper to safely fetch env vars (when using conftest --update-data mechanism)
# For now we simulate license blocklist via env var allow_licenses_blocklist (empty means skip)

# Final deny rules consumed by Conftest default output
deny[msg] {
  violation[msg]
}
