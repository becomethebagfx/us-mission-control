"""
Visual Asset Generator - Configuration
Brand palettes, platform sizes, template types, and system config.
"""

from pathlib import Path

# ──────────────────────────────────────────────────────────────
# Directory Config
# ──────────────────────────────────────────────────────────────

BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "data"
TEMPLATES_DIR = DATA_DIR / "templates"
OUTPUT_DIR = BASE_DIR / "output"
LIBRARY_DIR = BASE_DIR / "library"
LIBRARY_DB_PATH = LIBRARY_DIR / "assets.json"

# Ensure directories exist
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
LIBRARY_DIR.mkdir(parents=True, exist_ok=True)

# ──────────────────────────────────────────────────────────────
# Claude Model Config
# ──────────────────────────────────────────────────────────────

CLAUDE_MODEL = "claude-sonnet-4-20250514"
CLAUDE_MAX_TOKENS = 4096

# ──────────────────────────────────────────────────────────────
# Font Config
# ──────────────────────────────────────────────────────────────

FONT_HEADING = "Playfair Display"
FONT_BODY = "Inter"

# Fallback system fonts for Pillow rendering
FONT_HEADING_FALLBACK = "Georgia"
FONT_BODY_FALLBACK = "Arial"

# ──────────────────────────────────────────────────────────────
# Brand Palettes
# ──────────────────────────────────────────────────────────────

BRAND_PALETTES: dict[str, dict[str, str]] = {
    "us_framing": {
        "primary": "#1B2A4A",
        "accent": "#4A90D9",
        "text_light": "#FFFFFF",
        "text_dark": "#1B2A4A",
        "font_heading": FONT_HEADING,
        "font_body": FONT_BODY,
        "name_short": "USF",
        "name_full": "US Framing",
    },
    "us_drywall": {
        "primary": "#1B2A4A",
        "accent": "#B8860B",
        "text_light": "#FFFFFF",
        "text_dark": "#1B2A4A",
        "font_heading": FONT_HEADING,
        "font_body": FONT_BODY,
        "name_short": "USD",
        "name_full": "US Drywall",
    },
    "us_exteriors": {
        "primary": "#1B2A4A",
        "accent": "#2D5F2D",
        "text_light": "#FFFFFF",
        "text_dark": "#1B2A4A",
        "font_heading": FONT_HEADING,
        "font_body": FONT_BODY,
        "name_short": "USE",
        "name_full": "US Exteriors",
    },
    "us_development": {
        "primary": "#1B2A4A",
        "accent": "#C4AF94",
        "text_light": "#FFFFFF",
        "text_dark": "#1B2A4A",
        "font_heading": FONT_HEADING,
        "font_body": FONT_BODY,
        "name_short": "USDv",
        "name_full": "US Development",
    },
    "us_interiors": {
        "primary": "#1B2A4A",
        "accent": "#8B5E3C",
        "text_light": "#FFFFFF",
        "text_dark": "#1B2A4A",
        "font_heading": FONT_HEADING,
        "font_body": FONT_BODY,
        "name_short": "USI",
        "name_full": "US Interiors",
    },
}

# ──────────────────────────────────────────────────────────────
# Platform Sizes
# ──────────────────────────────────────────────────────────────

PLATFORM_SIZES: dict[str, dict[str, int | float | str]] = {
    "linkedin_post": {
        "name": "LinkedIn Post",
        "width": 1200,
        "height": 627,
        "aspect_ratio": 1200 / 627,
    },
    "linkedin_banner": {
        "name": "LinkedIn Banner",
        "width": 1128,
        "height": 191,
        "aspect_ratio": 1128 / 191,
    },
    "instagram_post": {
        "name": "Instagram Post",
        "width": 1080,
        "height": 1080,
        "aspect_ratio": 1.0,
    },
    "instagram_story": {
        "name": "Instagram Story",
        "width": 1080,
        "height": 1920,
        "aspect_ratio": 1080 / 1920,
    },
    "facebook_post": {
        "name": "Facebook Post",
        "width": 1200,
        "height": 630,
        "aspect_ratio": 1200 / 630,
    },
    "facebook_cover": {
        "name": "Facebook Cover",
        "width": 820,
        "height": 312,
        "aspect_ratio": 820 / 312,
    },
    "gbp_post": {
        "name": "Google Business Profile Post",
        "width": 720,
        "height": 540,
        "aspect_ratio": 720 / 540,
    },
    "twitter_post": {
        "name": "Twitter Post",
        "width": 1200,
        "height": 675,
        "aspect_ratio": 1200 / 675,
    },
}

# ──────────────────────────────────────────────────────────────
# Template Types
# ──────────────────────────────────────────────────────────────

TEMPLATE_TYPES: dict[str, dict[str, str | list[str]]] = {
    "project_showcase": {
        "name": "Project Showcase",
        "html_path": "project_showcase.html",
        "description": "Project completion graphics with stats overlay",
        "variables": [
            "company_name",
            "accent_color",
            "primary_color",
            "project_name",
            "sqft",
            "timeline",
            "location",
            "stats",
        ],
    },
    "social_quote": {
        "name": "Social Quote Card",
        "html_path": "social_quote.html",
        "description": "Testimonial card with quote and attribution",
        "variables": [
            "quote_text",
            "quote_author",
            "quote_role",
            "company_name",
            "accent_color",
            "primary_color",
        ],
    },
    "stat_card": {
        "name": "Stat Card",
        "html_path": "stat_card.html",
        "description": "Infographic card for key metrics",
        "variables": [
            "stat_value",
            "stat_label",
            "stat_description",
            "company_name",
            "accent_color",
            "primary_color",
        ],
    },
    "company_header": {
        "name": "Company Header",
        "html_path": "company_header.html",
        "description": "Banner/header with company branding",
        "variables": [
            "company_name",
            "tagline",
            "accent_color",
            "primary_color",
        ],
    },
}

# ──────────────────────────────────────────────────────────────
# Company Registry (quick lookup)
# ──────────────────────────────────────────────────────────────

COMPANY_KEYS = list(BRAND_PALETTES.keys())

COMPANY_NAMES: dict[str, str] = {
    key: palette["name_full"] for key, palette in BRAND_PALETTES.items()
}

COMPANY_SHORT_NAMES: dict[str, str] = {
    key: palette["name_short"] for key, palette in BRAND_PALETTES.items()
}


def get_brand(company_key: str) -> dict[str, str]:
    """Get brand palette for a company. Raises KeyError if not found."""
    if company_key not in BRAND_PALETTES:
        valid = ", ".join(COMPANY_KEYS)
        raise KeyError(f"Unknown company '{company_key}'. Valid keys: {valid}")
    return BRAND_PALETTES[company_key]


def get_platform(platform_key: str) -> dict[str, int | float | str]:
    """Get platform size config. Raises KeyError if not found."""
    if platform_key not in PLATFORM_SIZES:
        valid = ", ".join(PLATFORM_SIZES.keys())
        raise KeyError(f"Unknown platform '{platform_key}'. Valid keys: {valid}")
    return PLATFORM_SIZES[platform_key]
