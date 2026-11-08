from sqlalchemy.ext.asyncio import AsyncSession
from datetime import datetime, timedelta
from ..database.models import SessionRow
from ..core.config import get_settings
from sqlalchemy import delete, select 
from sqlalchemy.orm import joinedload

class UserSessionStore:
  async def create(
    self,
    session: AsyncSession,
    user_id: str,
    session_hash: str,
    now: datetime
  ) -> SessionRow:
    row = SessionRow(
      user_id=user_id,
      session_hash=session_hash,
      last_seen_at=now,
      expires_at=now + timedelta(days=get_settings().session_expire_days),
    )
  
    session.add(row)
    await session.commit()

    return row

  async def get(
    self,
    session: AsyncSession,
    session_hash: str,        
  ) -> SessionRow | None:
    result = await session.execute(
      select(SessionRow)
        .options(joinedload(SessionRow.user))
        .where(SessionRow.session_hash == session_hash)
    )
    return result.scalar_one_or_none()

  async def update_last_seen(
    self,
    session: AsyncSession,
    session_hash: str,
    now: datetime
  ) -> SessionRow | None:
    existing_session = await session.get(SessionRow, session_hash)
    if (existing_session is not None):
      existing_session.last_seen_at = now
      await session.commit()

    return existing_session

  async def clear(
    self,
    session: AsyncSession,
    user_id: str
  ) -> None:
    stmt = delete(SessionRow).where(SessionRow.user_id == user_id)
    await session.execute(stmt, execution_options={"synchronize_session": "fetch"})