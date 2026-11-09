from pydantic import BaseModel, Field

from .security import MAX_PASSWORD_BYTES, MIN_PASSWORD_BYTES


class MeResponse(BaseModel):
  username: str

class RegisterBody(BaseModel):
  username: str = Field(strip_whitespace=True,min_length=1,to_lower=True)
  password: str = Field(strip_whitespace=True,min_length=MIN_PASSWORD_BYTES,max_length=MAX_PASSWORD_BYTES)