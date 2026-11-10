import uuid
from collections.abc import Callable
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, Query, status

from ..auth.session import UserContext, require_user_session
from ..core.clock import get_clock
from ..core.errors import error_responses
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


@router.post("", response_model=Todo, responses=error_responses((status.HTTP_403_FORBIDDEN, "csrf_failed")))
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

@router.delete(
  "/{item_id}",
  response_model=Todo,
  responses=error_responses(
    (status.HTTP_403_FORBIDDEN, "csrf_failed"),
    (status.HTTP_404_NOT_FOUND, "todo_not_found"),
  )
)
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

@router.patch(
  "/{item_id}",
  response_model=Todo,
  responses=error_responses(
    (status.HTTP_403_FORBIDDEN, "csrf_failed"),
    (status.HTTP_404_NOT_FOUND, "todo_not_found"),
    (status.HTTP_409_CONFLICT, "stale_order"),
  )
)
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
  if body.lft is not None or body.rgt is not None:
    if body.model_fields_set - {"lft", "rgt"}:
      raise HTTPException(
        status_code=status.HTTP_422_UNPROCESSABLE_CONTENT,
        detail=[{"msg": "reorder (lft/rgt) cannot be combined with other fields"}]
      )
    return await store.reorder(session, body, item_id, ctx.user_id, clock())

  return await store.update(session, body, item_id, ctx.user_id, clock())

@router.get("/{item_id}", response_model=Todo, responses=error_responses((status.HTTP_404_NOT_FOUND, "todo_not_found")))
async def get(
  item_id: uuid.UUID,
  session: SessionDep,
  store: TodoStoreDep,
  ctx: Annotated[
    UserContext, Depends(require_user_session)
  ]
):
 return await store.get(session, item_id, ctx.user_id)