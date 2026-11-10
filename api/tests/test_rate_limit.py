import pytest
from httpx import ASGITransport, AsyncClient

from app.main import app
from app.net.service import InMemoryTokenBucket

pytestmark = pytest.mark.asyncio

CREDS = {"username": "alice", "password": "correct-horse-battery"}


async def test_login_is_limited_per_ip_and_refills(client, monotonic):
  for _ in range(5):
    assert (await client.post("/api/auth/login", json=CREDS)).status_code == 401

  resp = await client.post("/api/auth/login", json=CREDS)
  assert resp.status_code == 429
  assert resp.json() == {"detail": [{"msg": "rate_limited"}]}
  assert int(resp.headers["Retry-After"]) >= 1

  # login refills 5 tokens per minute -> one token every 12s
  monotonic.advance(12)
  assert (await client.post("/api/auth/login", json=CREDS)).status_code == 401
  assert (await client.post("/api/auth/login", json=CREDS)).status_code == 429


async def test_routes_have_separate_buckets(client):
  for _ in range(6):
    await client.post("/api/auth/login", json=CREDS)

  resp = await client.post("/api/auth/register", json=CREDS)
  assert resp.status_code == 200, resp.text


async def test_todos_are_limited_per_user(auth_client):
  async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as bob:
    resp = await bob.post(
      "/api/auth/register",
      json={"username": "bob", "password": "correct-horse-battery"},
    )
    assert resp.status_code == 200, resp.text

    for _ in range(30):
      assert (await auth_client.get("/api/todos")).status_code == 200
    resp = await auth_client.get("/api/todos")
    assert resp.status_code == 429
    assert "Retry-After" in resp.headers

    # same IP, different user: own bucket
    assert (await bob.get("/api/todos")).status_code == 200


async def test_unauthenticated_todos_get_401_not_429(client):
  for _ in range(40):
    assert (await client.get("/api/todos")).status_code == 401


async def test_eviction_drops_only_full_buckets():
  now = [0.0]
  limiter = InMemoryTokenBucket(now=lambda: now[0], max_keys=2)

  await limiter.check("used", 5, 1)
  await limiter.check("used", 5, 1)  # 3 left: refills to full after 2s
  await limiter.check("drained", 2, 0.1)
  await limiter.check("drained", 2, 0.1)  # 0 left: needs 20s to refill

  now[0] = 5.0
  await limiter.check("new", 5, 1)  # third key triggers eviction

  assert set(limiter._buckets) == {"drained", "new"}


async def _login_from(ip: str, creds: dict) -> int:
  # a separate client per source IP so the per-IP bucket never trips
  transport = ASGITransport(app=app, client=(ip, 1234))
  async with AsyncClient(transport=transport, base_url="http://test") as c:
    return (await c.post("/api/auth/login", json=creds)).status_code


async def test_login_is_limited_per_username_across_ips(client, monotonic):
  for i in range(10):
    assert await _login_from(f"10.0.0.{i}", CREDS) == 401
  # 11th try on "alice" from a fresh IP
  assert await _login_from("10.0.1.1", CREDS) == 429

  # other accounts are unaffected
  bob = {"username": "bob", "password": "correct-horse-battery"}
  assert await _login_from("10.0.1.2", bob) == 401

  # 10 tokens per 15 min -> one token back after 90s
  monotonic.advance(90)
  assert await _login_from("10.0.2.1", CREDS) == 401
  assert await _login_from("10.0.2.2", CREDS) == 429


async def test_username_bucket_is_normalized(client):
  for i in range(10):
    assert await _login_from(f"10.0.0.{i}", {**CREDS, "username": "Alice"}) == 401
  assert await _login_from("10.0.1.1", {**CREDS, "username": " alice "}) == 429
