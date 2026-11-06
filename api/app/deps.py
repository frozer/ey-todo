from collections.abc import AsyncIterator
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from .database.engine import SessionFactory

async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionFactory() as session:
        yield session

SessionDep = Annotated[AsyncSession, Depends(get_session)]