## Supply Chain Security Overview

This repository implements a layered container & artifact security model focused on:

- Vulnerability scanning (Trivy + Grype) with SARIF upload
- SBOM generation (CycloneDX & SPDX via Syft)
- SBOM drift analysis between runs
- Policy gating on CVSS-derived severity counts & license blocklist
- OpenVEX generation for clean builds
- Provenance and SBOM attestations (Cosign keyless)
- Security manifest (aggregated metadata + hashes) published & signed
- Optional enforcement requiring provenance + SBOM attestations
- Central attestation verification reusable workflow
- Automated base image digest pinning (single & multi, scheduled)

### Core Workflow: `container-security-lite.yml`

Key inputs (workflow_dispatch):

| Input | Purpose | Default |
|-------|---------|---------|
| fail-on | Severity gate (critical/high/medium/any/none) | critical |
| license-blocklist | Comma list of disallowed licenses | (empty) |
| push-sbom | Push image & attach SBOM + create attestations | false |
| publish-manifest | Publish security manifest as OCI only | false |
| image-ref | Override image reference | ghcr.io/<repo>:lite-scan |
| require-attestation | Enforce provenance & SBOM attestation | false |

Major artifacts (when pushing):

- `sbom.cdx.json`, `sbom.spdx.json` (SBOMs)
- `provenance-attestation.json` (SLSA-ish predicate)
- `policy-evaluation.json` (decision, counts)
- `security-manifest.json` (consolidated manifest) + detached signature & attestation
- Attestations: provenance (slsaprovenance), SBOM CycloneDX (cyclonedx), SBOM SPDX (spdxjson), optional securitymanifest

When NOT pushing, the SPDX SBOM is signed locally (sign-blob) producing
`sbom.spdx.sig` and `sbom.spdx.cert` for offline validation.

### Attestations

Attestations are created with Cosign in keyless mode via GitHub OIDC. Types used:

- `slsaprovenance` – build provenance predicate (subject image digest)
- `spdxjson` – SPDX SBOM attestation
- `cyclonedx` – CycloneDX SBOM attestation
- `securitymanifest` – consolidated security manifest attestation

Enforcement (set `require-attestation: true` and `push-sbom: true`) fails the job if
provenance OR SBOM attestations are missing/failed and also requires security
manifest signing success.

### Verification

Two verification paths now exist:

1. **On-demand / reusable**: `verify-attestations.yml` – supports single `predicate_type` OR a JSON
  array via `predicate_types_json` for multi-predicate verification (e.g. provenance plus both SBOM
  formats in one run). Produces a combined `predicate-summary.json` artifact with per predicate
  pass/fail counts.
2. **Scheduled**: `scheduled-attestation-verify.yml` – nightly cron verifying default tags
  (`latest`, `stable`) across multiple predicate types (defaults: `spdxjson`, `cyclonedx`,
  `slsaprovenance`). Can be manually dispatched and overridden with inputs.

Example caller (multi-predicate) YAML:

```yaml
jobs:
  verify:
    uses: ./.github/workflows/verify-attestations.yml
    with:
      images_json: '["ghcr.io/my-org/my-repo:lite-scan"]'
      predicate_types_json: '["spdxjson","cyclonedx","slsaprovenance"]'
      require_all: 'true'
```

### Digest Pinning (Single & Multi)

**Single**: `pin-single-image.yml` (now hardened)

- Regex validation of parsed base image
- Skips if already pinned unless override is provided
- Adds inline comment `# pinned for reproducible builds`

**Multi**: `pin-base-images.yml`

- Accepts `dockerfiles_json` (array of Dockerfile paths)
- Matrix resolves each base image digest in parallel using `skopeo`
- Aggregates changed Dockerfiles and opens a single PR (`chore/pin-base-images`)
- Optional `force: true` to re-pin even if already digest locked

#### Scheduling & Enforcement

- Weekly scheduled run (cron) in `pin-base-images.yml` reduces unreviewed base image drift.
- Enforcement workflow `enforce-base-image-pinning.yml` fails PRs/pushes to `main` when any
  `FROM` line lacks a digest, encouraging timely pinning.

Both workflows ensure idempotency and explanatory comments for reviewers.

### Local Validation

To verify a locally downloaded SBOM signature (file mode run):

```bash
cosign verify-blob --certificate sbom.spdx.cert --signature sbom.spdx.sig sbom.spdx.json
```

To verify remote SBOM attestation (image pushed):

```bash
cosign verify-attestation --type spdxjson ghcr.io/ORG/REPO:lite-scan \
  --certificate-oidc-issuer https://token.actions.githubusercontent.com \
  --certificate-identity-regexp ".*"
```

### Security Manifest

`security-manifest.json` captures:

- Image reference & digest
- Hashes of SBOMs, provenance, policy report, top CVEs, drift report
- Attestation creation statuses
- Base image provenance verification result
- Tool versions (cosign, syft, grype, trivy DB)

It is signed (detached sign-blob) and optionally attested; signature + certificate artifacts enable detached verification:

```bash
cosign verify-blob --certificate manifest.pem --signature manifest.sig security-manifest.json
```

### Effective Image Digest Artifact

Every run producing provenance (or when `push-sbom: true`) now emits:

- `effective-image-digest.txt` – raw digest value (real if the image was pushed; synthetic
  commit-derived hash otherwise when operating in no-push mode)
- `effective-image-digest.json` – JSON object: `{ "digest": "<sha256>", "synthetic": "true|false" }`

This normalizes downstream consumption (e.g., deployment gating or audit logging) regardless of push mode.

### Extensibility Roadmap (Updated)

- Enriched SLSA provenance predicate (source materials granularity)
- Automated diff of successive security manifests & policy regression alerts
- Optional integration with OpenVEX trust policy engine
- Multi-registry replication attestation verification
- Digest drift alert surfacing (actionable notifications) building on `effective-image-digest-drift` artifact

### Operational Guidance

- Run with `push-sbom: true` on protected branches to produce attestations
- Use the verification workflow in downstream deploy gates
- Use weekly scheduled `pin-base-images.yml` to keep all base images pinned & current
- Enforce digest pinning via `enforce-base-image-pinning.yml` on protected branches
- Leverage digest drift artifact (`effective-image-digest-drift`) to audit unexpected base image changes
- Rely on the scheduled verification workflow for continuous attestation hygiene; use on-demand verification in release pipelines

---
Questions or enhancement proposals: open an issue tagged `supply-chain`.
