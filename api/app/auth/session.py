from ..database.models import SessionRow
from dataclasses import dataclass
from fastapi import Depends, HTTPException, Request, status
from .security import hash_session_token
from datetime import datetime, timedelta
from ..core.clock import is_past, get_clock
from ..core.config import Settings
from typing import Annotated
from collections.abc import Callable
from sqlalchemy.ext.asyncio import AsyncSession
from ..deps import UserSessionStoreDep, SessionDep, UserSessionStore, SettingsDep

SESSION_COOKIE_KEY = "__Host-session"

@dataclass(frozen=True)
class UserContext:
  user_id: str
  username: str
  session_hash: str

def _not_authenticated() -> HTTPException:
  return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"description": "not_authenticated"})

def _session_token(request: Request) -> str:
  print(request.cookies.get(SESSION_COOKIE_KEY))
  return request.cookies.get(SESSION_COOKIE_KEY)

def _session_is_expired(user_session: SessionRow, now: datetime, session_idle: int) -> bool:
  idle_deadline = user_session.last_seen_at + timedelta(days=session_idle)
  return idle_deadline < now or is_past(user_session.expires_at, now)


def _session_is_live(user_session: SessionRow, now: datetime, session_idle: int) -> bool:
  return not _session_is_expired(user_session, now, session_idle)

async def _authenticate(
  request: Request,
  now: datetime,
  session: AsyncSession,
  user_session_store: UserSessionStore,
  settings: Settings
) -> UserContext:
  token = _session_token(request)
  if token is None:
    raise _not_authenticated()

  session_hash = hash_session_token(token)
  context: UserContext | None = None

  user_session = await user_session_store.get(session, session_hash)

  if _session_is_live(user_session, now, settings.session_idle_expire_minutes):
    await user_session_store.update_last_seen(session, session_hash, now)
    context = UserContext(
      user_id=user_session.user.id,
      username=user_session.user.username,
      session_hash=session_hash,
    )

  elif _session_is_expired(user_session, now):
    await user_session_store.clear(session, session_hash)

  if context is None:
    raise _not_authenticated()
    
  return context

async def require_user_session(
    request: Request,
    clock: Annotated[Callable[[], datetime], Depends(get_clock)],
    session: SessionDep,
    user_session_store: UserSessionStoreDep,
    settings: SettingsDep
) -> UserContext:
    return await _authenticate(request, clock(), session, user_session_store, settings)

UserSessionContext = Annotated[UserContext, Depends(require_user_session)]