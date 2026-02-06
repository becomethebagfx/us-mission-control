"""
Mission Control Dashboard — Quality Loop Router
Quality loop run management: list runs, get details, stats, trigger new runs.
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
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, default=str))


# ── Endpoints ─────────────────────────────────────────────────────
@router.get("/stats")
async def quality_stats(company: Optional[str] = Query(None)):
    """Aggregate quality loop stats: total runs, avg score, pass rate, by content type."""
    runs = load_json(config.QUALITY_FILE)
    if not isinstance(runs, list):
        runs = []

    if company:
        runs = [r for r in runs if r.get("company_slug") == company]

    total = len(runs)
    if total == 0:
        return {
            "total_runs": 0,
            "avg_score": 0,
            "pass_rate": 0,
            "avg_iterations": 0,
            "by_content_type": {},
            "by_status": {},
        }

    scores = [r.get("final_score", 0) for r in runs]
    avg_score = round(sum(scores) / total, 1)

    passed = sum(1 for r in runs if r.get("status") == "passed")
    pass_rate = round((passed / total) * 100, 1)

    iterations = [r.get("iteration_count", 0) for r in runs]
    avg_iterations = round(sum(iterations) / total, 1)

    by_type = {}
    for r in runs:
        ct = r.get("content_type", "unknown")
        if ct not in by_type:
            by_type[ct] = {"total": 0, "passed": 0, "avg_score": 0, "scores": []}
        by_type[ct]["total"] += 1
        by_type[ct]["scores"].append(r.get("final_score", 0))
        if r.get("status") == "passed":
            by_type[ct]["passed"] += 1

    for ct, data in by_type.items():
        data["avg_score"] = round(sum(data["scores"]) / len(data["scores"]), 1)
        data["pass_rate"] = round((data["passed"] / data["total"]) * 100, 1)
        del data["scores"]

    by_status = {}
    for r in runs:
        s = r.get("status", "unknown")
        by_status[s] = by_status.get(s, 0) + 1

    return {
        "total_runs": total,
        "avg_score": avg_score,
        "pass_rate": pass_rate,
        "avg_iterations": avg_iterations,
        "by_content_type": by_type,
        "by_status": by_status,
    }


@router.get("/runs")
async def list_runs(
    company: Optional[str] = Query(None),
    content_type: Optional[str] = Query(None),
    status: Optional[str] = Query(None),
):
    """List quality loop runs with optional filters."""
    runs = load_json(config.QUALITY_FILE)
    if not isinstance(runs, list):
        runs = []

    if company:
        runs = [r for r in runs if r.get("company_slug") == company]
    if content_type:
        runs = [r for r in runs if r.get("content_type") == content_type]
    if status:
        runs = [r for r in runs if r.get("status") == status]

    # Sort by created_at descending
    runs.sort(key=lambda r: r.get("created_at", ""), reverse=True)

    return runs


@router.get("/runs/{run_id}")
async def get_run(run_id: str):
    """Get a single quality loop run with full iteration details."""
    runs = load_json(config.QUALITY_FILE)
    if not isinstance(runs, list):
        runs = []

    for r in runs:
        if r.get("id") == run_id:
            return r

    raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")


@router.get("/content-types")
async def list_content_types():
    """Return available content types for quality loop."""
    return [
        {"value": "linkedin_post", "label": "LinkedIn Post"},
        {"value": "outreach_email", "label": "Outreach Email"},
        {"value": "aeo_capsule", "label": "AEO Capsule"},
        {"value": "gbp_post", "label": "GBP Post"},
        {"value": "review_response", "label": "Review Response"},
        {"value": "blog_article", "label": "Blog Article"},
    ]
