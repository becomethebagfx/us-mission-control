"""
AEO/GEO Content Engine Configuration

Company registry, target queries, geographic modifiers, scoring weights,
and AI model configuration for the US Construction Marketing family.
"""

from dataclasses import dataclass, field
from typing import Dict, List


# ---------------------------------------------------------------------------
# Claude AI Model Configuration
# ---------------------------------------------------------------------------
CLAUDE_MODEL = "claude-sonnet-4-20250514"
CLAUDE_MAX_TOKENS = 4096
CLAUDE_TEMPERATURE = 0.4  # Lower for factual, structured output


# ---------------------------------------------------------------------------
# AEO Scoring Weights (must sum to 100)
# ---------------------------------------------------------------------------
AEO_SCORING_WEIGHTS: Dict[str, int] = {
    "heading_structure": 20,
    "capsule_presence": 25,
    "schema_markup": 20,
    "bot_access": 15,
    "answer_density": 10,
    "word_count": 10,
}

assert sum(AEO_SCORING_WEIGHTS.values()) == 100, "Scoring weights must sum to 100"


# ---------------------------------------------------------------------------
# Geographic Modifiers
# ---------------------------------------------------------------------------
GEOGRAPHIC_MODIFIERS: List[str] = [
    "Louisville KY",
    "Lexington KY",
    "Nashville TN",
    "Charlotte NC",
    "Atlanta GA",
    "Cincinnati OH",
    "Indianapolis IN",
    "Columbus OH",
    "Knoxville TN",
    "Raleigh NC",
    "Greenville SC",
    "Memphis TN",
    "Birmingham AL",
    "Richmond VA",
    "Charleston SC",
]

PRIMARY_MARKETS: List[str] = [
    "Louisville KY",
    "Nashville TN",
    "Charlotte NC",
    "Atlanta GA",
]


# ---------------------------------------------------------------------------
# Company Registry
# ---------------------------------------------------------------------------
@dataclass
class CompanyInfo:
    """Registry entry for a company in the US Construction family."""

    slug: str
    name: str
    domain: str
    services: List[str]
    description: str
    phone: str
    address: str
    status: str = "active"  # active | coming_soon
    aggregate_rating: float = 4.8
    review_count: int = 50


COMPANIES: Dict[str, CompanyInfo] = {
    "us_framing": CompanyInfo(
        slug="us_framing",
        name="US Framing",
        domain="usframing.com",
        services=[
            "wood framing",
            "multi-family framing",
            "commercial framing",
            "residential framing",
            "light-gauge metal framing",
            "panelized framing",
            "floor systems",
            "roof framing",
        ],
        description="Professional wood and metal framing contractor specializing in multi-family and commercial projects across the Southeast.",
        phone="(502) 555-0101",
        address="Louisville, KY 40202",
        aggregate_rating=4.9,
        review_count=67,
    ),
    "us_drywall": CompanyInfo(
        slug="us_drywall",
        name="US Drywall",
        domain="usdrywall.com",
        services=[
            "drywall installation",
            "drywall finishing",
            "acoustical ceilings",
            "acoustical panels",
            "sound insulation",
            "fire-rated assemblies",
            "metal stud framing",
            "specialty ceilings",
        ],
        description="Full-service drywall and acoustical ceiling contractor for commercial and multi-family construction.",
        phone="(502) 555-0102",
        address="Louisville, KY 40202",
        aggregate_rating=4.8,
        review_count=54,
    ),
    "us_exteriors": CompanyInfo(
        slug="us_exteriors",
        name="US Exteriors",
        domain="usexteriors.com",
        services=[
            "commercial siding",
            "EIFS installation",
            "waterproofing",
            "exterior insulation",
            "rainscreen systems",
            "metal panel installation",
            "stucco application",
            "building envelope",
        ],
        description="Commercial exterior finishing contractor specializing in siding, EIFS, waterproofing, and building envelope solutions.",
        phone="(502) 555-0103",
        address="Louisville, KY 40202",
        aggregate_rating=4.7,
        review_count=41,
    ),
    "us_development": CompanyInfo(
        slug="us_development",
        name="US Development",
        domain="usdevelopment.com",
        services=[
            "construction management",
            "general contracting",
            "design-build",
            "pre-construction services",
            "project management",
            "value engineering",
            "multi-family development",
            "commercial development",
        ],
        description="Construction management and general contracting firm delivering multi-family and commercial projects from pre-construction through completion.",
        phone="(502) 555-0104",
        address="Louisville, KY 40202",
        aggregate_rating=4.9,
        review_count=38,
    ),
    "us_interiors": CompanyInfo(
        slug="us_interiors",
        name="US Interiors",
        domain="usinteriors.com",
        services=[
            "interior finishing",
            "trim carpentry",
            "millwork installation",
            "cabinet installation",
            "doors and hardware",
            "specialty finishes",
            "punch-out services",
            "final clean",
        ],
        description="Interior finishing contractor providing trim, millwork, and specialty finish services for commercial and multi-family projects.",
        phone="(502) 555-0105",
        address="Louisville, KY 40202",
        status="coming_soon",
        aggregate_rating=0.0,
        review_count=0,
    ),
}


