"""
Reactivation Router — Database reactivation lead management.
Tracks leads through the reactivation funnel with scoring and sequencing.
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


# ── Leads CRUD ───────────────────────────────────────────────────


@router.get("/leads")
def list_leads(
    company: Optional[str] = Query(None, description="Filter by company slug"),
    status: Optional[str] = Query(
        None,
        description="Filter by status",
        regex="^(new|contacted|engaged|converted|dead)$",
    ),
    min_score: Optional[int] = Query(None, description="Minimum lead score"),
):
    """List reactivation leads with optional filters."""
    leads = load_json(config.LEADS_FILE)

    if company:
        leads = [l for l in leads if l.get("company") == company]
    if status:
        leads = [l for l in leads if l.get("status") == status]
    if min_score is not None:
        leads = [l for l in leads if l.get("score", 0) >= min_score]

    return {"leads": leads, "total": len(leads)}


@router.get("/leads/{lead_id}")
def get_lead(lead_id: str):
    """Get a single lead by ID."""
    leads = load_json(config.LEADS_FILE)

    for lead in leads:
        if str(lead.get("id")) == lead_id:
            return lead

    raise HTTPException(status_code=404, detail=f"Lead {lead_id} not found")


@router.put("/leads/{lead_id}")
def update_lead(lead_id: str, updates: dict):
    """Update lead status and/or score."""
    leads = load_json(config.LEADS_FILE)

    for i, lead in enumerate(leads):
        if str(lead.get("id")) == lead_id:
            allowed_fields = {"status", "score", "notes", "sequence_step", "last_contact"}
            for key, value in updates.items():
                if key in allowed_fields:
                    leads[i][key] = value
            save_json(config.LEADS_FILE, leads)
            return leads[i]

    raise HTTPException(status_code=404, detail=f"Lead {lead_id} not found")


# ── Funnel Metrics ───────────────────────────────────────────────


@router.get("/funnel")
def get_funnel():
    """Return funnel metrics: counts by status and conversion rates."""
    leads = load_json(config.LEADS_FILE)

    statuses = ["new", "contacted", "engaged", "converted", "dead"]
    counts = {s: 0 for s in statuses}

    for lead in leads:
        s = lead.get("status", "new")
        if s in counts:
            counts[s] += 1

    total = len(leads)
    active = total - counts["dead"]

    conversion_rates = {}
    if total > 0:
        conversion_rates["contacted_rate"] = round(
            (counts["contacted"] + counts["engaged"] + counts["converted"]) / total * 100, 1
        )
        conversion_rates["engaged_rate"] = round(
            (counts["engaged"] + counts["converted"]) / total * 100, 1
        )
        conversion_rates["converted_rate"] = round(
            counts["converted"] / total * 100, 1
        )
        conversion_rates["dead_rate"] = round(counts["dead"] / total * 100, 1)
    else:
        conversion_rates = {
            "contacted_rate": 0,
            "engaged_rate": 0,
            "converted_rate": 0,
            "dead_rate": 0,
        }

    return {
        "counts": counts,
        "total": total,
        "active": active,
        "conversion_rates": conversion_rates,
    }


# ── Pipeline Metrics ─────────────────────────────────────────────


@router.get("/metrics")
def get_metrics():
    """Pipeline value by company, average score, top leads."""
    leads = load_json(config.LEADS_FILE)

    if not leads:
        return {
            "by_company": {},
            "avg_score": 0,
            "top_leads": [],
            "total_pipeline_value": 0,
        }

    # Group by company
    by_company = {}
    scores = []
    for lead in leads:
        company = lead.get("company", "unknown")
        value = lead.get("pipeline_value", 0)
        score = lead.get("score", 0)
        scores.append(score)

        if company not in by_company:
            by_company[company] = {"count": 0, "pipeline_value": 0, "avg_score": 0}
        by_company[company]["count"] += 1
        by_company[company]["pipeline_value"] += value

    # Calculate avg score per company
    for company in by_company:
        company_leads = [l for l in leads if l.get("company") == company]
        company_scores = [l.get("score", 0) for l in company_leads]
        by_company[company]["avg_score"] = round(
            sum(company_scores) / len(company_scores), 1
        ) if company_scores else 0

    avg_score = round(sum(scores) / len(scores), 1) if scores else 0

    # Top leads by score
    top_leads = sorted(leads, key=lambda l: l.get("score", 0), reverse=True)[:10]

    total_pipeline = sum(l.get("pipeline_value", 0) for l in leads)

    return {
        "by_company": by_company,
        "avg_score": avg_score,
        "top_leads": top_leads,
        "total_pipeline_value": total_pipeline,
    }


# ── Sequence Grouping ───────────────────────────────────────────


@router.get("/sequences")
def get_sequences():
    """Return leads grouped by sequence step (0-4)."""
    leads = load_json(config.LEADS_FILE)

    sequences = {str(i): [] for i in range(5)}

    for lead in leads:
        step = str(lead.get("sequence_step", 0))
        if step in sequences:
            sequences[step].append(lead)

    summary = {
        step: {"count": len(items), "leads": items}
        for step, items in sequences.items()
    }

    return {"sequences": summary, "total": len(leads)}
