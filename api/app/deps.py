from collections.abc import AsyncIterator
from typing import Annotated

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from .auth.service import UserSessionStore
from .core.config import Settings, get_settings
from .database.engine import SessionFactory
from .todos.service import TodoStore
from .users.service import UserStore


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

_todo_store = TodoStore()

def get_todo_store() -> TodoStore:
    return _todo_store

TodoStoreDep = Annotated[TodoStore, Depends(get_todo_store)]

SettingsDep = Annotated[Settings, Depends(get_settings)]
