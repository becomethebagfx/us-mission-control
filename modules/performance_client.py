"""
Monitoring — PageSpeed Insights Client
Fetches performance scores using Google's free PageSpeed API.
"""

import time
from typing import Optional

import httpx

API_URL = "https://www.googleapis.com/pagespeedonline/v5/runPagespeed"

# 1-hour cache
_cache: dict = {}
CACHE_TTL = 3600


async def get_scores(url: str, strategy: str = "mobile") -> dict:
    """Get PageSpeed scores for a URL.

    Args:
        url: Full URL to test
        strategy: 'mobile' or 'desktop'

    Returns:
        {score, fcp_ms, lcp_ms, cls, tbt_ms, si_ms}
    """
    cache_key = f"{url}|{strategy}"
    cached = _cache.get(cache_key)
    if cached and time.time() - cached["time"] < CACHE_TTL:
        return cached["data"]

    try:
        async with httpx.AsyncClient(timeout=45.0) as client:
            resp = await client.get(
                API_URL,
                params={
                    "url": url,
                    "strategy": strategy,
                    "category": "performance",
                },
            )

        if resp.status_code != 200:
            return _fallback_scores(strategy)

        data = resp.json()
        lighthouse = data.get("lighthouseResult", {})
        categories = lighthouse.get("categories", {})
        audits = lighthouse.get("audits", {})

        result = {
            "score": int((categories.get("performance", {}).get("score", 0)) * 100),
            "fcp_ms": _get_metric(audits, "first-contentful-paint"),
            "lcp_ms": _get_metric(audits, "largest-contentful-paint"),
            "cls": _get_metric(audits, "cumulative-layout-shift", precision=3),
            "tbt_ms": _get_metric(audits, "total-blocking-time"),
            "si_ms": _get_metric(audits, "speed-index"),
            "strategy": strategy,
            "url": url,
            "fetched_at": time.time(),
        }

        _cache[cache_key] = {"data": result, "time": time.time()}
        return result

    except Exception:
        return _fallback_scores(strategy)


async def get_all_scores(url: str) -> dict:
    """Get both mobile and desktop scores."""
    mobile = await get_scores(url, "mobile")
    desktop = await get_scores(url, "desktop")
    return {"mobile": mobile, "desktop": desktop}


def _get_metric(audits: dict, key: str, precision: int = 0) -> float:
    """Extract a numeric metric from Lighthouse audits."""
    audit = audits.get(key, {})
    value = audit.get("numericValue", 0)
    if precision > 0:
        return round(value, precision)
    return int(value)


def _fallback_scores(strategy: str) -> dict:
    """Return demo scores when API is unavailable."""
    return {
        "score": 92 if strategy == "desktop" else 78,
        "fcp_ms": 1200 if strategy == "desktop" else 2100,
        "lcp_ms": 1800 if strategy == "desktop" else 3200,
        "cls": 0.05,
        "tbt_ms": 150 if strategy == "desktop" else 350,
        "si_ms": 1600 if strategy == "desktop" else 2800,
        "strategy": strategy,
        "url": "demo",
        "fetched_at": time.time(),
        "demo": True,
    }
