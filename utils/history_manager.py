import re
import json
from datetime import datetime
from pathlib import Path
from config.settings import HISTORY_DIR

# Saved chats are stored per user under HISTORY_DIR/<user_key>/ so one user's
# sidebar never shows another user's conversations. The key is the logged-in
# username (already restricted to a safe charset by auth validation); we
# sanitize defensively and fall back to "anonymous" so a missing key can't
# escape the history directory.
_SAFE_KEY_RE = re.compile(r"[^A-Za-z0-9_.-]")


def _user_key(user_key) -> str:
    key = _SAFE_KEY_RE.sub("_", str(user_key or "").strip())
    # Reject empty or all-dot names ("", ".", "..") which would resolve to the
    # history dir itself or its parent.
    if not key or set(key) <= {"."}:
        return "anonymous"
    return key


def _user_history_dir(user_key) -> Path:
    path = HISTORY_DIR / _user_key(user_key)
    path.mkdir(parents=True, exist_ok=True)
    return path


def save_chat_history(messages, persona, slm, user_key=None):
    """
    Saves the current chat session to a JSON file inside the current user's
    private history directory.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"chat_{timestamp}.json"
    file_path = _user_history_dir(user_key) / filename

    data = {
        "timestamp": timestamp,
        "persona": persona,
        "slm": slm,
        "messages": messages,
    }

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    return str(file_path)


def _derive_title(data):
    """
    Use the first user message as the chat's title (like ChatGPT), truncated.
    Falls back to the timestamp if the chat has no user message yet.
    """
    for message in data.get("messages", []):
        if message.get("role") == "user" and message.get("content"):
            text = " ".join(message["content"].split())  # collapse whitespace
            return text[:38] + "…" if len(text) > 38 else text
    return data.get("timestamp", "Untitled chat")


def load_all_histories(user_key=None):
    """
    Loads metadata of the CURRENT USER's saved chat histories, including a
    `title` derived from the first question in each chat. Only reads the user's
    own directory, so histories are isolated per user.
    """
    histories = []
    user_dir = _user_history_dir(user_key)

    for file in sorted(user_dir.glob("chat_*.json"), reverse=True):
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                histories.append({
                    "file": file.name,
                    "path": str(file),
                    "timestamp": data.get("timestamp"),
                    "persona": data.get("persona"),
                    "slm": data.get("slm"),
                    "title": _derive_title(data),
                })
        except Exception:
            continue

    return histories


def load_chat_history(file_path, user_key=None):
    """
    Loads a single chat history JSON. If user_key is given, the path is checked
    to be inside that user's history directory first, so a user can only load
    their own saved chats (defends against a tampered path).
    """
    path = Path(file_path).resolve()

    if user_key is not None:
        user_dir = _user_history_dir(user_key).resolve()
        if user_dir not in path.parents:
            raise ValueError("Refusing to load a chat outside your history.")

    with open(path, "r", encoding="utf-8") as f:
        return json.load(f)
