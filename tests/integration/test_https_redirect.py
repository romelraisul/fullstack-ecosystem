import requests

BASE_URL_HTTP = "http://localhost:8080"
BASE_URL_HTTPS = "https://localhost:8444"


def test_http_to_https_redirect():
    """
    Tests that a request to the HTTP endpoint is redirected to the HTTPS endpoint.
    """
    response = requests.get(BASE_URL_HTTP, allow_redirects=False, verify=False)
    assert response.status_code == 301
    assert response.headers["Location"] == BASE_URL_HTTPS + "/"
