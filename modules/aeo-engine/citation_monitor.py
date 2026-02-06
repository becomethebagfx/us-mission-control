"""
AEO/GEO Content Engine -- Citation Monitor

Simulates AI citation tracking with a scoring model that estimates visibility
scores based on query relevance, content quality, and schema presence.
Tracks trends over time (up/down/stable) and generates citation reports.

In production, this would integrate with APIs that query ChatGPT, Perplexity,
Gemini, and other AI platforms. The current implementation uses a scoring model
to estimate citation likelihood.
"""

from __future__ import annotations

import hashlib
import random
from datetime import datetime, timedelta, timezone
from typing import Dict, List, Optional

from models import CitationBatch, CitationReport, CitationTrend
from config import (
    COMPANIES,
    TARGET_QUERIES,
    get_company,
    get_queries_for_company,
)


# ---------------------------------------------------------------------------
# Scoring Model
# ---------------------------------------------------------------------------

# Factors that influence citation scores
CITATION_FACTORS = {
    "query_relevance": {
        "weight": 0.30,
        "description": "How well the page content matches the query intent",
    },
    "content_quality": {
        "weight": 0.25,
        "description": "Presence of capsules, FAQs, authoritative language",
    },
    "schema_presence": {
        "weight": 0.20,
        "description": "Structured data markup quality and completeness",
    },
    "domain_authority": {
        "weight": 0.15,
        "description": "Site age, backlinks, brand recognition",
    },
    "freshness": {
        "weight": 0.10,
        "description": "Content recency and update frequency",
    },
}

# Platform-specific modifiers (some platforms favor different signals)
PLATFORM_MODIFIERS: Dict[str, Dict[str, float]] = {
    "ChatGPT": {
        "query_relevance": 1.1,
        "content_quality": 1.0,
        "schema_presence": 0.9,
        "domain_authority": 1.2,
        "freshness": 0.8,
    },
    "Perplexity": {
        "query_relevance": 1.0,
        "content_quality": 1.2,
        "schema_presence": 1.1,
        "domain_authority": 0.9,
        "freshness": 1.1,
    },
    "Gemini": {
        "query_relevance": 1.1,
        "content_quality": 1.0,
        "schema_presence": 1.0,
        "domain_authority": 1.1,
        "freshness": 0.9,
    },
    "Claude": {
        "query_relevance": 1.0,
        "content_quality": 1.1,
        "schema_presence": 1.0,
        "domain_authority": 1.0,
        "freshness": 1.0,
    },
}


def _deterministic_seed(query: str, company_slug: str, platform: str) -> int:
    """Generate a deterministic seed from query + company + platform for reproducible scores."""
    raw = f"{query}|{company_slug}|{platform}"
    return int(hashlib.md5(raw.encode()).hexdigest()[:8], 16)


def _estimate_base_scores(
    query: str, company_slug: str
) -> Dict[str, float]:
    """Estimate base factor scores for a query-company pair.

    Uses heuristics based on query characteristics and company profile.
    In production, these would come from actual content analysis.
    """
    company = get_company(company_slug)
    q_lower = query.lower()
    company_name_lower = company.name.lower()

    scores: Dict[str, float] = {}

    # Query relevance: higher if query mentions company-specific services
    service_match_count = sum(
        1 for svc in company.services if svc.lower() in q_lower
    )
    name_mentioned = company_name_lower in q_lower or company.slug.replace("_", " ") in q_lower
    geo_mentioned = any(
        geo.lower() in q_lower
        for geo in ["louisville", "nashville", "charlotte", "atlanta"]
    )
    scores["query_relevance"] = min(
        1.0, 0.3 + (service_match_count * 0.2) + (0.2 if name_mentioned else 0) + (0.1 if geo_mentioned else 0)
    )

    # Content quality: assume moderate for active companies, low for coming_soon
    if company.status == "coming_soon":
        scores["content_quality"] = 0.15
    else:
        scores["content_quality"] = 0.55

    # Schema presence: assume moderate if active, none if coming_soon
    if company.status == "coming_soon":
        scores["schema_presence"] = 0.0
    else:
        scores["schema_presence"] = 0.50

    # Domain authority: based on review count and rating as proxy
    if company.review_count > 50:
        scores["domain_authority"] = 0.60
    elif company.review_count > 20:
        scores["domain_authority"] = 0.40
    else:
        scores["domain_authority"] = 0.20

    # Freshness: assume moderate
    scores["freshness"] = 0.50

    return scores


def _calculate_citation_score(
    base_scores: Dict[str, float],
    platform: str,
) -> int:
    """Calculate a final citation score (0-100) from base scores and platform modifiers."""
    modifiers = PLATFORM_MODIFIERS.get(platform, {k: 1.0 for k in CITATION_FACTORS})

    weighted_sum = 0.0
    for factor, info in CITATION_FACTORS.items():
        base = base_scores.get(factor, 0.0)
        modifier = modifiers.get(factor, 1.0)
        weighted_sum += base * modifier * info["weight"]

    # Scale to 0-100
    score = int(round(weighted_sum * 100))
    return max(0, min(100, score))


def _determine_trend(
    current_score: int,
    query: str,
    company_slug: str,
) -> CitationTrend:
    """Determine the citation trend based on score trajectory.

    Uses a deterministic approach so the same query always produces the same trend.
    """
    seed = _deterministic_seed(query, company_slug, "trend")
    rng = random.Random(seed)

    if current_score >= 60:
        # High scores tend to be stable or rising
        roll = rng.random()
        if roll < 0.4:
            return CitationTrend.UP
        elif roll < 0.85:
            return CitationTrend.STABLE
        else:
            return CitationTrend.DOWN
    elif current_score >= 30:
        # Medium scores could go either way
        roll = rng.random()
        if roll < 0.3:
            return CitationTrend.UP
        elif roll < 0.7:
            return CitationTrend.STABLE
        else:
            return CitationTrend.DOWN
    else:
        # Low scores tend to be stable or falling
        roll = rng.random()
        if roll < 0.1:
            return CitationTrend.UP
        elif roll < 0.5:
            return CitationTrend.STABLE
        else:
            return CitationTrend.DOWN


