"""Bootstrap entrypoint used for PyInstaller frozen builds.

This script parses a minimal CLI to set SAFE_MODE early (before importing the
application) so the frozen binary can be started with --safe reliably. It
then imports and runs the FastAPI app via uvicorn programmatic API when
executed as __main__.

Keep this file minimal and avoid importing heavy modules at top-level.
"""

import argparse
import os
import sys


def parse_args(argv=None):
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("--safe", action="store_true")
    parser.add_argument("--host", default=os.getenv("HOST", "127.0.0.1"))
    parser.add_argument("--port", type=int, default=int(os.getenv("PORT", "8000")))
    parser.add_argument("--workers", type=int, default=int(os.getenv("WORKERS", "1")))
    # allow passing through unknown args to the underlying app
    args, _ = parser.parse_known_args(argv)
    return args


def main(argv=None):
    args = parse_args(argv)
    if args.safe:
        os.environ["SAFE_MODE"] = "1"

    # Import the app after SAFE_MODE is set to ensure deferred initialization
    # in autogen.advanced_backend uses the correct mode.
    try:
        pass  # type: ignore
    except Exception:
        # If import fails, print the phase marker to stderr for diagnostics
        sys.stderr.write("[PHASE] BOOTSTRAP: failed importing autogen.advanced_backend\n")
        raise

    import uvicorn

    # Run uvicorn programmatically. When frozen, uvicorn.run will spawn a
    # loop that serves the ASGI app.
    uvicorn.run(
        "autogen.advanced_backend:app",
        host=args.host,
        port=args.port,
        workers=args.workers,
        log_level="info",
    )


if __name__ == "__main__":
    main(sys.argv[1:])
