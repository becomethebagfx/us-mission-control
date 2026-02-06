"""
GBP Automation Module - Configuration
Google Business Profile API v4.9 settings, company registry, and photo specs.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Google Business Profile API
# ---------------------------------------------------------------------------

GBP_API_VERSION = "v4.9"
GBP_BASE_URL = f"https://mybusiness.googleapis.com/{GBP_API_VERSION}"
GBP_ACCOUNTS_URL = f"{GBP_BASE_URL}/accounts"

OAUTH_SCOPES = [
    "https://www.googleapis.com/auth/business.manage",
]

RATE_LIMIT_DAILY = 500  # max API calls per day
RATE_LIMIT_PER_SECOND = 10  # burst limit

# ---------------------------------------------------------------------------
# AI Model
# ---------------------------------------------------------------------------

CLAUDE_MODEL = "claude-sonnet-4-20250514"
CLAUDE_MAX_TOKENS = 1024

# ---------------------------------------------------------------------------
# Photo Specifications
# ---------------------------------------------------------------------------

PHOTO_SPECS = {
    "COVER": {
        "width": 1024,
        "height": 576,
        "label": "Cover photo",
    },
    "PROFILE": {
        "width": 720,
        "height": 720,
        "label": "Profile photo",
    },
    "ADDITIONAL": {
        "width": 720,
        "height": 720,
        "label": "General / gallery photo",
    },
    "POST": {
        "width": 720,
        "height": 540,
        "label": "Post media photo",
    },
}

PHOTO_ALLOWED_FORMATS = {"JPEG", "JPG", "PNG"}
PHOTO_MIN_BYTES = 10 * 1024       # 10 KB
PHOTO_MAX_BYTES = 5 * 1024 * 1024  # 5 MB

# ---------------------------------------------------------------------------
# Company Registry
# ---------------------------------------------------------------------------


@dataclass(frozen=True)
class CompanyInfo:
    name: str
    slug: str
    accent_color: str
    address: str
    phone: str
    email: str
    coming_soon: bool = False
    service_areas: List[str] = field(default_factory=list)


COMPANIES: Dict[str, CompanyInfo] = {
    "us_framing": CompanyInfo(
        name="US Framing",
        slug="us-framing",
        accent_color="#4A90D9",
        address="123 Builder Blvd, Suite 100, Dallas, TX 75201",
        phone="+1-214-555-0101",
        email="info@usframing.com",
        service_areas=["Dallas-Fort Worth", "Houston", "Austin", "San Antonio"],
    ),
    "us_drywall": CompanyInfo(
        name="US Drywall",
        slug="us-drywall",
        accent_color="#B8860B",
        address="456 Finish Ave, Suite 200, Dallas, TX 75202",
        phone="+1-214-555-0102",
        email="info@usdrywall.com",
        service_areas=["Dallas-Fort Worth", "Houston", "Austin"],
    ),
    "us_exteriors": CompanyInfo(
        name="US Exteriors",
        slug="us-exteriors",
        accent_color="#2D5F2D",
        address="789 Facade Ln, Suite 300, Dallas, TX 75203",
        phone="+1-214-555-0103",
        email="info@usexteriors.com",
        service_areas=["Dallas-Fort Worth", "Houston"],
    ),
    "us_development": CompanyInfo(
        name="US Development",
        slug="us-development",
        accent_color="#C4AF94",
        address="321 Capital Dr, Suite 400, Dallas, TX 75204",
        phone="+1-214-555-0104",
        email="info@usdevelopment.com",
        service_areas=["Dallas-Fort Worth", "Austin", "San Antonio"],
    ),
    "us_interiors": CompanyInfo(
        name="US Interiors",
        slug="us-interiors",
        accent_color="#8B5E3C",
        address="654 Design Way, Suite 500, Dallas, TX 75205",
        phone="+1-214-555-0105",
        email="info@usinteriors.com",
        coming_soon=True,
        service_areas=["Dallas-Fort Worth"],
    ),
}

ACTIVE_COMPANIES = {k: v for k, v in COMPANIES.items() if not v.coming_soon}


def get_company(slug_or_key: str) -> Optional[CompanyInfo]:
    """Look up a company by registry key or slug."""
    if slug_or_key in COMPANIES:
        return COMPANIES[slug_or_key]
    for company in COMPANIES.values():
        if company.slug == slug_or_key:
            return company
    return None


# ---------------------------------------------------------------------------
# Paths & Storage
# ---------------------------------------------------------------------------

DATA_DIR = "data"
INSIGHTS_FILE = f"{DATA_DIR}/insights.json"
RATE_LIMIT_FILE = f"{DATA_DIR}/rate_limits.json"
