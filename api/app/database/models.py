import uuid
from datetime import UTC, datetime

from sqlalchemy import DateTime, ForeignKey, MetaData, String, Uuid
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship
from sqlalchemy.types import TypeDecorator

# Define a standard naming convention
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

class UTCDateTime(TypeDecorator):
  impl = DateTime
  cache_ok = True

  def process_bind_param(self, value: datetime | None, _dialect):
    if value is None:
      return None

    if value.tzinfo is None:
      raise ValueError("Naive datetime is not allowed")
    
    return value.astimezone(UTC)

  def process_result_value(self, value: datetime | None, dialect):
    if value is None:
      return None

    if value.tzinfo is None:
      return value.replace(tzinfo=UTC)

    return value.astimezone(UTC)
        
class Base(DeclarativeBase):
   metadata = MetaData(naming_convention=naming_convention)

class UserRow(Base):
  __tablename__ = "users"
  id: Mapped[uuid.UUID] = mapped_column(
    Uuid(native_uuid=False), 
    primary_key=True, 
    default=uuid.uuid4
  )
  username: Mapped[str] = mapped_column(String(50), unique=True)
  password_hash: Mapped[str] = mapped_column(String(255))
  sessions = relationship("SessionRow", back_populates="user")

class TodoRow(Base):
  __tablename__ = "todos"
  id: Mapped[uuid.UUID] = mapped_column(
    Uuid(native_uuid=False), 
    primary_key=True, 
    default=uuid.uuid4
  )
  label: Mapped[str] = mapped_column(String(50))
  text: Mapped[str | None] = mapped_column(String(200), nullable=True)
  position: Mapped[int] = mapped_column(default=0, index=True)
  status: Mapped[str] = mapped_column(String(50), default="")
  created_at: Mapped[datetime] = mapped_column(UTCDateTime())
  modified_at: Mapped[datetime | None] = mapped_column(
    UTCDateTime(),
    nullable=True,
    default=None
  )
  user_id: Mapped[uuid.UUID] = mapped_column(
    Uuid(native_uuid=False), 
    ForeignKey("users.id", ondelete="CASCADE"),
    index=True,
    nullable=False
  )
  removed_at: Mapped[datetime | None] = mapped_column(
    UTCDateTime(),
    nullable=True,
    index=True,
    default=None
  )
  is_removed: Mapped[bool] = mapped_column(default=False)

class SessionRow(Base):
  __tablename__ = "sessions"
  session_hash: Mapped[str] = mapped_column(String(255), primary_key=True)
  expires_at: Mapped[datetime] = mapped_column(UTCDateTime(),)
  last_seen_at: Mapped[datetime] = mapped_column(UTCDateTime(),)
  revoked_at: Mapped[datetime|None] = mapped_column(UTCDateTime(),)
  csrf_token: Mapped[str | None] = mapped_column(String(64), nullable=True)
  user_id: Mapped[uuid.UUID] = mapped_column(
    Uuid(native_uuid=False), 
    ForeignKey("users.id", ondelete="CASCADE"), 
    nullable=False
  )
  user: Mapped["UserRow"] = relationship("UserRow", back_populates="sessions")