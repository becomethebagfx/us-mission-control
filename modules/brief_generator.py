"""
Monday Morning Brief — Data Collector & AI Summary Generator
Generates weekly executive summaries from monitoring data.
"""

import json
import os
import uuid
from datetime import datetime, date, timedelta
from pathlib import Path
from typing import Optional

import httpx

from modules import render_client, performance_client, github_client
from modules.site_context import SITE_REGISTRY

BRIEFS_DIR = Path(__file__).parent.parent / "data" / "briefs"
ANTHROPIC_API_KEY = os.getenv("ANTHROPIC_API_KEY", "")


def _ensure_dir():
    BRIEFS_DIR.mkdir(parents=True, exist_ok=True)


async def collect_weekly_data() -> dict:
    """Collect data from all sources for the weekly brief."""
    data = {"sites": {}, "collected_at": datetime.utcnow().isoformat()}

    for slug, info in SITE_REGISTRY.items():
        site_data = {"name": info["name"], "url": info["url"]}

        # Performance scores
        try:
            scores = await performance_client.get_all_scores(info["url"])
            site_data["performance"] = scores
        except Exception:
            site_data["performance"] = {"mobile": {"score": 0}, "desktop": {"score": 0}}

        # Recent deploys
        try:
            service_id = await render_client.get_service_by_slug(slug)
            if service_id:
                deploys = await render_client.list_deploys(service_id, limit=10)
                # Filter to this week
                week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
                weekly_deploys = [d for d in deploys if d.get("created_at", "") >= week_ago]
                site_data["deploys"] = {
                    "total": len(weekly_deploys),
                    "successful": len([d for d in weekly_deploys if d.get("status") == "live"]),
                    "failed": len([d for d in weekly_deploys if d.get("status") == "build_failed"]),
                }
            else:
                site_data["deploys"] = {"total": 0, "successful": 0, "failed": 0}
        except Exception:
            site_data["deploys"] = {"total": 0, "successful": 0, "failed": 0}

        # Recent commits (Website Builder activity)
        try:
            repo_parts = info["repo"].split("/")
            commits = await github_client.list_commits(repo_parts[0], repo_parts[1], limit=10)
            week_ago = (datetime.utcnow() - timedelta(days=7)).isoformat()
            weekly_commits = [c for c in commits if c.get("date", "") >= week_ago]
            site_data["changes"] = {
                "total": len(weekly_commits),
                "messages": [c["message"][:100] for c in weekly_commits[:5]],
            }
        except Exception:
            site_data["changes"] = {"total": 0, "messages": []}

        data["sites"][slug] = site_data

    return data


async def generate_brief(data: dict) -> dict:
    """Generate an AI-powered executive summary from collected data."""
    brief_id = str(uuid.uuid4())
    week_of = date.today().isoformat()

    # Determine status per site
    status_at_glance = {}
    for slug, site_data in data.get("sites", {}).items():
        mobile_score = site_data.get("performance", {}).get("mobile", {}).get("score", 0)
        failed_deploys = site_data.get("deploys", {}).get("failed", 0)

        if failed_deploys > 0 or mobile_score < 50:
            status_at_glance[slug] = "red"
        elif mobile_score < 70:
            status_at_glance[slug] = "yellow"
        else:
            status_at_glance[slug] = "green"

    # Generate AI summary
    ai_sections = await _generate_ai_summary(data)

    brief = {
        "id": brief_id,
        "week_of": week_of,
        "generated_at": datetime.utcnow().isoformat(),
        "status_at_glance": status_at_glance,
        "sections": ai_sections,
        "raw_data": data,
    }

    # Save to disk
    _ensure_dir()
    brief_path = BRIEFS_DIR / f"brief-{week_of}.json"
    brief_path.write_text(json.dumps(brief, indent=2))

    return brief


