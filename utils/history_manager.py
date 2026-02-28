import json
from datetime import datetime
from pathlib import Path
from config.settings import HISTORY_DIR


def save_chat_history(messages, persona, slm):
    """
    Saves the current chat session to a JSON file.
    """

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"chat_{timestamp}.json"
    file_path = HISTORY_DIR / filename

    data = {
        "timestamp": timestamp,
        "persona": persona,
        "slm": slm,
        "messages": messages
    }

    with open(file_path, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

    return str(file_path)


def load_all_histories():
    """
    Loads metadata of all saved chat histories.
    """
    histories = []

    for file in sorted(HISTORY_DIR.glob("chat_*.json"), reverse=True):
        try:
            with open(file, "r", encoding="utf-8") as f:
                data = json.load(f)
                histories.append({
                    "file": file.name,
                    "path": str(file),
                    "timestamp": data.get("timestamp"),
                    "persona": data.get("persona"),
                    "slm": data.get("slm")
                })
        except Exception:
            continue

    return histories


def load_chat_history(file_path):
    """
    Loads a single chat history JSON.
    """
    with open(file_path, "r", encoding="utf-8") as f:
        return json.load(f)
