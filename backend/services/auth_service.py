"""
Authentication service — per-user accounts.

Provides the deterministic building blocks for auth, independent of FastAPI:
- a SQLite-backed user store (username + bcrypt password hash),
- password hashing/verification (bcrypt),
- JWT bearer-token creation/validation (HS256).

The web layer (backend/main.py) wraps these in /auth/* endpoints and a
`get_current_user` dependency that protects the other endpoints. Keeping the
logic here (no FastAPI imports) makes it unit-testable offline with no network.

Storage is SQLite for now (single-file, zero-config), the same file-based
approach the rest of the app uses; it migrates to Postgres later per the
production-readiness plan (P1 #6).
"""

import os
import re
import sqlite3
import logging
import datetime as dt

import bcrypt
import jwt

from config.settings import (
    AUTH_DB_PATH,
    JWT_SECRET,
    JWT_ALGORITHM,
    JWT_EXPIRY_HOURS,
)

logger = logging.getLogger(__name__)

# Usernames: 3-32 chars, letters/digits and a few safe separators. Deliberately
# strict so a username is always a clean identifier (also used to key per-user
# data in the next step).
_USERNAME_RE = re.compile(r"^[A-Za-z0-9_.-]{3,32}$")

MIN_PASSWORD_LEN = 8
MAX_PASSWORD_LEN = 128

# bcrypt only considers the first 72 bytes of a password and newer releases
# raise on longer input; truncate consistently in both hash and verify so a
# long passphrase behaves predictably instead of erroring.
_BCRYPT_MAX_BYTES = 72


class AuthError(Exception):
    """Raised for any auth failure (bad credentials, duplicate user, invalid
    or expired token, validation error). The web layer maps it to a 4xx."""


def _db_path() -> str:
    """Read the DB path at call time (not import time) so tests can point at a
    throwaway file via the AUTH_DB_PATH env var regardless of import order."""
    return os.environ.get("AUTH_DB_PATH", AUTH_DB_PATH)


def _connect() -> sqlite3.Connection:
    conn = sqlite3.connect(_db_path())
    conn.row_factory = sqlite3.Row
    return conn


def init_db() -> None:
    """Create the users table if it doesn't exist. Safe to call on every boot."""
    with _connect() as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS users (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                username      TEXT UNIQUE NOT NULL,
                password_hash TEXT NOT NULL,
                created_at    TEXT NOT NULL
            )
            """
        )
        conn.commit()
    logger.info("Auth user store ready at %s", _db_path())


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
    """Raise AuthError if the username/password don't meet the basic rules."""
    if not username or not _USERNAME_RE.match(username):
        raise AuthError(
            "Username must be 3-32 characters using letters, numbers, or . _ -"
        )
    if not password or len(password) < MIN_PASSWORD_LEN:
        raise AuthError(f"Password must be at least {MIN_PASSWORD_LEN} characters.")
    if len(password) > MAX_PASSWORD_LEN:
        raise AuthError(f"Password must be at most {MAX_PASSWORD_LEN} characters.")


# -------------------------------------------------
# User store
# -------------------------------------------------
def register_user(username: str, password: str) -> dict:
    """Create a new user. Returns {'id', 'username'}. Raises AuthError if the
    input is invalid or the username is already taken."""
    username = (username or "").strip()
    validate_credentials(username, password)

    password_hash = hash_password(password)
    now = dt.datetime.now(dt.timezone.utc).isoformat()
    try:
        with _connect() as conn:
            cur = conn.execute(
                "INSERT INTO users (username, password_hash, created_at) "
                "VALUES (?, ?, ?)",
                (username, password_hash, now),
            )
            conn.commit()
            return {"id": cur.lastrowid, "username": username}
    except sqlite3.IntegrityError:
        raise AuthError("That username is already taken.")


def authenticate(username: str, password: str) -> dict:
    """Verify credentials. Returns {'id', 'username'} on success, else raises
    AuthError with a deliberately generic message (don't reveal which of the
    username/password was wrong)."""
    username = (username or "").strip()
    with _connect() as conn:
        row = conn.execute(
            "SELECT id, username, password_hash FROM users WHERE username = ?",
            (username,),
        ).fetchone()

    if not row or not verify_password(password, row["password_hash"]):
        raise AuthError("Invalid username or password.")
    return {"id": row["id"], "username": row["username"]}


# -------------------------------------------------
# JWT tokens
# -------------------------------------------------
def create_token(user: dict) -> str:
    """Issue a signed JWT for a user dict ({'id', 'username'})."""
    now = dt.datetime.now(dt.timezone.utc)
    payload = {
        "sub": str(user["id"]),
        "username": user["username"],
        "iat": now,
        "exp": now + dt.timedelta(hours=JWT_EXPIRY_HOURS),
    }
    return jwt.encode(payload, JWT_SECRET, algorithm=JWT_ALGORITHM)


def decode_token(token: str) -> dict:
    """Validate a bearer token and return {'id', 'username'}. Raises AuthError
    on an expired, tampered, or malformed token."""
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
