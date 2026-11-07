from collections.abc import AsyncIterator
from typing import Annotated
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import Depends

from .database.engine import SessionFactory
from .users.service import UserStore
from .auth.service import UserSessionStore

async def get_session() -> AsyncIterator[AsyncSession]:
    async with SessionFactory() as session:
        yield session

SessionDep = Annotated[AsyncSession, Depends(get_session)]

_user_store = UserStore()

def get_user_store() -> UserStore:
    return _user_store

UserStoreDep = Annotated[UserStore, Depends(get_user_store)]

_user_session_store = UserSessionStore()

def get_user_session_store() -> UserStore:
    return _user_session_store

UserSessionStoreDep = Annotated[UserSessionStore, Depends(get_user_session_store)]
