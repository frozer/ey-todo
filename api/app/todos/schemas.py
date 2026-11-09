import uuid
from datetime import datetime
from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

StrippedStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]

class TodoCreate(BaseModel):
  label: StrippedStr = Field(examples=["Build todo app"])
  text: str | None = Field(strip_whitespace=True, default=None)
  status: str | None = Field(strip_whitespace=True, default=None)

class TodoUpdate(BaseModel):
  label: StrippedStr | None = None
  text: StrippedStr | None = None
  status: StrippedStr | None = None
  position: int | None = Field(default=None, ge=0)

class Todo(BaseModel):
  id: uuid.UUID
  label: StrippedStr
  text: str | None = None
  created_at: datetime
  status:  str | None = None
  position: int | None
  removed_at: datetime | None = None
  modified_at: datetime | None = None

class TodosResponse(BaseModel):
  items: list[Todo]

class FilterParams(BaseModel):
  q: str | None = Field(strip_whitespace=True,to_lower=True,default=None)