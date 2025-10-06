import sys

import requests

BASE_URL_HTTP = "http://localhost:8080"
BASE_URL_HTTPS = "https://localhost:8444"

EXPECTED_HEADERS = [
    "Content-Security-Policy",
    "Strict-Transport-Security",
    "X-Content-Type-Options",
    "X-Frame-Options",
]


def test_http_to_https_redirect():
    """
    Tests that a request to the HTTP endpoint is redirected to the HTTPS endpoint.
    """
    response = requests.get(BASE_URL_HTTP, allow_redirects=False, verify=False)
    assert response.status_code == 301
    assert response.headers["Location"] == BASE_URL_HTTPS + "/"
    print("HTTP to HTTPS redirect test passed.")


def test_security_headers_present():
    """
    Tests that the specified security headers are present in the response.
    """
    response = requests.get(BASE_URL_HTTPS, verify=False)
    missing_headers = []
    for header in EXPECTED_HEADERS:
        if header not in response.headers:
            missing_headers.append(header)

    if missing_headers:
        print(f"Error: Missing security headers: {missing_headers}")
        sys.exit(1)

    print("Security headers test passed.")


def main():
    """
    Runs all the endpoint probes.
    """
    try:
        test_http_to_https_redirect()
        test_security_headers_present()
    except Exception as e:
        print(f"Error during endpoint probe: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()
