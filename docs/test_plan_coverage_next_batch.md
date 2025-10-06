# Coverage Uplift Plan (Batch 3)

Goal: Increase backend coverage from ~43% to ≥49% (+6 points) to enable raising threshold to 48–49%.

## Scope Targets

1. Bridge module persistence & error branches
2. Orchestrate endpoints (`/orchestrate/demo`, `/orchestrate/delegate`) minimal path
3. Control endpoints (`/control/start-all`, `/control/stop-all`, `/control/restart-all`)
4. Latency targets negative / error validation paths (bad input bodies)
5. Latency sampler loop success + failure branch (mock httpx)

## Current Gaps (High-Level)

Bridge and large orchestration sections (main.py lines ~985–1563) are mostly uncovered.
Error validation in latency admin endpoints and control orchestration endpoints also
missing. Bridge file (~44% covered) leaves data IO and status/owner recomputation
paths unexercised (404 branches, multiple updates, experiment creation).

## Detailed Test Cases

### 1. Bridge Module

File: `backend/app/bridge.py`

Test Case B1: Create input basic path

- POST `/bridge/inputs` minimal valid payload.
- Assert id=1, status new, counter increment (optional grep metrics output).

Test Case B2: Filtering logic

- Create 3 inputs with varying owner / status / tags.
- GET by owner → subset.
- GET by tag → inclusion.
- Update one to reviewing, then GET by status reviewing.

Test Case B3: Update owner success & 404

- PATCH existing id owner.
- PATCH non-existent id → 404.

Test Case B4: Update status success & 404

- PATCH status to approved.
- PATCH non-existent id → 404.

Test Case B5: Approve experiment success & 404

- POST experiment for existing input.
- POST experiment for missing id → 404.

Test Case B6: Metrics gauge recomputation

- After changes GET /metrics; assert presence of owner & status lines.

Estimated Impact: ~+2 points.

### 2. Orchestrate Endpoints (Main)

Endpoints: `/orchestrate/demo`, `/orchestrate/delegate`, `/orchestrate/delegate-enterprise`,
`/orchestrate/quantum`, `/orchestrate/full-experiment`.

Strategy: Hit light endpoints first; if heavy calls arise, monkeypatch helpers.

Test Case O1: POST demo minimal JSON; assert 200 + basic keys.
Test Case O2: POST delegate minimal body; assert structure.
Test Case O3: POST one advanced (quantum or full-experiment) minimal body; skip others if costly.

Estimated Impact: ~+1.5–2 points.

### 3. Control Endpoints

Endpoints: `/control/start-all`, `/control/stop-all`, `/control/restart-all`.

Test Case C1: POST each; assert 200 and expected key(s) (`action` or `status`).

Estimated Impact: ~+0.5–1 point.

### 4. Latency Admin Error Validation

Endpoint: `/admin/latency-targets`

Test Case L1: Body = [] → 400.
Test Case L2: Body = {} (no targets) → 400.
Test Case L3: Body with targets: [] → 400.
Test Case L4: Body with invalid targets (empty name/url) → 400.

Estimated Impact: ~+0.5 point.

### 5. Latency Sampler Success / Failure Branch

Loop interval is 15s; avoid waits. Inject failing sample manually.

Test Case S1: Append failing sample (ok False) to one service; GET service-latencies
and assert failure_rate_pct > 0 and latest_class reflects failure.

Estimated Impact: ~+0.2 point.

## Implementation Order (Max Parallel Feedback)

1. Latency admin error cases (fast, deterministic).
2. Bridge CRUD + error paths (build fixture inputs early to reuse across tests).
3. Latency sampler failure augmentation.
4. Orchestrate endpoints (skip or adjust if errors; patch internals as needed).
5. Control endpoints last (simple).

## Risk & Mitigations

- Orchestrate endpoints may need external modules or be slow. Mitigation: wrap
  in try/except and mark `xfail`, or monkeypatch heavy calls.
- Metrics scraping nondeterminism → assert presence of metric name substrings.
- Bridge DATA_PATH absolute path → monkeypatch to tmp path to avoid pollution.

## Tooling Helpers (Proposed)

Helper module `tests/utils/bridge_test_helpers.py`:

- Context manager to monkeypatch `bridge.DATA_PATH` to tmp file and init JSON.
- Helper to load current JSON for assertions.

## Estimated Coverage Gain Summary

| Area | Est Points |
|------|------------|
| Bridge CRUD & errors | 2.0 |
| Orchestrate endpoints | 1.5–2.0 |
| Control endpoints | 0.5–1.0 |
| Latency admin errors | 0.5 |
| Sampler failure case | 0.2 |
| Buffer / variance | 0.3 |
| **Total** | **~4.7–6.0** |

Lower bound (~4.7) may land just under 49%. If coverage <49% add another
orchestrate endpoint or second bridge 404 path.

## Exit Criteria

- New coverage run shows ≥49% total backend.
- CI threshold updated (PR) to 48 or 49.
- Plan updated with results and next target (mid-term: 55%).

## Next Steps

After approval:

1. Implement bridge DATA_PATH monkeypatch helper.
2. Add bridge test file covering B1–B6.
3. Add latency admin error tests.
4. Add sampler failure augmentation test.
5. Add orchestrate & control endpoint tests (skip heavy if needed; TODO remaining).
6. Run coverage & ratchet threshold.

---
Generated: Batch 3 planning (date: 2025-10-02)
