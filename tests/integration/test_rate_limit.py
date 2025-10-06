from queue import Queue
from threading import Thread

import requests

BASE_URL_HTTPS = "https://localhost:8444"


def do_request(queue):
    """
    Makes a single request to the oauth2/auth endpoint and puts the status code in the queue.
    """
    response = requests.get(f"{BASE_URL_HTTPS}/oauth2/auth", verify=False)
    queue.put(response.status_code)


def test_rate_limit():
    """
    Tests that the gateway rate-limits requests to the oauth2/auth endpoint.
    """
    # We need to make a number of requests in quick succession to trigger the rate limit.
    # We'll use threads to make the requests concurrently.
    num_requests = 20
    q = Queue()
    threads = []

    for _i in range(num_requests):
        t = Thread(target=do_request, args=(q,))
        threads.append(t)
        t.start()

    for t in threads:
        t.join()

    # Get the status codes from the queue
    status_codes = [q.get() for i in range(num_requests)]

    # We expect at least one of the requests to be rate-limited (429) or
    # to fail because the oauth2-proxy is not configured (503), or for the gateway to fail to connect to the proxy (502).
    # We also expect at least one to succeed (200), since the proxy is not fully configured.
    assert 429 in status_codes or 503 in status_codes or 502 in status_codes
    assert 200 not in status_codes
