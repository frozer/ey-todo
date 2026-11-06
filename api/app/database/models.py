import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Uuid, ForeignKey
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

class Base(DeclarativeBase):
  pass

class UserRow(Base):
  __tablename__ = "users"
  id: Mapped[uuid.UUID] = mapped_column(
    Uuid(native_uuid=False), 
    primary_key=True, 
    default=uuid.uuid4
  )
  username: Mapped[str] = mapped_column(String(50), primary_key=True)
  hashed_password: Mapped[str] = mapped_column(String(255))

class TodoRow(Base):
  __tablename__ = "todos"
  id: Mapped[uuid.UUID] = mapped_column(
    Uuid(native_uuid=False), 
    primary_key=True, 
    default=uuid.uuid4
  )
  label: Mapped[str] = mapped_column(String(50))
  text: Mapped[str] = mapped_column(String(200))
  lft: Mapped[int]
  rgt: Mapped[int]
  status: Mapped[str] = mapped_column(String(50))
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
  user_id: Mapped[uuid.UUID] = mapped_column(
    Uuid(native_uuid=False), 
    ForeignKey("users.id", ondelete="CASCADE"), 
    nullable=False
  )
