from sqlalchemy.ext.asyncio import AsyncSession
from datetime import UTC, datetime, timedelta
from ..database.models import SessionRow
from ..core.config import get_settings
from sqlalchemy import delete

class UserSessionStore:
  async def create(
        self,
        session: AsyncSession,
        user_id: str,
        session_hash: str,
    ) -> SessionRow:
      last_seen_at = datetime.now(UTC)
      row = SessionRow(
        user_id=user_id,
        session_hash=session_hash,
        last_seen_at=last_seen_at,
        expires_at=last_seen_at + timedelta(days=get_settings().session_expire_days),
      )
  
      session.add(row)
      await session.commit()

      return row

  async def get(
        self,
        session: AsyncSession,
        session_hash: str
  ) -> SessionRow | None:
     return await session.get(SessionRow, session_hash)

  async def update_last_seen(
        self,
        session: AsyncSession,
        session_hash: str
  ) -> SessionRow | None:
     existing_session = await session.get(SessionRow, session_hash)
     if (existing_session is not None):
        existing_session.last_seen_at = datetime.now(UTC)
        await session.commit()

     return existing_session

  async def clear(
          self,
          session: AsyncSession,
          user_id: str
    ) -> None:
       stmt = delete(SessionRow).where(SessionRow.user_id == user_id)
       await session.execute(stmt, execution_options={"synchronize_session": "fetch"})