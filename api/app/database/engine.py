from sqlalchemy import event
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from ..core.config import get_settings

engine = create_async_engine(get_settings().database_path, echo=True)

@event.listens_for(engine.sync_engine, "connect")
def set_async_sqlite_pragma(dbapi_connection, _connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA foreign_keys=ON")
    cursor.close()

SessionFactory = async_sessionmaker(engine, expire_on_commit=False)