import json
import time
from datetime import datetime, timedelta, timezone
from pathlib import Path

from fastapi.testclient import TestClient

from governance_app.app import app
from governance_app.persistence import DB_PATH, init_db

BADGE_PATH = Path("badge-governance-stats.json")
HISTORY_DIR = Path("metrics-history")


def main():
    if not DB_PATH.exists():
        init_db()  # in case no runs yet; badge will show zeros
    client = TestClient(app)
    stats = client.get("/stats").json()
    label = "governance"
    total_runs = stats["total_runs"]
    total_findings = stats["total_findings"]
    # compute pinned/unpinned first (done below but we predeclare for message)
    unpinned = 0
    pinned = 0
    for a in stats.get("actions", []):
        unpinned += a.get("unpinned", 0) or 0
        pinned += a.get("pinned", 0) or 0
    total_actions = pinned + unpinned
    unpinned_pct = (unpinned / total_actions * 100) if total_actions else 0
    message = f"runs:{total_runs} findings:{total_findings} unpinned:{unpinned_pct:.0f}%"
    # color weighting prioritizes high unpinned ratio over raw count
    if unpinned_pct == 0:
        color = "brightgreen"
    elif unpinned_pct <= 25:
        color = "green"
    elif unpinned_pct <= 50:
        color = "yellow"
    elif unpinned_pct <= 75:
        color = "orange"
    else:
        color = "red"
    ts = int(time.time())
    # Compute simple pinned vs unpinned if available
    # unpinned/pinned already computed above
    ratio = None
    if (unpinned + pinned) > 0:
        ratio = f"unpinned:{unpinned} pinned:{pinned}"  # extended info (not primary message)
    badge = {
        "schemaVersion": 1,
        "label": label,
        "message": message,
        "color": color,
        "timestamp": ts,
        "unpinned": unpinned,
        "pinned": pinned,
        "ratio": ratio,
    }
    BADGE_PATH.write_text(json.dumps(badge, indent=2))
    print(f"Wrote {BADGE_PATH}")
    # Snapshot
    HISTORY_DIR.mkdir(exist_ok=True)
    snap_name = datetime.now(timezone.utc).strftime("governance-stats-%Y%m%d%H%M%S.json")
    (HISTORY_DIR / snap_name).write_text(json.dumps(badge))
    print(f"Snapshot -> {HISTORY_DIR / snap_name}")
    # Prune snapshots older than 90 days
    cutoff = datetime.now(timezone.utc) - timedelta(days=90)
    for f in HISTORY_DIR.glob("governance-stats-*.json"):
        try:
            stamp = f.name.removeprefix("governance-stats-").removesuffix(".json")
            dt = datetime.strptime(stamp, "%Y%m%d%H%M%S")
            dt = dt.replace(tzinfo=timezone.utc)
            if dt < cutoff:
                f.unlink()
        except Exception:
            continue


if __name__ == "__main__":
    main()
