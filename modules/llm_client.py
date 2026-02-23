"""
Website Builder — LLM Client
Anthropic Claude API wrapper with rate limiting and cost tracking.
"""

import json
import os
import time
from datetime import datetime, date
from pathlib import Path
from typing import Optional

import httpx

ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")
MODEL = os.getenv("LLM_MODEL", "claude-sonnet-4-20250514")
API_URL = "https://api.anthropic.com/v1/messages"

# Rate limits
MAX_TOKENS_PER_MESSAGE = 4096
MAX_MESSAGES_PER_SESSION = 50
MAX_TOKENS_PER_DAY = 100_000

# Usage tracking
USAGE_FILE = Path(__file__).parent.parent / "data" / "builder" / "usage.json"


def _load_usage() -> dict:
    if USAGE_FILE.exists():
        return json.loads(USAGE_FILE.read_text())
    return {"daily": {}, "sessions": {}}


def _save_usage(usage: dict):
    USAGE_FILE.parent.mkdir(parents=True, exist_ok=True)
    USAGE_FILE.write_text(json.dumps(usage, indent=2))


def _today() -> str:
    return date.today().isoformat()


def check_rate_limit(session_id: str) -> Optional[str]:
    """Check rate limits. Returns error message if limit exceeded, None if OK."""
    usage = _load_usage()
    today = _today()

    # Check daily token limit
    daily_tokens = usage.get("daily", {}).get(today, 0)
    if daily_tokens >= MAX_TOKENS_PER_DAY:
        return f"Daily token limit reached ({MAX_TOKENS_PER_DAY:,} tokens). Try again tomorrow."

    # Check session message limit
    session_msgs = usage.get("sessions", {}).get(session_id, {}).get("message_count", 0)
    if session_msgs >= MAX_MESSAGES_PER_SESSION:
        return f"Session message limit reached ({MAX_MESSAGES_PER_SESSION} messages). Start a new session."

    return None


def record_usage(session_id: str, input_tokens: int, output_tokens: int):
    """Record token usage for rate limiting and cost tracking."""
    usage = _load_usage()
    today = _today()
    total = input_tokens + output_tokens

    # Daily usage
    if "daily" not in usage:
        usage["daily"] = {}
    usage["daily"][today] = usage["daily"].get(today, 0) + total

    # Session usage
    if "sessions" not in usage:
        usage["sessions"] = {}
    if session_id not in usage["sessions"]:
        usage["sessions"][session_id] = {"message_count": 0, "total_tokens": 0}
    usage["sessions"][session_id]["message_count"] += 1
    usage["sessions"][session_id]["total_tokens"] += total

    _save_usage(usage)


def build_system_prompt(site_context: dict) -> str:
    """Build the system prompt for the website builder LLM."""
    pages_list = "\n".join(
        f"  - {p['path']}: {p.get('title', 'Untitled')}" for p in site_context.get("pages", [])
    )

    return f"""You are an AI website editor for a commercial construction company website.
You help the business owner make changes to their website through natural conversation.

## Current Website: {site_context.get('name', 'Unknown')}
URL: {site_context.get('url', 'N/A')}

## Available Pages:
{pages_list}

## Your Role:
1. When the user asks to make changes, propose a PLAN first. Do NOT make changes without approval.
2. Describe what you'll change in clear, non-technical language.
3. If the user uploads images, reference them in your plan.
4. When proposing changes, structure your response with:
   - **What I'll change**: Description of modifications
   - **Files affected**: Which pages will be modified
   - **Preview**: What it will look like after changes

## Important Rules:
- Only modify HTML content, not the overall site structure or navigation
- Preserve all existing CSS classes and Tailwind styling
- Keep responsive design intact
- Do not remove any existing functionality
- Images should use descriptive alt text
- All text should be professional and appropriate for a B2B construction company

## When proposing changes, output a JSON plan block like this:
```json
{{"plan": [{{"file": "index.html", "action": "replace", "selector": "description of what to find", "old_text": "text to find", "new_text": "replacement text"}}]}}
```

Keep your responses concise and focused on the requested changes."""


async def chat(
    message: str,
    session_messages: list,
    site_context: dict,
    session_id: str,
) -> dict:
    """Send a message to the LLM and get a response.

    Returns: {"response": str, "plan": list|None, "usage": dict}
    """
    if not ANTHROPIC_API_KEY:
        return {
            "response": "The AI assistant is not configured. Please set the ANTHROPIC_API_KEY environment variable.",
            "plan": None,
            "usage": {"input_tokens": 0, "output_tokens": 0},
        }

    # Check rate limits
    limit_error = check_rate_limit(session_id)
    if limit_error:
        return {"response": limit_error, "plan": None, "usage": {"input_tokens": 0, "output_tokens": 0}}

    # Build messages array
    system_prompt = build_system_prompt(site_context)
    messages = []
    for msg in session_messages:
        messages.append({"role": msg["role"], "content": msg["content"]})
    messages.append({"role": "user", "content": message})

    async with httpx.AsyncClient(timeout=60.0) as client:
        resp = await client.post(
            API_URL,
            headers={
                "x-api-key": ANTHROPIC_API_KEY,
                "anthropic-version": "2023-06-01",
                "content-type": "application/json",
            },
            json={
                "model": MODEL,
                "max_tokens": MAX_TOKENS_PER_MESSAGE,
                "system": system_prompt,
                "messages": messages,
            },
        )

    if resp.status_code != 200:
        error_detail = resp.text[:200]
        return {
            "response": f"AI service error ({resp.status_code}). Please try again.",
            "plan": None,
            "usage": {"input_tokens": 0, "output_tokens": 0},
        }

    data = resp.json()
    response_text = ""
    for block in data.get("content", []):
        if block.get("type") == "text":
            response_text += block["text"]

    # Extract usage
    usage_data = data.get("usage", {})
    input_tokens = usage_data.get("input_tokens", 0)
    output_tokens = usage_data.get("output_tokens", 0)

    # Record usage
    record_usage(session_id, input_tokens, output_tokens)

    # Try to extract plan from response
    plan = _extract_plan(response_text)

    return {
        "response": response_text,
        "plan": plan,
        "usage": {"input_tokens": input_tokens, "output_tokens": output_tokens},
    }


def _extract_plan(response_text: str) -> Optional[list]:
    """Extract a JSON plan block from the LLM response, if present."""
    import re

    pattern = r'```json\s*(\{[^`]*?"plan"\s*:\s*\[.*?\]\s*\})\s*```'
    match = re.search(pattern, response_text, re.DOTALL)
    if match:
        try:
            parsed = json.loads(match.group(1))
            return parsed.get("plan")
        except json.JSONDecodeError:
            pass
    return None


def get_usage_stats() -> dict:
    """Get current usage statistics."""
    usage = _load_usage()
    today = _today()
    return {
        "daily_tokens_used": usage.get("daily", {}).get(today, 0),
        "daily_token_limit": MAX_TOKENS_PER_DAY,
        "active_sessions": len(usage.get("sessions", {})),
    }
