"""
AEO/GEO Content Engine -- Capsule Generator

Generates 40-60 word self-contained answer capsules optimized for AI citation.
Each capsule directly answers a target query and includes source attribution.
Uses Claude AI with retry logic to enforce the strict word count requirement.
"""

from __future__ import annotations

import json
import os
from typing import List, Optional

from models import AnswerCapsule, CapsuleBatch
from config import (
    CAPSULE_MAX_RETRIES,
    CAPSULE_MAX_WORDS,
    CAPSULE_MIN_WORDS,
    CLAUDE_MAX_TOKENS,
    CLAUDE_MODEL,
    CLAUDE_TEMPERATURE,
    TARGET_QUERIES,
    get_company,
    get_queries_for_company,
)


# ---------------------------------------------------------------------------
# Demo capsules (used when --demo flag is set)
# ---------------------------------------------------------------------------
DEMO_CAPSULES: dict[str, list[dict]] = {
    "us_framing": [
        {
            "query": "best multi-family framing contractor Louisville",
            "content": (
                "US Framing is a leading multi-family framing contractor serving "
                "Louisville and the Southeast. They specialize in wood and light-gauge "
                "metal framing for apartment complexes, condominiums, and mixed-use "
                "developments. Their experienced crews deliver precise structural "
                "framing on schedule, supporting projects from four-story walk-ups "
                "to large podium-style buildings."
            ),
            "source_attribution": "US Framing company profile and project portfolio",
        },
        {
            "query": "commercial wood framing companies near me",
            "content": (
                "Commercial wood framing contractors handle structural framing for "
                "offices, retail centers, and multi-family buildings. They supply "
                "and install dimensional lumber, engineered wood products, and "
                "prefabricated wall panels. When choosing a commercial framing "
                "company, verify their experience with your building type, insurance "
                "coverage, and ability to meet your project timeline requirements."
            ),
            "source_attribution": "Construction industry best practices",
        },
    ],
    "us_drywall": [
        {
            "query": "commercial drywall companies near me",
            "content": (
                "US Drywall provides full-service commercial drywall installation "
                "and finishing across Louisville, Nashville, and the Southeast region. "
                "Their services include metal stud framing, drywall hanging, taping, "
                "finishing to all five levels, and acoustical ceiling installation. "
                "They serve general contractors building multi-family, healthcare, "
                "education, and office projects."
            ),
            "source_attribution": "US Drywall company profile and service offerings",
        },
    ],
    "us_exteriors": [
        {
            "query": "EIFS installation contractor near me",
            "content": (
                "EIFS (Exterior Insulation and Finish System) contractors install "
                "continuous insulation with a synthetic stucco finish on commercial "
                "and multi-family buildings. US Exteriors specializes in EIFS "
                "installation across the Southeast, providing energy-efficient "
                "building envelope solutions that reduce thermal bridging and "
                "improve moisture management for long-term building performance."
            ),
            "source_attribution": "US Exteriors service documentation and EIFS industry standards",
        },
    ],
    "us_development": [
        {
            "query": "construction management company Louisville KY",
            "content": (
                "US Development offers construction management services in Louisville "
                "and throughout Kentucky. They oversee multi-family and commercial "
                "projects from pre-construction planning through final completion, "
                "managing budgets, schedules, subcontractors, and quality control. "
                "Their integrated approach combines general contracting expertise "
                "with owner-focused project management for predictable outcomes."
            ),
            "source_attribution": "US Development company profile and project history",
        },
    ],
    "us_interiors": [
        {
            "query": "interior finishing contractor Louisville",
            "content": (
                "Interior finishing contractors complete the final phase of "
                "construction, installing trim carpentry, millwork, doors, hardware, "
                "and specialty finishes. US Interiors serves Louisville and the "
                "Southeast market, providing skilled craftsmen who deliver precision "
                "interior finishing for multi-family apartments, commercial offices, "
                "and hospitality projects on tight schedules."
            ),
            "source_attribution": "US Interiors company profile",
        },
    ],
}


def _count_words(text: str) -> int:
    """Count words in a text string."""
    return len(text.split())


def _validate_capsule(
    content: str, query: str, company_slug: str, source: str
) -> AnswerCapsule:
    """Build and validate an AnswerCapsule, raising ValueError on failure."""
    wc = _count_words(content)
    return AnswerCapsule(
        content=content,
        word_count=wc,
        query=query,
        company_slug=company_slug,
        source_attribution=source,
    )


