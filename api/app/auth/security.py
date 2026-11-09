
import hashlib
import secrets
from functools import lru_cache

from argon2 import PasswordHasher
from argon2.exceptions import VerifyMismatchError

MIN_PASSWORD_BYTES = 8
MAX_PASSWORD_BYTES = 72

# Initialize the hasher (uses Argon2id by default)
ph = PasswordHasher()

def hash_password(plain: str) -> str:
  return ph.hash(plain)

def verify_password(plain: str, hashed: str) -> bool:
  try:
    return ph.verify(hashed, plain)
  except (ValueError, TypeError, VerifyMismatchError):
    return False
   
def generate_session_token() -> str:
  return secrets.token_urlsafe(32)

def hash_session_token(token: str) -> str:
  return hashlib.sha256(token.encode()).hexdigest()

@lru_cache(maxsize=1)
def dummy_hash() -> str:
  """A real hash for unknown users, so a miss takes as long as a hit."""
  return hash_password("dummy-password-for-timing-only")

def password_policy_error(
  new: str, username: str, current: str | None = None
) -> str | None:
  """The policy code for a new password, or None if it is acceptable.

  `current` is given only when the person changes their own password, so a
  reuse check applies.
  """
  if current is not None and new == current:
    return "password_reused"
  if new.lower() == username.lower():
    return "password_equals_username"
  return None
