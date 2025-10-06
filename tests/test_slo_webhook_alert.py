import http.server
import json
import os
import socketserver
import threading
import time
from contextlib import contextmanager

# We must set env vars BEFORE importing the app
os.environ["SLO_ERROR_RATE_THRESHOLD"] = "0.0"  # force alert on first error
os.environ["SLO_ERROR_RATE_WINDOW"] = "5"
os.environ["SLO_ALERT_COOLDOWN_SECONDS"] = "0"  # no cooldown to simplify

_received = []


class _Handler(http.server.BaseHTTPRequestHandler):
    def do_POST(self):  # noqa: N802
        length = int(self.headers.get("Content-Length", "0"))
        body = self.rfile.read(length)
        try:
            _received.append(json.loads(body.decode("utf-8")))
        except Exception:  # pragma: no cover
            pass
        self.send_response(200)
        self.end_headers()

    def log_message(self, *args, **kwargs):
        return


@contextmanager
def webhook_server():
    with socketserver.TCPServer(("127.0.0.1", 0), _Handler) as httpd:
        port = httpd.server_address[1]
        t = threading.Thread(target=httpd.serve_forever, daemon=True)
        t.start()
        try:
            yield port
        finally:
            httpd.shutdown()


def test_slo_error_rate_webhook_triggers_payload():
    _received.clear()
    with webhook_server() as port:
        os.environ["SLO_ALERT_WEBHOOK_URL"] = f"http://127.0.0.1:{port}/hook"
        # Import after env vars set
        from fastapi.testclient import TestClient

        from autogen.advanced_backend import app

        client = TestClient(app)
        # Create one failing request by hitting a non-existent endpoint
        r = client.get("/nope/notfound")
        assert r.status_code == 404
        # Give middleware async thread time to POST
        deadline = time.time() + 2
        while time.time() < deadline and not _received:
            time.sleep(0.05)
        assert _received, "Expected at least one webhook payload"
        payload = _received[-1]
        assert "type" in payload and payload["type"].startswith("slo_")
        assert "timestamp" in payload
        assert "path" in payload
        # When threshold is 0.0 the overall error rate breach is most likely first
        # We don't assert exact type to avoid flakiness if latency breach fires first.
