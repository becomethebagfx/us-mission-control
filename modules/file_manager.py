"""
Website Builder — File Manager
Handles file uploads with validation and storage.
"""

import re
import uuid
from pathlib import Path
from typing import Optional

UPLOADS_DIR = Path(__file__).parent.parent / "data" / "builder" / "uploads"

ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp", ".gif", ".ico"}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB per file
MAX_SESSION_SIZE = 50 * 1024 * 1024  # 50MB per session

UUID_PATTERN = re.compile(r'^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$')


def _ensure_dir(session_id: str) -> Path:
    if not UUID_PATTERN.match(session_id):
        raise ValueError("Invalid session ID")
    session_dir = UPLOADS_DIR / session_id
    session_dir.mkdir(parents=True, exist_ok=True)
    return session_dir


def validate_file(filename: str, size: int, session_id: str) -> Optional[str]:
    """Validate a file before upload. Returns error message or None."""
    ext = Path(filename).suffix.lower()
    if ext not in ALLOWED_EXTENSIONS:
        return f"File type '{ext}' not allowed. Allowed: {', '.join(sorted(ALLOWED_EXTENSIONS))}"

    if size > MAX_FILE_SIZE:
        return f"File too large ({size / 1024 / 1024:.1f}MB). Maximum: {MAX_FILE_SIZE / 1024 / 1024:.0f}MB"

    # Check session total size
    session_dir = UPLOADS_DIR / session_id
    if session_dir.exists():
        total = sum(f.stat().st_size for f in session_dir.iterdir() if f.is_file())
        if total + size > MAX_SESSION_SIZE:
            return f"Session upload limit reached ({MAX_SESSION_SIZE / 1024 / 1024:.0f}MB). Start a new session."

    return None


async def save_file(session_id: str, filename: str, content: bytes) -> dict:
    """Save an uploaded file. Returns file metadata."""
    session_dir = _ensure_dir(session_id)

    # Generate unique filename
    ext = Path(filename).suffix.lower()
    safe_name = f"{uuid.uuid4().hex[:8]}{ext}"
    file_path = session_dir / safe_name

    file_path.write_bytes(content)

    return {
        "name": filename,
        "stored_name": safe_name,
        "path": str(file_path.relative_to(UPLOADS_DIR.parent.parent)),
        "size": len(content),
        "type": ext.lstrip("."),
        "url": f"/uploads/{session_id}/{safe_name}",
    }


def get_session_files(session_id: str) -> list:
    """List all uploaded files for a session."""
    session_dir = UPLOADS_DIR / session_id
    if not session_dir.exists():
        return []

    files = []
    for f in sorted(session_dir.iterdir()):
        if f.is_file():
            files.append({
                "name": f.name,
                "size": f.stat().st_size,
                "type": f.suffix.lstrip("."),
                "url": f"/uploads/{session_id}/{f.name}",
            })
    return files
