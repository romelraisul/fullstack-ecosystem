# Image Signing & Provenance (Cosign)

This repository uses Sigstore Cosign for keyless container signing and SBOM attestation.

## Workflow

`container-sign-provenance.yml` triggers on tag push (v*) or manual dispatch with `imageTag` input.

Steps:
1. Build image (current example: `Dockerfile.orchestrator`).
2. Push to GHCR (`ghcr.io/<org>/<repo>:<tag>`).
3. Generate CycloneDX SBOM with Trivy.
4. Sign image: `cosign sign --yes ghcr.io/<org>/<repo>:<tag>`.
5. Attach SBOM attestation (predicate type `cyclonedx`).

## Verification

Example (local):
```bash
cosign verify ghcr.io/<org>/<repo>:v1.2.3
cosign verify-attestation --type cyclonedx ghcr.io/<org>/<repo>:v1.2.3
```

Expect a valid certificate referencing the GitHub workflow identity.

## Policy Ideas

- Admission control requiring both signature and SBOM attestation.
- Rekor log monitoring for unexpected signatures.
- Integration with `cosign triangulate` for provenance mapping.

## Extending to Multi-Image Matrix

Add matrix strategy in the signing workflow for all production Dockerfiles,
ensuring each is built, signed, and attested consistently.

## Future Enhancements

- SLSA provenance attestation (`cosign attest --predicate provenance.json --type slsa-provenance`).
- In-toto link metadata generation.
- Automated revocation / blocklist for compromised dependencies derived from SBOM diffing.
