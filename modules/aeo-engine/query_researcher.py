"""
AEO/GEO Content Engine -- Query Researcher

Discovers and ranks questions by search intent using Claude AI.
Categorizes queries as informational, transactional, or navigational,
cross-references against existing target queries, and returns a
prioritized list per company/service.
"""

from __future__ import annotations

import json
import os
from typing import List, Optional

from models import QueryIntent, TargetQuery
from config import (
    CLAUDE_MAX_TOKENS,
    CLAUDE_MODEL,
    CLAUDE_TEMPERATURE,
    COMPANIES,
    GEOGRAPHIC_MODIFIERS,
    PRIMARY_MARKETS,
    QUERY_INTENT_CATEGORIES,
    TARGET_QUERIES,
    get_company,
    get_queries_for_company,
)


# ---------------------------------------------------------------------------
# Demo data (used when --demo flag is set or no API key)
# ---------------------------------------------------------------------------
DEMO_QUERIES: dict[str, list[dict]] = {
    "us_framing": [
        {
            "query": "how long does it take to frame a multi-family building",
            "intent": "informational",
            "priority": 8,
            "service": "multi-family framing",
        },
        {
            "query": "best framing contractor for 5-over-1 construction Louisville KY",
            "intent": "transactional",
            "priority": 9,
            "service": "multi-family framing",
        },
        {
            "query": "wood framing vs light gauge steel for apartments",
            "intent": "informational",
            "priority": 7,
            "service": "wood framing",
        },
        {
            "query": "framing contractor insurance requirements commercial",
            "intent": "informational",
            "priority": 5,
            "service": "commercial framing",
        },
        {
            "query": "panelized wall framing supplier Southeast US",
            "intent": "transactional",
            "priority": 6,
            "service": "panelized framing",
        },
    ],
    "us_drywall": [
        {
            "query": "what is Level 5 drywall finish and when do you need it",
            "intent": "informational",
            "priority": 8,
            "service": "drywall finishing",
        },
        {
            "query": "commercial drywall contractor for hospital construction",
            "intent": "transactional",
            "priority": 7,
            "service": "drywall installation",
        },
        {
            "query": "acoustical ceiling tile installation cost per square foot",
            "intent": "informational",
            "priority": 8,
            "service": "acoustical ceilings",
        },
        {
            "query": "fire-rated wall assembly drywall specifications",
            "intent": "informational",
            "priority": 6,
            "service": "fire-rated assemblies",
        },
        {
            "query": "best acoustical ceiling contractor Nashville TN",
            "intent": "transactional",
            "priority": 9,
            "service": "acoustical ceilings",
        },
    ],
    "us_exteriors": [
        {
            "query": "EIFS vs stucco which is better for commercial buildings",
            "intent": "informational",
            "priority": 8,
            "service": "EIFS installation",
        },
        {
            "query": "commercial waterproofing contractor below grade",
            "intent": "transactional",
            "priority": 7,
            "service": "waterproofing",
        },
        {
            "query": "rainscreen cladding system benefits for multi-family",
            "intent": "informational",
            "priority": 7,
            "service": "rainscreen systems",
        },
        {
            "query": "building envelope consultant vs contractor difference",
            "intent": "informational",
            "priority": 5,
            "service": "building envelope",
        },
        {
            "query": "best EIFS installer for apartment buildings Charlotte NC",
            "intent": "transactional",
            "priority": 9,
            "service": "EIFS installation",
        },
    ],
    "us_development": [
        {
            "query": "construction management vs general contracting which to choose",
            "intent": "informational",
            "priority": 8,
            "service": "construction management",
        },
        {
            "query": "design build contractor multi-family Louisville KY",
            "intent": "transactional",
            "priority": 9,
            "service": "design-build",
        },
        {
            "query": "pre-construction services what is included",
            "intent": "informational",
            "priority": 7,
            "service": "pre-construction services",
        },
        {
            "query": "value engineering saves how much on construction projects",
            "intent": "informational",
            "priority": 6,
            "service": "value engineering",
        },
        {
            "query": "top general contractor for apartment complex Atlanta GA",
            "intent": "transactional",
            "priority": 9,
            "service": "general contracting",
        },
    ],
    "us_interiors": [
        {
            "query": "interior finishing timeline for multi-family construction",
            "intent": "informational",
            "priority": 7,
            "service": "interior finishing",
        },
        {
            "query": "commercial millwork installation contractor near me",
            "intent": "transactional",
            "priority": 8,
            "service": "millwork installation",
        },
        {
            "query": "what does punch-out mean in construction",
            "intent": "informational",
            "priority": 6,
            "service": "punch-out services",
        },
    ],
}