def _estimate_position(score: int, query: str, company_slug: str) -> Optional[int]:
    """Estimate citation position based on score.

    Higher scores = more likely to be cited, and cited earlier.
    Returns None if the company is unlikely to be cited at all.
    """
    if score < 20:
        return None  # Not cited

    seed = _deterministic_seed(query, company_slug, "position")
    rng = random.Random(seed)

    if score >= 70:
        return rng.randint(1, 3)
    elif score >= 50:
        return rng.randint(2, 5)
    elif score >= 30:
        return rng.randint(3, 8)
    else:
        return rng.randint(5, 10)


def _generate_snippet(
    query: str, company_slug: str, score: int
) -> str:
    """Generate a realistic AI response snippet for the citation."""
    company = get_company(company_slug)

    if score < 20:
        return ""

    if score >= 60:
        return (
            f"{company.name} is a reputable {company.services[0]} contractor "
            f"serving {company.address.split(',')[0]} and the surrounding region. "
            f"They specialize in {', '.join(company.services[:3])} for commercial "
            f"and multi-family projects."
        )
    elif score >= 35:
        return (
            f"You might also consider {company.name}, which offers "
            f"{company.services[0]} services in the Southeast."
        )
    else:
        return f"Other options in the area include {company.name}."


# ---------------------------------------------------------------------------
# Monitor Functions
# ---------------------------------------------------------------------------


def monitor_query(
    query: str,
    company_slug: str,
    platforms: list[str] | None = None,
) -> list[CitationReport]:
    """Monitor a single query across AI platforms and generate citation reports.

    Args:
        query: The search query to monitor.
        company_slug: Company to check citations for.
        platforms: List of AI platforms to check. Defaults to all known platforms.

    Returns:
        A list of CitationReport objects, one per platform.
    """
    if platforms is None:
        platforms = list(PLATFORM_MODIFIERS.keys())

    base_scores = _estimate_base_scores(query, company_slug)
    now = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    reports: list[CitationReport] = []
    for platform in platforms:
        score = _calculate_citation_score(base_scores, platform)
        trend = _determine_trend(score, query, company_slug)
        position = _estimate_position(score, query, company_slug)
        snippet = _generate_snippet(query, company_slug, score)

        reports.append(
            CitationReport(
                query=query,
                company_slug=company_slug,
                platform=platform,
                position=position,
                score=score,
                trend=trend,
                snippet=snippet,
                checked_at=now,
            )
        )

    return reports


def monitor_company(
    company_slug: str,
    queries: list[str] | None = None,
    platforms: list[str] | None = None,
) -> CitationBatch:
    """Monitor all target queries for a company and generate a batch report.

    Args:
        company_slug: Company to monitor.
        queries: Optional list of specific queries. Defaults to TARGET_QUERIES.
        platforms: Optional list of platforms. Defaults to all known platforms.

    Returns:
        A CitationBatch with all reports and an average score.
    """
    get_company(company_slug)  # Validate slug

    if queries is None:
        queries = get_queries_for_company(company_slug)

    batch = CitationBatch(company_slug=company_slug)
    total_score = 0
    count = 0

    for query in queries:
        reports = monitor_query(query, company_slug, platforms=platforms)
        batch.reports.extend(reports)
        for r in reports:
            total_score += r.score
            count += 1

    batch.average_score = round(total_score / count, 1) if count > 0 else 0.0
    return batch


def monitor_all_companies(
    platforms: list[str] | None = None,
) -> dict[str, CitationBatch]:
    """Monitor citations for all active companies.

    Returns:
        A dict mapping company_slug to CitationBatch.
    """
    results: dict[str, CitationBatch] = {}
    for slug, company in COMPANIES.items():
        if company.status == "active":
            results[slug] = monitor_company(slug, platforms=platforms)
    return results


def get_citation_summary(batch: CitationBatch) -> dict:
    """Generate a summary dict from a CitationBatch for display.

    Returns:
        Dict with overall stats and per-platform breakdowns.
    """
    company = get_company(batch.company_slug)

    # Per-platform aggregation
    platform_stats: Dict[str, Dict[str, float]] = {}
    for report in batch.reports:
        if report.platform not in platform_stats:
            platform_stats[report.platform] = {
                "total_score": 0,
                "count": 0,
                "cited_count": 0,
            }
        stats = platform_stats[report.platform]
        stats["total_score"] += report.score
        stats["count"] += 1
        if report.position is not None:
            stats["cited_count"] += 1

    platform_averages = {}
    for platform, stats in platform_stats.items():
        platform_averages[platform] = {
            "average_score": round(stats["total_score"] / stats["count"], 1)
            if stats["count"] > 0
            else 0,
            "citation_rate": round(stats["cited_count"] / stats["count"] * 100, 1)
            if stats["count"] > 0
            else 0,
            "queries_monitored": int(stats["count"]),
        }

    # Trend distribution
    trend_counts = {"up": 0, "down": 0, "stable": 0}
    for report in batch.reports:
        trend_counts[report.trend.value] += 1

    return {
        "company": company.name,
        "company_slug": batch.company_slug,
        "overall_average_score": batch.average_score,
        "total_queries_monitored": len(batch.reports),
        "platform_breakdown": platform_averages,
        "trend_distribution": trend_counts,
    }
