"""
Build 1: Session Store
========================
Save and resume conversations on disk. Load AGENTS.md into the system prompt.

Tasks:
  1. create_session() -> session_id
  2. save_session(session_id, messages, title?)
  3. load_session(session_id) -> {id, title, messages, ...}
  4. list_sessions() -> [{id, title, updated_at}, ...]
  5. build_system_prompt() -> base + AGENTS.md contents

Run twice: save a session in run 1, load it in run 2 and confirm messages restored.
"""

import json
import os
import uuid
from datetime import datetime, timezone

SESSIONS_DIR = ".agent/sessions"
AGENTS_PATHS = ("AGENTS.md", ".agent/AGENTS.md")

BASE_PROMPT = "You are Research Desk, a helpful research assistant."


def create_session() -> str:
    """Return a new 8-char hex session ID."""
    os.makedirs(SESSIONS_DIR, exist_ok=True)
    session_id = uuid.uuid4().hex[:8]
    return session_id

def save_session(session_id: str, messages: list, title: str = "Untitled") -> None:
    """Write session JSON to .agent/sessions/{id}.json"""
    os.makedirs(SESSIONS_DIR, exist_ok=True)

    session_data = {
        "id": session_id,
        "title": title,
        "created_at": datetime.now(timezone.utc).isoformat(),
        "updated_at": datetime.now(timezone.utc).isoformat(),
        "messages": messages
    }

    file_path = os.path.join(
        SESSIONS_DIR,
        f"{session_id}.json"
    )

    with open(
        file_path,
        "w",
        encoding="utf-8"
    ) as f:
        json.dump(
            session_data,
            f,
            indent=2
        )


def load_session(session_id: str) -> dict:
    """Load and return session dict including messages list."""
    file_path = os.path.join(
        SESSIONS_DIR,
        f"{session_id}.json"
    )

    with open(
        file_path,
        "r",
        encoding="utf-8"
    ) as f:
        return json.load(f)


def list_sessions() -> list[dict]:
    """Return sessions sorted by updated_at descending."""
    sessions = []

    if not os.path.exists(SESSIONS_DIR):
        return sessions

    for filename in os.listdir(SESSIONS_DIR):

        if not filename.endswith(".json"):
            continue

        file_path = os.path.join(
            SESSIONS_DIR,
            filename
        )

        with open(
            file_path,
            "r",
            encoding="utf-8"
        ) as f:

            data = json.load(f)

            sessions.append(
                {
                    "id": data.get("id"),
                    "title": data.get("title"),
                    "updated_at": data.get("updated_at")
                }
            )

    sessions.sort(
        key=lambda s: s["updated_at"],
        reverse=True
    )

    return sessions
    
def build_system_prompt() -> str:
    """Base prompt + AGENTS.md if it exists."""
    parts = [BASE_PROMPT]

    for path in AGENTS_PATHS:

        if os.path.isfile(path):

            with open(
                path,
                "r",
                encoding="utf-8"
            ) as f:

                parts.append(
                    "\n\nProject Rules:\n"
                    + f.read()
                )

            break

    return "\n".join(parts)


if __name__ == "__main__":
    sid = create_session()
    messages = [
        {"role": "system", "content": build_system_prompt()},
        {"role": "user", "content": "What is a surface code?"},
        {"role": "assistant", "content": "A surface code is a type of quantum error correcting code."},
    ]
    save_session(sid, messages, title="Quantum error correction")
    print(f"Saved session: {sid}")
    print(f"All sessions: {list_sessions()}")
    print(f"Loaded: {load_session(sid)['title']}")
