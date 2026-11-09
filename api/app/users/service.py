from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import UserRow


class UserStore:
  async def create(
      self,
      session: AsyncSession,
      username: str,
      password_hash: str
  ) -> UserRow | None:
    row = UserRow(
      username=username,
      password_hash=password_hash
    )

    try:
      session.add(row)
      await session.commit()
    except IntegrityError as e:
      await session.rollback()
      
      print(f"Unique constraint or integrity violation occurred: {e}")
      
      if "unique" in str(e.orig).lower() or "duplicate" in str(e.orig).lower():
        raise ValueError("Username already exists!")
      
    return row

  async def get(
        self,
        session: AsyncSession,
        username: str,
    ) -> UserRow | None:
      return await session.scalar(select(UserRow).where(UserRow.username == username))
      
