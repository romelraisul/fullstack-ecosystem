#!/usr/bin/env python
"""Compare captured Grafana dashboard panel metadata against a baseline.

Exits non-zero if required panels are missing or overlapping differences detected.
Baseline format: list of panel objects with keys: title, type (optional), gridPos{x,y,w,h}.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def load_panels(path: Path):
    data = json.loads(path.read_text())
    # Accept either wrapper object or direct list
    if isinstance(data, dict) and "panels" in data:
        panels = data["panels"]
    elif isinstance(data, list):
        panels = data
    else:
        panels = data.get("dashboard", {}).get("panels", []) if isinstance(data, dict) else []
    norm = []
    for p in panels:
        gp = p.get("gridPos") or {}
        norm.append(
            {
                "title": p.get("title"),
                "type": p.get("type"),
                "x": gp.get("x"),
                "y": gp.get("y"),
                "w": gp.get("w"),
                "h": gp.get("h"),
            }
        )
    return norm


def overlaps(a, b):
    return not (
        a["x"] + a["w"] <= b["x"]
        or b["x"] + b["w"] <= a["x"]
        or a["y"] + a["h"] <= b["y"]
        or b["y"] + b["h"] <= a["y"]
    )


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--baseline", required=True)
    ap.add_argument("--current-glob", required=True, help="Glob for current captured dashboards")
    ap.add_argument("--min-panels", type=int, default=5)
    ap.add_argument(
        "--pos-tolerance",
        type=int,
        default=0,
        help="Allow x/y movement within this tolerance without failing",
    )
    ap.add_argument(
        "--report", default="", help="Optional JSON report path for layout drift summary"
    )
    ap.add_argument(
        "--size-threshold",
        type=int,
        default=-1,
        help="Max percent of baseline panels allowed to change size before failing (-1 disable gating)",
    )
    ap.add_argument(
        "--prom-metrics",
        default="",
        help="Optional path to write Prometheus metrics exposition format",
    )
    args = ap.parse_args()

    import glob

    current_files = glob.glob(args.current_glob)
    if not current_files:
        print("No current dashboard files found", file=sys.stderr)
        sys.exit(1)

    baseline_panels = load_panels(Path(args.baseline))
    required_titles = {p["title"] for p in baseline_panels if p.get("title")}
    baseline_index = {p["title"]: p for p in baseline_panels if p.get("title")}

    found_titles = set()
    current_panels_all = []
    for f in current_files:
        current_panels_all.extend(load_panels(Path(f)))
    for p in current_panels_all:
        if p.get("title") in required_titles:
            found_titles.add(p["title"])

    missing = required_titles - found_titles
    minor_drift = []  # list of (title, dx, dy)
    major_drift = []  # list of (title, dx, dy, dw, dh)
    size_changes_minor = []  # (title, dw, dh)
    size_changes_major = []  # (title, dw, dh)
    # Assess positional and size drift for panels present in both baseline & current
    for p in current_panels_all:
        t = p.get("title")
        if t in baseline_index and t in found_titles:
            bp = baseline_index[t]
            coords_present = all(k in p and p[k] is not None for k in ("x", "y")) and all(
                k in bp and bp[k] is not None for k in ("x", "y")
            )
            if not coords_present:
                continue
            dx = abs((p["x"] or 0) - (bp["x"] or 0))
            dy = abs((p["y"] or 0) - (bp["y"] or 0))
            dw = None
            dh = None
            if p.get("w") is not None and bp.get("w") is not None:
                dw = p["w"] - bp["w"]
            if p.get("h") is not None and bp.get("h") is not None:
                dh = p["h"] - bp["h"]
            size_changed = (dw not in (None, 0)) or (dh not in (None, 0))
            if dx == 0 and dy == 0:
                if size_changed:
                    size_changes_minor.append((t, dw or 0, dh or 0))
                continue
            if dx <= args.pos_tolerance and dy <= args.pos_tolerance:
                minor_drift.append((t, dx, dy))
                if size_changed:
                    size_changes_minor.append((t, dw or 0, dh or 0))
            else:
                major_drift.append((t, dx, dy, dw, dh))
                if size_changed:
                    size_changes_major.append((t, dw or 0, dh or 0))
    if missing:
        print("Missing required panels:", sorted(missing), file=sys.stderr)

    # Overlap detection within current set (rudimentary)
    overlaps_found = []
    for i in range(len(current_panels_all)):
        a = current_panels_all[i]
        if None in (a.get("x"), a.get("y"), a.get("w"), a.get("h")):
            continue
        for j in range(i + 1, len(current_panels_all)):
            b = current_panels_all[j]
            if None in (b.get("x"), b.get("y"), b.get("w"), b.get("h")):
                continue
            if overlaps(a, b):
                overlaps_found.append((a["title"], b["title"]))

    if len(current_panels_all) < args.min_panels:
        print(f"Panel count {len(current_panels_all)} < minimum {args.min_panels}", file=sys.stderr)

    total_panels = len(current_panels_all)

    # Panel area aggregates (treat missing width/height as 0)
    def panel_area(p):
        try:
            return int(p.get("w") or 0) * int(p.get("h") or 0)
        except Exception:
            return 0

    total_area_current = sum(panel_area(p) for p in current_panels_all)
    total_area_baseline = sum(panel_area(p) for p in baseline_panels)
    area_changed_panels = 0
    cumulative_area_delta = 0
    for t, dw, dh in size_changes_minor + size_changes_major:
        bp = baseline_index.get(t)
        cp = next((p for p in current_panels_all if p.get("title") == t), None)
        if bp and cp and bp.get("w") and bp.get("h") and cp.get("w") and cp.get("h"):
            area_before = (bp["w"] or 0) * (bp["h"] or 0)
            area_after = (cp["w"] or 0) * (cp["h"] or 0)
            delta = area_after - area_before
            if delta != 0:
                area_changed_panels += 1
                cumulative_area_delta += delta
    minor_pct = (len(minor_drift) / total_panels * 100.0) if total_panels and minor_drift else 0.0
    size_change_total = len(size_changes_minor) + len(size_changes_major)
    baseline_count = len(baseline_panels)
    size_change_pct_baseline = (
        (size_change_total / baseline_count * 100.0)
        if baseline_count and size_change_total
        else 0.0
    )
    size_threshold_breach = False
    if args.size_threshold >= 0 and size_change_pct_baseline > args.size_threshold:
        size_threshold_breach = True
        print(
            f"Size change percent {size_change_pct_baseline:.2f}% exceeds threshold {args.size_threshold}%",
            file=sys.stderr,
        )
    failing = bool(
        missing
        or overlaps_found
        or len(current_panels_all) < args.min_panels
        or major_drift
        or size_threshold_breach
    )
    if failing:
        if overlaps_found:
            print("Overlapping panels detected:", overlaps_found, file=sys.stderr)
        if major_drift:
            print("Panel major drift beyond tolerance detected:", major_drift, file=sys.stderr)
        if minor_drift:
            print(
                f"NOTE: Minor tolerated drift ({len(minor_drift)} panels = {minor_pct:.1f}% of current):",
                minor_drift,
            )
    else:
        if minor_drift:
            print(
                f"Grafana layout check passed with tolerated minor drift ({len(minor_drift)} panels = {minor_pct:.1f}% of current):",
                minor_drift,
            )
        else:
            print("Grafana layout check passed. Panels:", len(current_panels_all))

    if args.report:
        try:
            import os

            report_dir = os.path.dirname(args.report)
            if report_dir and not os.path.exists(report_dir):
                os.makedirs(report_dir, exist_ok=True)
            minor_pct_baseline = (
                (len(minor_drift) / baseline_count * 100.0)
                if baseline_count and minor_drift
                else 0.0
            )
            payload = {
                "schema_version": 2,
                "status": "fail" if failing else "pass",
                "baseline_panel_count": baseline_count,
                "current_panel_count": len(current_panels_all),
                "missing_panels": sorted(missing),
                "overlaps": overlaps_found,
                "minor_drift": minor_drift,
                "major_drift": major_drift,
                "minor_drift_percent_current": round(minor_pct, 2),
                "minor_drift_percent_baseline": round(minor_pct_baseline, 2),
                "size_changes_minor": size_changes_minor,
                "size_changes_major": size_changes_major,
                "size_change_percent_baseline": round(size_change_pct_baseline, 2),
                "size_threshold": args.size_threshold,
                "size_threshold_breach": size_threshold_breach,
                "tolerance": args.pos_tolerance,
            }
            with open(args.report, "w", encoding="utf-8") as rf:
                json.dump(payload, rf, indent=2)
            print(f"Wrote layout drift report to {args.report}")
        except Exception as ex:
            print(f"Failed to write layout report: {ex}", file=sys.stderr)

    # compute baseline minor pct even if no report for metrics
    minor_pct_baseline = (
        (len(minor_drift) / baseline_count * 100.0) if baseline_count and minor_drift else 0.0
    )

    if args.prom_metrics:
        try:
            lines = []

            def m(name, value, help_text):
                lines.append(f"# HELP {name} {help_text}")
                lines.append(f"# TYPE {name} gauge")
                lines.append(f"{name} {value}")

            m(
                "layout_minor_drift_panels",
                len(minor_drift),
                "Number of panels with minor positional drift",
            )
            m(
                "layout_major_drift_panels",
                len(major_drift),
                "Number of panels with major positional drift",
            )
            m("layout_size_change_panels", size_change_total, "Number of panels with size changes")
            m(
                "layout_size_change_percent_baseline",
                round(size_change_pct_baseline, 2),
                "Percent of baseline panels with size change",
            )
            m(
                "layout_minor_drift_percent_baseline",
                round(minor_pct_baseline, 2),
                "Percent baseline panels minor drift",
            )
            m(
                "layout_minor_drift_percent_current",
                round(minor_pct, 2),
                "Percent current panels minor drift",
            )
            m("layout_failing", 1 if failing else 0, "Layout validation failing flag")
            m("layout_total_panels", total_panels, "Total current panels considered")
            m("layout_baseline_panels", baseline_count, "Baseline panel count")
            m("layout_missing_panels", len(missing), "Number of baseline panels missing in current")
            m(
                "layout_overlapping_pairs",
                len(overlaps_found),
                "Count of detected overlapping panel pairs",
            )
            # Direct overlap presence flag
            m(
                "layout_any_overlap",
                1 if overlaps_found else 0,
                "Flag indicating at least one overlapping panel pair detected",
            )
            m(
                "layout_total_area_current",
                total_area_current,
                "Sum of areas (w*h) of current panels",
            )
            m(
                "layout_total_area_baseline",
                total_area_baseline,
                "Sum of areas (w*h) of baseline panels",
            )
            m(
                "layout_area_changed_panels",
                area_changed_panels,
                "Panels whose area changed vs baseline",
            )
            m(
                "layout_area_cumulative_delta",
                cumulative_area_delta,
                "Cumulative area delta (current-baseline)",
            )
            # Percent area delta vs baseline total (absolute cumulative delta / baseline total * 100)
            area_delta_percent = 0.0
            if total_area_baseline > 0 and cumulative_area_delta != 0:
                area_delta_percent = abs(cumulative_area_delta) / total_area_baseline * 100.0
            m(
                "layout_panel_area_delta_percent",
                round(area_delta_percent, 2),
                "Percent absolute cumulative area delta vs baseline total area",
            )
            # Aggregate change detector: 1 if any drift/size/missing/overlap condition; else 0
            any_change = bool(
                missing
                or overlaps_found
                or minor_drift
                or major_drift
                or size_change_total
                or area_changed_panels
            )
            m(
                "layout_changes_detected",
                1 if any_change else 0,
                "Flag indicating any layout drift, missing panels, overlaps or size/area changes",
            )
            if size_threshold_breach:
                m("layout_size_threshold_breach", 1, "Flag indicating size threshold breached")
            with open(args.prom_metrics, "w", encoding="utf-8") as f:
                f.write("\n".join(lines) + "\n")
            print(f"Wrote Prometheus metrics to {args.prom_metrics}")
        except Exception as ex:
            print(f"Failed writing Prometheus metrics: {ex}", file=sys.stderr)

    if failing:
        sys.exit(2)


if __name__ == "__main__":
    main()
