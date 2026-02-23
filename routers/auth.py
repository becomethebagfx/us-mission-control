"""
Mission Control — GitHub OAuth Authentication Router
Handles login, callback, logout, and session management.
"""

import hashlib
import hmac
import json
import time
import base64

import httpx
from fastapi import APIRouter, Request
from fastapi.responses import RedirectResponse, JSONResponse

from config import config

router = APIRouter(prefix="/auth", tags=["Auth"])

COOKIE_NAME = "mc_session"
SESSION_TTL = 86400  # 24 hours


def _sign(payload: str) -> str:
    """HMAC-SHA256 sign a payload string."""
    sig = hmac.new(
        config.SESSION_SECRET.encode(), payload.encode(), hashlib.sha256
    ).hexdigest()
    return sig


def create_session_cookie(user_data: dict) -> str:
    """Create a signed session cookie value."""
    user_data["exp"] = int(time.time()) + SESSION_TTL
    payload = base64.urlsafe_b64encode(json.dumps(user_data).encode()).decode()
    sig = _sign(payload)
    return f"{payload}.{sig}"


def verify_session(request: Request) -> dict | None:
    """Verify and decode the session cookie. Returns user dict or None."""
    raw = request.cookies.get(COOKIE_NAME)
    if not raw:
        return None
    try:
        payload, sig = raw.rsplit(".", 1)
        if not hmac.compare_digest(_sign(payload), sig):
            return None
        data = json.loads(base64.urlsafe_b64decode(payload))
        if data.get("exp", 0) < time.time():
            return None
        return data
    except Exception:
        return None


@router.get("/login")
async def login(request: Request):
    """Redirect to GitHub OAuth authorization page."""
    if not config.GITHUB_CLIENT_ID:
        return JSONResponse(
            {"error": "GitHub OAuth not configured"}, status_code=500
        )
    state = hmac.new(
        config.SESSION_SECRET.encode(),
        str(time.time()).encode(),
        hashlib.sha256,
    ).hexdigest()[:16]
    github_url = (
        f"https://github.com/login/oauth/authorize"
        f"?client_id={config.GITHUB_CLIENT_ID}"
        f"&scope=read:user"
        f"&state={state}"
    )
    response = RedirectResponse(github_url)
    response.set_cookie("oauth_state", state, httponly=True, max_age=600, samesite="lax")
    return response


@router.get("/callback")
async def callback(request: Request, code: str = "", state: str = ""):
    """Exchange GitHub code for access token, verify user, set session."""
    if not code:
        return RedirectResponse("/auth/login?error=no_code")

    # Validate OAuth state to prevent CSRF
    stored_state = request.cookies.get("oauth_state")
    if not stored_state or not state or not hmac.compare_digest(stored_state, state):
        return RedirectResponse("/auth/login?error=invalid_state")

    # Exchange code for token
    async with httpx.AsyncClient() as client:
        token_resp = await client.post(
            "https://github.com/login/oauth/access_token",
            json={
                "client_id": config.GITHUB_CLIENT_ID,
                "client_secret": config.GITHUB_CLIENT_SECRET,
                "code": code,
            },
            headers={"Accept": "application/json"},
        )
        if token_resp.status_code != 200:
            return RedirectResponse("/auth/login?error=token_failed")
        token_data = token_resp.json()
        access_token = token_data.get("access_token")
        if not access_token:
            return RedirectResponse("/auth/login?error=no_token")

        # Get user info
        user_resp = await client.get(
            "https://api.github.com/user",
            headers={
                "Authorization": f"Bearer {access_token}",
                "Accept": "application/json",
            },
        )
        if user_resp.status_code != 200:
            return RedirectResponse("/auth/login?error=user_failed")
        user = user_resp.json()

    username = user.get("login", "")

    # Check allowlist (skip if no ALLOWED_USERS configured = open access)
    if config.ALLOWED_USERS and username not in config.ALLOWED_USERS:
        return RedirectResponse("/auth/login?error=not_allowed")

    # Build session
    session_data = {
        "username": username,
        "avatar_url": user.get("avatar_url", ""),
        "name": user.get("name", "") or username,
    }
    cookie_value = create_session_cookie(session_data)

    response = RedirectResponse("/")
    response.set_cookie(
        COOKIE_NAME,
        cookie_value,
        httponly=True,
        secure=True,
        samesite="lax",
        max_age=SESSION_TTL,
    )
    response.delete_cookie("oauth_state")
    return response


@router.get("/logout")
async def logout():
    """Clear session and redirect to login."""
    response = RedirectResponse("/auth/login")
    response.delete_cookie(COOKIE_NAME)
    return response


@router.get("/me")
async def me(request: Request):
    """Return current authenticated user info."""
    session = verify_session(request)
    if not session:
        return JSONResponse({"error": "not authenticated"}, status_code=401)
    return {
        "username": session.get("username", ""),
        "avatar_url": session.get("avatar_url", ""),
        "name": session.get("name", ""),
    }
