import datetime as dt

import jwt
import pytest

from src.auth.security import (
  TokenType,
  create_access_token,
  create_refresh_token,
  decode_token,
  hash_password,
  verify_password,
)


def test_password():
  password = "test"
  hashed = hash_password(password)
  assert verify_password(password, hashed)
  
  assert not verify_password("test2", hashed)

  assert hashed != hash_password(password)

  assert verify_password(password, hash_password(password))

@pytest.mark.time_machine(dt.datetime(2026, 6, 30, 12, 0, 0))
def test_tokens(time_machine):
  assert decode_token(create_access_token("alice"), [TokenType.ACCESS]).sub == "alice"

  refresh_token = create_refresh_token("alice")

  with pytest.raises(jwt.InvalidTokenError):
    decode_token(refresh_token, [TokenType.ACCESS])
  
  with pytest.raises(jwt.InvalidTokenError):
    decode_token(create_access_token("alice").swapcase(), [TokenType.ACCESS])

  # expired token test
  access_token = create_access_token("alice")
  time_machine.shift(dt.timedelta(hours=2))
  with pytest.raises(jwt.InvalidTokenError):
    decode_token(access_token, [TokenType.ACCESS])
  

