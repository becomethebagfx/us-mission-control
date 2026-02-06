"""
Brand Audit Router — Brand consistency auditor.
Tracks brand health across companies with scoring and issue categorization.
"""

from fastapi import APIRouter, HTTPException
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


def _load_brand_audit() -> dict:
    """Load brand audit data, handling both dict and list formats."""
    raw = load_json(config.BRAND_AUDIT_FILE)
    if isinstance(raw, dict):
        return raw
    return {"audits": raw}


# ── List Audits ──────────────────────────────────────────────────


@router.get("/")
def list_audits():
    """List all brand audit results."""
    data = _load_brand_audit()
    audits = data.get("audits", [])
    return {"audits": audits, "total": len(audits)}


# ── Summary (MUST be before /{company_slug}) ─────────────────────


@router.get("/summary")
def get_summary():
    """Overall brand health: avg score, worst categories, total issues."""
    data = _load_brand_audit()
    audits = data.get("audits", [])

    if not audits:
        return {
            "avg_score": 0,
            "total_audits": 0,
            "total_issues": 0,
            "worst_categories": [],
            "by_company": {},
        }

    # Average score (handle both "score" and "overall_score" keys)
    scores = [a.get("overall_score", a.get("score", 0)) for a in audits]
    scores = [s for s in scores if s is not None]
    avg_score = round(sum(scores) / len(scores), 1) if scores else 0

    # Collect all issues
    total_issues = 0
    all_issues = []
    for audit in audits:
        issues = audit.get("issues", [])
        total_issues += len(issues)
        for issue in issues:
            # Issues can be strings or dicts
            if isinstance(issue, str):
                all_issues.append(issue)
            elif isinstance(issue, dict):
                all_issues.append(issue.get("description", str(issue)))

    # By company summary
    by_company = {}
    for audit in audits:
        company = audit.get("company", "unknown")
        by_company[company] = {
            "score": audit.get("overall_score", audit.get("score", 0)),
            "issues": len(audit.get("issues", [])),
            "last_audited": audit.get("last_audited", None),
        }

    return {
        "avg_score": avg_score,
        "total_audits": len(audits),
        "total_issues": total_issues,
        "issues": all_issues,
        "by_company": by_company,
    }


# ── Company Audit ────────────────────────────────────────────────


@router.get("/{company_slug}")
def get_company_audit(company_slug: str):
    """Get audit for a specific company."""
    data = _load_brand_audit()
    audits = data.get("audits", [])

    for audit in audits:
        if audit.get("company") == company_slug or audit.get("slug") == company_slug:
            return audit

    raise HTTPException(
        status_code=404,
        detail=f"No brand audit found for company '{company_slug}'",
    )
