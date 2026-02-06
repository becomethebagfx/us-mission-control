"""
Mission Control Dashboard — Posts Router
LinkedIn post queue management: list, filter, update, approve, reject, reschedule.
"""

from fastapi import APIRouter, Query, HTTPException
from pydantic import BaseModel
import json
from config import config
from typing import Optional, List
from pathlib import Path
from datetime import datetime

router = APIRouter()


# ── Helpers ────────────────────────────────────────────────────────
def load_json(path: Path):
    if path.exists():
        return json.loads(path.read_text())
    return []


def save_json(path: Path, data):
    path.write_text(json.dumps(data, indent=2, default=str))


def _find_post(posts: list, post_id: str) -> tuple:
    """Return (index, post) or raise 404."""
    for idx, p in enumerate(posts):
        if str(p.get("id")) == str(post_id):
            return idx, p
    raise HTTPException(status_code=404, detail=f"Post {post_id} not found")


# ── Pydantic Models ───────────────────────────────────────────────
class PostUpdate(BaseModel):
    title: Optional[str] = None
    content: Optional[str] = None
    scheduled_date: Optional[str] = None
    hashtags: Optional[List[str]] = None


class RescheduleRequest(BaseModel):
    scheduled_date: str


# ── Endpoints ─────────────────────────────────────────────────────
@router.get("/stats")
async def post_stats(company: Optional[str] = Query(None)):
    """Return counts by status and by company."""
    posts = load_json(config.POSTS_FILE)
    if not isinstance(posts, list):
        posts = []

    if company:
        posts = [p for p in posts if p.get("company_slug") == company]

    # Counts by status
    status_counts: dict[str, int] = {}
    for p in posts:
        s = p.get("status", "unknown")
        status_counts[s] = status_counts.get(s, 0) + 1

    # Counts by company
    company_counts: dict[str, int] = {}
    for p in posts:
        c = p.get("company_slug", "unknown")
        company_counts[c] = company_counts.get(c, 0) + 1

    return {
        "total": len(posts),
        "by_status": status_counts,
        "by_company": company_counts,
    }


@router.get("/")
async def list_posts(
    company: Optional[str] = Query(None, description="Filter by company slug"),
    status: Optional[str] = Query(None, description="Filter by status: scheduled|draft|published|rejected"),
):
    """List all posts with optional company and status filters."""
    posts = load_json(config.POSTS_FILE)
    if not isinstance(posts, list):
        posts = []

    if company:
        posts = [p for p in posts if p.get("company_slug") == company]
    if status:
        posts = [p for p in posts if p.get("status") == status]

    return posts


@router.get("/{post_id}")
async def get_post(post_id: str):
    """Get a single post by id."""
    posts = load_json(config.POSTS_FILE)
    if not isinstance(posts, list):
        posts = []

    _, post = _find_post(posts, post_id)
    return post


@router.put("/{post_id}")
async def update_post(post_id: str, update: PostUpdate):
    """Update post fields (title, content, scheduled_date, hashtags)."""
    posts = load_json(config.POSTS_FILE)
    if not isinstance(posts, list):
        posts = []

    idx, post = _find_post(posts, post_id)

    if update.title is not None:
        post["title"] = update.title
    if update.content is not None:
        post["content"] = update.content
    if update.scheduled_date is not None:
        post["scheduled_date"] = update.scheduled_date
    if update.hashtags is not None:
        post["hashtags"] = update.hashtags

    post["updated_at"] = datetime.utcnow().isoformat()
    posts[idx] = post
    save_json(config.POSTS_FILE, posts)

    return post


@router.post("/{post_id}/approve")
async def approve_post(post_id: str):
    """Set post status to 'scheduled'."""
    posts = load_json(config.POSTS_FILE)
    if not isinstance(posts, list):
        posts = []

    idx, post = _find_post(posts, post_id)
    post["status"] = "scheduled"
    post["updated_at"] = datetime.utcnow().isoformat()
    posts[idx] = post
    save_json(config.POSTS_FILE, posts)

    return {"message": f"Post {post_id} approved and scheduled", "post": post}


@router.post("/{post_id}/reject")
async def reject_post(post_id: str):
    """Set post status to 'rejected'."""
    posts = load_json(config.POSTS_FILE)
    if not isinstance(posts, list):
        posts = []

    idx, post = _find_post(posts, post_id)
    post["status"] = "rejected"
    post["updated_at"] = datetime.utcnow().isoformat()
    posts[idx] = post
    save_json(config.POSTS_FILE, posts)

    return {"message": f"Post {post_id} rejected", "post": post}


@router.post("/{post_id}/reschedule")
async def reschedule_post(post_id: str, req: RescheduleRequest):
    """Update scheduled_date while keeping status as 'scheduled'."""
    posts = load_json(config.POSTS_FILE)
    if not isinstance(posts, list):
        posts = []

    idx, post = _find_post(posts, post_id)
    post["scheduled_date"] = req.scheduled_date
    post["status"] = "scheduled"
    post["updated_at"] = datetime.utcnow().isoformat()
    posts[idx] = post
    save_json(config.POSTS_FILE, posts)

    return {"message": f"Post {post_id} rescheduled to {req.scheduled_date}", "post": post}
