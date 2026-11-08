from pydantic import BaseModel, Field
from ..auth.security import MIN_PASSWORD_BYTES

class UserCreate(BaseModel):
  username: str = Field(min_length=3, max_length=50)
  password: str = Field(min_length=MIN_PASSWORD_BYTES)
