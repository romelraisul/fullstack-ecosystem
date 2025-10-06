import logging
import os
import re

import pytest
from fastapi.testclient import TestClient

from autogen.ultimate_enterprise_summary import create_app


@pytest.fixture(scope="module")
def client():
    # Ensure JSON logging enabled
    os.environ.setdefault("SUMMARY_JSON_LOGGING", "1")
    app = create_app()
    return TestClient(app)


TRACE_RE = re.compile(r'"trace_id"\s*:\s*"([0-9a-f]{32})"')
SPAN_RE = re.compile(r'"span_id"\s*:\s*"([0-9a-f]{16})"')


@pytest.mark.skipif(
    "OTEL_EXPORTER_OTLP_ENDPOINT" not in os.environ,
    reason="Tracing not enabled environment variable missing",
)
def test_trace_and_span_ids_present_in_logs(client, capsys):
    # Invoke an endpoint to generate logs; choose /metrics (should be quick) or root if available
    client.get("/metrics")
    # Flush logging handlers
    for h in logging.getLogger().handlers:
        h.flush()
    captured = capsys.readouterr().out
    # Look for at least one log line containing trace_id and span_id
    trace_found = bool(TRACE_RE.search(captured))
    span_found = bool(SPAN_RE.search(captured))
    assert (
        trace_found and span_found
    ), f"Expected trace/span ids in logs. Output snippet: {captured.splitlines()[:5]}"
