import math
from typing import Annotated

from fastapi import Depends, HTTPException, Request, status

from ..auth.session import UserContext, require_user_session
from .service import InMemoryTokenBucket, RateLimiter

_limiter = InMemoryTokenBucket()

def get_rate_limiter() -> RateLimiter:
  return _limiter

RateLimiterDep = Annotated[RateLimiter, Depends(get_rate_limiter)]

def _route_label(request: Request) -> str:
  route_function = request.scope.get("endpoint")
  return route_function.__name__ if route_function else "unknown"

async def _consume(limiter: RateLimiter, key: str, capacity: float, refill_rate_token_per_sec: float) -> None:
  d = await limiter.check(key, capacity, refill_rate_token_per_sec)
  if not d.allowed:
    raise HTTPException(
      status_code=status.HTTP_429_TOO_MANY_REQUESTS,
      headers={"Retry-After": str(math.ceil(d.retry_after))},
      detail=[{"msg": "rate_limited"}],
    )

def rate_limit(capacity: float, refill_rate_token_per_sec: float):
  """Per client IP and route; for anonymous endpoints."""
  async def dep(request: Request, limiter: RateLimiterDep) -> None:
    client_ip = request.client.host if request.client else "-"
    await _consume(limiter, f"{_route_label(request)}:ip:{client_ip}", capacity, refill_rate_token_per_sec)

  return Depends(dep)

def user_rate_limit(capacity: float, refill_rate_token_per_sec: float):
  """Per authenticated user and route; unauthenticated requests get 401 first."""
  async def dep(
    request: Request,
    limiter: RateLimiterDep,
    # cached per request: shares the endpoint's own require_user_session call
    ctx: Annotated[UserContext, Depends(require_user_session)],
  ) -> None:
    await _consume(limiter, f"{_route_label(request)}:user:{ctx.user_id}", capacity, refill_rate_token_per_sec)

  return Depends(dep)
