"""
Chat-history storage, backed by the database (was per-user JSON files).

Each saved chat belongs to a user (ChatHistory.user_id), so listing and loading
are inherently per-user — the same isolation the file-folder approach gave, now
enforced at the DB level and safe across multiple app instances.
"""

import json
import datetime as dt

from sqlalchemy import select

from backend.db import session_scope
from backend.models import ChatHistory


def derive_title(messages) -> str:
    """The chat's title = its first user message (like ChatGPT), truncated.
    Falls back to a timestamp when there's no user message yet."""
    for message in messages or []:
        if isinstance(message, dict) and message.get("role") == "user" and message.get("content"):
            text = " ".join(str(message["content"]).split())
            return text[:38] + "…" if len(text) > 38 else text
    return dt.datetime.now(dt.timezone.utc).strftime("%Y%m%d_%H%M%S")


def save_history(user_id: int, messages, persona=None, slm=None) -> int:
    """Persist a chat for a user; returns the new row id."""
    with session_scope() as session:
        row = ChatHistory(
            user_id=user_id,
            title=derive_title(messages),
            persona=persona,
            slm=slm,
            messages=json.dumps(messages or [], ensure_ascii=False),
        )
        session.add(row)
        session.flush()
        return row.id


def list_histories(user_id: int) -> list:
    """List a user's saved chats (metadata only), newest first."""
    with session_scope() as session:
        rows = session.execute(
            select(ChatHistory)
            .where(ChatHistory.user_id == user_id)
            .order_by(ChatHistory.created_at.desc(), ChatHistory.id.desc())
        ).scalars().all()
        return [
            {
                "id": r.id,
                "title": r.title,
                "persona": r.persona,
                "slm": r.slm,
                "created_at": r.created_at.isoformat() if r.created_at else None,
            }
            for r in rows
        ]


def get_history(user_id: int, history_id: int):
    """Load one chat, but only if it belongs to this user. Returns None otherwise
    (so a user can never read another user's chat by guessing an id)."""
    with session_scope() as session:
        row = session.get(ChatHistory, history_id)
        if row is None or row.user_id != user_id:
            return None
        return {
            "id": row.id,
            "title": row.title,
            "persona": row.persona,
            "slm": row.slm,
            "messages": json.loads(row.messages or "[]"),
            "created_at": row.created_at.isoformat() if row.created_at else None,
        }


def delete_history(user_id: int, history_id: int) -> bool:
    """Delete one chat if it belongs to this user. Returns True if deleted."""
    with session_scope() as session:
        row = session.get(ChatHistory, history_id)
        if row is None or row.user_id != user_id:
            return False
        session.delete(row)
        return True
