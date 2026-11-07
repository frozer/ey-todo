from pydantic import BaseModel

class MeResponse(BaseModel):
  username: str

class RegisterBody(BaseModel):
  username: str
  password: str