from collections.abc import AsyncIterator
from pathlib import Path

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient

from app.core.config import Settings
from app.main import create_app

INDEX = "<!doctype html><title>spa</title>"


@pytest.fixture
def dist(tmp_path: Path) -> Path:
  root = tmp_path / "dist"
  (root / "assets").mkdir(parents=True)
  (root / "index.html").write_text(INDEX)
  (root / "favicon.svg").write_text("<svg/>")
  (root / "assets" / "app-abc.js").write_text("console.log(1)")
  (tmp_path / "secret.txt").write_text("top secret")
  return root


async def _client(webapp_dir: str | None) -> AsyncClient:
  app = create_app(Settings(webapp_dir=webapp_dir))
  return AsyncClient(transport=ASGITransport(app=app), base_url="http://test")


@pytest_asyncio.fixture
async def spa(dist: Path) -> AsyncIterator[AsyncClient]:
  async with await _client(str(dist)) as c:
    yield c


@pytest.mark.asyncio
@pytest.mark.parametrize("path", ["/", "/login", "/todo", "/todo?id=1"])
async def test_client_routes_get_index(spa: AsyncClient, path: str) -> None:
  resp = await spa.get(path)
  assert resp.status_code == 200
  assert resp.text == INDEX
  assert resp.headers["content-type"].startswith("text/html")
  assert "no-cache" in resp.headers["cache-control"]


@pytest.mark.asyncio
async def test_head_index(spa: AsyncClient) -> None:
  resp = await spa.head("/login")
  assert resp.status_code == 200


@pytest.mark.asyncio
async def test_assets_are_immutable(spa: AsyncClient) -> None:
  resp = await spa.get("/assets/app-abc.js")
  assert resp.status_code == 200
  assert resp.text == "console.log(1)"
  assert "immutable" in resp.headers["cache-control"]


@pytest.mark.asyncio
async def test_missing_asset_is_404(spa: AsyncClient) -> None:
  resp = await spa.get("/assets/missing.js")
  assert resp.status_code == 404


@pytest.mark.asyncio
async def test_root_public_file(spa: AsyncClient) -> None:
  resp = await spa.get("/favicon.svg")
  assert resp.status_code == 200
  assert resp.text == "<svg/>"


@pytest.mark.asyncio
@pytest.mark.parametrize("path", ["/api", "/api/nope", "/api/todos/x/y/z"])
async def test_unknown_api_path_is_json_404(spa: AsyncClient, path: str) -> None:
  resp = await spa.get(path)
  assert resp.status_code == 404
  assert resp.headers["content-type"].startswith("application/json")


@pytest.mark.asyncio
async def test_api_routes_still_win(spa: AsyncClient) -> None:
  assert (await spa.get("/health")).json() == {"status": "ok"}
  assert (await spa.get("/openapi.json")).status_code == 200


@pytest.mark.asyncio
@pytest.mark.parametrize("path", ["/..%2fsecret.txt", "/%2e%2e/secret.txt", "/assets/..%2f..%2fsecret.txt"])
async def test_no_path_traversal(spa: AsyncClient, path: str) -> None:
  resp = await spa.get(path)
  assert "top secret" not in resp.text


@pytest.mark.asyncio
async def test_disabled_without_webapp_dir() -> None:
  async with await _client(None) as c:
    assert (await c.get("/")).status_code == 404


@pytest.mark.asyncio
async def test_disabled_when_index_missing(tmp_path: Path) -> None:
  async with await _client(str(tmp_path)) as c:
    assert (await c.get("/")).status_code == 404
