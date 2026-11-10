import uuid
from datetime import datetime
from typing import Annotated

from pydantic import AfterValidator, BaseModel, Field, StringConstraints

StrippedStr = Annotated[str, StringConstraints(strip_whitespace=True, min_length=1)]

OptionalText = Annotated[
  Annotated[str, StringConstraints(strip_whitespace=True, max_length=200)] | None,
  AfterValidator(lambda v: v or None),
]

class TodoCreate(BaseModel):
  label: StrippedStr = Field(examples=["Build todo app"])
  text: OptionalText = None
  status: Annotated[str, StringConstraints(strip_whitespace=True)] | None = None

class TodoUpdate(BaseModel):
  label: StrippedStr | None = None
  text: OptionalText = None
  status: StrippedStr | None = None
  lft: uuid.UUID | None = Field(default=None)
  rgt: uuid.UUID | None = Field(default=None)

class Todo(BaseModel):
  id: uuid.UUID
  label: StrippedStr
  text: str | None = None
  created_at: datetime
  status:  str | None = None
  position: int | None
  removed_at: datetime | None = None
  modified_at: datetime | None = None

class TodosMeta(BaseModel):
  has_more: bool
  
class TodosResponse(BaseModel):
  items: list[Todo]
  meta: TodosMeta

class FilterParams(BaseModel):
  q: Annotated[str, StringConstraints(strip_whitespace=True, to_lower=True)] | None = None