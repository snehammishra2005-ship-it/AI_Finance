"""
Authentication service — per-user accounts.

Deterministic auth building blocks, independent of FastAPI:
- the user store (now the SQLAlchemy `User` model, so it runs on SQLite for
  dev/tests and Postgres in production — see backend/db.py),
- password hashing/verification (bcrypt),
- JWT bearer-token creation/validation (HS256).

The web layer (backend/main.py) wraps these in /auth/* endpoints and a
`get_current_user` dependency. Keeping the logic here (no FastAPI imports) makes
it unit-testable offline with no network.
"""

import re
import logging
import datetime as dt

import bcrypt
import jwt
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError

from config.settings import JWT_SECRET, JWT_ALGORITHM, JWT_EXPIRY_HOURS
from backend.db import session_scope
from backend.models import User

logger = logging.getLogger(__name__)

# Usernames: 3-32 chars, letters/digits and a few safe separators.
_USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{3,32}$")

MIN_PASSWORD_LEN = 8
MAX_PASSWORD_LEN = 128

# bcrypt only considers the first 72 bytes and newer releases raise on longer
# input; truncate consistently in hash and verify.
_BCRYPT_MAX_BYTES = 72


class AuthError(Exception):
    """Raised for any auth failure (bad credentials, duplicate user, invalid or
    expired token, validation error). The web layer maps it to a 4xx."""


# -------------------------------------------------
# Password hashing
# -------------------------------------------------
def _pw_bytes(password: str) -> bytes:
    return (password or "").encode("utf-8")[:_BCRYPT_MAX_BYTES]


def hash_password(password: str) -> str:
    return bcrypt.hashpw(_pw_bytes(password), bcrypt.gensalt()).decode("utf-8")


def verify_password(password: str, password_hash: str) -> bool:
    try:
        return bcrypt.checkpw(_pw_bytes(password), (password_hash or "").encode("utf-8"))
    except (ValueError, TypeError):
        return False


# -------------------------------------------------
# Validation
# -------------------------------------------------
def validate_credentials(username: str, password: str) -> None:
    if not username or not _USERNAME_RE.match(username):
        raise AuthError(
            "Username must be 3-32 characters using letters, numbers, or . _ -"
        )
    if not password or len(password) < MIN_PASSWORD_LEN:
        raise AuthError(f"Password must be at least {MIN_PASSWORD_LEN} characters.")
    if len(password) > MAX_PASSWORD_LEN:
        raise AuthError(f"Password must be at most {MAX_PASSWORD_LEN} characters.")


# -------------------------------------------------
# User store (SQLAlchemy)
# -------------------------------------------------
def register_user(username: str, password: str) -> dict:
    """Create a new user. Returns {'id', 'username'}. Raises AuthError on invalid
    input or a duplicate username."""
    username = (username or "").strip()
    validate_credentials(username, password)
    password_hash = hash_password(password)

    try:
        with session_scope() as session:
            user = User(username=username, password_hash=password_hash)
            session.add(user)
            session.flush()  # assign id + trigger the UNIQUE constraint now
            result = {"id": user.id, "username": user.username}
        return result
    except IntegrityError:
        raise AuthError("That username is already taken.")


def authenticate(username: str, password: str) -> dict:
    """Verify credentials. Returns {'id', 'username'} on success, else raises
    AuthError with a deliberately generic message."""
    username = (username or "").strip()
    with session_scope() as session:
        user = session.execute(
            select(User).where(User.username == username)
        ).scalar_one_or_none()

        if user is None or not verify_password(password, user.password_hash):
            raise AuthError("Invalid username or password.")
        return {"id": user.id, "username": user.username}


# -------------------------------------------------
# JWT tokens
# -------------------------------------------------
def create_token(user: dict) -> str:
    now = dt.datetime.now(dt.timezone.utc)
    payload = {
        "sub": str(user["id"]),
        "username": user["username"],
        "iat": now,
        "exp": now + dt.timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, JWT_SECRET, algorithms=[JWT_ALGORITHM])
    except jwt.ExpiredSignatureError:
        raise AuthError("Your session has expired. Please log in again.")
    except jwt.InvalidTokenError:
        raise AuthError("Invalid authentication token.")

    try:
        return {"id": int(payload["sub"]), "username": payload.get("username")}
    except (KeyError, ValueError, TypeError):
        raise AuthError("Invalid authentication token.")
