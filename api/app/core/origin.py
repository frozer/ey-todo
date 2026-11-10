"""Origin / Referer validation for state-changing requests (CSRF defence in depth).

It is the only CSRF protection for login and register, which have no session
and therefore no synchronizer token yet.

An unsafe request is accepted when any of these holds:
* the browser marks it `Sec-Fetch-Site: same-origin`
* its Origin (or Referer origin) equals the origin it was sent to, i.e. the
  SPA is served by this same server; the victim's browser sets both Origin
  and Host, so a cross-site page cannot forge a match
* its Origin is in the configured trusted list (other front-end origins)
* it carries neither Origin nor Referer (not a browser, so not a CSRF vector)

Behind a reverse proxy the request scheme comes from X-Forwarded-Proto only
when the proxy is trusted (uvicorn `--forwarded-allow-ips`), and the proxy
must forward the original Host header.
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


def own_origin(request: Request) -> str | None:
  """The origin this request was addressed to: scheme + Host header."""
  host = request.headers.get("host")
  if not host:
    return None
  return f"{request.url.scheme}://{host}".lower()


def origin_check_middleware(trusted_origins: list[str]):
  trusted = {origin.rstrip("/").lower() for origin in trusted_origins}

  async def check_origin(
    request: Request,
    call_next: Callable[[Request], Awaitable[Response]],
  ) -> Response:
    if request.method not in SAFE_METHODS and not _is_allowed(request):
      return JSONResponse(
        status_code=status.HTTP_403_FORBIDDEN,
        content={"detail": [{"msg": "origin_not_allowed"}]},
      )

    return await call_next(request)

  def _is_allowed(request: Request) -> bool:
    # set by the browser itself and not settable by page scripts
    if request.headers.get("sec-fetch-site") == "same-origin":
      return True

    origin = request_origin(request)
    # no Origin and no Referer: not a browser, so not a CSRF vector
    if origin is None:
      return True

    origin = origin.rstrip("/").lower()
    return origin == own_origin(request) or origin in trusted

  return check_origin
