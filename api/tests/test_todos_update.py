import pytest

pytestmark = pytest.mark.asyncio


async def _create(client, label: str) -> dict:
  resp = await client.post("/api/todos", json={"label": label, "text": "t"})
  assert resp.status_code == 200, resp.text
  return resp.json()


async def _list(client) -> list[dict]:
  resp = await client.get("/api/todos")
  assert resp.status_code == 200, resp.text
  return resp.json()["items"]


async def test_patch_label_keeps_position(auth_client):
  todo = await _create(auth_client, "first")
  await _create(auth_client, "second")  # pushes "first" off position 0

  resp = await auth_client.patch(f"/api/todos/{todo['id']}", json={"label": "renamed"})
  assert resp.status_code == 200, resp.text

  updated = (await auth_client.get(f"/api/todos/{todo['id']}")).json()
  assert updated["label"] == "renamed"
  assert updated["position"] == todo["position"]


async def test_patch_reorder_between_neighbours(auth_client):
  c = await _create(auth_client, "c")
  b = await _create(auth_client, "b")
  a = await _create(auth_client, "a")
  assert [t["label"] for t in await _list(auth_client)] == ["a", "b", "c"]

  # move "a" between "b" and "c"
  resp = await auth_client.patch(f"/api/todos/{a['id']}", json={"lft": b["id"], "rgt": c["id"]})
  assert resp.status_code == 200, resp.text
  assert [t["label"] for t in await _list(auth_client)] == ["b", "a", "c"]

  # move "c" to the top (no left neighbour)
  resp = await auth_client.patch(f"/api/todos/{c['id']}", json={"lft": None, "rgt": b["id"]})
  assert resp.status_code == 200, resp.text
  assert [t["label"] for t in await _list(auth_client)] == ["c", "b", "a"]


async def test_patch_mixing_reorder_and_fields_is_422(auth_client):
  a = await _create(auth_client, "a")
  b = await _create(auth_client, "b")

  resp = await auth_client.patch(f"/api/todos/{a['id']}", json={"label": "x", "lft": b["id"]})
  assert resp.status_code == 422
