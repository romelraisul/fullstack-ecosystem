#!/usr/bin/env python
"""Generate a simple HTML dashboard & optional Prometheus metrics summarizing
alert taxonomy severity distribution and runbook completeness.

Inputs:
  --taxonomy alerts_taxonomy.json (expects {"alerts":[{"alert":...,"severity":...,"runbook":...}]})
Outputs:
  --html path/to/dashboard.html (default: severity_runbook_dashboard.html)
  --prom path/to/metrics.prom (optional)

Metrics exposed (if --prom):
  taxonomy_alerts_total{severity="<sev>"} count
  taxonomy_alerts_runbook_missing total_missing
  taxonomy_alerts_runbook_coverage_percent coverage_percent

HTML includes an embedded summary table + colored bars for severity mix.

Exit codes:
 0 success
 2 validation / parsing error
"""

from __future__ import annotations

import argparse
import html
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


def load_taxonomy(path: str):
    with open(path, encoding="utf-8") as f:
        data = json.load(f)
    alerts = data.get("alerts") or []
    norm = []
    for a in alerts:
        if not isinstance(a, dict):
            continue
        name = a.get("alert")
        if not name:
            continue
        norm.append(
            {
                "alert": name,
                "severity": a.get("severity") or "unknown",
                "runbook": a.get("runbook"),
                "deprecated": bool(a.get("deprecated")),
            }
        )
    return norm


def build_html(alerts: list[dict]) -> str:
    severities = [a["severity"] for a in alerts if a["severity"]]
    sev_counts = Counter(severities)
    total = len(alerts)
    runbook_missing = [a for a in alerts if not a.get("runbook") or a.get("runbook") in ("", "TBD")]
    coverage = 0.0 if total == 0 else (1 - len(runbook_missing) / total) * 100.0
    # Simple bar segments
    palette = {
        "critical": "#d32f2f",
        "high": "#f57c00",
        "medium": "#fbc02d",
        "low": "#388e3c",
        "unknown": "#607d8b",
    }
    bar_segments = []
    for sev, count in sev_counts.items():
        0 if total == 0 else (count / total) * 100
        bar_segments.append(
            f'<div title="{sev}: {count}" style="flex:{count};background:{palette.get(sev, "#424242")};height:18px"></div>'
        )
    bar_html = (
        '<div style="display:flex;width:100%;border:1px solid #ccc;border-radius:4px;overflow:hidden">'
        + "".join(bar_segments)
        + "</div>"
    )

    rows = []
    for a in sorted(alerts, key=lambda x: x["alert"]):
        rb = a.get("runbook") or ""
        rb_status = "✅" if rb and rb not in ("TBD", "") else "❌"
        rows.append(
            f"<tr><td>{html.escape(a['alert'])}</td><td>{html.escape(a['severity'])}</td><td>{rb_status}</td><td>{html.escape(rb)}</td></tr>"
        )

    now = datetime.now(timezone.utc).isoformat()
    return f"""
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="utf-8" />
  <title>Alert Severity & Runbook Dashboard</title>
  <style>
    body {{ font-family: system-ui, Arial, sans-serif; margin: 1.2rem; }}
    h1 {{ margin-top:0; }}
    table {{ border-collapse: collapse; width: 100%; font-size: 0.85rem; }}
    th, td {{ border:1px solid #ccc; padding:4px 6px; text-align:left; }}
    th {{ background:#f5f5f5; }}
    .kpi {{ display:inline-block; margin-right:1.2rem; }}
    .kpi span.value {{ font-size:1.4rem; font-weight:600; display:block; }}
  </style>
</head>
<body>
  <h1>Alert Severity & Runbook Dashboard</h1>
  <p>Generated: {now}</p>
  <div class="kpis">
    <div class="kpi"><span class="value">{total}</span>Total Alerts</div>
    <div class="kpi"><span class="value">{len(runbook_missing)}</span>Runbook Missing</div>
    <div class="kpi"><span class="value">{coverage:.1f}%</span>Runbook Coverage</div>
  </div>
  <h2>Severity Mix</h2>
  {bar_html}
  <p style="font-size:0.75rem;margin-top:4px;">{", ".join(f"{k}:{v}" for k, v in sev_counts.items())}</p>
  <h2>Alerts</h2>
  <table>
    <thead><tr><th>Alert</th><th>Severity</th><th>Runbook?</th><th>Runbook Ref</th></tr></thead>
    <tbody>
      {"".join(rows)}
    </tbody>
  </table>
</body>
</html>
""".strip()


def write_prom(alerts: list[dict], path: str):
    severities = [a["severity"] for a in alerts if a.get("severity")]
    counts = Counter(severities)
    total = len(alerts)
    runbook_missing = [a for a in alerts if not a.get("runbook") or a.get("runbook") in ("", "TBD")]
    coverage = 0.0 if total == 0 else (1 - len(runbook_missing) / total) * 100.0
    lines = [
        "# HELP taxonomy_alerts_total Total number of alerts by severity",
        "# TYPE taxonomy_alerts_total gauge",
    ]
    for sev, c in counts.items():
        lines.append(f'taxonomy_alerts_total{{severity="{sev}"}} {c}')
    lines += [
        "# HELP taxonomy_alerts_runbook_missing Alerts missing runbook reference",
        "# TYPE taxonomy_alerts_runbook_missing gauge",
        f"taxonomy_alerts_runbook_missing {len(runbook_missing)}",
        "# HELP taxonomy_alerts_runbook_coverage_percent Runbook coverage percent",
        "# TYPE taxonomy_alerts_runbook_coverage_percent gauge",
        f"taxonomy_alerts_runbook_coverage_percent {coverage:.2f}",
    ]
    with open(path, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--taxonomy", default="alerts_taxonomy.json")
    ap.add_argument("--html", default="severity_runbook_dashboard.html")
    ap.add_argument("--prom", default="")
    args = ap.parse_args()
    try:
        alerts = load_taxonomy(args.taxonomy)
    except Exception as ex:  # noqa: BLE001
        print(f"Failed to load taxonomy: {ex}", file=sys.stderr)
        sys.exit(2)

    html_doc = build_html(alerts)
    Path(args.html).write_text(html_doc, encoding="utf-8")
    print(f"Wrote dashboard HTML: {args.html} (alerts={len(alerts)})")
    if args.prom:
        write_prom(alerts, args.prom)
        print(f"Wrote taxonomy metrics: {args.prom}")


if __name__ == "__main__":
    main()