# ---------------------------------------------------------------------------
# Target Queries by Company and Service
# ---------------------------------------------------------------------------
TARGET_QUERIES: Dict[str, List[str]] = {
    # -- US Framing ----------------------------------------------------------
    "us_framing": [
        "best multi-family framing contractor Louisville",
        "commercial wood framing companies near me",
        "multi-family framing contractor Southeast",
        "wood framing vs metal framing for apartments",
        "how much does commercial framing cost per square foot",
        "panelized framing contractor Louisville KY",
        "light gauge metal framing installer",
        "apartment building framing contractor Nashville",
        "residential framing company Charlotte NC",
        "who does framing for multi-family construction",
        "best framing subcontractor for general contractors",
    ],
    # -- US Drywall -----------------------------------------------------------
    "us_drywall": [
        "commercial drywall companies near me",
        "best drywall contractor for apartments Louisville",
        "acoustical ceiling installation contractor",
        "drywall finishing levels explained",
        "fire-rated drywall assembly installer",
        "commercial drywall cost per square foot",
        "acoustical panel installation Nashville TN",
        "sound insulation contractor multi-family",
        "drywall subcontractor for large projects",
        "specialty ceiling contractor Southeast",
        "metal stud and drywall contractor",
    ],
    # -- US Exteriors ---------------------------------------------------------
    "us_exteriors": [
        "commercial siding contractor Louisville KY",
        "EIFS installation contractor near me",
        "building waterproofing contractor Southeast",
        "rainscreen system installer commercial",
        "exterior insulation and finish system contractor",
        "metal panel siding installation",
        "commercial stucco contractor Nashville",
        "building envelope contractor Charlotte NC",
        "best EIFS contractor for apartments",
        "waterproofing subcontractor multi-family",
    ],
    # -- US Development -------------------------------------------------------
    "us_development": [
        "construction management company Louisville KY",
        "general contractor multi-family development",
        "design build contractor Southeast",
        "pre-construction services Louisville",
        "multi-family construction manager Nashville TN",
        "commercial general contractor Charlotte NC",
        "value engineering construction services",
        "apartment construction company Atlanta GA",
        "best general contractor for multi-family",
        "construction management firm near me",
    ],
    # -- US Interiors ---------------------------------------------------------
    "us_interiors": [
        "interior finishing contractor Louisville",
        "commercial trim carpentry contractor",
        "millwork installation company near me",
        "apartment interior finishing Nashville",
        "commercial door and hardware installer",
        "specialty interior finishes contractor",
        "punch-out contractor multi-family",
        "interior finishing subcontractor Southeast",
    ],
}


# ---------------------------------------------------------------------------
# Query Intent Categories
# ---------------------------------------------------------------------------
QUERY_INTENT_CATEGORIES: Dict[str, str] = {
    "informational": "User wants to learn or understand something (how, what, why, explained)",
    "transactional": "User wants to hire, buy, or engage a service (best, top, cost, near me, contractor)",
    "navigational": "User is looking for a specific company or website (brand name, domain)",
}


# ---------------------------------------------------------------------------
# Capsule Generation Settings
# ---------------------------------------------------------------------------
CAPSULE_MIN_WORDS = 40
CAPSULE_MAX_WORDS = 60
CAPSULE_MAX_RETRIES = 3


# ---------------------------------------------------------------------------
# FAQ Generation Settings
# ---------------------------------------------------------------------------
FAQ_MIN_PAIRS = 8
FAQ_MAX_PAIRS = 12


# ---------------------------------------------------------------------------
# Page Optimizer Settings
# ---------------------------------------------------------------------------
ALLOWED_BOTS = ["GPTBot", "PerplexityBot", "Google-Extended", "ClaudeBot", "Bingbot"]
MIN_ANSWER_DENSITY = 0.02  # Ratio of answer-like sentences to total sentences


# ---------------------------------------------------------------------------
# Citation Monitor Settings
# ---------------------------------------------------------------------------
CITATION_SCORE_RANGE = (0, 100)
CITATION_TREND_OPTIONS = ["up", "down", "stable"]


# ---------------------------------------------------------------------------
# Helper Functions
# ---------------------------------------------------------------------------
def get_company(slug: str) -> CompanyInfo:
    """Retrieve a company by slug, raising KeyError if not found."""
    if slug not in COMPANIES:
        raise KeyError(f"Unknown company slug: {slug}. Valid: {list(COMPANIES.keys())}")
    return COMPANIES[slug]


def get_active_companies() -> Dict[str, CompanyInfo]:
    """Return only companies with status 'active'."""
    return {k: v for k, v in COMPANIES.items() if v.status == "active"}


def get_all_queries() -> List[str]:
    """Flatten all target queries across all companies."""
    return [q for queries in TARGET_QUERIES.values() for q in queries]


def get_queries_for_company(slug: str) -> List[str]:
    """Return target queries for a specific company."""
    return TARGET_QUERIES.get(slug, [])


def expand_query_with_geo(query: str, markets: List[str] | None = None) -> List[str]:
    """Expand a generic query with geographic modifiers.

    If the query already contains a geographic reference, return it as-is.
    Otherwise, produce one variant per market.
    """
    markets = markets or PRIMARY_MARKETS
    # Simple heuristic: if the query already has a state abbreviation, skip expansion
    state_abbrevs = ["KY", "TN", "NC", "GA", "OH", "IN", "SC", "AL", "VA"]
    if any(f" {abbr}" in query for abbr in state_abbrevs):
        return [query]
    return [f"{query} {market}" for market in markets]
