from datetime import datetime

from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import TodoRow
from .schemas import Todo, TodoCreate, TodoUpdate


class TodoStore:
  async def getAll(
    self,
    session: AsyncSession,
    user_id: str,
    filter: dict[str,str] | None = None,
    limit: int = 10,
  ) -> list[Todo]:
    
    conditions = [
      TodoRow.user_id == user_id,
      TodoRow.is_removed == False
    ]
        
    if filter is not None:
      for key, value in filter.items():
        if key == "q":        
          conditions.append(TodoRow.label.ilike(value))
    
    stmt = select(TodoRow).where(*conditions).order_by(
      TodoRow.position,
      TodoRow.created_at
    )
    
    result = await session.stream_scalars(stmt)

    items: list[Todo] = []

    async for row in result:
      items.append(Todo(
        id=str(row.id),
        label=row.label,
        text=row.text,
        position=row.position,
        created_at=row.created_at,
        modified_at=row.modified_at,
        status=row.status
      ))

    return items

  async def create(
      self,
      session: AsyncSession,
      item: TodoCreate,
      user_id: str,
      now: datetime
  ) -> Todo:
    row = TodoRow(
      user_id=user_id,
      label=item.label,
      text=item.text,
      created_at=now
    )

    session.add(row)

    await session.commit()

    return Todo(
      id=row.id,
      label=row.label,
      text=row.text,
      position=row.position,
      created_at=row.created_at,
      status=row.status
    )

  async def delete(
      self,
      session: AsyncSession,
      id: str,
      user_id: str,
      now: datetime
  ) -> None:
    conditions = [
      TodoRow.id == id, 
      TodoRow.user_id == user_id
    ]
    stmt = update(TodoRow).where(*conditions).values(
      is_removed=True,
      removed_at=now
    ).returning(TodoRow)
    
    result = await session.execute(stmt)
    await session.commit()
    
    row = result.scalar_one()
    return Todo(
      id=row.id,
      label=row.label,
      text=row.text,
      position=row.position,
      created_at=row.created_at,
      removed_at=row.removed_at,
      status=row.status
    )
  
  async def update(
      self,
      session: AsyncSession,
      item: TodoUpdate,
      id: str,
      user_id: str,
      now: datetime
  ) -> Todo:
    conditions = [
      TodoRow.id == id, 
      TodoRow.user_id == user_id,
      TodoRow.is_removed == False
    ]
    update_data = item.model_dump(exclude_unset=True)
    update_data["modified_at"] = now
    stmt = update(TodoRow).where(*conditions).values(**update_data).returning(TodoRow)

    result = await session.execute(stmt)
    await session.commit()

    row = result.scalar_one()

    return Todo(
      id=row.id,
      label=row.label,
      text=row.text,
      position=row.position,
      created_at=row.created_at,
      modified_at=row.modified_at,
      status=row.status
    )