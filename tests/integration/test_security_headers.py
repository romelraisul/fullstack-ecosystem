import os
import time

import pytest
import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning

urllib3.disable_warnings(category=InsecureRequestWarning)

DEFAULT_URLS = [
    "https://localhost:8444/blockchain",
]

env_urls = os.getenv("SECURITY_HEADER_URLS", "")
URLS = [u.strip() for u in env_urls.split(",") if u.strip()] or DEFAULT_URLS

EXPECTED_HEADERS = [
    "Content-Security-Policy",
    "Strict-Transport-Security",
    "X-Content-Type-Options",
    "X-Frame-Options",
]


@pytest.mark.parametrize("url", URLS)
@pytest.mark.parametrize("header", EXPECTED_HEADERS)
def test_security_headers_present(url, header):
    """Ensure each expected header is present for each configured URL."""
    deadline = time.time() + 10
    last_exc = None
    while time.time() < deadline:
        try:
            response = requests.get(url, verify=False, timeout=2)
            break
        except Exception as exc:
            last_exc = exc
            time.sleep(0.5)
    else:  # pragma: no cover
        raise AssertionError(f"Service at {url} not reachable within wait window: {last_exc}")

    assert (
        header in response.headers
    ), f"{url} Missing header {header}; present keys: {list(response.headers.keys())}"
