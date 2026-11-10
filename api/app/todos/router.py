import uuid
from collections.abc import Callable
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, Query

from ..auth.session import UserContext, require_user_session
from ..core.clock import get_clock
from ..deps import SessionDep, TodoStoreDep
from .schemas import FilterParams, Todo, TodoCreate, TodosResponse, TodoUpdate

router = APIRouter(prefix="/todos", tags=["todo"])

@router.get("", response_model=TodosResponse)
async def list(
  filter_query: Annotated[FilterParams, Query()],
  session: SessionDep,
  store: TodoStoreDep,
  ctx: Annotated[
    UserContext, Depends(require_user_session)
  ],
  q: str | None = None
):
  filter: dict[str,str] = {}
  
  if filter_query.q:
    filter["q"] = filter_query.q

  return await store.getAll(session, ctx.user_id, filter)


@router.post("", response_model=Todo)
async def create(
  body: TodoCreate,
  session: SessionDep,
  store: TodoStoreDep,
  ctx: Annotated[
    UserContext, Depends(require_user_session)
  ],
  clock: Annotated[Callable[[], datetime], Depends(get_clock)],
):
  return await store.create(session, body, ctx.user_id, clock())

@router.delete("/{item_id}", response_model=None)
async def delete(
  item_id: uuid.UUID,
  session: SessionDep,
  store: TodoStoreDep,
  ctx: Annotated[
    UserContext, Depends(require_user_session)
  ],
  clock: Annotated[Callable[[], datetime], Depends(get_clock)],
):
  return await store.delete(session, item_id, ctx.user_id, clock())

@router.patch("/{item_id}", response_model=None)
async def update(
  item_id: uuid.UUID,
  body: TodoUpdate,
  session: SessionDep,
  store: TodoStoreDep,
  ctx: Annotated[
    UserContext, Depends(require_user_session)
  ],
  clock: Annotated[Callable[[], datetime], Depends(get_clock)],
):
  if hasattr(body,"rgt") and hasattr(body,"rgt"):
    return await store.reorder(session, TodoUpdate(lft=body.lft,rgt=body.rgt), item_id, ctx.user_id, clock())    
  
  return await store.update(session, body, item_id, ctx.user_id, clock())

@router.get("/{item_id}", response_model=Todo)
async def get(
  item_id: uuid.UUID,
  session: SessionDep,
  store: TodoStoreDep,
  ctx: Annotated[
    UserContext, Depends(require_user_session)
  ]
):
 return await store.get(session, item_id, ctx.user_id)