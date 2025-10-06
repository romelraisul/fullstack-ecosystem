# Security Workflow Modularization Guide

This document outlines how to decompose the monolithic
`container-security-lite.yml` into smaller, reusable GitHub Actions workflows
for maintainability, clearer ownership, faster iteration, and selective re-use
by other repositories or components.

## High-Level Phases

1. Build & Scan
2. Policy Evaluation & SBOM/Drift Analysis
3. Attestation & Signing
4. Publication (OCI push + manifest + ORAS)
5. Verification (detached signature & attestation bundle)
6. Policy-as-Code (OPA / Conftest)
7. Notification & Observability

Each phase can map to one reusable workflow and expose outputs that downstream workflows consume via `workflow_call`.

---

## Suggested Workflow Split

### 1. `security-build-scan.yml`

Purpose: Build the container image and run vulnerability + SBOM generation.

Inputs:

- `image-ref`
- `push-sbom`
Outputs:
- `sbom_cdx_path`
- `sbom_spdx_path`
- `severity_critical|high|medium`
- `license_count`
Artifacts:
- `sbom-provenance`

### 2. `security-drift-policy.yml`

Purpose: Perform SBOM drift comparison + policy severity evaluation.

Inputs:

- `fail-on`
- `license-blocklist`
- `allowed-base-image-registries`
- Artifact download from previous phase
Outputs:
- `policy_decision`
- `policy_reason`
- `drift_status`
Artifacts:
- `policy-evaluation`
- `sbom-drift`

### 3. `security-attest-sign.yml`

Purpose: Create attestations (SBOM / provenance / manifest) & optional key-based
signing.

Inputs:

- `image-ref`
- `sign-artifacts`
Artifacts:
- `provenance-attestation`
- `sbom-attestation`
- `key-signatures`
- `security-manifest`
Outputs:
- `effective_digest`
- `manifest_digest`

### 4. `security-publish.yml`

Purpose: Publish security manifest via ORAS & sign/attest manifest.

Inputs:

- `image-ref`
- requires manifest artifact
Outputs:
- `manifest_sign_status`
Artifacts:
- `manifest-signature`
- `manifest-attestation-bundle`

### 5. `security-verify.yml`

Purpose: Detached signature + attestation verification of manifest & (optional)
key-based verification.

Inputs:

- `image-ref`
Artifacts consumed: `manifest-signature`, `security-manifest`, `manifest-attestation-bundle`.
Outputs:
- `verification_status`

### 6. `security-policy-as-code.yml`

Purpose: Run Conftest / Rego policies against `policy-evaluation.json` and
other produced metadata.

Inputs:

- `fail-on`
Outputs:
- `conftest_status`
Artifacts consumed: `policy-evaluation`

### 7. `security-notify.yml`

Purpose: Notify on digest drift, high severity findings, or gate failures.
Central use of the composite action `drift-notify` plus future channels
(email, Slack, etc.).

Inputs:

- `provider`
- `webhook`
- `email-*`
- `smtp-*`
Outputs:
- `notification_posted`
- `latency_ms`
Artifacts consumed: `effective-image-digest-drift`

---

## Orchestration Pattern

```yaml
  workflow_dispatch:


  build_scan:
    uses: ./.github/workflows/security-build-scan.yml
    with:
      image-ref: ghcr.io/${{ github.repository }}:lite-scan
    uses: ./.github/workflows/security-drift-policy.yml
    with:
    needs: [build_scan, drift_policy]
    uses: ./.github/workflows/security-attest-sign.yml

      sign-artifacts: true

  publish:
    needs: attest_sign
    uses: ./.github/workflows/security-publish.yml

  verify:

  policy_as_code:


  notify:
    needs: [drift_policy]
    uses: ./.github/workflows/security-notify.yml
      webhook: ${{ secrets.SECURITY_SLACK_WEBHOOK }}
```

---

- Use lowercase, hyphen-separated workflow inputs: `fail-on`, `sign-artifacts`.
- Step outputs exposed as `outputs` in reusable workflows.
- Artifact naming stable across phases (`sbom-provenance`, `policy-evaluation`, `security-manifest`).

---
Add a `version` output to each reusable workflow for traceability. Store a `workflow-metadata.json` artifact containing:

```json
{
  "workflow": "security-build-scan",

  "generated_at": "<timestamp>",
  "git_sha": "<sha>"
}
```

Consumers can merge these into the consolidated security manifest or attach as an SBOM extension
---

## Failure Handling & Gates

- Conftest gate: separate to allow independent policy evolution.
- Verification gate: final cryptographic assurance stage.

- Notifications should always run (`if: always()`) but degrade gracefully when prerequisites absent.

---

## Migration Plan

1. Extract the current logic sections into their own reusable workflow files (copy/paste + prune unused envs).
2. Replace monolithic workflow with orchestrator referencing the new reusable workflows.

## Security Considerations

- Scope secrets minimally per reusable workflow (principle of least privilege).
- Use `permissions:` blocks per job (`contents: read`, `packages: write` only where pushing).

---

## Observability & Metrics

Add a tiny metrics JSON artifact per phase:

- `metrics-drift-policy.json`: drift status, decision
- `metrics-attest-sign.json`: attest statuses, manifest digests
- `metrics-notify.json`: notification attempts, latency

Aggregate with a later `metrics-aggregate.yml` or a reporting action.

---

## Future Enhancements

- Add SARIF aggregation reusable workflow.
- Add license compliance policy Rego with SPDX license expression parsing.
- Push metrics to an internal endpoint via another reusable workflow (opt-in).

- Introduce ephemeral secrets fetching (e.g., Vault) in signing workflow.

---

## Minimal Reusable Workflow Skeleton Example

```yaml
name: Security Build & Scan
on:
  workflow_call:
    inputs:
      image-ref:
        required: false
        type: string
      push-sbom:
        required: false
        type: boolean
        default: false
    outputs:
      critical:
        description: Critical count
        value: ${{ jobs.scan.outputs.critical }}

jobs:
  scan:
    runs-on: ubuntu-latest
    outputs:
      critical: ${{ steps.sev.outputs.critical }}
    steps:
      - uses: actions/checkout@v4
      - name: Build
        run: docker build -f Dockerfile -t local-scan:latest .
      - name: Trivy
        uses: aquasecurity/trivy-action@0.20.0
        with:
          image-ref: local-scan:latest
          format: 'sarif'
          output: trivy.sarif
```

---

## Summary

Breaking the workflow into modular, reusable segments enhances clarity, security boundary enforcement, testability, and long-term maintainability while preserving the rich security context already implemented.
