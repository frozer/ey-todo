"""Origin / Referer validation for state-changing requests (CSRF defence in depth).

It is the only CSRF protection for login and register, which have no session
and therefore no synchronizer token yet.
"""
from collections.abc import Awaitable, Callable
from urllib.parse import urlsplit

from fastapi import Request, Response, status
from fastapi.responses import JSONResponse

SAFE_METHODS = {"GET", "HEAD", "OPTIONS"}


def _origin_of(url: str) -> str | None:
  parts = urlsplit(url)
  if not parts.scheme or not parts.netloc:
    return None
  return f"{parts.scheme}://{parts.netloc}"


def request_origin(request: Request) -> str | None:
  """The browser-reported origin of the request: Origin, else the Referer's origin."""
  origin = request.headers.get("origin")
  if origin:
    return origin

  referer = request.headers.get("referer")
  if referer:
    # an unparseable Referer counts as untrusted, not as absent
    return _origin_of(referer) or referer

  return None


def origin_check_middleware(trusted_origins: list[str]):
  trusted = {origin.rstrip("/") for origin in trusted_origins}

  async def check_origin(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
  ) -> Response:
    if request.method not in SAFE_METHODS:
      origin = request_origin(request)
      # no Origin and no Referer: not a browser, so not a CSRF vector
      if origin is not None and origin.rstrip("/") not in trusted:
        return JSONResponse(
          status_code=status.HTTP_403_FORBIDDEN,
          content={"detail": [{"msg": "origin_not_allowed"}]},
        )

    return await call_next(request)

  return check_origin
