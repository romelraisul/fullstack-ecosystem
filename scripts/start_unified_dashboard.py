#!/usr/bin/env python
"""Unified Master Dashboard startup wrapper.

Provides a thin layer around uvicorn/fastapi app defined in unified_master_dashboard.py.
Auto-detects whether an ASGI 'app' object exists; falls back to executing the module.

Usage examples:
  python scripts/start_unified_dashboard.py
  python scripts/start_unified_dashboard.py --port 8099 --reload
  python scripts/start_unified_dashboard.py --host 0.0.0.0 --log-level debug

Environment:
  UMD_PORT (int) default 8088 if --port not supplied
  UMD_HOST (str) default 127.0.0.1 if --host not supplied

Exits non‑zero on failure; prints diagnostic guidance for common errors (port in use,
missing module, import errors).
"""
from __future__ import annotations
import argparse, importlib, os, sys, socket

DEFAULT_HOST = "127.0.0.1"
DEFAULT_PORT = int(os.environ.get("UMD_PORT", "8088"))


def port_available(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        s.settimeout(0.25)
        return s.connect_ex((host, port)) != 0


def load_dashboard_module():
    try:
        return importlib.import_module("unified_master_dashboard")
    except ModuleNotFoundError as e:
        print("[ERROR] Could not import unified_master_dashboard.py (ensure repo root on PYTHONPATH)", file=sys.stderr)
        raise


def main():
    parser = argparse.ArgumentParser(description="Start Unified Master Dashboard (FastAPI)")
    parser.add_argument("--host", default=os.environ.get("UMD_HOST", DEFAULT_HOST))
    parser.add_argument("--port", type=int, default=DEFAULT_PORT)
    parser.add_argument("--reload", action="store_true", help="Enable auto-reload (dev only)")
    parser.add_argument("--log-level", default="info")
    parser.add_argument("--workers", type=int, default=1)
    args = parser.parse_args()

    if not port_available(args.host, args.port):
        print(f"[WARN] Port {args.port} already in use on {args.host}. Continuing attempt to bind...", file=sys.stderr)

    mod = load_dashboard_module()
    app = getattr(mod, "app", None)

    if app is None:
        print("[INFO] No 'app' attribute found; executing module as script.")
        # Fallback: exec module file directly (will likely start its own server)
        with open(mod.__file__, "rb") as f:  # type: ignore[arg-type]
            code = compile(f.read(), mod.__file__, 'exec')  # type: ignore[arg-type]
            exec(code, {"__name__": "__main__"})
        return

    try:
    import uvicorn  # type: ignore[import-not-found]
    except ImportError:
        print("[ERROR] uvicorn not installed. Install with 'pip install uvicorn'", file=sys.stderr)
        sys.exit(2)

    print(f"[INFO] Starting Unified Master Dashboard on http://{args.host}:{args.port}")
    uvicorn.run(app, host=args.host, port=args.port, reload=args.reload, log_level=args.log_level, workers=args.workers)


if __name__ == "__main__":
    main()
