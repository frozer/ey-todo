from typing import Annotated

from pydantic import BaseModel, Field, StringConstraints

from .security import MAX_PASSWORD_BYTES, MIN_PASSWORD_BYTES

# matches users.username String(50)
Username = Annotated[
  str,
  StringConstraints(strip_whitespace=True, to_lower=True, min_length=1, max_length=50),
]


class MeResponse(BaseModel):
  username: str
  # send back in the X-CSRF-Token header on every POST/PATCH/PUT/DELETE
  csrf_token: str

class RegisterBody(BaseModel):
  username: Username
  # never strip or otherwise alter passwords: what the user typed is what gets hashed
  password: str = Field(min_length=MIN_PASSWORD_BYTES, max_length=MAX_PASSWORD_BYTES)
