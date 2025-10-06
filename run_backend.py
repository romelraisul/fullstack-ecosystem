"""Small CLI wrapper to run the backend with a `--safe` flag that sets SAFE_MODE
before importing the heavy module. This avoids SAFE_MODE detection timing issues when
launching from a frozen executable or the CLI.
"""

import argparse
import os

parser = argparse.ArgumentParser(description="Run advanced backend with optional SAFE_MODE")
parser.add_argument("--host", default="127.0.0.1")
parser.add_argument("--port", type=int, default=8000)
parser.add_argument("--safe", action="store_true", help="Enable SAFE_MODE before importing the app")
parser.add_argument("--workers", type=int, default=1)
args = parser.parse_args()

if args.safe:
    os.environ["SAFE_MODE"] = "1"

# Import here after SAFE_MODE is set

import uvicorn

if __name__ == "__main__":
    uvicorn.run(
        "autogen.advanced_backend:app",
        host=args.host,
        port=args.port,
        workers=args.workers,
        log_level="info",
    )
