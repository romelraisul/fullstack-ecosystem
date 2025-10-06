"""Performance regression comparison utility (multi-endpoint + p95 aware).

Reads Locust CSV (perf/locust_stats.csv) and builds a metrics map keyed by
"<METHOD> <ENDPOINT>" capturing median, average and (if present) p95.

Baseline schema (perf/performance_baseline.json):
{
    "version": 2,
    "endpoints": {
         "GET /api/v1/ping": {"median_ms": 42.0, "p95_ms": 90.0},
         "POST /api/v1/workflows/execute": {"median_ms": 130.0}
    }
}

Env Vars:
    REG_TOL_MEDIAN_MS: default 50 (per-endpoint allowed +delta on median)
    REG_TOL_P95_MS: default 80 (per-endpoint allowed +delta on p95)
    TRACK_ENDPOINTS: optional comma list of endpoint patterns to enforce (substring match); if empty all endpoints enforced
    UPDATE_BASELINE: when 'true', writes new baseline (overwrites) with observed medians/p95 for tracked endpoints

Exit Codes:
    0 pass / within tolerance / baseline updated
    1 regression beyond tolerance (any tracked endpoint median or p95 exceeds tolerance)
"""

from __future__ import annotations

import contextlib
import json
import os
from pathlib import Path
from typing import Any

STATS_PATH = Path("perf/locust_stats.csv")
SUMMARY_PATH = Path("perf/locust_summary.json")
BASELINE_PATH = Path("perf/performance_baseline.json")
JUNIT_REPORT_PATH = Path("perf/performance_junit.xml")


def parse_stats() -> dict[str, dict[str, float]]:
    """Parse Locust stats CSV returning mapping endpoint -> metrics.

    Locust default CSV header (simplified example):
    Method,Name,# requests,# failures,Median response time,Average response time,Min response time,Max response time,Average Content Size,Requests/s
    Some versions / custom exports may include 95 percentile as an added column (we try to detect).
    We attempt flexible parsing: median at index 4, average at 5, p95 at 6 or 9 if recognized string '95%'.
    """
    metrics: dict[str, dict[str, float]] = {}
    if not STATS_PATH.exists():
        return metrics
    try:
        lines = STATS_PATH.read_text(encoding="utf-8").splitlines()
    except Exception:
        return metrics
    if not lines:
        return metrics
    header = [h.strip() for h in lines[0].split(",")]
    # Heuristic for p95 column index
    p95_index = None
    for i, h in enumerate(header):
        if "95" in h and "%" in h:
            p95_index = i
            break
    for line in lines[1:]:
        parts = [p.strip() for p in line.split(",")]
        if len(parts) < 6:
            continue
        method = parts[0]
        name = parts[1]
        if method not in {"GET", "POST", "PUT", "DELETE", "PATCH"}:
            continue
        key = f"{method} {name}"
        try:
            median = float(parts[4])
        except Exception:
            continue
        try:
            avg = float(parts[5])
        except Exception:
            avg = median
        entry: dict[str, float] = {"median_ms": median, "average_ms": avg}
        if p95_index is not None and p95_index < len(parts):
            with contextlib.suppress(Exception):
                entry["p95_ms"] = float(parts[p95_index])
        metrics[key] = entry
    return metrics


def load_baseline() -> dict[str, Any] | None:
    if not BASELINE_PATH.exists():
        return None
    try:
        return json.loads(BASELINE_PATH.read_text(encoding="utf-8"))
    except Exception:
        return None


