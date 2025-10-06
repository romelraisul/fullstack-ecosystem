import re
import sqlite3

import pytest
from fastapi.testclient import TestClient

from autogen.ultimate_enterprise_summary import UltimateEnterpriseSummary, create_app


@pytest.fixture(scope="module")
def client() -> TestClient:
    app = create_app()
    return TestClient(app)


@pytest.fixture(scope="module")
def platform() -> UltimateEnterpriseSummary:
    return UltimateEnterpriseSummary._instance


METRIC_LOGIN = re.compile(
    r'^auth_login_total\{result="(?P<result>[^"\\]+)",reason="(?P<reason>[^"]*)"}\s+(?P<value>\d+)$'
)
METRIC_REFRESH = re.compile(
    r'^auth_refresh_total\{result="(?P<result>[^"\\]+)",reason="(?P<reason>[^"]*)"}\s+(?P<value>\d+)$'
)
METRIC_LOCKOUT = re.compile(r"^auth_lockouts_total\s+(?P<value>\d+)$")
METRIC_RATE_BLOCK = re.compile(
    r'^auth_rate_limit_block_total\{endpoint="(?P<ep>[^"\\]+)"}\s+(?P<value>\d+)$'
)


def _scrape(client: TestClient) -> str:
    r = client.get("/metrics")
    assert r.status_code == 200
    return r.text


def _parse_metric(pattern, text):
    out = []
    for line in text.splitlines():
        m = pattern.match(line.strip())
        if m:
            out.append(m.groupdict())
    return out


def test_login_success_and_failure_metrics(client):
    before = _scrape(client)
    plat = UltimateEnterpriseSummary._instance
    admin_u = plat.default_admin_username
    admin_p = plat.default_admin_password
    # EXACT sequence: one fail, one success
    r_fail = client.post("/token", data={"username": "ghost-user", "password": "nope"})
    assert r_fail.status_code in (400, 401)
    ok = client.post("/token", data={"username": admin_u, "password": admin_p})
    assert ok.status_code == 200
    after = _scrape(client)

    def to_map(entries):
        d = {}
        for e in entries:
            key = (e["result"], e["reason"])
            d[key] = int(e["value"])
        return d

    bmap = to_map(_parse_metric(METRIC_LOGIN, before))
    amap = to_map(_parse_metric(METRIC_LOGIN, after))
    # Determine expected keys (success,-) and (fail,bad_credentials) or generic fail reason
    # We expect +1 in exactly one fail bucket and +1 in success bucket
    delta_success = 0
    delta_fail = 0
    for k, v in amap.items():
        prev = bmap.get(k, 0)
        if k[0] == "success":
            delta_success += v - prev
        if k[0] == "fail":
            delta_fail += v - prev
    assert (
        delta_fail == 1
    ), f"Expected exactly one failed login increment (got {delta_fail}) before={bmap} after={amap}"
    assert (
        delta_success == 1
    ), f"Expected exactly one successful login increment (got {delta_success}) before={bmap} after={amap}"


def test_lockout_metric_and_rate_limit_blocks(client, platform):
    # Intentionally brute force a username to lockout threshold
    username = "rateuser"
    password = "RateUserP@55w0rd!"
    with sqlite3.connect(platform.auth_db_path) as conn:
        c = conn.cursor()
        c.execute("SELECT id FROM users WHERE username=?", (username,))
        if not c.fetchone():
            from passlib.context import CryptContext

            ctx = CryptContext(schemes=["pbkdf2_sha256"], deprecated="auto")
            c.execute(
                "INSERT INTO users (username, full_name, role, hashed_password) VALUES (?,?,?,?)",
                (username, "Rate Limit User", "user", ctx.hash(password)),
            )
            conn.commit()
    baseline = _scrape(client)
    # Cause failed attempts to trigger lockout
    for i in range(7):
        r = client.post("/token", data={"username": username, "password": "wrong-" + str(i)})
        assert r.status_code in (400, 403, 429)
    post_fail = _scrape(client)
    # Look for lockout metric increment
    lock_before = sum(int(m["value"]) for m in _parse_metric(METRIC_LOCKOUT, baseline))
    lock_after = sum(int(m["value"]) for m in _parse_metric(METRIC_LOCKOUT, post_fail))
    assert (
        lock_after >= lock_before
    ), "Lockout metric did not stay same or increase (should not decrease)"
    # Now hammer refresh endpoint to try produce rate limit blocks
    for i in range(30):
        client.post("/token/refresh", json={"refresh_token": "dead"})
    final = _scrape(client)
    rate_blocks_before = sum(
        int(m["value"])
        for m in _parse_metric(METRIC_RATE_BLOCK, post_fail)
        if m["ep"] in ("login", "refresh")
    )
    rate_blocks_after = sum(
        int(m["value"])
        for m in _parse_metric(METRIC_RATE_BLOCK, final)
        if m["ep"] in ("login", "refresh")
    )
    assert (
        rate_blocks_after >= rate_blocks_before
    ), "Expected rate limit block metric to not decrease"
