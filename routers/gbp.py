"""
GBP Router — Google Business Profile management.
Locations, posts, and performance insights.
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


def _load_gbp() -> dict:
    """Load GBP data, handling both dict and list formats."""
    raw = load_json(config.GBP_FILE)
    if isinstance(raw, dict):
        return raw
    return {"locations": raw, "posts": []}


# ── Locations ────────────────────────────────────────────────────


@router.get("/locations")
def list_locations():
    """List all GBP locations."""
    data = _load_gbp()
    locations = data.get("locations", [])
    return {"locations": locations, "total": len(locations)}


@router.get("/locations/{company_slug}")
def get_location(company_slug: str):
    """Get GBP location for a specific company."""
    data = _load_gbp()
    locations = data.get("locations", [])

    for loc in locations:
        if loc.get("company") == company_slug or loc.get("slug") == company_slug:
            return loc

    raise HTTPException(
        status_code=404,
        detail=f"No GBP location found for company '{company_slug}'",
    )


# ── Posts ────────────────────────────────────────────────────────


@router.get("/posts")
def list_posts():
    """List all GBP posts."""
    data = _load_gbp()
    posts = data.get("posts", [])
    return {"posts": posts, "total": len(posts)}


# ── Insights ─────────────────────────────────────────────────────


@router.get("/insights")
def get_all_insights():
    """Aggregated insights (views, clicks, calls, directions) per company."""
    data = _load_gbp()
    locations = data.get("locations", [])

    insights_by_company = {}
    totals = {"views": 0, "clicks": 0, "calls": 0, "directions": 0}

    for loc in locations:
        company = loc.get("company", "unknown")
        loc_insights = loc.get("insights", {})

        views = loc_insights.get("views", 0)
        clicks = loc_insights.get("clicks", 0)
        calls = loc_insights.get("calls", 0)
        directions = loc_insights.get("directions", 0)

        insights_by_company[company] = {
            "views": views,
            "clicks": clicks,
            "calls": calls,
            "directions": directions,
            "total_interactions": views + clicks + calls + directions,
        }

        totals["views"] += views
        totals["clicks"] += clicks
        totals["calls"] += calls
        totals["directions"] += directions

    totals["total_interactions"] = sum(totals.values())

    return {
        "by_company": insights_by_company,
        "totals": totals,
        "companies_tracked": len(insights_by_company),
    }


@router.get("/insights/{company_slug}")
def get_company_insights(company_slug: str):
    """Insights for a specific company."""
    data = _load_gbp()
    locations = data.get("locations", [])

    for loc in locations:
        if loc.get("company") == company_slug or loc.get("slug") == company_slug:
            loc_insights = loc.get("insights", {})
            views = loc_insights.get("views", 0)
            clicks = loc_insights.get("clicks", 0)
            calls = loc_insights.get("calls", 0)
            directions = loc_insights.get("directions", 0)

            return {
                "company": company_slug,
                "views": views,
                "clicks": clicks,
                "calls": calls,
                "directions": directions,
                "total_interactions": views + clicks + calls + directions,
            }

    raise HTTPException(
        status_code=404,
        detail=f"No GBP insights found for company '{company_slug}'",
    )
