"""
Configuration for the US Construction Marketing Review Management System.

Platform API configs, company registry with brand voice, sentiment thresholds,
review solicitation cadence, and AI model settings.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Platform API configurations
# ---------------------------------------------------------------------------

PLATFORM_CONFIGS: Dict[str, dict] = {
    "google": {
        "name": "Google Business Profile",
        "api_base": "https://mybusiness.googleapis.com/v4",
        "auth_type": "oauth2",
        "scopes": ["https://www.googleapis.com/auth/business.manage"],
        "rate_limit_per_minute": 60,
        "review_endpoint": "/accounts/{account_id}/locations/{location_id}/reviews",
        "reply_endpoint": "/accounts/{account_id}/locations/{location_id}/reviews/{review_id}/reply",
        "enabled": True,
    },
    "facebook": {
        "name": "Facebook / Meta",
        "api_base": "https://graph.facebook.com/v18.0",
        "auth_type": "oauth2",
        "scopes": ["pages_read_engagement", "pages_manage_metadata"],
        "rate_limit_per_minute": 200,
        "review_endpoint": "/{page_id}/ratings",
        "reply_endpoint": "/{review_id}/comments",
        "enabled": True,
    },
    "yelp": {
        "name": "Yelp",
        "api_base": "https://api.yelp.com/v3",
        "auth_type": "api_key",
        "scopes": [],
        "rate_limit_per_minute": 500,
        "review_endpoint": "/businesses/{business_id}/reviews",
        "reply_endpoint": None,  # Yelp does not support programmatic replies
        "enabled": True,
    },
    "buildingconnected": {
        "name": "BuildingConnected",
        "api_base": "https://api.buildingconnected.com/v1",
        "auth_type": "api_key",
        "scopes": [],
        "rate_limit_per_minute": 100,
        "review_endpoint": "/contractors/{contractor_id}/reviews",
        "reply_endpoint": "/contractors/{contractor_id}/reviews/{review_id}/reply",
        "enabled": False,  # Mocked - no public review API exists yet
    },
}


# ---------------------------------------------------------------------------
# Company registry with brand voice keywords
# ---------------------------------------------------------------------------

@dataclass
class CompanyProfile:
    """Profile for a single company within the US Construction family."""

    slug: str
    name: str
    full_name: str
    status: str  # "active" | "coming_soon"
    services: List[str]
    brand_voice_keywords: List[str]
    google_place_id: Optional[str] = None
    facebook_page_id: Optional[str] = None
    yelp_business_id: Optional[str] = None
    buildingconnected_id: Optional[str] = None
    review_request_sender_email: str = ""
    review_request_sender_name: str = ""
    tagline: str = ""
    website: str = ""
    phone: str = ""


COMPANIES: Dict[str, CompanyProfile] = {
    "us_framing": CompanyProfile(
        slug="us_framing",
        name="US Framing",
        full_name="US Framing LLC",
        status="active",
        services=["wood framing", "metal framing", "structural framing", "rough carpentry"],
        brand_voice_keywords=[
            "precision", "structural integrity", "on-schedule",
            "expert craftsmanship", "safety-first", "reliable",
            "built right", "load-bearing", "code-compliant",
        ],
        tagline="Building the Backbone of Every Structure",
        website="https://usframing.com",
        phone="(555) 100-2001",
        review_request_sender_email="reviews@usframing.com",
        review_request_sender_name="The US Framing Team",
    ),
    "us_drywall": CompanyProfile(
        slug="us_drywall",
        name="US Drywall",
        full_name="US Drywall LLC",
        status="active",
        services=["drywall installation", "drywall finishing", "taping", "texture", "soundproofing"],
        brand_voice_keywords=[
            "flawless finish", "smooth walls", "attention to detail",
            "dust-controlled", "clean worksite", "premium materials",
            "level-5 finish", "seamless", "professional",
        ],
        tagline="Flawless Finishes, Every Surface",
        website="https://usdrywall.com",
        phone="(555) 100-2002",
        review_request_sender_email="reviews@usdrywall.com",
        review_request_sender_name="The US Drywall Team",
    ),
    "us_exteriors": CompanyProfile(
        slug="us_exteriors",
        name="US Exteriors",
        full_name="US Exteriors LLC",
        status="active",
        services=["siding", "stucco", "exterior trim", "waterproofing", "facade renovation"],
        brand_voice_keywords=[
            "curb appeal", "weather-resistant", "durable",
            "energy-efficient", "exterior transformation", "protective",
            "weatherproof", "beautiful exteriors", "lasting beauty",
        ],
        tagline="Transforming Exteriors, Protecting Investments",
        website="https://usexteriors.com",
        phone="(555) 100-2003",
        review_request_sender_email="reviews@usexteriors.com",
        review_request_sender_name="The US Exteriors Team",
    ),
    "us_development": CompanyProfile(
        slug="us_development",
        name="US Development",
        full_name="US Development LLC",
        status="active",
        services=["general contracting", "project management", "commercial development", "tenant improvement"],
        brand_voice_keywords=[
            "turnkey solutions", "on-time delivery", "budget-conscious",
            "project leadership", "full-service", "transparent communication",
            "milestone-driven", "partnership", "results-oriented",
        ],
        tagline="From Blueprint to Reality",
        website="https://usdevelopment.com",
        phone="(555) 100-2004",
        review_request_sender_email="reviews@usdevelopment.com",
        review_request_sender_name="The US Development Team",
    ),
    "us_interiors": CompanyProfile(
        slug="us_interiors",
        name="US Interiors",
        full_name="US Interiors LLC",
        status="coming_soon",
        services=["interior finishing", "trim carpentry", "cabinetry", "millwork", "paint"],
        brand_voice_keywords=[
            "refined interiors", "custom craftsmanship", "elegant finish",
            "design-forward", "meticulous detail", "premium quality",
            "bespoke", "luxury finishes", "artisan",
        ],
        tagline="Crafting Interiors That Inspire",
        website="https://usinteriors.com",
        phone="(555) 100-2005",
        review_request_sender_email="reviews@usinteriors.com",
        review_request_sender_name="The US Interiors Team",
    ),
}


def get_active_companies() -> Dict[str, CompanyProfile]:
    """Return only companies with status 'active'."""
    return {k: v for k, v in COMPANIES.items() if v.status == "active"}


def get_company(slug: str) -> CompanyProfile:
    """Return a company by slug. Raises KeyError if not found."""
    if slug not in COMPANIES:
        raise KeyError(
            f"Unknown company '{slug}'. Valid slugs: {list(COMPANIES.keys())}"
        )
    return COMPANIES[slug]


# ---------------------------------------------------------------------------
# Sentiment thresholds
# ---------------------------------------------------------------------------

SENTIMENT_POSITIVE_THRESHOLD: float = 0.3
SENTIMENT_NEGATIVE_THRESHOLD: float = -0.3
# Neutral sits in the range (-0.3, 0.3) inclusive of boundaries handled elsewhere


# ---------------------------------------------------------------------------
# Review solicitation cadence (days after project completion)
# ---------------------------------------------------------------------------

SOLICITATION_CADENCE_DAYS: List[int] = [0, 3, 7, 14]

SOLICITATION_SUBJECTS: Dict[int, str] = {
    0: "Thank you for choosing {company_name}!",
    3: "Quick favor? Share your experience with {company_name}",
    7: "Your feedback matters to {company_name}",
    14: "Last chance to share your {company_name} experience",
}


# ---------------------------------------------------------------------------
# AI model configuration (Claude Sonnet for response generation)
# ---------------------------------------------------------------------------

AI_MODEL_CONFIG = {
    "model": "claude-sonnet-4-20250514",
    "max_tokens": 1024,
    "temperature": 0.7,
    "system_prompt": (
        "You are a professional review response writer for a family of US-based "
        "construction companies. Write genuine, warm, and professional responses "
        "to customer reviews. Match the brand voice of the specific company. "
        "Never be defensive. Always thank the reviewer. If the review mentions "
        "specific work, reference it. Keep responses concise (2-4 sentences for "
        "positive, 3-5 sentences for negative with resolution offer)."
    ),
}


# ---------------------------------------------------------------------------
# Data storage paths (JSON-based for demo / lightweight usage)
# ---------------------------------------------------------------------------

DATA_DIR = "data"
REVIEWS_FILE = f"{DATA_DIR}/reviews.json"
RESPONSES_FILE = f"{DATA_DIR}/responses.json"
SOLICITATIONS_FILE = f"{DATA_DIR}/solicitations.json"
TIMESTAMPS_FILE = f"{DATA_DIR}/timestamps.json"
TESTIMONIALS_FILE = f"{DATA_DIR}/testimonials.json"
SENTIMENT_FILE = f"{DATA_DIR}/sentiment_results.json"


# ---------------------------------------------------------------------------
# Logging
# ---------------------------------------------------------------------------

LOG_LEVEL = "INFO"
LOG_FORMAT = "%(asctime)s | %(name)s | %(levelname)s | %(message)s"
