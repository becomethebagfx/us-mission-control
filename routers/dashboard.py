"""
Mission Control Dashboard — Summary Router
Aggregates data from all systems into a single dashboard overview.
"""

from fastapi import APIRouter, Query
import json
from config import config
from typing import Optional

router = APIRouter()


def load_json(path):
    """Load JSON data from a file path, returning empty list/dict on failure."""
    if path.exists():
        return json.loads(path.read_text())
    return {}


@router.get("/summary")
async def dashboard_summary(company: Optional[str] = Query(None)):
    """Aggregated dashboard summary across all systems."""
    posts = load_json(config.POSTS_FILE)
    articles = load_json(config.ARTICLES_FILE)
    leads = load_json(config.LEADS_FILE)
    tokens = load_json(config.TOKENS_FILE)

    # Normalize to lists
    posts = posts if isinstance(posts, list) else []
    articles = articles if isinstance(articles, list) else []
    leads = leads if isinstance(leads, list) else []

    # Filter by company if specified
    if company:
        posts = [p for p in posts if p.get("company_slug") == company]
        articles = [a for a in articles if a.get("company_slug") == company]
        leads = [l for l in leads if l.get("company_slug") == company]

    # LinkedIn stats
    scheduled_posts = [p for p in posts if p.get("status") == "scheduled"]
    published_posts = [p for p in posts if p.get("status") == "published"]
    total_engagement = sum(
        p.get("engagement", {}).get("likes", 0)
        + p.get("engagement", {}).get("comments", 0)
        + p.get("engagement", {}).get("shares", 0)
        for p in published_posts
    )

    # Content stats
    approved_articles = [a for a in articles if a.get("status") == "approved"]
    published_articles = [a for a in articles if a.get("status") == "published"]
    avg_aeo = sum(a.get("aeo_score", 0) for a in articles) / max(len(articles), 1)

    # Reactivation stats
    active_leads = [
        l for l in leads if l.get("status") in ("new", "contacted", "engaged")
    ]
    converted_leads = [l for l in leads if l.get("status") == "converted"]
    total_pipeline = sum(l.get("deal_value", 0) for l in active_leads)

    # Token health
    token_statuses = {}
    for t in tokens if isinstance(tokens, list) else []:
        token_statuses[t.get("company_slug", "")] = (
            t.get("linkedin_token", {}).get("status", "unknown")
        )

    return {
        "linkedin": {
            "scheduled": len(scheduled_posts),
            "published": len(published_posts),
            "drafts": len([p for p in posts if p.get("status") == "draft"]),
            "total_engagement": total_engagement,
            "posts_this_week": len(scheduled_posts),
        },
        "content": {
            "total_articles": len(articles),
            "approved": len(approved_articles),
            "published": len(published_articles),
            "avg_aeo_score": round(avg_aeo, 1),
        },
        "reactivation": {
            "active_leads": len(active_leads),
            "converted": len(converted_leads),
            "pipeline_value": total_pipeline,
            "conversion_rate": round(
                len(converted_leads) / max(len(leads), 1) * 100, 1
            ),
        },
        "tokens": token_statuses,
        "companies": len(config.ACTIVE_COMPANIES),
    }
