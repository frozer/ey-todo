import asyncio
from collections.abc import Callable
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Response, status

from ..core.clock import get_clock
from ..database.models import UserRow
from ..deps import SessionDep, SettingsDep, UserSessionStoreDep, UserStoreDep
from .schemas import MeResponse, RegisterBody
from .security import (
  dummy_hash,
  hash_password,
  password_policy_error,
  verify_password,
)
from .session import (
  UserContext,
  require_user_session,
  set_session_cookie,
)

router = APIRouter(prefix="/auth", tags=["auth"])

def _check_password(password: str, stored: str | None) -> bool:
  return verify_password(password, stored or dummy_hash())

def _failure_reason(user: UserRow | None, password_ok: bool) -> str | None:
  if user is None:
    return "unknown_user"
  if not password_ok:
    return "bad_password"
  return None

@router.post("/register",
  response_model=MeResponse,
  responses={
    status.HTTP_422_UNPROCESSABLE_CONTENT: {"description": "data validation failure"},
    status.HTTP_409_CONFLICT: {"description": "Given username already exists, pick another one"}
  }
)
async def register(
  body: RegisterBody,
  response: Response,
  session: SessionDep,
  user_store: UserStoreDep,
  user_session_store: UserSessionStoreDep,
  settings: SettingsDep,
  clock: Annotated[Callable[[], datetime], Depends(get_clock)],
):

  violation = password_policy_error(
    body.password, body.username, ""
  )

  if violation is not None:
    raise HTTPException(
      status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
      detail=[{"msg": violation}]
    )
  
  password_hash = await asyncio.to_thread(hash_password, body.password)

  try:
    user = await user_store.create(session, body.username, password_hash)

    await set_session_cookie(
      response,
      clock(),
      session,
      user_session_store,
      user.id,
      settings.environment == "DEV"
    )
    
    return MeResponse(username=body.username)
  
  except ValueError:
    raise HTTPException(
      status_code=status.HTTP_409_CONFLICT,
      detail=[{"msg": "Given username already exists, pick another one"}]
    )

@router.post("/login",
  response_model=MeResponse,
  responses={
    status.HTTP_401_UNAUTHORIZED: {"description": "invalid_credentials"}
  }
)
async def login(
  body: RegisterBody,
  response: Response, 
  session: SessionDep, 
  user_store: UserStoreDep,
  user_session_store: UserSessionStoreDep,
  settings: SettingsDep,
  clock: Annotated[Callable[[], datetime], Depends(get_clock)],
):
  user = await user_store.get(session, body.username)
  stored = user.password_hash if user is not None else None
  
  password_ok = await asyncio.to_thread(_check_password, body.password, stored)

  reason = _failure_reason(user, password_ok)

  if reason is None:
    await set_session_cookie(
      response,
      clock(),
      session,
      user_session_store,
      user.id,
      settings.environment == "DEV"
    )
  else:
    raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail=[{"msg": "invalid_credentials"}])

  return MeResponse(username=body.username)

@router.get("/me", 
            response_model=MeResponse,
            responses={
              status.HTTP_401_UNAUTHORIZED: {"description": "not_authenticated"}
            })
async def me(
  ctx: Annotated[
        UserContext, Depends(require_user_session)
    ],
):
  return MeResponse(
        username=ctx.username
    )

@router.post("/logout",
  response_model=None,
  responses={
    status.HTTP_401_UNAUTHORIZED: {"description": "not_authenticated"}
  }
)
async def logout(
  session: SessionDep, 
  session_store: UserSessionStoreDep,
  ctx: Annotated[
        UserContext, Depends(require_user_session)
    ],
):
  await session_store.clear(session, ctx.user_id)