# Supply Chain Integrity

This document outlines controls added to strengthen software supply chain security.

## Components

1. Requirements Hashing (pip-tools)
2. Vulnerability Baseline Drift Enforcement
3. SBOM Generation (CycloneDX + SPDX)
4. Image Signing & Provenance (Cosign) – scaffolded

---
## 1. Requirements Hashing

We maintain `requirements.in` (unpinned hashes) and produce a locked
`requirements.txt` with `--generate-hashes` using pip-tools.

Benefits:

- Reproducible builds (integrity validation by pip)
- Enables SLSA style immutability and tamper detection

Workflow: `.github/workflows/requirements-lock.yml` regenerates on demand and
fails if the committed `requirements.txt` is outdated.

Regenerate locally:

```bash
pip install pip-tools
pip-compile --generate-hashes --output-file requirements.txt requirements.in
```

## 2. Vulnerability Baseline Drift

File: `security/vuln_baseline.json` stores the accepted set of CRITICAL
vulnerabilities (initially empty). Nightly scans run Trivy and the script
`security/compare_vuln_baseline.py`:

- New CRITICAL finding not in baseline → build fails (exit 2).
- Main branch (after review) can update baseline with `--update-baseline` (future enhancement / guarded input).

Rationale: Prevent unnoticed introduction of new critical issues while allowing known items to be triaged separately.

## 3. SBOM Generation

During container security scan workflow we generate CycloneDX and SPDX JSON
SBOMs per image using Trivy. Artifacts are uploaded for retention and can feed
downstream systems (dependency mapping, license checks, provenance attestation).

Artifacts naming: `sbom-<dockerfile-slug>.cdx.json` and `sbom-<dockerfile-slug>.spdx.json`.

## 4. Image Signing & Provenance (Cosign)

Workflow: `.github/workflows/container-sign-provenance.yml`

Implements keyless signing using GitHub OIDC + Cosign. Steps:

1. Build & push each matrix image to GHCR.
2. Generate CycloneDX SBOM per image.
3. `cosign sign` each image (transparency log entry).
4. `cosign attest` SBOM (predicate type cyclonedx).
5. `cosign attest` provisional SLSA-style provenance predicate.


Future Enhancements:

- Integrate SLSA provenance attestations.
- Enforce signature verification policy in deployment (e.g., Kyverno / Cosign
  verify in admission).
- Sigstore policy-controller or Connaisseur gating.


## Operational Guidance

| Control | Update Frequency | Owner | Automation |
|---------|------------------|-------|------------|
| Requirements Hashes | On dependency change | Dev | requirements-lock.yml |
| Vulnerability Baseline | After triage (guarded) | Sec/Dev | container-security-scan.yml (guarded env) |
| SBOM | Every build/scan | CI | container-security-scan.yml / signing |
| Image Signing | On release tag | CI | container-sign-provenance.yml |
| Provenance Attestation | On release tag | CI | container-sign-provenance.yml |

## Threats Mitigated

- Dependency substitution / poisoning (hash pinning).
- Silent introduction of new critical CVEs (baseline drift gate).
- Omission of dependency inventory (SBOM).
- Untrusted image origins (signing / provenance).

## Manual Baseline Update (future pattern)

After reviewing nightly scan results, update baseline on main:

```bash
python security/compare_vuln_baseline.py --sarif path/to/last-run.sarif \
  --baseline security/vuln_baseline.json --update-baseline
git add security/vuln_baseline.json \
  && git commit -m "chore(security): update vuln baseline" \
  && git push
```


---

## Next Steps (Optional)

- Add enforcement: only allow baseline update via PR label `security-approved` (current guard uses env ALLOW_BASELINE_UPDATE).
- Add `cosign verify` gate in deployment pipeline.
- Add license policy scanning using SBOM (e.g., ORT / ScanCode).
- Integrate Grype as a second scanner for redundancy.
