import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Uuid, Integer, ForeignKey
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
  password_hash: Mapped[str] = mapped_column(String(255))

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

class SessionRow(Base):
  __tablename__ = "sessions"
  id: Mapped[Integer] = mapped_column(Integer, primary_key=True )
  session_hash: Mapped[str] = mapped_column(String(255))
  expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
  last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
  revoked_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
  user_id: Mapped[uuid.UUID] = mapped_column(
    Uuid(native_uuid=False), 
    ForeignKey("users.id", ondelete="CASCADE"), 
    nullable=False
  )
  user: Mapped["UserRow"] = relationship("UserRow", back_populates="sessions")