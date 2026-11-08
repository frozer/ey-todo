from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from ..database.models import UserRow


class UserStore:
  async def create(
      self,
      session: AsyncSession,
      username: str,
      password_hash: str
  ) -> str:
    row = UserRow(
      username=username,
      password_hash=password_hash
    )

    session.add(row)
    await session.commit()

    return username

  async def get(
        self,
        session: AsyncSession,
        username: str,
    ) -> UserRow | None:
      return await session.scalar(select(UserRow).where(UserRow.username == username))
      
