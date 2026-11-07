import uuid
from datetime import datetime
from sqlalchemy import String, DateTime, Uuid, ForeignKey, MetaData
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship

# Define a standard naming convention
naming_convention = {
    "ix": "ix_%(column_0_label)s",
    "uq": "uq_%(table_name)s_%(column_0_name)s",
    "ck": "ck_%(table_name)s_%(constraint_name)s",
    "fk": "fk_%(table_name)s_%(column_0_name)s_%(referred_table_name)s",
    "pk": "pk_%(table_name)s"
}

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
  text: Mapped[str] = mapped_column(String(200))
  lft: Mapped[int]
  rgt: Mapped[int]
  status: Mapped[str] = mapped_column(String(50))
  created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
  user_id: Mapped[uuid.UUID] = mapped_column(
    Uuid(native_uuid=False), 
    ForeignKey("users.id", ondelete="CASCADE"),
    index=True,
    nullable=False
  )

class SessionRow(Base):
  __tablename__ = "sessions"
  session_hash: Mapped[str] = mapped_column(String(255), primary_key=True)
  expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
  last_seen_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
  revoked_at: Mapped[datetime|None] = mapped_column(DateTime(timezone=True))
  user_id: Mapped[uuid.UUID] = mapped_column(
    Uuid(native_uuid=False), 
    ForeignKey("users.id", ondelete="CASCADE"), 
    nullable=False
  )
  user: Mapped["UserRow"] = relationship("UserRow", back_populates="sessions")