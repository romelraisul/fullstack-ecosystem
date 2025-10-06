#!/usr/bin/env python3
"""Generate taxonomy metrics & Shields.io badge JSON files.

Outputs (in working directory):
  - badge-taxonomy.json                (last update date)
  - badge-taxonomy-age.json            (days since last change)
  - badge-alerts-total.json            (total alert count)
  - badge-alerts-deprecated.json       (deprecated ratio)
  - badge-alerts-churn.json            (30d churn)
  - badge-alerts-stability.json        (stability score)
  - badge-runbook-completeness.json    (runbook completeness %)
  - taxonomy-metrics.json              (aggregate metrics for programmatic use)

Churn definition (30d): Set difference between current alert set and the alert set
as-of the commit prior to (now - 30 days). Added = current - baseline; removed = baseline - current.
This approximates unique changes over the window (not counting intermediate flips).

Stability score: 1 - (churn_count / max(total_alerts, 1))
Runbook completeness: % of active (non-deprecated) alerts whose runbook field is NOT a placeholder.
Placeholder detection mirrors sync_alert_taxonomy lint (TODO/TBD/placeholder or empty).
"""

from __future__ import annotations

import contextlib
import json
import os
import subprocess
import sys
from datetime import date, datetime, timezone
from pathlib import Path

TAXONOMY_PATH = Path("alerts_taxonomy.json")


def load_current():
    data = json.loads(TAXONOMY_PATH.read_text(encoding="utf-8"))
    return data, data.get("alerts", [])


def get_baseline_commit(days: int = 30) -> str | None:
    """Return commit SHA of latest commit before 'days' ago touching taxonomy file, else None."""
    try:
        cmd = [
            "git",
            "rev-list",
            "-1",
            f"--before={days} days ago",
            "HEAD",
            "--",
            str(TAXONOMY_PATH),
        ]
        sha = subprocess.check_output(cmd, text=True).strip()
        return sha or None
    except Exception:
        return None


def load_alert_names_at_commit(commit: str) -> set[str]:
    try:
        raw = subprocess.check_output(["git", "show", f"{commit}:{TAXONOMY_PATH}"], text=True)
        obj = json.loads(raw)
        return {a.get("alert") for a in obj.get("alerts", []) if a.get("alert")}
    except Exception:
        return set()


def placeholder(text: str | None) -> bool:
    if not text:
        return True
    t = text.strip().lower()
    if not t:
        return True
    return t.startswith("todo") or t in {"tbd", "placeholder"}


