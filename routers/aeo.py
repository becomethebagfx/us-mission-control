"""
AEO Router — AEO/GEO content engine data.
Tracks queries, answer capsules, and page-level AEO scores.
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


def _load_aeo() -> dict:
    """Load AEO data, handling both dict and list formats."""
    raw = load_json(config.AEO_FILE)
    if isinstance(raw, dict):
        return raw
    return {"queries": raw, "capsules": [], "pages": []}


# ── Queries ──────────────────────────────────────────────────────


@router.get("/queries")
def list_queries(
    company: Optional[str] = Query(None, description="Filter by company slug"),
):
    """List tracked queries with positions/scores."""
    data = _load_aeo()
    queries = data.get("queries", [])

    if company:
        queries = [q for q in queries if q.get("company") == company]

    return {"queries": queries, "total": len(queries)}


# ── Answer Capsules ──────────────────────────────────────────────


@router.get("/capsules")
def list_capsules(
    company: Optional[str] = Query(None, description="Filter by company slug"),
    status: Optional[str] = Query(None, description="Filter by capsule status"),
):
    """List answer capsules with optional filters."""
    data = _load_aeo()
    capsules = data.get("capsules", [])

    if company:
        capsules = [c for c in capsules if c.get("company") == company]
    if status:
        capsules = [c for c in capsules if c.get("status") == status]

    return {"capsules": capsules, "total": len(capsules)}


# ── Pages ────────────────────────────────────────────────────────


@router.get("/pages")
def list_pages(
    company: Optional[str] = Query(None, description="Filter by company slug"),
):
    """List page AEO scores."""
    data = _load_aeo()
    pages = data.get("pages", [])

    if company:
        pages = [p for p in pages if p.get("company") == company]

    return {"pages": pages, "total": len(pages)}


# ── Stats ────────────────────────────────────────────────────────


@router.get("/stats")
def get_stats():
    """Summary: avg score, total queries, capsule count, pages audited."""
    data = _load_aeo()

    queries = data.get("queries", [])
    capsules = data.get("capsules", [])
    pages = data.get("pages", [])

    # Average AEO score from pages
    page_scores = [p.get("aeo_score", 0) for p in pages if p.get("aeo_score") is not None]
    avg_score = round(sum(page_scores) / len(page_scores), 1) if page_scores else 0

    # Average query position
    positions = [q.get("position", 0) for q in queries if q.get("position") is not None]
    avg_position = round(sum(positions) / len(positions), 1) if positions else 0

    # Capsule status breakdown
    capsule_statuses = {}
    for c in capsules:
        s = c.get("status", "unknown")
        capsule_statuses[s] = capsule_statuses.get(s, 0) + 1

    # By company
    companies_tracked = set()
    for item in queries + capsules + pages:
        company = item.get("company")
        if company:
            companies_tracked.add(company)

    return {
        "avg_aeo_score": avg_score,
        "avg_query_position": avg_position,
        "total_queries": len(queries),
        "total_capsules": len(capsules),
        "capsule_statuses": capsule_statuses,
        "pages_audited": len(pages),
        "companies_tracked": len(companies_tracked),
    }
