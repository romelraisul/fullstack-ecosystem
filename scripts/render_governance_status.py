#!/usr/bin/env python3
"""Render a composite governance status HTML page.

Inputs (expected in CWD):
  - stability-metrics.json (optional)
  - breaking-status.json (optional)
  - placeholder-streak-badge.json (optional)
  - stability-badge.json (optional)
  - breaking-badge.json (optional)

Output:
  - governance-status.html (written to current directory unless --out specified)

The page is a lightweight static artifact that can be committed into the schemas branch (e.g. status/index.html)
so consumers (dashboards, wiki embeds) can reference a single entrypoint.
"""
from __future__ import annotations
import json, argparse, datetime, os, html

BADGE_KEYS = [
    ("breaking-badge.json", "Breaking Change Badge"),
    ("stability-badge.json", "Stability Badge"),
    ("placeholder-streak-badge.json", "Placeholder Streak Badge"),
    ("governance-combined-badge.json", "Governance + SemVer Badge"),
]

def load_json(path: str):
    if not os.path.exists(path):
        return None
    try:
        with open(path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception:
        return None

def render_badge_section():
    parts = []
    for filename, title in BADGE_KEYS:
        data = load_json(filename)
        if not data:
            continue
        # Shields.io endpoint JSON: expected keys schemaVersion, label, message, color
        label = html.escape(str(data.get('label', title)))
        message = html.escape(str(data.get('message', '')))
        color = html.escape(str(data.get('color', 'lightgrey')))
        # Inline style simple pill
        parts.append(
            f'<div class="badge"><span class="pill" style="background:{color};">{label}: {message}</span></div>'
        )
    if not parts:
        return '<p>No badges available.</p>'
    return '\n'.join(parts)


def summarize_stability(metrics: dict | None) -> str:
    if not metrics:
        return '<p>No stability metrics available.</p>'
    if metrics.get('placeholder'):
        streak = metrics.get('extensions', {}).get('placeholder_streak')
        return f'<p><strong>Placeholder metrics active.</strong> Placeholder streak: {streak}</p>'
    fields = []
    def add(label, key, transform=lambda v: v):
        v = metrics.get(key)
        if v is not None:
            try:
                v = transform(v)
            except Exception:
                pass
            fields.append(f'<li>{html.escape(label)}: {html.escape(str(v))}</li>')
    add('Window Stability Ratio', 'window_stability_ratio', lambda v: f"{v*100:.2f}%")
    add('Window Size', 'window_size')
    add('Stable Count (Window)', 'window_stable_count')
    add('Total Count (Window)', 'window_total_count')
    add('Current Stable Streak', 'current_stable_streak')
    add('Longest Stable Streak', 'longest_stable_streak')
    add('Window Mean Score', 'window_mean_score', lambda v: f"{v:.2f}")
    add('Overall Stability Ratio', 'overall_stability_ratio', lambda v: f"{v*100:.2f}%")
    return '<ul>' + '\n'.join(fields) + '</ul>' if fields else '<p>No detailed stability fields present.</p>'


def summarize_breaking(breaking: dict | None) -> str:
    if not breaking:
        return '<p>No breaking change summary available.</p>'
    added = breaking.get('breaking_changes', [])
    count = len(added) if isinstance(added, list) else 'n/a'
    score = breaking.get('score')
    lines = [f'<li>Breaking Changes Count: {html.escape(str(count))}</li>']
    if score is not None:
        lines.append(f'<li>Diff Score: {html.escape(str(score))}</li>')
    return '<ul>' + '\n'.join(lines) + '</ul>'


def summarize_semver() -> str:
    data = load_json('semver-validation.json')
    if not data:
        return '<p>No semantic version validation artifact.</p>'
    status = html.escape(str(data.get('status', 'unknown')))
    msgs = data.get('messages') or []
    recs = data.get('recommendations') or []
    color = {
        'ok': '#28a745',
        'warn': '#d4a72c',
        'fail': '#d73a49'
    }.get(data.get('status'), '#6a737d')
    body = [f'<p><strong>Status:</strong> <span style="color:{color};">{status}</span></p>']
    if msgs:
        body.append('<details><summary>Messages</summary><ul>' + ''.join(f'<li>{html.escape(str(m))}</li>' for m in msgs) + '</ul></details>')
    if recs:
        body.append('<details><summary>Recommendations</summary><ul>' + ''.join(f'<li>{html.escape(str(m))}</li>' for m in recs) + '</ul></details>')
    return '\n'.join(body)

def summarize_operations_delta() -> str:
    data = load_json('operations-classification.json')
    if not data:
        return '<p>No per-operation classification artifact.</p>'
    counts = data.get('counts') or {}
    added = data.get('operations_added') or []
    removed = data.get('operations_removed') or []
    parts = [
        '<ul>' + ''.join(
            f'<li>{html.escape(k)}: {html.escape(str(counts.get(k)))}'</li>' for k in ['added','removed','total_new','total_old'] if k in counts
        ) + '</ul>'
    ]
    if added:
        parts.append('<details><summary>Added Operations (' + str(len(added)) + ')</summary><ul>' + ''.join(
            f'<li><code>{html.escape(op.get("method","?"))}</code> {html.escape(op.get("path",""))}</li>' for op in added[:200]
        ) + ('<li>… truncated …</li>' if len(added) > 200 else '') + '</ul></details>')
    if removed:
        parts.append('<details><summary>Removed Operations (' + str(len(removed)) + ')</summary><ul>' + ''.join(
            f'<li><code>{html.escape(op.get("method","?"))}</code> {html.escape(op.get("path",""))}</li>' for op in removed[:200]
        ) + ('<li>… truncated …</li>' if len(removed) > 200 else '') + '</ul></details>')
    return '\n'.join(parts)

def build_page(stability, breaking) -> str:
    now = datetime.datetime.utcnow().isoformat() + 'Z'
    return f"""<!DOCTYPE html>
<html lang=\"en\">\n<head>\n<meta charset=\"utf-8\"/>\n<title>API Governance Status</title>\n<meta http-equiv=\"Cache-Control\" content=\"no-store, no-cache, must-revalidate\"/>\n<meta http-equiv=\"Pragma\" content=\"no-cache\"/>\n<meta http-equiv=\"Expires\" content=\"0\"/>\n<meta http-equiv=\"refresh\" content=\"300\"/>\n<style>
 body {{ font-family: system-ui, Arial, sans-serif; margin: 1.5rem; }}
 h1 {{ font-size: 1.6rem; }}
 h2 {{ margin-top: 2rem; }}
 .pill {{ display:inline-block; padding:4px 10px; border-radius:999px; color:#fff; font-size:0.85rem; margin:4px 8px 4px 0; }}
 .badge {{ display:inline-block; }}
 .section {{ background:#f8f9fa; padding:1rem 1.2rem; border:1px solid #e1e4e8; border-radius:6px; }}
 footer { margin-top:3rem; font-size:0.75rem; color:#666; }
 code { background:#f0f0f0; padding:2px 4px; border-radius:4px; }
</style>\n</head>\n<body>\n<h1>API Governance Status</h1>
<p>Generated: {now}</p>
<section class=\"section\">\n<h2>Badges</h2>\n{render_badge_section()}\n</section>
<section class=\"section\">\n<h2>Stability Metrics</h2>\n{summarize_stability(stability)}\n</section>
<section class=\"section\">\n<h2>Breaking Changes</h2>\n{summarize_breaking(breaking)}\n</section>
<section class=\"section\">\n<h2>Semantic Version Policy</h2>\n{summarize_semver()}\n</section>
<section class=\"section\">\n<h2>Per-Operation Delta</h2>\n{summarize_operations_delta()}\n</section>
<footer>Composite status artifact. Source repository: <code>{html.escape(os.environ.get('GITHUB_REPOSITORY',''))}</code></footer>
</body>\n</html>"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', default='governance-status.html')
    args = parser.parse_args()
    stability = load_json('stability-metrics.json')
    breaking = load_json('breaking-status.json')
    html_doc = build_page(stability, breaking)
    with open(args.out, 'w', encoding='utf-8') as f:
        f.write(html_doc)
    print(f"Wrote {args.out}")

if __name__ == '__main__':
    main()