def compute_runbook_sla(alerts: list[dict]) -> dict:
    """Compute runbook SLA stats (days to completion) for alerts list.

    Returns a dict with keys: count, median_days, avg_days, max_days
    """
    sla_days: list[int] = []
    for a in alerts:
        created = a.get("created_at")
        runbook = a.get("runbook")
        if not created or placeholder(runbook):
            continue
        try:
            cdt = datetime.fromisoformat(created.replace("Z", "+00:00"))
            days = (datetime.now(timezone.utc) - cdt).days
            sla_days.append(days)
        except Exception:
            continue
    stats = {
        "count": len(sla_days),
        "median_days": (sorted(sla_days)[len(sla_days) // 2] if sla_days else None),
        "avg_days": (round(sum(sla_days) / len(sla_days), 2) if sla_days else None),
        "max_days": (max(sla_days) if sla_days else None),
    }
    return stats


def ensure_alert_id(a: dict) -> str:
    """Return stable id for alert. If taxonomy provides `id`, use it; otherwise derive a slug.
    The slug is alert name lowercased with non-alnum replaced. This helps track renames when
    authors include a stable `id` field in the taxonomy alerts.
    """
    if a.get("id"):
        return str(a.get("id"))
    name = (a.get("alert") or "").lower()
    # simple slug
    slug = "".join(ch if ch.isalnum() else "-" for ch in name).strip("-")
    if not slug:
        slug = f"alert-{abs(hash(name))}"
    return slug


def color_scale_percentage(pct: float) -> str:
    if pct >= 95:
        return "brightgreen"
    if pct >= 90:
        return "green"
    if pct >= 80:
        return "yellowgreen"
    if pct >= 65:
        return "yellow"
    if pct >= 50:
        return "orange"
    return "red"


def color_scale_inverse(pct: float) -> str:
    if pct == 0:
        return "brightgreen"
    if pct < 5:
        return "green"
    if pct < 10:
        return "yellowgreen"
    if pct < 20:
        return "yellow"
    if pct < 30:
        return "orange"
    return "red"


def color_for_churn(churn: int) -> str:
    if churn <= 2:
        return "brightgreen"
    if churn <= 5:
        return "green"
    if churn <= 10:
        return "yellowgreen"
    if churn <= 15:
        return "yellow"
    if churn <= 25:
        return "orange"
    return "red"


def color_for_stability(score: float) -> str:
    if score >= 0.95:
        return "brightgreen"
    if score >= 0.90:
        return "green"
    if score >= 0.80:
        return "yellowgreen"
    if score >= 0.65:
        return "yellow"
    if score >= 0.50:
        return "orange"
    return "red"


def main():
    tax_obj, alerts = load_current()
    last_updated = tax_obj.get("last_updated")
    now = datetime.now(timezone.utc)
    age_days = None
    if last_updated:
        try:
            dt = datetime.fromisoformat(last_updated.replace("Z", "+00:00"))
            age_days = (now - dt).days
        except Exception:
            age_days = None

    total = len(alerts)
    deprecated_alerts = [a for a in alerts if a.get("deprecated")]
    deprecated_count = len(deprecated_alerts)
    deprecated_pct = (deprecated_count / total * 100) if total else 0.0

    baseline_commit = get_baseline_commit(30)
    if baseline_commit:
        baseline_names = load_alert_names_at_commit(baseline_commit)
        try:
            baseline_ts = subprocess.check_output(
                ["git", "show", "-s", "--format=%cI", baseline_commit], text=True
            ).strip()
        except Exception:
            baseline_ts = None
    else:
        baseline_names = set()
        baseline_ts = None

    current_names = {a.get("alert") for a in alerts if a.get("alert")}
    added_30d = sorted(current_names - baseline_names)
    removed_30d = sorted(baseline_names - current_names)
    churn_30d = len(added_30d) + len(removed_30d)

    # Risk-weighted churn (severity weighting)
    # Default weights: critical=5, high=3, medium=2, low=1 (fallback 1)
    severity_weights = {"critical": 5, "high": 3, "medium": 2, "low": 1}

    # Build mapping alert name -> severity weight for current & baseline
    def weight_for(alert_name: str, container_list):
        for a in container_list:
            if a.get("alert") == alert_name:
                sev = (a.get("severity") or "").lower()
                return severity_weights.get(sev, 1)
        return 1

    weighted_added = sum(weight_for(a, alerts) for a in added_30d)
    # For removed alerts we need their old severity; fetch from baseline JSON
    baseline_alert_objs = []
    if baseline_commit:
        try:
            raw_base = subprocess.check_output(
                ["git", "show", f"{baseline_commit}:{TAXONOMY_PATH}"], text=True
            )
            baseline_alert_objs = json.loads(raw_base).get("alerts", [])
        except Exception:
            baseline_alert_objs = []
    weighted_removed = 0
    for name in removed_30d:
        for a in baseline_alert_objs:
            if a.get("alert") == name:
                sev = (a.get("severity") or "").lower()
                weighted_removed += severity_weights.get(sev, 1)
                break
    risk_churn_30d = weighted_added + weighted_removed

    stability_score = 1.0 - (churn_30d / total) if total else 1.0
    if stability_score < 0:
        stability_score = 0.0
    stability_pct = round(stability_score * 100, 2)

    # Risk-weighted stability: subtract weighted churn from max weighted count (approx)
    # Max weighted count approximated by sum of weights of current alerts (treat each once)
    current_weight_total = 0
    for a in alerts:
        sev = (a.get("severity") or "").lower()
        current_weight_total += severity_weights.get(sev, 1)
    if current_weight_total <= 0:
        risk_stability_score = 1.0
    else:
        risk_stability_score = 1.0 - (risk_churn_30d / current_weight_total)
    if risk_stability_score < 0:
        risk_stability_score = 0.0
    risk_stability_pct = round(risk_stability_score * 100, 2)

    active_alerts = [a for a in alerts if not a.get("deprecated")]
    active_total = len(active_alerts)
    runbooks_complete = sum(1 for a in active_alerts if not placeholder(a.get("runbook")))
    runbook_pct = round((runbooks_complete / active_total * 100), 2) if active_total else 100.0

    # --- Time-to-runbook SLA tracking ---
    sla_stats = compute_runbook_sla(alerts)

    def write_badge(path: str, label: str, message: str, color: str):
        Path(path).write_text(
            json.dumps({"schemaVersion": 1, "label": label, "message": message, "color": color}),
            encoding="utf-8",
        )

    write_badge("badge-taxonomy.json", "alerts updated", (last_updated or "unknown")[:10], "blue")
    if age_days is not None:
        age_color = (
            "brightgreen"
            if age_days <= 1
            else (
                "green"
                if age_days <= 3
                else (
                    "yellowgreen"
                    if age_days <= 7
                    else "yellow" if age_days <= 14 else "orange" if age_days <= 30 else "red"
                )
            )
        )
        write_badge("badge-taxonomy-age.json", "days since change", str(age_days), age_color)
    write_badge("badge-alerts-total.json", "alerts", str(total), "blue")
    write_badge(
        "badge-alerts-deprecated.json",
        "deprecated",
        f"{deprecated_count}/{total} ({int(round(deprecated_pct))}%)" if total else "0",
        color_scale_inverse(deprecated_pct),
    )
    write_badge("badge-alerts-churn.json", "30d churn", str(churn_30d), color_for_churn(churn_30d))
    write_badge(
        "badge-alerts-stability.json",
        "stability",
        f"{stability_pct:.0f}%",
        color_for_stability(stability_score),
    )
    write_badge(
        "badge-runbook-completeness.json",
        "runbook complete",
        f"{int(round(runbook_pct))}%",
        color_scale_percentage(runbook_pct),
    )
    # New risk-weighted badges
    write_badge(
        "badge-alerts-risk-churn.json",
        "30d risk churn",
        str(risk_churn_30d),
        color_for_churn(risk_churn_30d),
    )
    write_badge(
        "badge-alerts-risk-stability.json",
        "risk stability",
        f"{int(round(risk_stability_pct))}%",
        color_for_stability(risk_stability_score),
    )

    metrics = {
        "generated_at": datetime.utcnow().isoformat() + "Z",
        "last_updated": last_updated,
        "age_days": age_days,
        "total_alerts": total,
        "deprecated_alerts": deprecated_count,
        "deprecated_percent": round(deprecated_pct, 2),
        "added_30d": added_30d,
        "removed_30d": removed_30d,
        "churn_30d": churn_30d,
        "baseline_commit_30d": baseline_commit,
        "baseline_commit_timestamp": baseline_ts,
        "stability_score": round(stability_score, 4),
        "stability_percent": stability_pct,
        "runbook_completeness_percent": runbook_pct,
        "active_alerts": active_total,
        "runbooks_complete": runbooks_complete,
        "runbook_sla": sla_stats,
        "risk_churn_30d": risk_churn_30d,
        "risk_stability_score": round(risk_stability_score, 4),
        "risk_stability_percent": risk_stability_pct,
        "severity_weights": severity_weights,
        "weighted_added_30d": weighted_added,
        "weighted_removed_30d": weighted_removed,
        "current_weight_total": current_weight_total,
    }
    Path("taxonomy-metrics.json").write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")

    # --- History snapshotting ---
    # Create metrics-history directory if not exists
    hist_dir = Path("metrics-history")
    hist_dir.mkdir(exist_ok=True)
    today_str = date.today().isoformat()
    daily_path = hist_dir / f"metrics-{today_str}.json"
    if not daily_path.exists():  # only create once per day
        daily_path.write_text(json.dumps(metrics, indent=2) + "\n", encoding="utf-8")

    # Build aggregated history (sorted by filename date) with pruning
    history_entries = []
    for p in sorted(hist_dir.glob("metrics-*.json")):
        try:
            obj = json.loads(p.read_text(encoding="utf-8"))
            obj["_snapshot_date"] = p.stem.replace("metrics-", "")
            history_entries.append(obj)
        except Exception:
            continue
    # Keep only last 180 snapshots (roughly 6 months)
    if len(history_entries) > 180:
        # Remove older files beyond last 180
        to_remove = history_entries[:-180]
        # Determine filenames to remove
        remove_dates = {e["_snapshot_date"] for e in to_remove}
        for d in remove_dates:
            fp = hist_dir / f"metrics-{d}.json"
            with contextlib.suppress(FileNotFoundError):
                fp.unlink()
        history_entries = history_entries[-180:]
    Path("taxonomy-metrics-history.json").write_text(
        json.dumps({"history": history_entries}, indent=2) + "\n", encoding="utf-8"
    )

    print("Metrics + badges generated (history updated)")

    # --- Anomaly detection (risk churn spike) ---
    try:
        spike_threshold = float(os.environ.get("RISK_CHURN_SPIKE_THRESHOLD", "2.0"))
        # compare with yesterday's risk_churn_30d
        prev = None
        if history_entries:
            # history_entries are sorted by filename - last element is newest
            prev = history_entries[-2] if len(history_entries) >= 2 else history_entries[-1]
        prev_risk = prev.get("risk_churn_30d") if prev else None
        if prev_risk is not None and prev_risk >= 0:
            # compute fold change
            fold = (risk_churn_30d / (prev_risk or 1)) if prev_risk else float("inf")
            if fold >= spike_threshold:
                msg = f"Anomaly: risk_churn_30d spike detected: {risk_churn_30d} vs previous {prev_risk} (fold {fold:.2f})"
                # Behavior: if RISK_CHURN_SPIKE_FAIL=1 then exit non-zero, else print warning
                if os.environ.get("RISK_CHURN_SPIKE_FAIL", "0") == "1":
                    print(msg, file=sys.stderr)
                    sys.exit(2)
                else:
                    print("Warning:", msg)
    except Exception as e:
        print("Anomaly detection error:", e)


if __name__ == "__main__":
    if not TAXONOMY_PATH.exists():
        print("alerts_taxonomy.json not found", file=sys.stderr)
        sys.exit(1)
    main()
