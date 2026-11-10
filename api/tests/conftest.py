from collections.abc import AsyncIterator
from datetime import UTC, datetime, timedelta

import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import StaticPool

from app.core.clock import get_clock
from app.core.config import Settings, get_settings
from app.database.models import Base
from app.deps import get_session
from app.main import app


class FakeClock:
  def __init__(self) -> None:
    self.now = datetime(2026, 1, 1, 12, 0, tzinfo=UTC)

  def advance(self, **kwargs) -> None:
    self.now += timedelta(**kwargs)

  def __call__(self) -> datetime:
    return self.now


@pytest_asyncio.fixture
async def session_factory() -> AsyncIterator[async_sessionmaker[AsyncSession]]:
  engine = create_async_engine(
    "sqlite+aiosqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
  )
  async with engine.begin() as conn:
    await conn.run_sync(Base.metadata.create_all)

  yield async_sessionmaker(engine, expire_on_commit=False)

  await engine.dispose()


@pytest_asyncio.fixture
def clock() -> FakeClock:
  return FakeClock()


@pytest_asyncio.fixture
async def client(session_factory, clock) -> AsyncIterator[AsyncClient]:
  settings = Settings(environment="DEV")

  async def override_session() -> AsyncIterator[AsyncSession]:
    async with session_factory() as session:
      yield session

  app.dependency_overrides[get_session] = override_session
  app.dependency_overrides[get_settings] = lambda: settings
  app.dependency_overrides[get_clock] = lambda: clock

  async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as c:
    yield c

  app.dependency_overrides.clear()


@pytest_asyncio.fixture
async def auth_client(client) -> AsyncClient:
  resp = await client.post(
    "/api/auth/register",
    json={"username": "alice", "password": "correct-horse-battery"},
  )
  assert resp.status_code == 200, resp.text
  return client
