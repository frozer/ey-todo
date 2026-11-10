"""Serve the built SPA (Vite `dist/`) from the API process.

`/assets/*` holds content-hashed bundles and is cached forever; every other
non-API path gets a root-level file if one exists (favicon.svg, ...) or
falls back to `index.html` so client-side routes survive a reload.
"""
import logging
from pathlib import Path

from fastapi import FastAPI, HTTPException, status
from fastapi.responses import FileResponse, HTMLResponse, Response
from fastapi.staticfiles import StaticFiles
from starlette.types import Scope

logger = logging.getLogger(__name__)

NO_CACHE_HEADERS: dict[str, str] = {"Cache-Control": "no-cache, no-store, must-revalidate"}
IMMUTABLE_CACHE = "public, max-age=31536000, immutable"


class ImmutableStaticFiles(StaticFiles):
  """StaticFiles for content-hashed bundles: safe to cache forever."""

  async def get_response(self, path: str, scope: Scope) -> Response:
    response = await super().get_response(path, scope)
    if response.status_code == status.HTTP_200_OK:
      response.headers["Cache-Control"] = IMMUTABLE_CACHE
    return response


def mount_webapp(app: FastAPI, directory: str | None) -> None:
  """Mount the SPA on `app`. Must be called after all other routes are registered."""
  if not directory:
    return

  root = Path(directory).resolve()
  index = root / "index.html"
  if not index.is_file():
    logger.warning("webapp dir %s has no index.html; SPA serving disabled", root)
    return

  html = index.read_text(encoding="utf-8")

  assets = root / "assets"
  if assets.is_dir():
    app.mount("/assets", ImmutableStaticFiles(directory=assets), name="assets")

  @app.api_route("/{path:path}", methods=["GET", "HEAD"], include_in_schema=False)
  def spa(path: str) -> Response:
    # unknown API paths stay JSON 404s instead of returning the SPA shell
    if path == "api" or path.startswith("api/"):
      raise HTTPException(status_code=status.HTTP_404_NOT_FOUND)

    if path:
      candidate = (root / path).resolve()
      if candidate.is_relative_to(root) and candidate.is_file():
        return FileResponse(candidate)

    return HTMLResponse(content=html, headers=NO_CACHE_HEADERS)
