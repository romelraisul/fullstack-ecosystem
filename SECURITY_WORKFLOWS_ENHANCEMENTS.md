# Security Workflow Enhancements

This document summarizes recent governance and provenance enhancements added to the container security workflows.

## New Inputs (container-security-lite.yml)

- `notify-webhook-url` (string, optional): If provided, sends a JSON notification (Slack simple text, Teams
  MessageCard, or Discord content) when digest drift status is `changed`.
- `notify-provider` (enum: `slack` | `teams` | `discord` | `mattermost` | `email`, default `slack`):
  Format to use for the drift notification payload.
  payload.
- `gate-on-digest-drift` (boolean string `true`/`false`, default `false`): When `true` and drift status is
  `changed`, the workflow fails if no accompanying base image pin PR is detected.
- `allowed-base-image-registries` (comma-separated string): Allowlist of registry prefixes (e.g.
  `ghcr.io,public.ecr.aws`) that base images in the primary Dockerfile must originate from. Fails fast if
  violated.
- `emit-openvex-drift` (boolean string, default `false`): Emit an OpenVEX statement indicating drift `affected`
  vs `not_affected` (changed vs unchanged).
- `auto-close-pin-pr` (boolean string, default `false`): Automatically closes open pin PRs once drift
  stabilizes (`unchanged`).

## Digest Drift

The workflow now standardizes an `effective-image-digest.txt` & `effective-image-digest.json` artifact every run
(synthetic when no push). Drift is detected by comparing the current digest with the previously archived artifact:

- Status values: `no_previous`, `unchanged`, `changed`.
- When `changed`:
  - Optional merge gating (if `gate-on-digest-drift` = `true`).
  - Slack / Teams webhook notification if configured.

Artifacts (if provenance or SBOM was requested):

- `digest-drift.json`
- `digest-drift-status.txt`
- `previous-effective-image-digest.txt`

## Base Image Registry Allowlist

The first `FROM` line of the main `Dockerfile` is parsed. The registry (substring before first `/`) must appear in
the provided allowlist (case-insensitive). Failure aborts the job early. This mitigates accidental pulls from
unapproved registries.

## SARIF for Unpinned Base Images

`enforce-base-image-pinning.yml` now:

- Scans all Dockerfiles for unpinned `FROM` (missing `@sha256:`).
- Emits a SARIF report (`UNPINNED_BASE_IMAGE` rule) listing each offending file with line number.
- Uploads SARIF via `github/codeql-action/upload-sarif` (requires `security-events: write`).
- Fails the job when unpinned images exist (post-upload so alerts and code scanning findings persist).

## Provenance Enrichment

`provenance-attestation.json` (SLSA-like) now includes:

- `externalParameters.userParameters`: Captured selected workflow inputs (image ref, push sbom flag, emit
  provenance flag, registry allowlist value).
- Tool versions snapshot (`syft`, `trivy`, `grype`, `cosign`) under `metadata.materials.tools`.
- Base image material: `materials.baseImage` with `ref` and best-effort resolved digest (if `skopeo` available) in `metadata.materials`.
- Multi-stage materials: `materials.multiStageBaseImages` array includes every distinct `FROM` base image (with
  resolved digest where possible).
- Existing resolved dependencies remain (source repo, builder image, OIDC issuer/subject).

Structure Snippet (truncated for brevity):

```json
{
  "_type": "https://in-toto.io/Statement/v0.1",
  "predicateType": "https://slsa.dev/provenance/v1",
  "subject": [ { "name": "<image_ref>", "digest": { "sha256": "<digest>" } } ],
  "predicate": {
    "buildDefinition": {
      "externalParameters": {
        "workflow": "container-security-lite",
        "userParameters": {
          "image_ref": "...",
          "push_sbom": "...",
          "emit_provenance": "...",
          "allowed_base_image_registries": "..."
        }
      }
    },
    "runDetails": {
      "metadata": {
        "materials": {
          "baseImage": { "ref": "registry/image:tag", "digest": "sha256:..." },
          "tools": { "syft": "...", "trivy": "...", "grype": "...", "cosign": "..." }
        }
      }
    }
  }
}
```

## Notification Payloads

- Slack: simple JSON `{ "text": "[Digest Drift] repo=... status=changed previous=... current=... :: <run_url>" }`.
- Teams: MessageCard with facts (repo, status, previous, current) and link to run.
- Discord / Mattermost: JSON `{ "text"|"content": "[Digest Drift] ..." }` simple message payload.
- Email: Basic RFC 2822 text message (stub in workflow; integrate SMTP action for production).

## OpenVEX Drift Statement

When `emit-openvex-drift=true`, an `openvex-drift.json` file is generated:

- `status=changed` -> VEX statement status `affected` with justification `configuration_change`.
- `status=unchanged` -> `not_affected` with justification `no_change`.
- Product identifier uses `pkg:container/<repo>@sha256:<digest>` when effective digest known, else `@latest`.
- The file is optionally signed via a cosign attestation (keyless if environment supports OIDC).

## Auto-Close Pin PRs

When `auto-close-pin-pr=true` and drift returns to `unchanged`, any open PRs with branch or title indicating
`pin-base-image` / `pin base image` are automatically closed (branch deleted). This keeps repository noise low once
pinning stabilization occurs.

## Operational Notes

- Digest drift gating checks for existing open PRs whose branch name contains `pin-base-image` or title contains
  `pin base image` (case-insensitive). If none found and gating enabled, the job fails.
- Provenance generation synthesizes a pseudo digest (SHA256 of `local-scan:latest-$GITHUB_SHA`) when an image push
  is skipped to keep subject deterministic.
- All JSON modifications use `jq` to minimize schema drift.
- Auto-close PR step now includes permission-denied fallback logging (suggesting elevated token if closure fails).

## Future Ideas

- Add OpenVEX statement linking drift changes to vulnerability status.
- Extend provenance with supply chain dependencies (e.g., base image layers SBOM) if available.
- Multi-base Dockerfile stage analysis for allowlist and materials.

---
Last updated: 2025-10-02
