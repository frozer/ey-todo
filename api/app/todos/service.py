import uuid
from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import TodoRow
from .schemas import Todo, TodoCreate, TodosMeta, TodosResponse, TodoUpdate

# naive implementation of sparse ordering
STEP = 1000

# columns that may not be NULL, so an explicit null in a PATCH means "leave as is"
NON_NULLABLE_UPDATE_FIELDS = {"label", "status"}


class TodoNotFound(LookupError):
  """The todo does not exist, is removed, or belongs to another user."""


class RebalanceRequired(Exception):
  """No integer position is left between the two neighbours."""


class InvalidNeighbours(ValueError):
  """The left neighbour is not before the right one (stale client order)."""


def generate_position(left: int | None, right: int | None) -> int:
    if left is None and right is None:
        return 0  # First record

    if left is None:
        return right - STEP

    if right is None:
        return left + STEP

    if left >= right:
        raise InvalidNeighbours()

    if right - left == 1:
        raise RebalanceRequired()

    return (left + right) // 2


def _to_todo(row: TodoRow) -> Todo:
  return Todo(
    id=row.id,
    label=row.label,
    text=row.text,
    position=row.position,
    created_at=row.created_at,
    modified_at=row.modified_at,
    removed_at=row.removed_at,
    status=row.status
  )


class TodoStore:
  def _active(self, user_id: str):
    return [
      TodoRow.user_id == user_id,
      TodoRow.is_removed == False
    ]

  async def getAll(
    self,
    session: AsyncSession,
    user_id: str,
    filter: dict[str,str] | None = None,
    limit: int = 100,
    offset: int = 0,
  ) -> TodosResponse:

    conditions = self._active(user_id)

    if filter is not None:
      for key, value in filter.items():
        if key == "q":
          conditions.append(TodoRow.label.ilike(f"%{value}%"))

    # fetch one extra row to learn whether another page exists
    stmt = select(TodoRow).where(*conditions).order_by(
      TodoRow.position,
      TodoRow.created_at
    ).limit(limit + 1).offset(offset)

    rows = (await session.scalars(stmt)).all()

    return TodosResponse(
      items=[_to_todo(row) for row in rows[:limit]],
      meta=TodosMeta(has_more=len(rows) > limit)
    )

  async def create(
      self,
      session: AsyncSession,
      item: TodoCreate,
      user_id: str,
      now: datetime
  ) -> Todo:
    min_position = await session.scalar(
      select(func.min(TodoRow.position)).where(*self._active(user_id))
    )

    row = TodoRow(
      user_id=user_id,
      label=item.label,
      text=item.text,
      created_at=now,
      position=generate_position(None, min_position)
    )

    session.add(row)
    await session.commit()

    return _to_todo(row)

  async def delete(
      self,
      session: AsyncSession,
      id: uuid.UUID,
      user_id: str,
      now: datetime
  ) -> Todo:
    stmt = update(TodoRow).where(
      TodoRow.id == id, *self._active(user_id)
    ).values(
      is_removed=True,
      removed_at=now
    ).returning(TodoRow)

    row = (await session.execute(stmt)).scalar_one_or_none()
    if row is None:
      raise TodoNotFound()

    await session.commit()
    return _to_todo(row)

  async def update(
      self,
      session: AsyncSession,
      item: TodoUpdate,
      id: uuid.UUID,
      user_id: str,
      now: datetime
  ) -> Todo:
    update_data = {
      key: value
      for key, value in item.model_dump(exclude_unset=True, exclude={"lft", "rgt"}).items()
      if not (value is None and key in NON_NULLABLE_UPDATE_FIELDS)
    }
    update_data["modified_at"] = now

    stmt = update(TodoRow).where(
      TodoRow.id == id, *self._active(user_id)
    ).values(**update_data).returning(TodoRow)

    row = (await session.execute(stmt)).scalar_one_or_none()
    if row is None:
      raise TodoNotFound()

    await session.commit()
    return _to_todo(row)

  async def get(
      self,
      session: AsyncSession,
      id: uuid.UUID,
      user_id: str
  ) -> Todo:
    row = await session.scalar(
      select(TodoRow).where(TodoRow.id == id, *self._active(user_id))
    )
    if row is None:
      raise TodoNotFound()

    return _to_todo(row)

  async def _position_of(
      self,
      session: AsyncSession,
      id: uuid.UUID | None,
      user_id: str
  ) -> int | None:
    # a column select bypasses the identity map, so it sees bulk updates
    if id is None:
      return None

    position = await session.scalar(
      select(TodoRow.position).where(TodoRow.id == id, *self._active(user_id))
    )
    if position is None:
      raise TodoNotFound()

    return position

  async def _rebalance(self, session: AsyncSession, user_id: str) -> None:
    """Respace the user's active todos to multiples of STEP, keeping their order."""
    ids = (await session.scalars(
      select(TodoRow.id).where(*self._active(user_id)).order_by(
        TodoRow.position,
        TodoRow.created_at
      )
    )).all()

    await session.execute(
      update(TodoRow),
      [{"id": todo_id, "position": index * STEP} for index, todo_id in enumerate(ids)]
    )

  async def reorder(
      self,
      session: AsyncSession,
      item: TodoUpdate,
      id: uuid.UUID,
      user_id: str,
      now: datetime
  ) -> Todo:
    await self._position_of(session, id, user_id)  # 404 before any rebalance

    async def neighbours() -> tuple[int | None, int | None]:
      return (
        await self._position_of(session, item.lft, user_id),
        await self._position_of(session, item.rgt, user_id),
      )

    try:
      position = generate_position(*await neighbours())
    except RebalanceRequired:
      await self._rebalance(session, user_id)
      position = generate_position(*await neighbours())

    stmt = update(TodoRow).where(
      TodoRow.id == id, *self._active(user_id)
    ).values(
      position=position,
      modified_at=now
    ).returning(TodoRow)

    row = (await session.execute(stmt)).scalar_one()
    await session.commit()
    return _to_todo(row)
