"""
Reviews Router — Review management across platforms.
Aggregates reviews from Google, Yelp, and Facebook with reply support.
"""

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
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


def _load_reviews() -> dict:
    """Load reviews data, handling both dict and list formats."""
    raw = load_json(config.REVIEWS_FILE)
    if isinstance(raw, dict):
        return raw
    return {"reviews": raw, "summary": {}}


class ReplyBody(BaseModel):
    reply: str


# ── List Reviews ─────────────────────────────────────────────────


@router.get("/")
def list_reviews(
    company: Optional[str] = Query(None, description="Filter by company slug"),
    platform: Optional[str] = Query(
        None,
        description="Filter by platform",
        regex="^(google|yelp|facebook)$",
    ),
    min_rating: Optional[int] = Query(None, description="Minimum rating (1-5)", ge=1, le=5),
):
    """List reviews with optional filters."""
    data = _load_reviews()
    reviews = data.get("reviews", [])

    if company:
        reviews = [r for r in reviews if r.get("company") == company]
    if platform:
        reviews = [r for r in reviews if r.get("platform") == platform]
    if min_rating is not None:
        reviews = [r for r in reviews if r.get("rating", 0) >= min_rating]

    return {"reviews": reviews, "total": len(reviews)}


# ── Review Summary (MUST be before /{review_id}) ────────────────


@router.get("/summary")
def get_summary():
    """Aggregate: total reviews, avg rating, by platform, by company."""
    data = _load_reviews()
    reviews = data.get("reviews", [])

    if not reviews:
        return {
            "total_reviews": 0,
            "avg_rating": 0,
            "by_platform": {},
            "by_company": {},
            "reply_rate": 0,
        }

    # Overall
    ratings = [r.get("rating", 0) for r in reviews]
    avg_rating = round(sum(ratings) / len(ratings), 2) if ratings else 0
    replied = sum(1 for r in reviews if r.get("reply"))

    # By platform
    by_platform = {}
    for r in reviews:
        plat = r.get("platform", "unknown")
        if plat not in by_platform:
            by_platform[plat] = {"count": 0, "total_rating": 0, "avg_rating": 0}
        by_platform[plat]["count"] += 1
        by_platform[plat]["total_rating"] += r.get("rating", 0)

    for plat, info in by_platform.items():
        if info["count"] > 0:
            info["avg_rating"] = round(info["total_rating"] / info["count"], 2)
        del info["total_rating"]

    # By company
    by_company = {}
    for r in reviews:
        comp = r.get("company", "unknown")
        if comp not in by_company:
            by_company[comp] = {"count": 0, "total_rating": 0, "avg_rating": 0}
        by_company[comp]["count"] += 1
        by_company[comp]["total_rating"] += r.get("rating", 0)

    for comp, info in by_company.items():
        if info["count"] > 0:
            info["avg_rating"] = round(info["total_rating"] / info["count"], 2)
        del info["total_rating"]

    return {
        "total_reviews": len(reviews),
        "avg_rating": avg_rating,
        "by_platform": by_platform,
        "by_company": by_company,
        "replied": replied,
        "reply_rate": round(replied / len(reviews) * 100, 1) if reviews else 0,
    }


# ── Single Review ────────────────────────────────────────────────


@router.get("/{review_id}")
def get_review(review_id: str):
    """Get a single review by ID."""
    data = _load_reviews()
    reviews = data.get("reviews", [])

    for review in reviews:
        if str(review.get("id")) == review_id:
            return review

    raise HTTPException(status_code=404, detail=f"Review {review_id} not found")


# ── Reply to Review ──────────────────────────────────────────────


@router.post("/{review_id}/reply")
def reply_to_review(review_id: str, body: ReplyBody):
    """Add reply text to a review."""
    data = _load_reviews()
    reviews = data.get("reviews", [])

    for i, review in enumerate(reviews):
        if str(review.get("id")) == review_id:
            reviews[i]["reply"] = body.reply
            reviews[i]["reply_status"] = "pending"
            data["reviews"] = reviews
            save_json(config.REVIEWS_FILE, data)
            return reviews[i]

    raise HTTPException(status_code=404, detail=f"Review {review_id} not found")
