#!/usr/bin/env python3
"""Lightweight HTTP server exposing taxonomy for Grafana JSON API datasource.

Endpoints:
  GET /taxonomy          -> full taxonomy JSON
  GET /taxonomy/alerts   -> list of alert objects (alerts[])
  GET /healthz           -> 200 OK

Usage:
  python scripts/serve_taxonomy_http.py --taxonomy ../../alerts_taxonomy.json --port 8099

Grafana JSON API datasource configuration:
  URL: http://host:8099
  Allowed paths: /taxonomy, /taxonomy/alerts

Security: For local/internal use. Add auth / CORS as needed for production.
"""

from __future__ import annotations

import argparse
import json
from datetime import datetime
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path


class TaxonomyHandler(BaseHTTPRequestHandler):
    taxonomy = {}

    def _write(self, code: int, data: dict | list | str):
        body = data if isinstance(data, str) else json.dumps(data)
        b = body.encode("utf-8")
        self.send_response(code)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(b)))
        self.end_headers()
        self.wfile.write(b)

    def log_message(self, fmt, *args):  # suppress noisy default logs
        return

    def do_GET(self):  # noqa: N802
        if self.path == "/healthz":
            self._write(200, {"status": "ok", "time": datetime.utcnow().isoformat() + "Z"})
            return
        if self.path == "/taxonomy":
            self._write(200, self.taxonomy)
            return
        if self.path == "/taxonomy/alerts":
            self._write(200, self.taxonomy.get("alerts", []))
            return
        self._write(404, {"error": "not found"})


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--taxonomy", required=True)
    ap.add_argument("--port", type=int, default=8099)
    args = ap.parse_args()

    path = Path(args.taxonomy)
    TaxonomyHandler.taxonomy = json.loads(path.read_text(encoding="utf-8"))

    httpd = HTTPServer(("0.0.0.0", args.port), TaxonomyHandler)
    print(f"Serving taxonomy on :{args.port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("Shutting down")


if __name__ == "__main__":
    main()