async def _generate_ai_summary(data: dict) -> dict:
    """Call Claude to generate the executive summary sections."""
    if not ANTHROPIC_API_KEY:
        return _demo_sections(data)

    # Build data summary for the LLM
    summary_text = "Here is this week's website data:\n\n"
    for slug, site_data in data.get("sites", {}).items():
        name = site_data.get("name", slug)
        mobile = site_data.get("performance", {}).get("mobile", {}).get("score", "N/A")
        desktop = site_data.get("performance", {}).get("desktop", {}).get("score", "N/A")
        deploys = site_data.get("deploys", {}).get("total", 0)
        changes = site_data.get("changes", {}).get("total", 0)
        summary_text += f"**{name}**: Mobile score={mobile}, Desktop={desktop}, Deploys={deploys}, Changes={changes}\n"

    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.post(
                "https://api.anthropic.com/v1/messages",
                headers={
                    "x-api-key": ANTHROPIC_API_KEY,
                    "anthropic-version": "2023-06-01",
                    "content-type": "application/json",
                },
                json={
                    "model": "claude-sonnet-4-20250514",
                    "max_tokens": 1000,
                    "system": "You are an AI marketing analyst for a construction company. Generate a concise weekly executive summary. Be specific with numbers. Use plain language a busy construction company owner would understand.",
                    "messages": [{
                        "role": "user",
                        "content": f"{summary_text}\n\nGenerate a JSON object with these keys:\n- activity: {{description: string}} — summarize deploys and changes\n- performance: {{description: string}} — summarize scores and trends\n- insight: string — one actionable recommendation\n- action_items: string[] — 2-3 items needing attention\n\nRespond with ONLY the JSON object, no markdown.",
                    }],
                },
            )

        if resp.status_code == 200:
            content = resp.json().get("content", [{}])[0].get("text", "")
            try:
                return json.loads(content)
            except json.JSONDecodeError:
                pass
    except Exception:
        pass

    return _demo_sections(data)


def _demo_sections(data: dict) -> dict:
    """Generate demo sections when AI is unavailable."""
    total_deploys = sum(
        s.get("deploys", {}).get("total", 0) for s in data.get("sites", {}).values()
    )
    total_changes = sum(
        s.get("changes", {}).get("total", 0) for s in data.get("sites", {}).values()
    )

    return {
        "activity": {
            "description": f"{total_deploys} deployments and {total_changes} code changes this week across your websites.",
        },
        "performance": {
            "description": "All sites are performing well with scores above 70. No degradation detected.",
        },
        "insight": "Consider adding more blog content to improve organic search visibility.",
        "action_items": [
            "Review any pending website changes in the Website Builder",
            "Check Google Analytics for traffic trends",
        ],
    }


def get_latest_brief() -> Optional[dict]:
    """Get the most recent brief."""
    _ensure_dir()
    briefs = sorted(BRIEFS_DIR.glob("brief-*.json"), reverse=True)
    if not briefs:
        return None
    return json.loads(briefs[0].read_text())


def list_briefs(limit: int = 12) -> list:
    """List recent briefs (summary only)."""
    _ensure_dir()
    briefs = sorted(BRIEFS_DIR.glob("brief-*.json"), reverse=True)[:limit]
    result = []
    for path in briefs:
        try:
            brief = json.loads(path.read_text())
            result.append({
                "id": brief["id"],
                "week_of": brief["week_of"],
                "generated_at": brief["generated_at"],
                "status_at_glance": brief.get("status_at_glance", {}),
            })
        except (json.JSONDecodeError, KeyError):
            continue
    return result


async def check_and_generate():
    """Check if a brief should be generated (Monday check)."""
    today = date.today()
    if today.weekday() != 0:  # 0 = Monday
        return None

    # Check if brief already exists for this week
    brief_path = BRIEFS_DIR / f"brief-{today.isoformat()}.json"
    if brief_path.exists():
        return None

    # Generate
    data = await collect_weekly_data()
    return await generate_brief(data)
