"""
SQLAlchemy models for the app's structured data.

Portable across SQLite (dev/tests) and Postgres (production): chat messages are
stored as a JSON-encoded string in a Text column rather than a backend-specific
JSON type, so the same schema works on both.
"""

import datetime as dt

from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey

from backend.db import Base


def _utcnow():
    return dt.datetime.now(dt.timezone.utc)


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(64), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)


class ChatHistory(Base):
    __tablename__ = "chat_histories"

    id = Column(Integer, primary_key=True)
    # Scopes each saved chat to its owner — the DB-level guarantee behind
    # per-user history isolation (P0 #2), replacing the per-user file folders.
    user_id = Column(
        Integer, ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True
    )
    title = Column(String(200), nullable=False, default="")
    persona = Column(String(120))
    slm = Column(String(120))
    # JSON-encoded list of {role, content} messages (portable across DBs).
    messages = Column(Text, nullable=False, default="[]")
    created_at = Column(DateTime(timezone=True), default=_utcnow, nullable=False)
