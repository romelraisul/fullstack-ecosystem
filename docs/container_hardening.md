# Container Hardening & Vulnerability Scanning

This document summarizes the hardening pattern applied to project Dockerfiles
and how to keep images patched and monitored.

## Goals

- Reduce CVE exposure (timely `dist-upgrade` + minimal packages)
- Provide reproducibility (ARG pin enables digest injection in CI)
- Ensure provenance (OCI labels with commit + build date)
- Enforce non-root runtime
- Separate dependency & application layers for efficient rebuilds
- Automate daily vulnerability visibility (Trivy workflow)

## Pattern Overview

Key features now standardized:

| Aspect | Approach |
|--------|----------|
| Base image pin | `ARG PYTHON_IMAGE=python:3.11.6-slim-bookworm` (CI can override with digest) |
| Security updates | `apt-get dist-upgrade -y --no-install-recommends` early in single layer |
| Package minimization | Only required build/runtime libs; purge & remove apt lists afterward |
| Environment vars | `PYTHONDONTWRITEBYTECODE=1`, `PYTHONUNBUFFERED=1`, pip cache + version check disabled |
| Non-root user | Deterministic UID/GID (e.g. 1001) via `groupadd` + `useradd` |
| OCI metadata | `org.opencontainers.image.*` labels (title, revision, created, source) |
| Dependency install | Dedicated layer, pinned or constrained where reasonable |
| Cleanup | Remove `/var/lib/apt/lists/*`, docs/man pages, temp dirs |
| Vulnerability scan | Nightly Trivy fs + image scan GitHub Action |
| Percentile bench context | Build args supply `GIT_COMMIT` + `BUILD_DATE` |

## Updating the Base Image Digest

1. Pull latest upstream tag (or use Dependabot / Renovate).
2. Resolve its immutable digest:

   ```bash
   docker pull python:3.11.6-slim-bookworm
   docker inspect --format='{{index .RepoDigests 0}}' python:3.11.6-slim-bookworm
   ```

3. In CI (or locally), pass `--build-arg PYTHON_IMAGE="python:3.11.6-slim-bookworm@sha256:<digest>"`.
4. (Optional) Record digest in a central `BASE_IMAGE_DIGESTS.md` if compliance requires.

## Adding a New Service Dockerfile

1. Copy a hardened example (`Dockerfile.smoke` or backend variant).
2. Adjust only required system packages.
3. Keep user creation and labels intact.
4. Add to the matrix in `.github/workflows/container-security-scan.yml` if it needs scanning.

## Trivy Workflow

The workflow (`container-security-scan.yml`) executes:

- Filesystem scan (CRITICAL,HIGH) → SARIF upload (GitHub Security tab)
- Matrix build of key Dockerfiles → image scans → SARIF

Tune severity or include `--exit-code 1` later to enforce policy (initially informational).

## Local Scanning Quickstart

```bash
# Filesystem scan
trivy fs --severity CRITICAL,HIGH --ignore-unfixed .
# Image scan (after build)
docker build -f Dockerfile.smoke -t local/smoke .
trivy image --severity CRITICAL,HIGH --ignore-unfixed local/smoke
```

## Guardrails & Suggested Policy Evolution

| Stage | Recommendation |
|-------|---------------|
| Initial | Monitor findings (no fail) |
| Phase 2 | Fail build on NEW CRITICAL (baseline diff) |
| Phase 3 | Enforce max age of base digest (e.g. 14 days) |
| Phase 4 | Add SLSA provenance attestation (GitHub OIDC + cosign) |

## Frequently Asked Questions

**Q:** Why not pin digest directly in Dockerfile?  
**A:** Using a build arg allows automated rotation without editing N files; CI injects the verified digest.

**Q:** Why `dist-upgrade` instead of `upgrade`?  
**A:** Ensures security-related transitional packages are applied (still minimized by `--no-install-recommends`).

**Q:** Why remove man pages/docs?  
**A:** Shrinks attack surface and image size; debugging shells aren't the prod norm.

**Q:** How to add additional Python libs?  
**A:** Append them to the requirements file to preserve layer cache rather than ad-hoc pip installs.

## Next Improvements (Optional)

- Introduce SBOM export (`trivy sbom` or `syft`) and attach as artifact.
- Add `--security-opt=no-new-privileges` in runtime orchestrations (Compose/K8s manifests).
- Enforce pinned hashes in requirements (`pip-compile --generate-hashes`).
- Integrate cosign for image signing.

---
Maintainers: Update this doc alongside any structural Dockerfile changes.
