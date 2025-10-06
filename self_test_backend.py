"""Self-test helper: starts backend in SAFE_MODE, polls /health and /executive_dashboard.html,
then terminates the server process. Exits with code 0 on success, 1 on failure.
"""

import contextlib
import os
import socket
import subprocess
import sys
import time

import requests

ROOT = os.path.dirname(__file__)
PY = sys.executable

# Find a free port to avoid conflicts/permission issues
sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
sock.bind(("127.0.0.1", 0))
free_port = sock.getsockname()[1]
sock.close()

proc = subprocess.Popen([PY, "run_backend.py", "--safe", "--port", str(free_port)], cwd=ROOT)
try:
    # Wait for server to start
    timeout = 20
    deadline = time.time() + timeout
    health_ok = False
    dash_ok = False
    while time.time() < deadline:
        try:
            r = requests.get(f"http://127.0.0.1:{free_port}/health", timeout=1.0)
            if r.status_code == 200:
                health_ok = True
        except Exception:
            pass
        try:
            r2 = requests.get(f"http://127.0.0.1:{free_port}/executive_dashboard.html", timeout=1.0)
            if r2.status_code == 200:
                dash_ok = True
        except Exception:
            pass
        if health_ok and dash_ok:
            print("SELF-TEST: PASS")
            proc.terminate()
            proc.wait(timeout=5)
            sys.exit(0)
        time.sleep(0.5)
    print("SELF-TEST: FAIL (timeout)")
    proc.terminate()
    proc.wait(timeout=5)
    sys.exit(1)
except KeyboardInterrupt:
    with contextlib.suppress(Exception):
        proc.terminate()
    sys.exit(1)
