import pytest
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.main import create_app

pytestmark = pytest.mark.asyncio

CREDS = {"username": "alice", "password": "correct-horse-battery"}


# --- synchronizer token ------------------------------------------------------

async def test_me_returns_csrf_token(auth_client):
  resp = await auth_client.get("/api/auth/me")
  assert resp.status_code == 200
  assert resp.json()["csrf_token"] == auth_client.headers["X-CSRF-Token"]


async def test_each_login_gets_a_new_token(auth_client):
  first = auth_client.headers["X-CSRF-Token"]
  resp = await auth_client.post("/api/auth/login", json=CREDS)
  assert resp.status_code == 200
  assert resp.json()["csrf_token"] != first


async def test_get_needs_no_token(auth_client):
  del auth_client.headers["X-CSRF-Token"]
  assert (await auth_client.get("/api/todos")).status_code == 200
  assert (await auth_client.get("/api/auth/me")).status_code == 200


@pytest.mark.parametrize("token", [None, "wrong-token"])
async def test_unsafe_requests_need_the_token(auth_client, token):
  todo = (await auth_client.post("/api/todos", json={"label": "x"})).json()

  if token is None:
    del auth_client.headers["X-CSRF-Token"]
  else:
    auth_client.headers["X-CSRF-Token"] = token

  expected = {"detail": [{"msg": "csrf_failed"}]}
  for resp in (
    await auth_client.post("/api/todos", json={"label": "y"}),
    await auth_client.patch(f"/api/todos/{todo['id']}", json={"label": "z"}),
    await auth_client.delete(f"/api/todos/{todo['id']}"),
    await auth_client.post("/api/auth/logout"),
  ):
    assert resp.status_code == 403
    assert resp.json() == expected


async def test_token_of_another_session_is_rejected(auth_client):
  async with AsyncClient(transport=ASGITransport(app=auth_client._transport.app), base_url="http://test") as other:
    resp = await other.post("/api/auth/login", json=CREDS)
    other_token = resp.json()["csrf_token"]

  auth_client.headers["X-CSRF-Token"] = other_token
  assert (await auth_client.post("/api/todos", json={"label": "x"})).status_code == 403


async def test_unauthenticated_unsafe_request_is_401_not_403(client):
  # no session: authentication fails first
  assert (await client.post("/api/todos", json={"label": "x"})).status_code == 401


# --- origin check --------------------------------------------------------------

async def test_login_from_foreign_origin_is_rejected(auth_client):
  resp = await auth_client.post(
    "/api/auth/login", json=CREDS, headers={"Origin": "https://evil.example"}
  )
  assert resp.status_code == 403
  assert resp.json() == {"detail": [{"msg": "origin_not_allowed"}]}


async def test_foreign_referer_without_origin_is_rejected(auth_client):
  resp = await auth_client.post(
    "/api/auth/login", json=CREDS, headers={"Referer": "https://evil.example/page"}
  )
  assert resp.status_code == 403


async def test_trusted_origin_is_accepted(auth_client):
  resp = await auth_client.post(
    "/api/auth/login", json=CREDS, headers={"Origin": "http://localhost:5173"}
  )
  assert resp.status_code == 200

  resp = await auth_client.post(
    "/api/auth/login", json=CREDS, headers={"Referer": "http://localhost:5173/login?from=/"}
  )
  assert resp.status_code == 200


async def test_no_origin_and_no_referer_is_accepted(auth_client):
  assert (await auth_client.post("/api/auth/login", json=CREDS)).status_code == 200


async def test_safe_methods_skip_origin_check(auth_client):
  resp = await auth_client.get("/api/auth/me", headers={"Origin": "https://evil.example"})
  assert resp.status_code == 200


# --- CORS --------------------------------------------------------------------------

async def test_no_cors_headers_by_default():
  app = create_app(Settings(environment="DEV"))
  async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
    resp = await c.get("/health", headers={"Origin": "https://evil.example"})
  assert "access-control-allow-origin" not in resp.headers


async def test_configured_cors_origin_is_allowed():
  app = create_app(Settings(environment="DEV", cors_origins=["http://app.example"]))
  async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
    resp = await c.get("/health", headers={"Origin": "http://app.example"})
    assert resp.headers["access-control-allow-origin"] == "http://app.example"
    assert resp.headers["access-control-allow-credentials"] == "true"

    preflight = await c.options("/api/todos", headers={
      "Origin": "http://app.example",
      "Access-Control-Request-Method": "POST",
      "Access-Control-Request-Headers": "content-type,x-csrf-token",
    })
    assert preflight.status_code == 200

    foreign = await c.get("/health", headers={"Origin": "https://evil.example"})
    assert "access-control-allow-origin" not in foreign.headers
