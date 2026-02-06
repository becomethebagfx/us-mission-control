"""
Assets Router — Visual asset management.
Tracks social posts, cover photos, OG images, flyers, and other branded assets.
"""

from fastapi import APIRouter, Query, HTTPException
import json
from config import config
from typing import Optional
from pathlib import Path

router = APIRouter()


def load_json(path: Path):
    if path.exists():
        return json.loads(path.read_text())
    return []


def save_json(path: Path, data):
    path.write_text(json.dumps(data, indent=2, default=str))


def _load_assets() -> dict:
    """Load assets data, handling both dict and list formats."""
    raw = load_json(config.ASSETS_FILE)
    if isinstance(raw, dict):
        return raw
    return {"assets": raw}


# ── List Assets ──────────────────────────────────────────────────


@router.get("/")
def list_assets(
    company: Optional[str] = Query(None, description="Filter by company slug"),
    type: Optional[str] = Query(
        None,
        description="Filter by asset type",
        alias="type",
        regex="^(social_post|cover_photo|og_image|flyer)$",
    ),
    status: Optional[str] = Query(None, description="Filter by status"),
):
    """List assets with optional filters."""
    data = _load_assets()
    assets = data.get("assets", [])

    if company:
        assets = [a for a in assets if a.get("company") == company]
    if type:
        assets = [a for a in assets if a.get("type") == type]
    if status:
        assets = [a for a in assets if a.get("status") == status]

    return {"assets": assets, "total": len(assets)}


# ── Stats (MUST be before /{asset_id}) ──────────────────────────


@router.get("/stats")
def get_stats():
    """Count by type, by company, by status."""
    data = _load_assets()
    assets = data.get("assets", [])

    if not assets:
        return {
            "total": 0,
            "by_type": {},
            "by_company": {},
            "by_status": {},
        }

    # By type
    by_type = {}
    for a in assets:
        t = a.get("type", "unknown")
        by_type[t] = by_type.get(t, 0) + 1

    # By company
    by_company = {}
    for a in assets:
        c = a.get("company", "unknown")
        by_company[c] = by_company.get(c, 0) + 1

    # By status
    by_status = {}
    for a in assets:
        s = a.get("status", "unknown")
        by_status[s] = by_status.get(s, 0) + 1

    return {
        "total": len(assets),
        "by_type": by_type,
        "by_company": by_company,
        "by_status": by_status,
    }


# ── Single Asset ─────────────────────────────────────────────────


@router.get("/{asset_id}")
def get_asset(asset_id: str):
    """Get a single asset by ID."""
    data = _load_assets()
    assets = data.get("assets", [])

    for asset in assets:
        if str(asset.get("id")) == asset_id:
            return asset

    raise HTTPException(status_code=404, detail=f"Asset {asset_id} not found")