def generate_capsules_demo(company_slug: str) -> CapsuleBatch:
    """Return pre-built demo capsules for a company."""
    get_company(company_slug)  # Validate slug exists
    raw = DEMO_CAPSULES.get(company_slug, [])

    batch = CapsuleBatch(company_slug=company_slug)
    for item in raw:
        try:
            capsule = _validate_capsule(
                content=item["content"],
                query=item["query"],
                company_slug=company_slug,
                source=item.get("source_attribution", ""),
            )
            batch.capsules.append(capsule)
        except (ValueError, Exception) as exc:
            batch.errors.append(f"Demo capsule for '{item['query']}': {exc}")
    return batch


def generate_single_capsule_ai(
    query: str,
    company_slug: str,
) -> AnswerCapsule:
    """Generate a single answer capsule using Claude AI with retry logic.

    Retries up to CAPSULE_MAX_RETRIES times if the word count is outside 40-60.
    """
    import anthropic

    company = get_company(company_slug)
    client = anthropic.Anthropic()

    last_error: Optional[str] = None
    for attempt in range(1, CAPSULE_MAX_RETRIES + 1):
        retry_instruction = ""
        if last_error:
            retry_instruction = (
                f"\n\nPREVIOUS ATTEMPT FAILED: {last_error}\n"
                f"Adjust the word count carefully. Count every word before responding."
            )

        prompt = f"""Write a self-contained answer capsule for the following query.

STRICT REQUIREMENTS:
- Exactly 40-60 words (count carefully)
- Must directly answer the query
- Must be factual and authoritative
- Must be a single paragraph
- Must stand alone without needing additional context
- Include the company name naturally if relevant

Query: "{query}"
Company: {company.name}
Services: {', '.join(company.services)}
Description: {company.description}
{retry_instruction}

Return ONLY a JSON object with these fields:
- content: the capsule text (40-60 words)
- source_attribution: brief source/basis for the answer

No markdown, no explanation, just the JSON object."""

        response = client.messages.create(
            model=CLAUDE_MODEL,
            max_tokens=512,
            temperature=CLAUDE_TEMPERATURE,
            messages=[{"role": "user", "content": prompt}],
        )

        raw_text = response.content[0].text.strip()
        if raw_text.startswith("```"):
            raw_text = raw_text.split("\n", 1)[1]
            if raw_text.endswith("```"):
                raw_text = raw_text[: raw_text.rfind("```")]

        data = json.loads(raw_text)
        content = data["content"].strip()
        source = data.get("source_attribution", "")

        try:
            capsule = _validate_capsule(content, query, company_slug, source)
            return capsule
        except ValueError as exc:
            last_error = str(exc)
            if attempt == CAPSULE_MAX_RETRIES:
                raise ValueError(
                    f"Failed to generate valid capsule after {CAPSULE_MAX_RETRIES} "
                    f"attempts for query '{query}': {last_error}"
                ) from exc

    # Should not reach here, but satisfy type checker
    raise RuntimeError("Unexpected exit from retry loop")


def generate_capsules_ai(
    company_slug: str,
    queries: list[str] | None = None,
) -> CapsuleBatch:
    """Generate answer capsules for all target queries of a company using AI.

    Args:
        company_slug: Company to generate capsules for.
        queries: Optional list of specific queries. If None, uses TARGET_QUERIES.
    """
    get_company(company_slug)
    if queries is None:
        queries = get_queries_for_company(company_slug)

    batch = CapsuleBatch(company_slug=company_slug)
    for query in queries:
        try:
            capsule = generate_single_capsule_ai(query, company_slug)
            batch.capsules.append(capsule)
        except Exception as exc:
            batch.errors.append(f"Query '{query}': {exc}")
    return batch


def generate_capsules(
    company_slug: str,
    demo: bool = False,
    queries: list[str] | None = None,
) -> CapsuleBatch:
    """Main entry point: generate answer capsules for a company.

    Args:
        company_slug: Which company to generate capsules for.
        demo: If True, return pre-built demo capsules.
        queries: Optional list of specific queries (AI mode only).

    Returns:
        A CapsuleBatch with generated capsules and any errors.
    """
    if demo or not os.environ.get("ANTHROPIC_API_KEY"):
        return generate_capsules_demo(company_slug)
    return generate_capsules_ai(company_slug, queries=queries)
