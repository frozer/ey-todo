from pydantic import BaseModel, Field
from dataclasses import dataclass
from enum import StrEnum
from datetime import datetime

class RefreshRequest(BaseModel):
  refresh_token: str

class Token(BaseModel):
  access_token: str
  refresh_token: str
  token_type: str = "bearer"

class TokenType(StrEnum):
    """The `type` claim. Why it matters: an access token and a refresh token are
    both just signed JWTs with the same secret — without a discriminator, a
    long-lived refresh token would be accepted as an access token,
    erasing the short-expiry protection. We check this claim on decode."""

    ACCESS = "access"
    REFRESH = "refresh"
    APP = "app"

@dataclass
class DecodedToken:
    jti: str
    sub: str
    type: TokenType
    iat: datetime
    exp: datetime