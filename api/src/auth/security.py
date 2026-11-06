
from datetime import UTC, datetime, timedelta
from uuid import uuid4

import bcrypt
import jwt

from src.config import get_settings
from .models import TokenType, DecodedToken

# ── Passwords ─────────────────────────────────────────────────────────────
# We use the `bcrypt` library directly rather than passlib's CryptContext. 
# bcrypt salts internally — the salt is stored INSIDE the hash string, 
# so we don't manage it separately.

# bcrypt only hashes the first 72 BYTES of input and (in 5.x) raises past that.
# Truncating defensively keeps a 200-char passphrase from blowing up at runtime.
_BCRYPT_MAX_BYTES = 72


def hash_password(plain: str) -> str:
    pw = plain.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    # gensalt() embeds the cost factor (default 12 rounds). hashpw returns bytes;
    # decode to store as a normal `str` in the varchar column.
    return bcrypt.hashpw(pw, bcrypt.gensalt()).decode("utf-8")


def verify_password(plain: str, hashed: str) -> bool:
    pw = plain.encode("utf-8")[:_BCRYPT_MAX_BYTES]
    # checkpw re-hashes `plain` using the salt+cost baked into `hashed`, then does
    # a constant-time compare. We never "decrypt" — bcrypt is one-way by design.
    return bcrypt.checkpw(pw, hashed.encode("utf-8"))

def _create_token(subject: str, 
                  token_type: TokenType,
                  expires_in: timedelta) -> str:
    now = datetime.now(UTC)
    payload = {
        "jti": str(uuid4()),
        "sub": subject,            # user
        "type": token_type.value,  # access vs refresh discriminator
        "iat": now,                # issued-at (pyjwt converts datetime -> epoch)
        "exp": now + expires_in,   # expiry — pyjwt ENFORCES this on decode
    }
    s = get_settings()
    return jwt.encode(payload, s.jwt_secret, algorithm=s.jwt_algorithm)


def create_access_token(subject: str) -> str:
    s = get_settings()
    return _create_token(
        subject, 
        TokenType.ACCESS,
        timedelta(minutes=s.access_token_expire_minutes)
    )


def create_refresh_token(subject: str) -> str:
    s = get_settings()
    return _create_token(
        subject, 
        TokenType.REFRESH,
        timedelta(days=s.refresh_token_expire_days)
    )

def create_app_token(subject: str) -> str:
    s = get_settings()
    return _create_token(
        subject, TokenType.APP, timedelta(days=s.app_token_expire_days)
    )

def decode_token(token: str, expected_types: list[TokenType]) -> DecodedToken:
    """Verify signature + expiry + type, return the subject. Raises jwt.* errors
    (InvalidTokenError and subclasses) which the caller maps to a 401.

    The `algorithms=[...]` arg is THE defense against the `alg:none` / algorithm-
    confusion attack: we tell pyjwt which algorithm to trust instead of reading
    it from the attacker-controlled header.
    """
    s = get_settings()
    payload = jwt.decode(token, s.jwt_secret, algorithms=[s.jwt_algorithm])

    if payload.get("type") not in {t.value for t in expected_types}:
        # Right signature, wrong kind of token (e.g. a refresh token on /todos).
        raise jwt.InvalidTokenError("unexpected token type")

    subject = payload.get("sub")
    if not subject:
        raise jwt.InvalidTokenError("missing subject")
    
    return DecodedToken(**payload)
