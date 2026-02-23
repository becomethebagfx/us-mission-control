"""
Monitoring — Render API Client
Fetches deploy history, logs, and metrics from Render.
"""

import os
import time
from typing import Optional

import httpx

RENDER_API_KEY = os.getenv("RENDER_API_KEY", "")
API_BASE = "https://api.render.com/v1"

# Simple in-memory cache (15-minute TTL)
_cache: dict = {}
CACHE_TTL = 900  # 15 minutes


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {RENDER_API_KEY}",
        "Accept": "application/json",
    }


def _cache_key(method: str, *args) -> str:
    return f"{method}:{'|'.join(str(a) for a in args)}"


def _get_cached(key: str) -> Optional[dict]:
    entry = _cache.get(key)
    if entry and time.time() - entry["time"] < CACHE_TTL:
        return entry["data"]
    return None


def _set_cache(key: str, data):
    _cache[key] = {"data": data, "time": time.time()}


# Service ID mapping — configured per deployment
# These would be set via env vars or config
SITE_SERVICE_MAP = {
    "us-exteriors": os.getenv("RENDER_SERVICE_EXTERIORS", ""),
    "us-drywall": os.getenv("RENDER_SERVICE_DRYWALL", ""),
    "us-mission-control": os.getenv("RENDER_SERVICE_MC", ""),
}


async def list_services() -> list:
    """List all Render services."""
    if not RENDER_API_KEY:
        return _demo_services()

    cache_key = _cache_key("services")
    cached = _get_cached(cache_key)
    if cached:
        return cached

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(f"{API_BASE}/services", headers=_headers())

    if resp.status_code != 200:
        return _demo_services()

    services = []
    for item in resp.json():
        svc = item.get("service", item)
        services.append({
            "id": svc.get("id"),
            "name": svc.get("name"),
            "type": svc.get("type"),
            "status": svc.get("suspended", "active"),
            "url": svc.get("serviceDetails", {}).get("url", ""),
            "created_at": svc.get("createdAt"),
        })

    _set_cache(cache_key, services)
    return services


async def list_deploys(service_id: str, limit: int = 20) -> list:
    """List deploys for a service."""
    if not RENDER_API_KEY or not service_id:
        return demo_deploys()

    cache_key = _cache_key("deploys", service_id)
    cached = _get_cached(cache_key)
    if cached:
        return cached

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{API_BASE}/services/{service_id}/deploys",
            headers=_headers(),
            params={"limit": limit},
        )

    if resp.status_code != 200:
        return demo_deploys()

    deploys = []
    for item in resp.json():
        d = item.get("deploy", item)
        deploys.append({
            "id": d.get("id"),
            "status": d.get("status", "unknown"),
            "commit_message": d.get("commit", {}).get("message", ""),
            "commit_sha": d.get("commit", {}).get("id", "")[:7],
            "created_at": d.get("createdAt"),
            "finished_at": d.get("finishedAt"),
        })

    _set_cache(cache_key, deploys)
    return deploys


async def get_deploy_logs(service_id: str, deploy_id: str) -> str:
    """Get build logs for a specific deploy."""
    if not RENDER_API_KEY or not service_id:
        return "Demo mode: No real logs available."

    async with httpx.AsyncClient(timeout=30.0) as client:
        resp = await client.get(
            f"{API_BASE}/services/{service_id}/deploys/{deploy_id}/logs",
            headers=_headers(),
        )

    if resp.status_code != 200:
        return f"Could not fetch logs (HTTP {resp.status_code})"

    logs = resp.json()
    if isinstance(logs, list):
        return "\n".join(entry.get("message", "") for entry in logs)
    return str(logs)


async def get_service_by_slug(site_slug: str) -> Optional[str]:
    """Get Render service ID for a site slug."""
    service_id = SITE_SERVICE_MAP.get(site_slug)
    if service_id:
        return service_id

    # Try to find by name
    services = await list_services()
    for svc in services:
        name = svc.get("name", "").lower()
        if site_slug.replace("-", "") in name.replace("-", ""):
            return svc.get("id")
    return None


# ── Demo Data ─────────────────────────────────────────────────

def _demo_services() -> list:
    return [
        {"id": "srv-demo-ext", "name": "us-exteriors", "type": "static_site", "status": "active", "url": "https://us-exteriors.onrender.com"},
        {"id": "srv-demo-dry", "name": "us-drywall", "type": "static_site", "status": "active", "url": "https://us-drywall.onrender.com"},
    ]


def demo_deploys() -> list:
    from datetime import datetime, timedelta
    now = datetime.utcnow()
    return [
        {"id": f"dep-{i}", "status": "live" if i < 3 else "deactivated", "commit_message": f"Update website content (demo)", "commit_sha": f"abc{i:04d}", "created_at": (now - timedelta(hours=i*6)).isoformat(), "finished_at": (now - timedelta(hours=i*6) + timedelta(minutes=2)).isoformat()}
        for i in range(5)
    ]
