import uuid
from datetime import datetime

from pydantic import BaseModel, Field


class TodoCreate(BaseModel):
  label: str = Field(min_length=1, examples="Build todo app")
  text: str

class Todo(TodoCreate):
  id: uuid.UUID
  created_at: datetime
  status: str
  lft: int
  rgt: int

class TodosResponse(BaseModel):
  items: list[Todo]
  