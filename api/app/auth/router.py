import asyncio
from fastapi import APIRouter, Depends, HTTPException, Request, Response, status
from .schemas import MeResponse, RegisterBody
from .security import hash_password, password_policy_error, verify_password, generate_session_token, hash_session_token, dummy_hash
from ..deps import SessionDep, UserStoreDep, UserSessionStoreDep, SettingsDep
from ..database.models import UserRow
from typing import Annotated
from .session import SESSION_COOKIE_KEY, UserContext, require_user_session
from ..core.clock import get_clock
from collections.abc import Callable
from datetime import datetime

router = APIRouter(prefix="/auth", tags=["auth"])

def _check_password(password: str, stored: str | None) -> bool:
  return verify_password(password, stored or dummy_hash())

def _failure_reason(user: UserRow | None, password_ok: bool) -> str | None:
  if user is None:
    return "unknown_user"
  if not password_ok:
    return "bad_password"
  return None

@router.post("/register", response_model=MeResponse)
async def register(
  body: RegisterBody,
  request: Request,
  session: SessionDep,
  user_store: UserStoreDep):
  username = body.username.strip().lower()

  if (len(username) < 1):
    raise HTTPException(
      status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, 
      detail={"description": "username_too_short"}
    )
  
  violation = password_policy_error(
    body.password, body.username, ""
  )

  if violation is not None:
    raise HTTPException(
      status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
      detail={"description": violation}
    )
  
  password_hash = await asyncio.to_thread(hash_password, body.password)

  await user_store.create(session, username, password_hash)

  return MeResponse(username=username)

@router.post("/login", response_model=MeResponse)
async def login(
  body: RegisterBody,
  response: Response, 
  session: SessionDep, 
  user_store: UserStoreDep,
  session_store: UserSessionStoreDep,
  settings: SettingsDep,
  clock: Annotated[Callable[[], datetime], Depends(get_clock)],
):
  username = body.username.strip().lower()

  user = await user_store.get(session, username)
  user_id = user.id if user is not None else None
  stored = user.password_hash if user is not None else None
  
  password_ok = await asyncio.to_thread(_check_password, body.password, stored)

  token = generate_session_token()
  token_hash = hash_session_token(token)

  reason = _failure_reason(user, password_ok)

  if reason is None:
    await session_store.clear(session, user_id)
    await session_store.create(session, user_id, token_hash)
  else:
    return HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail={"description": "invalid_credentials"})

  response.set_cookie(
    key=SESSION_COOKIE_KEY,
    value=token,
    httponly=True,
    secure=True if settings.environment == "DEV" else False,
    samesite="lax",
    path="/"
  )

  return MeResponse(username=username)

@router.get("/me", response_model=MeResponse)
async def me(
  ctx: Annotated[
        UserContext, Depends(require_user_session)
    ],
):
  return MeResponse(
        username=ctx.username
    )