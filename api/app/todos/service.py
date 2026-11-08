from datetime import datetime

from sqlalchemy import delete, select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import TodoRow
from .schemas import Todo


class TodoStore:
  async def getAll(
    self,
    session: AsyncSession,
    user_id: str,
    filter: dict[str,str] | None = None,
    limit: int = 10,
  ) -> list[Todo]:
    
    conditions = [TodoRow.user_id == user_id]
        
    if filter is not None:
      for key, value in filter.items():
        if key == "q":        
          conditions.append(TodoRow.label.ilike(value))
    
    stmt = select(TodoRow).where(*conditions).order_by(TodoRow.lft,TodoRow.created_at)
    
    result = await session.stream_scalars(stmt)

    items: list[Todo] = []

    async for row in result:
      items.append(Todo(
        id=str(row.id),
        label=row.label,
        text=row.text,
        lft=row.lft,
        rgt=row.rgt,
        created_at=row.created_at,
        status=row.status
      ))

    return items

  async def create(
      self,
      session: AsyncSession,
      label: str,
      text: str,
      user_id: str,
      now: datetime
  ) -> Todo:
    row = TodoRow(
      user_id=user_id,
      label=label,
      text=text,
      created_at=now
    )

    session.add(row)

    await session.commit()

    return Todo(
      id=row.id,
      label=row.label,
      text=row.text,
      lft=row.lft,
      rgt=row.rgt,
      created_at=row.created_at,
      status=row.status
    )

  async def delete(
      self,
      session: AsyncSession,
      id: str,
      user_id: str
  ) -> None:
    stmt = delete(TodoRow).where(TodoRow.id == id, TodoRow.user_id == user_id)
    await session.execute(stmt)
    await session.commit()
