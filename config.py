"""
Mission Control Dashboard — Unified Configuration
Imports and merges configs from all automation modules.
"""

import os
import sys
from pathlib import Path
from typing import Dict, Any, Optional

# Add parent automation directory to path for module imports
AUTOMATION_DIR = Path(__file__).parent.parent
sys.path.insert(0, str(AUTOMATION_DIR))

# Data directory for mock/live data
DATA_DIR = Path(__file__).parent / "data"
DATA_DIR.mkdir(exist_ok=True)


# ── Company Registry ─────────────────────────────────────────────
COMPANIES: Dict[str, Dict[str, Any]] = {
    "us_construction": {
        "name": "US Construction",
        "slug": "us-construction",
        "accent_color": "#6B7B8D",
        "accent_name": "steel",
        "website": "https://us-construction.onrender.com",
        "phone": "(502) 555-0100",
        "email": "info@usconstruction.com",
        "address": "4700 Shelbyville Rd, Suite 100, Louisville, KY 40207",
        "services": [
            "Turnkey Vertical Integration",
            "Multi-Trade Coordination",
            "One Call Framing Through Finish",
        ],
        "tagline": "One Call. Framing Through Finish.",
        "is_parent": True,
    },
    "us_framing": {
        "name": "US Framing",
        "slug": "us-framing",
        "accent_color": "#4A90D9",
        "accent_name": "sky",
        "website": "https://us-framing.onrender.com",
        "phone": "(502) 276-0284",
        "email": "info@usframing.com",
        "address": "P.O. Box 710, Pewee Valley, KY 40056",
        "services": [
            "Pre-Design & 3-D Modeling",
            "Pre-Construction",
            "Production Framing",
            "Project Management",
            "Takeover as a Service",
            "CLT / Mass Timber",
        ],
        "tagline": "Nation's largest multi-family wood framing group",
    },
    "us_drywall": {
        "name": "US Drywall",
        "slug": "us-drywall",
        "accent_color": "#B8860B",
        "accent_name": "gold",
        "website": "https://us-drywall.onrender.com",
        "phone": "(502) 555-0180",
        "email": "info@usdrywall.com",
        "address": "4700 Shelbyville Rd, Suite 200, Louisville, KY 40207",
        "services": [
            "Drywall Installation",
            "Metal Stud Framing",
            "Acoustical Ceilings",
            "Drywall Repair & Patching",
            "Fire-Rated Assemblies",
            "Specialty Finishes",
        ],
        "tagline": "Expert commercial drywall services",
    },
    "us_exteriors": {
        "name": "US Exteriors",
        "slug": "us-exteriors",
        "accent_color": "#2D5F2D",
        "accent_name": "forest",
        "website": "https://us-exteriors.onrender.com",
        "phone": "(502) 555-0192",
        "email": "info@usexteriors.com",
        "address": "4700 Shelbyville Rd, Suite 210, Louisville, KY 40207",
        "services": [
            "Siding Installation",
            "Roofing Systems",
            "EIFS / Exterior Insulation",
            "Waterproofing & Moisture Barrier",
            "Exterior Trim & Soffit",
            "Metal Panels & Cladding",
        ],
        "tagline": "Complete exterior envelope systems",
    },
    "us_interiors": {
        "name": "US Interiors",
        "slug": "us-interiors",
        "accent_color": "#5B7B99",
        "accent_name": "slate",
        "website": "https://us-interiors.onrender.com",
        "phone": "(502) 555-0190",
        "email": "info@usinteriors.com",
        "address": "4700 Shelbyville Rd, Suite 215, Louisville, KY 40207",
        "services": [
            "Acoustical Ceilings",
            "Specialty Finishes",
            "Painting & Coatings",
            "Millwork & Trim",
            "Wall Coverings",
            "Interior Restoration",
        ],
        "tagline": "Interior Finishing. Perfected.",
    },
    "us_development": {
        "name": "US Development",
        "slug": "us-development",
        "accent_color": "#C4AF94",
        "accent_name": "tan",
        "website": "https://us-development.onrender.com",
        "phone": "(502) 555-0195",
        "email": "info@usdevelopment.com",
        "address": "4965 US Highway 42, Suite 220, Louisville, KY 40222",
        "services": [
            "Land Acquisition & Site Selection",
            "Entitlements & Permitting",
            "Project Financing & Capital Stack",
            "Owner's Representation",
            "Pre-Development Services",
            "Asset Management",
        ],
        "tagline": "Real Estate Development",
    },
}

# Active companies (exclude coming_soon)
ACTIVE_COMPANIES = {
    k: v for k, v in COMPANIES.items() if v.get("status") != "coming_soon"
}


# ── Module Import Helpers ─────────────────────────────────────────
def try_import_module_config(module_name: str) -> Optional[Any]:
    """Try to import a config from an existing automation module."""
    try:
        module_path = AUTOMATION_DIR / module_name
        if module_path.exists():
            sys.path.insert(0, str(module_path))
            import importlib
            mod = importlib.import_module("config")
            sys.path.pop(0)
            return mod
    except Exception:
        pass
    return None


# ── Dashboard Config ──────────────────────────────────────────────
class DashboardConfig:
    """Central config for the Mission Control dashboard."""

    APP_NAME = "US Construction Mission Control"
    APP_VERSION = "1.0.0"
    HOST = os.getenv("HOST", "0.0.0.0")
    PORT = int(os.getenv("PORT", "8000"))
    DEBUG = os.getenv("DEBUG", "false").lower() == "true"
    DEMO_MODE = os.getenv("DEMO_MODE", "true").lower() == "true"

    # CORS
    ALLOWED_ORIGINS = [
        "http://localhost:8000",
        "http://127.0.0.1:8000",
        "https://us-mission-control.onrender.com",
        "https://us-marketing-dashboard.onrender.com",
    ]

    # Data paths
    DATA_DIR = DATA_DIR
    POSTS_FILE = DATA_DIR / "posts.json"
    ARTICLES_FILE = DATA_DIR / "articles.json"
    LEADS_FILE = DATA_DIR / "leads.json"
    EVENTS_FILE = DATA_DIR / "events.json"
    TOKENS_FILE = DATA_DIR / "tokens.json"
    GBP_FILE = DATA_DIR / "gbp.json"
    AEO_FILE = DATA_DIR / "aeo.json"
    REVIEWS_FILE = DATA_DIR / "reviews.json"
    BRAND_AUDIT_FILE = DATA_DIR / "brand_audit.json"
    ASSETS_FILE = DATA_DIR / "assets.json"
    QUALITY_FILE = DATA_DIR / "quality.json"

    # Companies
    COMPANIES = COMPANIES
    ACTIVE_COMPANIES = ACTIVE_COMPANIES


config = DashboardConfig()
