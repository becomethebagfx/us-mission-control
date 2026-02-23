"""
Website Builder — Session Store
Stores chat sessions as JSON files for persistence on Render free tier.
"""

import json
import re
import uuid
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional

SESSIONS_DIR = Path(__file__).parent.parent / "data" / "builder" / "sessions"
SESSION_EXPIRY_DAYS = 7

UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')


def _ensure_dir():
    SESSIONS_DIR.mkdir(parents=True, exist_ok=True)


def _session_path(session_id: str) -> Path:
    if not UUID_PATTERN.match(session_id):
        raise ValueError("Invalid session ID")
    return SESSIONS_DIR / f"{session_id}.json"


def create_session(user: str, site_slug: str) -> dict:
    """Create a new chat session."""
    _ensure_dir()
    session = {
        "id": str(uuid.uuid4()),
        "user": user,
        "site_slug": site_slug,
        "messages": [],
        "files": [],
        "proposed_changes": None,
        "status": "active",
        "created_at": datetime.utcnow().isoformat(),
        "updated_at": datetime.utcnow().isoformat(),
    }
    _save(session)
    return session


def get_session(session_id: str) -> Optional[dict]:
    """Get a session by ID."""
    path = _session_path(session_id)
    if not path.exists():
        return None
    return json.loads(path.read_text())


def add_message(session_id: str, role: str, content: str) -> Optional[dict]:
    """Add a message to a session."""
    session = get_session(session_id)
    if not session:
        return None

    session["messages"].append({
        "role": role,
        "content": content,
        "timestamp": datetime.utcnow().isoformat(),
    })
    session["updated_at"] = datetime.utcnow().isoformat()
    _save(session)
    return session


def set_proposed_changes(session_id: str, changes: list) -> Optional[dict]:
    """Set proposed changes on a session (from LLM plan)."""
    session = get_session(session_id)
    if not session:
        return None

    session["proposed_changes"] = changes
    session["updated_at"] = datetime.utcnow().isoformat()
    _save(session)
    return session


def clear_proposed_changes(session_id: str) -> Optional[dict]:
    """Clear proposed changes (after deploy or discard)."""
    session = get_session(session_id)
    if not session:
        return None

    session["proposed_changes"] = None
    session["updated_at"] = datetime.utcnow().isoformat()
    _save(session)
    return session


def add_file(session_id: str, file_info: dict) -> Optional[dict]:
    """Add an uploaded file reference to a session."""
    session = get_session(session_id)
    if not session:
        return None

    session["files"].append(file_info)
    session["updated_at"] = datetime.utcnow().isoformat()
    _save(session)
    return session


def list_sessions(user: str, limit: int = 10) -> list:
    """List sessions for a user, most recent first."""
    _ensure_dir()
    sessions = []
    for path in SESSIONS_DIR.glob("*.json"):
        try:
            session = json.loads(path.read_text())
            if session.get("user") == user and session.get("status") != "archived":
                sessions.append({
                    "id": session["id"],
                    "site_slug": session["site_slug"],
                    "message_count": len(session.get("messages", [])),
                    "first_message": session["messages"][0]["content"][:100] if session.get("messages") else "",
                    "created_at": session["created_at"],
                    "updated_at": session["updated_at"],
                })
        except (json.JSONDecodeError, KeyError):
            continue

    sessions.sort(key=lambda s: s["updated_at"], reverse=True)
    return sessions[:limit]


def archive_old_sessions():
    """Archive sessions inactive for more than SESSION_EXPIRY_DAYS."""
    _ensure_dir()
    cutoff = datetime.utcnow() - timedelta(days=SESSION_EXPIRY_DAYS)
    for path in SESSIONS_DIR.glob("*.json"):
        try:
            session = json.loads(path.read_text())
            updated = datetime.fromisoformat(session.get("updated_at", "2000-01-01"))
            if updated < cutoff and session.get("status") == "active":
                session["status"] = "archived"
                path.write_text(json.dumps(session, indent=2))
        except (json.JSONDecodeError, KeyError, ValueError):
            continue


def _save(session: dict):
    """Save session to disk."""
    _ensure_dir()
    path = _session_path(session["id"])
    path.write_text(json.dumps(session, indent=2))
