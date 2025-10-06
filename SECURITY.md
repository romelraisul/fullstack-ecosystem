# Security & Provenance Strategy

This repository implements a layered software supply chain assurance model focused on:

- Deterministic dependency locking (pip-tools with full SHA256 hashes)
- Dual vulnerability scanning (Trivy + Grype)
- SBOM generation (CycloneDX & SPDX) plus structured diff gating
- Provenance emission with hash binding to SBOM artifacts
- Embedded detached digest signature (sha256) for provenance integrity
- Alignment checks for AI-focused dependency subset
- Dependency graph (nodes + edges) with schema versioning

## Provenance Schema Versioning

Current provenance `schema_version`: `provenance-schema.v1` (SCHEMA_VERSION constant in
`security/generate_provenance.py`).

Guidelines for bumps:

- Additive, non-breaking fields: increment patch (e.g. v1.1) if using semantic sub-versioning and keep
  validator backward compatibility.
- Structural or semantic changes (renamed / removed keys): increment major (v2) and update
  `verify_provenance.py` to accept both old and new for one transition cycle.
- Always document changes in this section with a date + rationale.

Planned future additions:

- Supply chain attestations (SLSA buildType mapping)
- Richer build environment capture (toolchain digests, container base image hash)
- Optional signature algorithm upgrade metadata (algorithm, key id)

## Signature Roadmap

Current state: simple sha256 digest file `<provenance>.json.sha256` embedded under `materials.signature` for
tamper detection.

Next steps (in order):

1. Introduce stronger cryptographic signature: evaluate `cosign attest --predicate` vs `minisign` for
   simplicity.
2. Embed signature metadata fields: `materials.signature.{algorithm, type, key_id, issued}`.
3. Provide verification job extension validating external signature (public key from repository or OIDC
   fulcio root if cosign keyless).
4. Consider timestamp authority / Rekor inclusion for transparency (if using cosign).

## SBOM Diff Governance

- Any SBOM change (added / removed / version / hash) on a PR requires the `sbom-baseline-update` label.

## Vulnerability Baseline Governance

- Critical / High findings cause failure unless triaged and baseline updated with `security-baseline-update` label.

## Dependency Graph Schema

Current schema: `dep-graph-schema.v1`

Fields:

- nodes: array of `{name, version, line, hashes[]}`
- edges: array of `{from, to}`
- counts: node & edge counts (`count`, `edge_count`)
- schema_version

Change process mirrors provenance: additive first, major version on removals / renames.

## Testing & Validation

Pytest job `Security Tooling Tests` executes verification unit tests:

- Hash mismatch detection
- Signature mismatch detection
- Missing `schema_version` detection

Add new tests alongside schema or provenance logic changes to ensure backward compatibility.

## Reporting & Disclosure

Report suspected security issues privately via standard repository channels (e.g. a SECURITY advisory).
Avoid filing public issues for undisclosed vulnerabilities.

## Hardening Backlog

- Cosign / minisign integration
- SBOM attestation linking (in-toto statement)
- Base image digest pinning + verification
- Reproducible build attestation (record build args, Dockerfile digest)
- License policy auto-exception workflow (signed approvals)

---

Last updated: 2025-09-30