def _classify_intent(query: str) -> QueryIntent:
    """Heuristic intent classification for a query string."""
    q_lower = query.lower()
    transactional_signals = [
        "best",
        "top",
        "cost",
        "price",
        "near me",
        "contractor",
        "company",
        "hire",
        "install",
        "supplier",
    ]
    informational_signals = [
        "how",
        "what",
        "why",
        "when",
        "which",
        "difference",
        "vs",
        "explained",
        "guide",
        "benefits",
        "requirements",
        "specifications",
    ]
    if any(signal in q_lower for signal in transactional_signals):
        return QueryIntent.TRANSACTIONAL
    if any(signal in q_lower for signal in informational_signals):
        return QueryIntent.INFORMATIONAL
    return QueryIntent.INFORMATIONAL


def _deduplicate(
    new_queries: list[dict], existing_queries: list[str]
) -> list[dict]:
    """Remove queries that already exist in the target query list."""
    existing_lower = {q.lower().strip() for q in existing_queries}
    return [q for q in new_queries if q["query"].lower().strip() not in existing_lower]


def research_queries_demo(company_slug: str) -> list[TargetQuery]:
    """Return pre-built demo queries for a company.

    Used when --demo flag is set or when no API key is available.
    """
    company = get_company(company_slug)
    raw = DEMO_QUERIES.get(company_slug, [])
    existing = get_queries_for_company(company_slug)
    deduped = _deduplicate(raw, existing)

    results: list[TargetQuery] = []
    for item in deduped:
        results.append(
            TargetQuery(
                query=item["query"],
                company_slug=company_slug,
                service=item.get("service", ""),
                intent=QueryIntent(item.get("intent", "informational")),
                priority=item.get("priority", 5),
            )
        )
    return results


def research_queries_ai(
    company_slug: str,
    max_queries: int = 20,
) -> list[TargetQuery]:
    """Use Claude AI to discover and rank new target queries for a company.

    Requires ANTHROPIC_API_KEY environment variable.
    """
    import anthropic

    company = get_company(company_slug)
    existing = get_queries_for_company(company_slug)

    prompt = f"""You are an SEO and AEO (Answer Engine Optimization) specialist for the construction industry.

Company: {company.name}
Services: {', '.join(company.services)}
Description: {company.description}
Primary Markets: {', '.join(PRIMARY_MARKETS)}

Existing target queries (DO NOT duplicate these):
{json.dumps(existing, indent=2)}

Intent categories:
{json.dumps(QUERY_INTENT_CATEGORIES, indent=2)}

Task: Generate {max_queries} NEW target queries that potential customers would ask AI assistants
(ChatGPT, Perplexity, Gemini, Claude) about these services. Focus on queries where a
well-optimized page could earn an AI citation.

For each query provide:
- query: the exact search/question text
- intent: informational, transactional, or navigational
- priority: 1-10 (10 = highest business value)
- service: which company service this relates to

Return ONLY a JSON array of objects with these four fields. No explanation.
"""

    client = anthropic.Anthropic()
    response = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=CLAUDE_MAX_TOKENS,
        temperature=CLAUDE_TEMPERATURE,
        messages=[{"role": "user", "content": prompt}],
    )

    raw_text = response.content[0].text.strip()
    # Strip markdown code fences if present
    if raw_text.startswith("```"):
        raw_text = raw_text.split("\n", 1)[1]
        if raw_text.endswith("```"):
            raw_text = raw_text[: raw_text.rfind("```")]

    raw_queries = json.loads(raw_text)
    deduped = _deduplicate(raw_queries, existing)

    results: list[TargetQuery] = []
    for item in deduped:
        intent_str = item.get("intent", "informational").lower()
        try:
            intent = QueryIntent(intent_str)
        except ValueError:
            intent = QueryIntent.INFORMATIONAL

        results.append(
            TargetQuery(
                query=item["query"],
                company_slug=company_slug,
                service=item.get("service", ""),
                intent=intent,
                priority=min(max(int(item.get("priority", 5)), 1), 10),
            )
        )

    # Sort by priority descending
    results.sort(key=lambda q: q.priority, reverse=True)
    return results


def research_queries(
    company_slug: str,
    demo: bool = False,
    max_queries: int = 20,
) -> list[TargetQuery]:
    """Main entry point: discover and rank target queries for a company.

    Args:
        company_slug: Which company to research queries for.
        demo: If True, return pre-built demo data instead of calling AI.
        max_queries: Maximum number of new queries to generate (AI mode only).

    Returns:
        A list of TargetQuery objects sorted by priority (highest first).
    """
    if demo or not os.environ.get("ANTHROPIC_API_KEY"):
        return research_queries_demo(company_slug)
    return research_queries_ai(company_slug, max_queries=max_queries)
