import pytest
from httpx import ASGITransport, AsyncClient
from sqlalchemy import func, select

from app.database.models import SessionRow
from app.main import app

pytestmark = pytest.mark.asyncio


async def _session_count(session_factory) -> int:
  async with session_factory() as s:
    return await s.scalar(select(func.count()).select_from(SessionRow))


async def test_me_after_register(auth_client):
  resp = await auth_client.get("/api/auth/me")
  assert resp.status_code == 200
  assert resp.json()["username"] == "alice"


async def test_idle_session_expires_with_401_and_is_deleted(auth_client, clock, session_factory):
  assert await _session_count(session_factory) == 1

  clock.advance(minutes=31)
  resp = await auth_client.get("/api/auth/me")

  assert resp.status_code == 401
  assert await _session_count(session_factory) == 0


async def test_activity_slides_idle_window(auth_client, clock):
  for _ in range(3):
    clock.advance(minutes=29)
    assert (await auth_client.get("/api/auth/me")).status_code == 200


async def test_absolute_expiry_despite_activity(auth_client, clock):
  # touch the session every 20 minutes for 7 days
  for _ in range(7 * 24 * 3):
    clock.advance(minutes=20)
    await auth_client.get("/api/auth/me")

  clock.advance(minutes=1)
  assert (await auth_client.get("/api/auth/me")).status_code == 401


async def test_unknown_cookie_is_401(client):
  client.cookies.set("session", "bogus")
  assert (await client.get("/api/auth/me")).status_code == 401


async def test_username_is_normalized(client):
  resp = await client.post(
    "/api/auth/register",
    json={"username": "  Bob ", "password": "correct-horse-battery"},
  )
  assert resp.status_code == 200, resp.text
  assert resp.json()["username"] == "bob"

  dup = await client.post(
    "/api/auth/register",
    json={"username": "BOB", "password": "correct-horse-battery"},
  )
  assert dup.status_code == 409

  login = await client.post(
    "/api/auth/login",
    json={"username": "Bob", "password": "correct-horse-battery"},
  )
  assert login.status_code == 200


async def test_password_is_not_stripped(client):
  await client.post(
    "/api/auth/register",
    json={"username": "carol", "password": " spaced-password "},
  )
  bad = await client.post(
    "/api/auth/login",
    json={"username": "carol", "password": "spaced-password"},
  )
  assert bad.status_code == 401


# --- logout / revocation ------------------------------------------------------

async def _session_rows(session_factory) -> list[SessionRow]:
  async with session_factory() as s:
    return list((await s.scalars(select(SessionRow))).all())


async def test_logout_revokes_current_session(auth_client, clock, session_factory):
  token = auth_client.cookies.get("session")

  resp = await auth_client.post("/api/auth/logout")
  assert resp.status_code == 200
  set_cookie = resp.headers["set-cookie"]
  assert set_cookie.startswith('session=""') or "Max-Age=0" in set_cookie

  assert (await auth_client.get("/api/auth/me")).status_code == 401

  rows = await _session_rows(session_factory)
  assert len(rows) == 1
  assert rows[0].revoked_at == clock.now

  # replaying the old token after logout still fails, and the row is kept
  auth_client.cookies.set("session", token)
  assert (await auth_client.get("/api/auth/me")).status_code == 401
  assert len(await _session_rows(session_factory)) == 1


async def test_sessions_on_several_devices(auth_client, session_factory):
  async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as other:
    resp = await other.post(
      "/api/auth/login",
      json={"username": "alice", "password": "correct-horse-battery"},
    )
    assert resp.status_code == 200
    other.headers["X-CSRF-Token"] = resp.json()["csrf_token"]

    assert (await auth_client.get("/api/auth/me")).status_code == 200
    assert (await other.get("/api/auth/me")).status_code == 200

    assert (await other.post("/api/auth/logout")).status_code == 200

    assert (await other.get("/api/auth/me")).status_code == 401
    assert (await auth_client.get("/api/auth/me")).status_code == 200

  rows = await _session_rows(session_factory)
  assert sorted(row.revoked_at is not None for row in rows) == [False, True]
