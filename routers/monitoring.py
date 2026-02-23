"""
Monitoring — API Router
Deployments, performance scores, logs, and HTTP analytics.
"""

from fastapi import APIRouter, HTTPException, Query

from modules import render_client, performance_client
from modules.site_context import SITE_REGISTRY

router = APIRouter(prefix="/api/monitoring", tags=["Monitoring"])

# Map frontend time range strings to deploy limits
_RANGE_TO_LIMIT = {"6h": 5, "24h": 10, "3d": 20, "7d": 30, "30d": 50}


@router.get("/deploys")
async def list_deploys(site: str = "", time_range: str = Query("24h", alias="range")):
    """List deploys for a site (or all sites), filtered by time range."""
    limit = _RANGE_TO_LIMIT.get(time_range, 20)

    if site:
        service_id = await render_client.get_service_by_slug(site)
        if not service_id:
            return render_client.demo_deploys()
        deploys = await render_client.list_deploys(service_id, limit=limit)
        return deploys

    # All sites
    all_deploys = []
    for slug in SITE_REGISTRY:
        service_id = await render_client.get_service_by_slug(slug)
        if service_id:
            deploys = await render_client.list_deploys(service_id, limit=5)
            for d in deploys:
                d["site"] = slug
            all_deploys.extend(deploys)
        else:
            for d in render_client.demo_deploys()[:3]:
                d["site"] = slug
                all_deploys.append(d)

    all_deploys.sort(key=lambda d: d.get("created_at", ""), reverse=True)
    return all_deploys[:limit]


@router.get("/deploy/{deploy_id}")
async def get_deploy_detail(deploy_id: str, site: str = ""):
    """Get deploy details and logs."""
    service_id = None
    if site:
        service_id = await render_client.get_service_by_slug(site)

    if not service_id:
        return {"id": deploy_id, "logs": "Demo mode: Configure RENDER_API_KEY for real logs."}

    logs = await render_client.get_deploy_logs(service_id, deploy_id)
    return {"id": deploy_id, "logs": logs}


@router.get("/performance")
async def get_performance(site: str = ""):
    """Get PageSpeed scores for a site (or all sites)."""
    if site:
        info = SITE_REGISTRY.get(site)
        if not info:
            raise HTTPException(status_code=404, detail="Site not found")
        scores = await performance_client.get_all_scores(info["url"])
        return {"site": site, "name": info["name"], **scores}

    # All sites
    results = []
    for slug, info in SITE_REGISTRY.items():
        scores = await performance_client.get_all_scores(info["url"])
        results.append({"site": slug, "name": info["name"], **scores})
    return results


@router.get("/logs")
async def get_logs(site: str = "", level: str = "", time_range: str = Query("24h", alias="range")):
    """Get service logs. Returns demo data if Render API not configured."""
    # Render free tier has limited log access — generate demo logs
    from datetime import datetime, timedelta
    import random

    range_hours = {"6h": 6, "24h": 24, "3d": 72, "7d": 168, "30d": 720}.get(time_range, 24)
    limit = min(range_hours * 4, 200)  # ~4 log entries per hour

    levels = ["INFO", "WARN", "ERROR"] if not level else [level.upper()]
    messages = [
        "Deployment started",
        "Building static site...",
        "Uploading files...",
        "Deployment live",
        "Health check passed",
        "SSL certificate renewed",
        "Custom domain verified",
        "Cache purged",
    ]

    now = datetime.utcnow()
    logs = []
    for i in range(min(limit, 50)):
        lvl = random.choice(levels)
        logs.append({
            "timestamp": (now - timedelta(minutes=i * 15)).isoformat(),
            "level": lvl,
            "message": random.choice(messages),
            "site": site or random.choice(list(SITE_REGISTRY.keys())),
        })

    return logs


@router.get("/metrics")
async def get_metrics(site: str = "", time_range: str = Query("24h", alias="range")):
    """Get HTTP bandwidth and request metrics. Demo data for MVP."""
    # Render metrics API requires paid plan
    # For MVP, return structured demo data
    import random

    range_hours = {"6h": 6, "24h": 24, "3d": 72, "7d": 168, "30d": 720}.get(time_range, 24)

    return {
        "site": site or "all",
        "range": time_range,
        "requests_total": random.randint(500, 5000),
        "bandwidth_mb": round(random.uniform(10, 200), 1),
        "status_codes": {
            "200": random.randint(400, 4500),
            "301": random.randint(10, 100),
            "304": random.randint(50, 500),
            "404": random.randint(0, 20),
        },
        "avg_response_ms": random.randint(50, 300),
    }
