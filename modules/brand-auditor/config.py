"""
Brand Consistency Auditor - Configuration
==========================================
Central brand standards registry for all US Construction family companies.
Defines official NAP data, visual identity, voice guidelines, and audit parameters.
"""

from dataclasses import dataclass, field
from typing import Dict, List, Optional


# ---------------------------------------------------------------------------
# Company Brand Standards
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class BrandStandard:
    """Immutable record of a single company's brand identity."""
    official_name: str
    tagline: str
    accent_hex: str
    address_line1: str
    address_line2: str
    phone: str
    voice_keywords: List[str]
    status: str = "active"  # active | coming_soon


COMPANIES: Dict[str, BrandStandard] = {
    "us_framing": BrandStandard(
        official_name="US Framing",
        tagline="Nation's largest multi-family wood framing group",
        accent_hex="#4A90D9",
        address_line1="P.O. Box 710",
        address_line2="Pewee Valley KY 40056",
        phone="(502) 276-0284",
        voice_keywords=[
            "precision", "scale", "multi-family", "wood framing",
            "structural", "nationwide", "reliability", "craftsmanship",
        ],
    ),
    "us_drywall": BrandStandard(
        official_name="US Drywall",
        tagline="Expert commercial drywall services",
        accent_hex="#B8860B",
        address_line1="4700 Shelbyville Rd Suite 200",
        address_line2="Louisville KY 40207",
        phone="(502) 555-0180",
        voice_keywords=[
            "commercial", "drywall", "finish", "quality",
            "interior", "expertise", "professional", "detail",
        ],
    ),
    "us_exteriors": BrandStandard(
        official_name="US Exteriors",
        tagline="Complete exterior envelope systems",
        accent_hex="#2D5F2D",
        address_line1="4700 Shelbyville Rd Suite 210",
        address_line2="Louisville KY 40207",
        phone="(502) 555-0192",
        voice_keywords=[
            "exterior", "envelope", "weatherproofing", "cladding",
            "protection", "durability", "systems", "complete",
        ],
    ),
    "us_development": BrandStandard(
        official_name="US Development",
        tagline="Turnkey construction management",
        accent_hex="#C4AF94",
        address_line1="4965 US Highway 42 Suite 220",
        address_line2="Louisville KY 40222",
        phone="(502) 555-0195",
        voice_keywords=[
            "turnkey", "management", "development", "construction",
            "oversight", "delivery", "partnership", "solutions",
        ],
    ),
    "us_interiors": BrandStandard(
        official_name="US Interiors",
        tagline="",
        accent_hex="#8B5E3C",
        address_line1="",
        address_line2="",
        phone="",
        voice_keywords=[
            "interior", "finish", "design", "build",
            "renovation", "commercial", "residential", "quality",
        ],
        status="coming_soon",
    ),
}


# ---------------------------------------------------------------------------
# Shared Visual Identity
# ---------------------------------------------------------------------------

PRIMARY_NAVY = "#1B2A4A"

FONT_FAMILIES = {
    "heading": "Playfair Display",
    "body": "Inter",
}

ICON_LIBRARY = "Lucide"


# ---------------------------------------------------------------------------
# Fuzzy-Match Configuration
# ---------------------------------------------------------------------------

FUZZY_MATCH_THRESHOLD: float = 0.85


# ---------------------------------------------------------------------------
# Directory Listings to Audit
# ---------------------------------------------------------------------------

DIRECTORIES: List[str] = [
    "Google Business",
    "Yelp",
    "Facebook",
    "BBB",
    "Angi",
]


# ---------------------------------------------------------------------------
# Audit Scoring Weights (must sum to 100)
# ---------------------------------------------------------------------------

SCORING_WEIGHTS: Dict[str, int] = {
    "nap": 30,
    "visual": 25,
    "voice": 25,
    "directories": 20,
}

assert sum(SCORING_WEIGHTS.values()) == 100, "Scoring weights must sum to 100"


# ---------------------------------------------------------------------------
# Address Normalisation Map
# ---------------------------------------------------------------------------

ADDRESS_ABBREVIATIONS: Dict[str, str] = {
    "Rd": "Road",
    "St": "Street",
    "Ste": "Suite",
    "Ave": "Avenue",
    "Dr": "Drive",
    "Blvd": "Boulevard",
    "Ln": "Lane",
    "Ct": "Court",
    "Pl": "Place",
    "Hwy": "Highway",
    "Pkwy": "Parkway",
}


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def get_active_companies() -> Dict[str, BrandStandard]:
    """Return only companies with status == 'active'."""
    return {k: v for k, v in COMPANIES.items() if v.status == "active"}


def get_company(slug: str) -> Optional[BrandStandard]:
    """Look up a company by its slug key."""
    return COMPANIES.get(slug)


def company_slugs() -> List[str]:
    """Return all company slug keys."""
    return list(COMPANIES.keys())