def main() -> int:
    metrics = parse_stats()
    baseline = load_baseline() or {}
    baseline_endpoints = (baseline.get("endpoints") or {}) if isinstance(baseline, dict) else {}
    tol_median = float(os.getenv("REG_TOL_MEDIAN_MS", "50") or 50)
    tol_p95 = float(os.getenv("REG_TOL_P95_MS", "80") or 80)
    update_baseline = os.getenv("UPDATE_BASELINE", "").lower() in ("1", "true", "yes")
    track_raw = os.getenv("TRACK_ENDPOINTS", "").strip()
    track_filters: list[str] = (
        [t.strip() for t in track_raw.split(",") if t.strip()] if track_raw else []
    )

    summary: dict[str, Any] = {
        "version": 2,
        "tracked_filters": track_filters,
        "tolerances": {"median_ms": tol_median, "p95_ms": tol_p95},
        "observed": metrics,
        "regressions": [],
    }
    regression = False

    def tracked(key: str) -> bool:
        if not track_filters:
            return True
        return any(f in key for f in track_filters)

    for key, data in metrics.items():
        if not tracked(key):
            continue
        base = baseline_endpoints.get(key, {})
        # Median gating
        med = data.get("median_ms")
        base_med = base.get("median_ms") if isinstance(base, dict) else None
        if isinstance(base_med, (int, float)) and isinstance(med, (int, float)):
            delta = med - base_med
            if delta > tol_median:
                regression = True
                summary["regressions"].append(
                    {
                        "endpoint": key,
                        "metric": "median_ms",
                        "delta": delta,
                        "baseline": base_med,
                        "observed": med,
                    }
                )
        # p95 gating
        p95 = data.get("p95_ms")
        base_p95 = base.get("p95_ms") if isinstance(base, dict) else None
        if isinstance(base_p95, (int, float)) and isinstance(p95, (int, float)):
            delta_p95 = p95 - base_p95
            if delta_p95 > tol_p95:
                regression = True
                summary["regressions"].append(
                    {
                        "endpoint": key,
                        "metric": "p95_ms",
                        "delta": delta_p95,
                        "baseline": base_p95,
                        "observed": p95,
                    }
                )

    # Update baseline
    if update_baseline:
        new_base = {"version": 2, "endpoints": {}}
        for key, data in metrics.items():
            if not tracked(key):
                continue
            entry = {"median_ms": data.get("median_ms")}
            if "p95_ms" in data:
                entry["p95_ms"] = data["p95_ms"]
            new_base["endpoints"][key] = entry
        BASELINE_PATH.parent.mkdir(parents=True, exist_ok=True)
        BASELINE_PATH.write_text(json.dumps(new_base, indent=2) + "\n", encoding="utf-8")
        print("Updated performance baseline at", BASELINE_PATH)

    SUMMARY_PATH.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY_PATH.write_text(json.dumps(summary, indent=2) + "\n", encoding="utf-8")
    print("Wrote", SUMMARY_PATH)

    # Optional JUnit XML emission for CI test reporting dashboards
    if os.getenv("PERF_JUNIT", "").lower() in ("1", "true", "yes"):
        import xml.etree.ElementTree as ET

        testsuite = ET.Element(
            "testsuite", name="performance", tests=str(len([k for k in metrics if tracked(k)]))
        )
        # For deterministic ordering
        for key in sorted(metrics.keys()):
            if not tracked(key):
                continue
            data = metrics[key]
            case = ET.SubElement(testsuite, "testcase", classname="perf", name=key)
            med = data.get("median_ms")
            p95 = data.get("p95_ms")
            props = ET.SubElement(case, "properties")
            if med is not None:
                ET.SubElement(props, "property", name="median_ms", value=f"{med:.2f}")
            if p95 is not None:
                ET.SubElement(props, "property", name="p95_ms", value=f"{p95:.2f}")
            base = baseline_endpoints.get(key, {}) if isinstance(baseline_endpoints, dict) else {}
            if key in [r["endpoint"] for r in summary["regressions"]]:
                # Attach failure message
                reg_items = [r for r in summary["regressions"] if r["endpoint"] == key]
                msg_lines = [
                    f"{ri['metric']} +{ri['delta']:.2f}ms (baseline {ri['baseline']} -> {ri['observed']})"
                    for ri in reg_items
                ]
                ET.SubElement(case, "failure", message="; ".join(msg_lines)).text = "\n".join(
                    msg_lines
                )
        tree = ET.ElementTree(testsuite)
        JUNIT_REPORT_PATH.parent.mkdir(parents=True, exist_ok=True)
        tree.write(JUNIT_REPORT_PATH, encoding="utf-8", xml_declaration=True)
        print("Wrote JUnit performance report", JUNIT_REPORT_PATH)

    if regression:
        for r in summary["regressions"]:
            print(
                f"::error::Regression {r['endpoint']} {r['metric']} +{r['delta']:.2f}ms (baseline {r['baseline']} -> {r['observed']})"
            )
        return 1
    # Optional persistence of daily performance snapshot
    if os.getenv("PERF_RECORD", "").lower() in ("1", "true", "yes") and metrics:
        try:
            from datetime import datetime

            from autogen.advanced_backend import get_workflows_repo  # lazy import

            repo = get_workflows_repo()
            if repo and hasattr(repo, "upsert_daily_perf"):
                date_str = datetime.utcnow().date().isoformat()
                for endpoint, data in metrics.items():
                    repo.upsert_daily_perf(
                        date_str,
                        endpoint,
                        data.get("median_ms"),
                        data.get("p95_ms"),
                        int(data.get("samples", 0) or 0),
                    )
                print("Recorded daily performance metrics for", date_str)
        except Exception as e:  # pragma: no cover
            print("Warning: failed to record daily perf:", e)
    if not summary["regressions"] and baseline_endpoints:
        print("All tracked endpoints within tolerance or improved.")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())
