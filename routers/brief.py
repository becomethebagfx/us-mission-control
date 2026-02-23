"""
Monday Morning Brief — API Router
Weekly AI-generated executive summaries.
"""

import logging
import time

from fastapi import APIRouter, HTTPException, Request

from modules import brief_generator

logger = logging.getLogger(__name__)
router = APIRouter(prefix="/api/brief", tags=["Monday Morning Brief"])

_last_generate_time = 0
_GENERATE_COOLDOWN = 60  # seconds between generation requests


@router.get("/latest")
async def get_latest():
    """Get the most recent weekly brief."""
    brief = brief_generator.get_latest_brief()
    if not brief:
        return {"message": "No briefs generated yet. Click 'Generate Now' to create one.", "brief": None}
    return brief


@router.get("/history")
async def list_history(limit: int = 12):
    """List past briefs (last 12 weeks)."""
    return brief_generator.list_briefs(limit=limit)


@router.post("/generate")
async def generate_brief():
    """Manually trigger brief generation."""
    global _last_generate_time
    now = time.time()
    if now - _last_generate_time < _GENERATE_COOLDOWN:
        remaining = int(_GENERATE_COOLDOWN - (now - _last_generate_time))
        raise HTTPException(status_code=429, detail=f"Please wait {remaining}s before generating another brief.")
    try:
        _last_generate_time = now
        data = await brief_generator.collect_weekly_data()
        brief = await brief_generator.generate_brief(data)
        return brief
    except Exception as e:
        logger.exception("Failed to generate brief")
        raise HTTPException(status_code=500, detail="Brief generation failed. Please try again later.")


@router.get("/config")
async def get_config():
    """Get brief configuration."""
    return {
        "enabled": True,
        "schedule": "Monday 8:00 AM ET",
        "sections": ["activity", "performance", "insight", "action_items"],
        "recipients": [],
    }


@router.put("/config")
async def update_config(request: Request):
    """Update brief configuration (placeholder for future email delivery)."""
    try:
        body = await request.json()
    except Exception:
        body = {}
    # Placeholder — store config when email delivery is implemented
    return {"message": "Configuration updated", "status": "ok", "config": body}
