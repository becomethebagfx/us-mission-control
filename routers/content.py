"""
Mission Control Dashboard — Content Router
Content library article management: list, filter, update, approve, publish, stats, topics.
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


def _find_article(articles: list, article_id: str) -> tuple:
    """Return (index, article) or raise 404."""
    for idx, a in enumerate(articles):
        if str(a.get("id")) == str(article_id):
            return idx, a
    raise HTTPException(status_code=404, detail=f"Article {article_id} not found")


# ── Pydantic Models ───────────────────────────────────────────────
class ArticleUpdate(BaseModel):
    title: Optional[str] = None
    topic: Optional[str] = None
    tags: Optional[List[str]] = None
    status: Optional[str] = None


# ── Endpoints ─────────────────────────────────────────────────────
@router.get("/stats")
async def content_stats(company: Optional[str] = Query(None)):
    """Article counts by status, avg word count, avg AEO score, by company."""
    articles = load_json(config.ARTICLES_FILE)
    if not isinstance(articles, list):
        articles = []

    if company:
        articles = [a for a in articles if a.get("company_slug") == company]

    # Counts by status
    status_counts: dict[str, int] = {}
    for a in articles:
        s = a.get("status", "unknown")
        status_counts[s] = status_counts.get(s, 0) + 1

    # Counts by company
    company_counts: dict[str, int] = {}
    for a in articles:
        c = a.get("company_slug", "unknown")
        company_counts[c] = company_counts.get(c, 0) + 1

    # Average word count
    word_counts = [a.get("word_count", 0) for a in articles]
    avg_word_count = round(sum(word_counts) / max(len(word_counts), 1), 1)

    # Average AEO score
    aeo_scores = [a.get("aeo_score", 0) for a in articles if a.get("aeo_score") is not None]
    avg_aeo_score = round(sum(aeo_scores) / max(len(aeo_scores), 1), 1)

    return {
        "total": len(articles),
        "by_status": status_counts,
        "by_company": company_counts,
        "avg_word_count": avg_word_count,
        "avg_aeo_score": avg_aeo_score,
    }


@router.get("/topics")
async def list_topics():
    """Return unique topics across all articles."""
    articles = load_json(config.ARTICLES_FILE)
    if not isinstance(articles, list):
        articles = []

    topics = set()
    for a in articles:
        topic = a.get("topic")
        if topic:
            topics.add(topic)

    return sorted(topics)


@router.get("/")
async def list_articles(
    company: Optional[str] = Query(None, description="Filter by company slug"),
    status: Optional[str] = Query(None, description="Filter by status: draft|review|approved|published"),
    sort: Optional[str] = Query(None, description="Sort by: created_at|aeo_score"),
):
    """List articles with optional company, status filters and sorting."""
    articles = load_json(config.ARTICLES_FILE)
    if not isinstance(articles, list):
        articles = []

    if company:
        articles = [a for a in articles if a.get("company_slug") == company]
    if status:
        articles = [a for a in articles if a.get("status") == status]

    if sort == "created_at":
        articles.sort(key=lambda a: a.get("created_at", ""), reverse=True)
    elif sort == "aeo_score":
        articles.sort(key=lambda a: a.get("aeo_score", 0), reverse=True)

    return articles


@router.get("/{article_id}")
async def get_article(article_id: str):
    """Get a single article by id."""
    articles = load_json(config.ARTICLES_FILE)
    if not isinstance(articles, list):
        articles = []

    _, article = _find_article(articles, article_id)
    return article


@router.put("/{article_id}")
async def update_article(article_id: str, update: ArticleUpdate):
    """Update article fields (title, topic, tags, status)."""
    articles = load_json(config.ARTICLES_FILE)
    if not isinstance(articles, list):
        articles = []

    idx, article = _find_article(articles, article_id)

    if update.title is not None:
        article["title"] = update.title
    if update.topic is not None:
        article["topic"] = update.topic
    if update.tags is not None:
        article["tags"] = update.tags
    if update.status is not None:
        article["status"] = update.status

    article["updated_at"] = datetime.utcnow().isoformat()
    articles[idx] = article
    save_json(config.ARTICLES_FILE, articles)

    return article


@router.post("/{article_id}/approve")
async def approve_article(article_id: str):
    """Set article status to 'approved'."""
    articles = load_json(config.ARTICLES_FILE)
    if not isinstance(articles, list):
        articles = []

    idx, article = _find_article(articles, article_id)
    article["status"] = "approved"
    article["updated_at"] = datetime.utcnow().isoformat()
    articles[idx] = article
    save_json(config.ARTICLES_FILE, articles)

    return {"message": f"Article {article_id} approved", "article": article}


@router.post("/{article_id}/publish")
async def publish_article(article_id: str):
    """Set article status to 'published' and record published_at timestamp."""
    articles = load_json(config.ARTICLES_FILE)
    if not isinstance(articles, list):
        articles = []

    idx, article = _find_article(articles, article_id)
    article["status"] = "published"
    article["published_at"] = datetime.utcnow().isoformat()
    article["updated_at"] = datetime.utcnow().isoformat()
    articles[idx] = article
    save_json(config.ARTICLES_FILE, articles)

    return {"message": f"Article {article_id} published", "article": article}
