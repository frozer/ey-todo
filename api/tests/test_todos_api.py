import uuid

import pytest
from sqlalchemy import select, update

from app.database.models import TodoRow, UserRow
from app.todos.service import STEP, TodoStore

pytestmark = pytest.mark.asyncio


async def _create(client, label: str, **extra) -> dict:
  resp = await client.post("/api/todos", json={"label": label, **extra})
  assert resp.status_code == 200, resp.text
  return resp.json()


async def _labels(client) -> list[str]:
  resp = await client.get("/api/todos")
  assert resp.status_code == 200, resp.text
  return [t["label"] for t in resp.json()["items"]]


async def _set_positions(session_factory, positions: dict[str, int]) -> None:
  async with session_factory() as s:
    for todo_id, position in positions.items():
      await s.execute(
        update(TodoRow).where(TodoRow.id == uuid.UUID(todo_id)).values(position=position)
      )
    await s.commit()


# --- 404 -------------------------------------------------------------------

@pytest.mark.parametrize("method,body", [
  ("GET", None),
  ("PATCH", {"label": "x"}),
  ("DELETE", None),
])
async def test_unknown_todo_is_404(auth_client, method, body):
  resp = await auth_client.request(method, f"/api/todos/{uuid.uuid4()}", json=body)
  assert resp.status_code == 404
  assert resp.json() == {"detail": [{"msg": "todo_not_found"}]}


async def test_other_users_todo_is_404(auth_client):
  todo = await _create(auth_client, "alice's")

  # registering logs this client in as bob
  resp = await auth_client.post(
    "/api/auth/register", json={"username": "bob", "password": "correct-horse-battery"}
  )
  assert resp.status_code == 200

  assert (await auth_client.get(f"/api/todos/{todo['id']}")).status_code == 404
  assert (await auth_client.patch(f"/api/todos/{todo['id']}", json={"label": "x"})).status_code == 404
  assert (await auth_client.delete(f"/api/todos/{todo['id']}")).status_code == 404


async def test_delete_twice_is_404(auth_client):
  todo = await _create(auth_client, "once")
  assert (await auth_client.delete(f"/api/todos/{todo['id']}")).status_code == 200
  assert (await auth_client.delete(f"/api/todos/{todo['id']}")).status_code == 404


async def test_reorder_with_unknown_neighbour_is_404(auth_client):
  todo = await _create(auth_client, "a")
  resp = await auth_client.patch(f"/api/todos/{todo['id']}", json={"lft": str(uuid.uuid4())})
  assert resp.status_code == 404


# --- optional text ---------------------------------------------------------

async def test_create_without_text(auth_client):
  todo = await _create(auth_client, "no text")
  assert todo["text"] is None


async def test_blank_text_is_stored_as_null(auth_client):
  todo = await _create(auth_client, "blank", text="   ")
  assert todo["text"] is None


async def test_patch_empty_text_clears_it(auth_client):
  todo = await _create(auth_client, "has text", text="details")

  resp = await auth_client.patch(f"/api/todos/{todo['id']}", json={"text": ""})
  assert resp.status_code == 200, resp.text
  assert resp.json()["text"] is None


async def test_patch_null_label_and_status_are_ignored(auth_client):
  todo = await _create(auth_client, "keep me", status="open")

  resp = await auth_client.patch(
    f"/api/todos/{todo['id']}", json={"label": None, "status": None, "text": "new"}
  )
  assert resp.status_code == 200, resp.text
  body = resp.json()
  assert body["label"] == "keep me"
  assert body["status"] == todo["status"]
  assert body["text"] == "new"


async def test_patch_position_is_ignored(auth_client):
  todo = await _create(auth_client, "fixed")
  await auth_client.patch(f"/api/todos/{todo['id']}", json={"position": 5, "label": "fixed2"})

  got = (await auth_client.get(f"/api/todos/{todo['id']}")).json()
  assert got["position"] == todo["position"]
  assert got["label"] == "fixed2"


# --- has_more --------------------------------------------------------------

async def test_has_more_false_when_everything_fits(auth_client):
  await _create(auth_client, "a")
  await _create(auth_client, "b")
  resp = await auth_client.get("/api/todos")
  assert resp.json()["meta"] == {"has_more": False}


async def test_has_more_at_page_boundary(auth_client, session_factory):
  for label in ("a", "b", "c"):
    await _create(auth_client, label)

  store = TodoStore()
  async with session_factory() as s:
    user_id = await s.scalar(select(UserRow.id).where(UserRow.username == "alice"))

    page = await store.getAll(s, user_id, limit=2)
    assert len(page.items) == 2
    assert page.meta.has_more is True

    page = await store.getAll(s, user_id, limit=3)
    assert len(page.items) == 3
    assert page.meta.has_more is False


# --- rebalance ---------------------------------------------------------------

async def test_reorder_into_full_gap_rebalances(auth_client, session_factory):
  c = await _create(auth_client, "c")
  b = await _create(auth_client, "b")
  a = await _create(auth_client, "a")
  await _set_positions(session_factory, {a["id"]: 0, b["id"]: 1, c["id"]: 2})

  # no integer between 0 and 1: must rebalance, then insert
  resp = await auth_client.patch(f"/api/todos/{c['id']}", json={"lft": a["id"], "rgt": b["id"]})
  assert resp.status_code == 200, resp.text
  assert await _labels(auth_client) == ["a", "c", "b"]

  items = (await auth_client.get("/api/todos")).json()["items"]
  assert [t["position"] for t in items] == [0, STEP // 2, STEP]


async def test_reorder_with_stale_neighbours_is_409(auth_client):
  c = await _create(auth_client, "c")
  b = await _create(auth_client, "b")
  a = await _create(auth_client, "a")

  # lft (c) is after rgt (a) in the current order
  resp = await auth_client.patch(f"/api/todos/{b['id']}", json={"lft": c["id"], "rgt": a["id"]})
  assert resp.status_code == 409
  assert resp.json() == {"detail": [{"msg": "stale_order"}]}
  assert await _labels(auth_client) == ["a", "b", "c"]
