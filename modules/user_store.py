"""
Mission Control — User Store
JSON-based user account storage with PBKDF2 password hashing.
No external dependencies — uses Python built-in hashlib.
"""

import hashlib
import json
import os
import re
import secrets
from datetime import datetime
from pathlib import Path
from typing import Optional

USERS_DIR = Path(__file__).parent.parent / "data" / "users"
EMAIL_PATTERN = re.compile(r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$')


def _ensure_dir():
    USERS_DIR.mkdir(parents=True, exist_ok=True)


def _email_to_filename(email: str) -> str:
    """Convert email to a safe filename."""
    safe = email.lower().replace("@", "_at_").replace(".", "_")
    safe = re.sub(r'[^a-z0-9_]', '', safe)
    return safe


def _user_path(email: str) -> Path:
    return USERS_DIR / f"{_email_to_filename(email)}.json"


def _hash_password(password: str, salt: Optional[bytes] = None) -> tuple[str, str]:
    """Hash a password with PBKDF2-SHA256. Returns (hash_hex, salt_hex)."""
    if salt is None:
        salt = secrets.token_bytes(32)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations=260000)
    return dk.hex(), salt.hex()


def _verify_password(password: str, stored_hash: str, salt_hex: str) -> bool:
    """Verify a password against stored hash and salt."""
    salt = bytes.fromhex(salt_hex)
    dk = hashlib.pbkdf2_hmac("sha256", password.encode(), salt, iterations=260000)
    return secrets.compare_digest(dk.hex(), stored_hash)


def validate_email(email: str) -> Optional[str]:
    """Validate email format. Returns error message or None."""
    if not email or not EMAIL_PATTERN.match(email):
        return "Invalid email address"
    if len(email) > 254:
        return "Email address too long"
    return None


def validate_password(password: str) -> Optional[str]:
    """Validate password strength. Returns error message or None."""
    if len(password) < 8:
        return "Password must be at least 8 characters"
    if len(password) > 128:
        return "Password too long"
    return None


def create_user(email: str, password: str, name: str = "") -> dict:
    """Create a new user account. Returns user dict (without password)."""
    _ensure_dir()

    email = email.lower().strip()
    path = _user_path(email)
    if path.exists():
        raise ValueError("An account with this email already exists")

    pw_hash, salt = _hash_password(password)

    user = {
        "email": email,
        "name": name.strip() or email.split("@")[0],
        "password_hash": pw_hash,
        "salt": salt,
        "created_at": datetime.utcnow().isoformat(),
        "last_login": None,
    }
    path.write_text(json.dumps(user, indent=2))

    return _public_user(user)


def authenticate(email: str, password: str) -> Optional[dict]:
    """Authenticate a user. Returns public user dict or None."""
    email = email.lower().strip()
    path = _user_path(email)
    if not path.exists():
        return None

    try:
        user = json.loads(path.read_text())
    except (json.JSONDecodeError, KeyError):
        return None

    if not _verify_password(password, user["password_hash"], user["salt"]):
        return None

    # Update last login
    user["last_login"] = datetime.utcnow().isoformat()
    path.write_text(json.dumps(user, indent=2))

    return _public_user(user)


def get_user(email: str) -> Optional[dict]:
    """Get public user info by email."""
    email = email.lower().strip()
    path = _user_path(email)
    if not path.exists():
        return None
    try:
        user = json.loads(path.read_text())
        return _public_user(user)
    except (json.JSONDecodeError, KeyError):
        return None


def user_exists(email: str) -> bool:
    """Check if a user account exists for this email."""
    return _user_path(email.lower().strip()).exists()


def _public_user(user: dict) -> dict:
    """Return user dict without sensitive fields."""
    return {
        "email": user["email"],
        "name": user["name"],
        "created_at": user.get("created_at"),
        "last_login": user.get("last_login"),
    }
