from datetime import datetime

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import TodoRow
from .schemas import Todo, TodoCreate, TodosMeta, TodosResponse, TodoUpdate

# naive implementation of sparse ordering
STEP = 1000

def RebalanceRequired() -> ValueError:
   raise ValueError("Rebalance required")

def generate_position(left: int | None, right: int | None) -> int:
    if left is None and right is None:
        return 0  # First record

    if left is None:
        return right - STEP

    if right is None:
        return left + STEP

    if right - left <= 1:
        raise RebalanceRequired()

    return (left + right) // 2

class TodoStore:
  async def getAll(
    self,
    session: AsyncSession,
    user_id: str,
    filter: dict[str,str] | None = None,
    limit: int = 100,
    offset: int = 0,
  ) -> TodosResponse:
    
    conditions = [
      TodoRow.user_id == user_id,
      TodoRow.is_removed == False
    ]
        
    if filter is not None:
      for key, value in filter.items():
        if key == "q":        
          conditions.append(TodoRow.label.ilike(f"%{value}%"))
    
    stmt = select(TodoRow).where(*conditions).order_by(
      TodoRow.position,
      TodoRow.created_at
    ).limit(limit=limit).offset(offset=offset)
    
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

    return TodosResponse(
      items=items,
      meta= TodosMeta(
         has_more=len(items) < limit
      )
    ) 

  async def create(
      self,
      session: AsyncSession,
      item: TodoCreate,
      user_id: str,
      now: datetime
  ) -> Todo:
    
    conditions = [
      TodoRow.user_id == user_id,
      TodoRow.is_removed == False
    ]

    get_min_position_stmt = select(func.min(TodoRow.position)).where(*conditions)

    min_position = await session.scalar(get_min_position_stmt)

    position = generate_position(None, min_position)
    
    row = TodoRow(
      user_id=user_id,
      label=item.label,
      text=item.text,
      created_at=now,
      position=position
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
    
    update_data = item.model_dump(exclude_unset=True,exclude=["lft","rgt"])
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

  async def get(
        self,
        session: AsyncSession,
        id: str,
        user_id: str
    ) -> Todo:
      conditions = [
        TodoRow.id == id, 
        TodoRow.user_id == user_id,
        TodoRow.is_removed == False
      ]
      
      stmt = select(TodoRow).where(*conditions)
  
      result = await session.execute(stmt)
  
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

  async def reorder(
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

      lftItem = await self.get(session, item.lft, user_id) if item.lft is not None else None
      rgtItem = await self.get(session, item.rgt, user_id) if item.rgt is not None else None

      lft = lftItem.position if lftItem is not None else None
      rgt = rgtItem.position if rgtItem is not None else None

      position = generate_position(lft, rgt)

      update_data = {
         "position": position
      }
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