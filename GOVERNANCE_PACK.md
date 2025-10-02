# Starter Governance Pack

This repository now bundles a **Starter Governance Pack** you can reuse across projects to harden CI supply chain integrity, measure workflow hygiene, and visualize actionlint trends.

## Components

| Area | File / Path | Purpose |
|------|-------------|---------|
| Action Linting (Reusable) | `.github/workflows/reusable-actionlint.yml` | Central lint job with metrics, deltas, gating, badge generation. |
| Invoker Example | `.github/workflows/workflow-lint.yml` | Shows how to call the reusable workflow (pin by commit). |
| Metrics Publishing | `.github/workflows/publish-actionlint-metrics.yml` | Aggregates snapshots -> JSON, CSV, HTML dashboard, badges to Pages. |
| Snapshot Storage | `metrics-history/actionlint/` | Timestamped JSON snapshots + badges. Purged to last 200. |
| Version Pinning (actionlint) | `.github/actionlint-version.txt` | Single source of truth for actionlint version. |
| Auto Version Bump | `.github/workflows/actionlint-version-bump.yml` | Scheduled/manual workflow updating version file via PR. |
| Action SHA Pinning | `.github/workflows/pin-action-shas.yml` | Resolves mutable refs to commit SHAs, optional metadata vendoring. |
| Pin Script | `scripts/pin-action-shas.sh` | Shell logic to pin and vendor metadata. |
| Dependabot | `.github/dependabot.yml` | Weekly action dependency scanning. |
| Security Pipeline | `.github/workflows/container-security-lite.yml` | Build, scan, SBOM, attest, sign, verify. |

```

Deltas are computed relative to the previous *committed* snapshot on `main`. First snapshot initializes all deltas to `0`.
 

### Badges

Generated (all Shields endpoint JSON):

- `badge-actionlint.json` (errors)
- `badge-actionlint-errors-delta.json`
- `badge-actionlint-warnings.json`
- `badge-actionlint-warnings-delta.json`
- `badge-actionlint-rules.json`
- `badge-actionlint-rules-delta.json`
- `badge-actionlint-summary.json` (`E:x W:y`)

Embed example:

```markdown
![Errors](https://img.shields.io/endpoint?url=<raw>/metrics-history/actionlint/badge-actionlint.json)
![Errors Δ](https://img.shields.io/endpoint?url=<raw>/metrics-history/actionlint/badge-actionlint-errors-delta.json)
![Summary](https://img.shields.io/endpoint?url=<raw>/metrics-history/actionlint/badge-actionlint-summary.json)
```

Replace `<raw>` with:

```text
https://raw.githubusercontent.com/<owner>/<repo>/main
```

## Pages Dashboard

Enable GitHub Pages (Build & deployment: GitHub Actions). Workflow publishes:

- `history.json` (array snapshots)
- `history.csv`
- `index.html` (interactive table with deltas)
- All badges

## Governance Guarantees

- All actions pinned by commit SHA after scheduled pin job runs.
- SBOM + signing pipeline (container-security-lite) provides provenance & verification.
- actionlint errors gate CI; warnings tracked for hygiene improvement.
- Historical growth bounded (<= 200 snapshots).

## Suggested Adoption Steps (New Repo)

1. Copy `reusable-actionlint.yml` + `workflow-lint.yml` (update commit ref once pinned).
2. Add `actionlint-version.txt` and optionally schedule bump workflow.
3. Add pin script + workflow; run once to produce initial pinned grid.
4. Enable Pages, run lint workflow with `persist-history: true` to produce first snapshot.
5. Trigger publish workflow to build dashboard.
6. Add badges to README.

## GitHub App Blueprint (Future)

Goal: Multi-repo Governance Automation.

### High-Level Architecture

- GitHub App (installed on org) receives push / workflow_run / pull_request events.
- Dispatches a `repository_dispatch` to a central orchestration repo (this one) or triggers remote API.
- Orchestrator runs lint + pin + security verification in ephemeral workflow runs.
- Results summarized back to PR via Check Run + comment (errors, new deltas, remediation suggestions).

### Core Services

| Service | Responsibility |
|---------|----------------|
| Webhook Receiver | Validate HMAC, enqueue events. |
| Action Ref Auditor | On push/PR, diff action `uses:` blocks, flag newly introduced mutable refs. |
| Lint Runner | Optionally reuse the existing reusable workflow via `workflow_call`. |
| Delta Analyzer | Compare latest metrics vs last stable on `main` for that repo. |
| Remediation PR Bot | Optionally opens a PR pinning new refs (leverages `pin-action-shas.sh`). |
| Badge API (optional) | Serve consolidated org-level badge (aggregated errors/warnings). |

### Data Model (Minimal)

- `repositories` (id, name, default_branch)
- `snapshots` (repo_id, ts, errors, warnings, rules, deltas...)
- `action_refs` (repo_id, workflow_path, action_full, ref_type, pinned_sha, first_seen_ts)

### Event Flow

1. Push -> webhook -> analyze changed workflows.
2. If new mutable references: create advisory check (pending) + open fix PR.
3. Schedule / on-demand actionlint run -> store snapshot -> compute deltas.
4. Update aggregated org metrics (compute weighted error density, e.g., errors per workflow).
5. Expose UI / API for governance dashboards.

### Security & Hardening

- Least privilege GitHub App permissions (metadata, checks: write, contents: read, pull_requests: write).
- All outbound actions pinned & pinned script executed daily.
- Optionally sign webhook payload storage with timestamped envelopes.

### MVP Scope

- Webhook receiver (serverless or container) + simple queue.
- Snapshot persistence (SQLite/Postgres) + minimal REST for latest snapshot per repo.
- PR comment summarizing errors + link to dashboard.

### Expansion Ideas

- License policy enforcement (extend manifest tooling).
- CVE gating thresholds integrated with container security workflow outputs.
- Cross-repo risk scoring (ex: % pinned actions, mean time to remediate errors).

## Monetization Hooks

- Tiered pricing by number of repos + remediation PR volume.
- Add “Compliance Export” (JSON + PDF) as premium.
- Provide weekly governance email digests (delta trends & top offenders).

---
This document will evolve as automation matures. Contributions welcome.
