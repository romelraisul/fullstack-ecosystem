import os
import time

import pytest
import requests
import urllib3
from urllib3.exceptions import InsecureRequestWarning

urllib3.disable_warnings(category=InsecureRequestWarning)

DEFAULT_URLS = ["https://localhost:8444/blockchain"]
env_urls = os.getenv("SECURITY_HEADER_URLS", "")
URLS = [u.strip() for u in env_urls.split(",") if u.strip()] or DEFAULT_URLS

DISALLOWED_HEADERS = [
    "Server",  # prevent disclosing server stack
    "X-Powered-By",  # common framework leakage
    "X-AspNet-Version",  # framework disclosure
    "X-Powered-By-Plesk",  # hosting panel disclosure
]


@pytest.mark.parametrize("url", URLS)
@pytest.mark.parametrize("header", DISALLOWED_HEADERS)
def test_disallowed_headers_absent(url, header):
    deadline = time.time() + 10
    last_exc = None
    while time.time() < deadline:
        try:
            resp = requests.get(url, verify=False, timeout=2)
            break
        except Exception as exc:
            last_exc = exc
            time.sleep(0.5)
    else:  # pragma: no cover
        raise AssertionError(f"Service at {url} not reachable: {last_exc}")

    assert header not in resp.headers, f"Disallowed header {header} unexpectedly present on {url}"
