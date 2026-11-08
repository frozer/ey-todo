import uuid
from collections.abc import Callable
from datetime import datetime
from typing import Annotated

from fastapi import APIRouter, Depends, HTTPException, status

from ..auth.session import UserContext, require_user_session
from ..core.clock import get_clock
from ..deps import SessionDep, TodoStoreDep
from .schemas import Todo, TodoCreate, TodosResponse

router = APIRouter(prefix="/todos", tags=["todo"])

@router.get("", response_model=TodosResponse)
async def list(
  session: SessionDep,
  store: TodoStoreDep,
  ctx: Annotated[
    UserContext, Depends(require_user_session)
  ],
  q: str | None = None
):
  filter: dict[str,str] = {}
  
  if q is not None:
    filter["q"] = q

  items = await store.getAll(session, ctx.user_id, filter)

  return TodosResponse(
    items=items
  )

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
  label = body.label.strip()
  text = body.text.strip()

  if (len(label) < 1):
    raise HTTPException(
      status_code=status.HTTP_422_UNPROCESSABLE_CONTENT, 
      detail={"description": "label_too_short"}
    )

  return await store.create(session, label, text, ctx.user_id, clock())

@router.delete("/{item_id}", response_model=None)
async def delete(
  item_id: uuid.UUID,
  session: SessionDep,
  store: TodoStoreDep,
  ctx: Annotated[
    UserContext, Depends(require_user_session)
  ]
):
  return await store.delete(session, item_id, ctx.user_id)

@router.patch("/{item_id}", response_model=None)
async def update(
  body: Todo,
  session: SessionDep,
  store: TodoStoreDep,
  ctx: Annotated[
    UserContext, Depends(require_user_session)
  ]
):
  return await store.update(session, body, ctx.user_id)

