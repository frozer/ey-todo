from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timedelta
from typing import Annotated

from fastapi import Depends, HTTPException, Request, Response, status
from sqlalchemy.ext.asyncio import AsyncSession

from ..core.clock import get_clock, is_past
from ..core.config import Settings
from ..database.models import SessionRow
from ..deps import SessionDep, SettingsDep, UserSessionStore, UserSessionStoreDep
from .security import generate_session_token, hash_session_token

SESSION_COOKIE_KEY = "__Host-session"
DEV_SESSION_COOKIE_KEY = "session"

@dataclass(frozen=True)
class UserContext:
  user_id: str
  username: str
  session_hash: str

def get_cookie_key(is_dev: bool = False):
  return SESSION_COOKIE_KEY if is_dev == False else DEV_SESSION_COOKIE_KEY

def _not_authenticated() -> HTTPException:
  return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=[{"msg": "not_authenticated"}])

def _session_token(request: Request, is_dev: bool = False) -> str:
  return request.cookies.get(get_cookie_key(is_dev))

def _session_is_expired(user_session: SessionRow, now: datetime, idle_minutes: int) -> bool:
  idle_deadline = user_session.last_seen_at + timedelta(minutes=idle_minutes)
  return is_past(idle_deadline, now) or is_past(user_session.expires_at, now)

def _session_is_live(user_session: SessionRow, now: datetime, idle_minutes: int) -> bool:
  return not _session_is_expired(user_session, now, idle_minutes)

async def _authenticate(
  request: Request,
  now: datetime,
  session: AsyncSession,
  user_session_store: UserSessionStore,
  settings: Settings
) -> UserContext:
  token = _session_token(request, settings.environment == "DEV")
  if token is None:
    raise _not_authenticated()

  session_hash = hash_session_token(token)

  user_session = await user_session_store.get(session, session_hash)

  if user_session is None:
    raise _not_authenticated()

  if not _session_is_live(user_session, now, settings.session_idle_expire_minutes):
    await user_session_store.delete(session, session_hash)
    raise _not_authenticated()

  context = UserContext(
    user_id=user_session.user.id,
    username=user_session.user.username,
    session_hash=session_hash,
  )
  await user_session_store.update_last_seen(session, session_hash, now)

  return context

async def set_session_cookie(
    response: Response,
    now: datetime,
    session: AsyncSession,
    user_session_store: UserSessionStore,
    user_id: str,
    is_dev: bool = False
  ):
    token = generate_session_token()
    token_hash = hash_session_token(token)

    await user_session_store.clear(session, user_id)
    await user_session_store.create(session, user_id, token_hash, now)
    
    response.set_cookie(
      key=get_cookie_key(is_dev),
      value=token,
      httponly=True,
      secure=is_dev != True,
      samesite="lax",
      path="/"
    )

async def require_user_session(
    request: Request,
    clock: Annotated[Callable[[], datetime], Depends(get_clock)],
    session: SessionDep,
    user_session_store: UserSessionStoreDep,
    settings: SettingsDep
) -> UserContext:
    return await _authenticate(request, clock(), session, user_session_store, settings)

UserSessionContext = Annotated[UserContext, Depends(require_user_session)]