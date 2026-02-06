"""
Brand Consistency Auditor - Visual Auditor
============================================
Checks visual identity compliance: hex colours, font families,
primary navy usage, and accent colour consistency.
"""

from __future__ import annotations

import re
from typing import Dict, List, Optional, Tuple

from config import (
    COMPANIES,
    FONT_FAMILIES,
    PRIMARY_NAVY,
    get_active_companies,
    get_company,
)
from models import AuditCategory, BrandCheck, Inconsistency, Severity


# ---------------------------------------------------------------------------
# Demo data: simulated CSS / page scan results
# ---------------------------------------------------------------------------

DEMO_PAGE_SCANS: Dict[str, Dict[str, object]] = {
    "us_framing": {
        "hex_colors_found": ["#1B2A4A", "#4A90D9", "#FFFFFF", "#F5F5F5", "#333333", "#4a90d9"],
        "font_families_found": ["Playfair Display", "Inter", "Arial", "sans-serif"],
        "has_primary_navy": True,
        "has_accent_color": True,
        "off_brand_colors": ["#333333"],
        "missing_fonts": [],
        "extra_fonts": ["Arial"],
        "pages_scanned": 5,
        "pages_with_issues": 1,
    },
    "us_drywall": {
        "hex_colors_found": ["#1B2A4A", "#B8860B", "#FFFFFF", "#F0F0F0", "#222222", "#DAA520"],
        "font_families_found": ["Playfair Display", "Inter", "Roboto"],
        "has_primary_navy": True,
        "has_accent_color": True,
        "off_brand_colors": ["#222222", "#DAA520"],
        "missing_fonts": [],
        "extra_fonts": ["Roboto"],
        "pages_scanned": 4,
        "pages_with_issues": 2,
    },
    "us_exteriors": {
        "hex_colors_found": ["#1B2A4A", "#2D5F2D", "#FFFFFF", "#E8E8E8", "#2d5f2d", "#006400"],
        "font_families_found": ["Playfair Display", "Inter"],
        "has_primary_navy": True,
        "has_accent_color": True,
        "off_brand_colors": ["#006400"],
        "missing_fonts": [],
        "extra_fonts": [],
        "pages_scanned": 4,
        "pages_with_issues": 1,
    },
    "us_development": {
        "hex_colors_found": ["#1b2a4a", "#C4AF94", "#FFFFFF", "#F8F8F8", "#444444", "#A0522D"],
        "font_families_found": ["Inter", "Georgia"],
        "has_primary_navy": True,
        "has_accent_color": True,
        "off_brand_colors": ["#444444", "#A0522D"],
        "missing_fonts": ["Playfair Display"],
        "extra_fonts": ["Georgia"],
        "pages_scanned": 3,
        "pages_with_issues": 2,
    },
}


# ---------------------------------------------------------------------------
# Colour Helpers
# ---------------------------------------------------------------------------

def normalise_hex(hex_color: str) -> str:
    """Lowercase a hex colour for comparison."""
    return hex_color.strip().lower()


def hex_distance(a: str, b: str) -> float:
    """
    Compute a simple Euclidean distance in RGB space between two hex colours.
    Returns a value 0-1 where 0 is identical and 1 is max distance.
    """
    a = normalise_hex(a).lstrip("#")
    b = normalise_hex(b).lstrip("#")
    try:
        ar, ag, ab_val = int(a[0:2], 16), int(a[2:4], 16), int(a[4:6], 16)
        br, bg, bb = int(b[0:2], 16), int(b[2:4], 16), int(b[4:6], 16)
    except (ValueError, IndexError):
        return 1.0
    max_dist = (255**2 * 3) ** 0.5
    dist = ((ar - br) ** 2 + (ag - bg) ** 2 + (ab_val - bb) ** 2) ** 0.5
    return dist / max_dist


def extract_hex_colors(css_text: str) -> List[str]:
    """Pull all hex colour values from a CSS string."""
    return re.findall(r"#[0-9A-Fa-f]{3,8}\b", css_text)


def extract_font_families(css_text: str) -> List[str]:
    """Pull font-family declarations from CSS."""
    matches = re.findall(r"font-family:\s*([^;]+);", css_text, re.IGNORECASE)
    fonts: List[str] = []
    for match in matches:
        for font in match.split(","):
            cleaned = font.strip().strip("'\"")
            if cleaned and cleaned not in fonts:
                fonts.append(cleaned)
    return fonts


# ---------------------------------------------------------------------------
# Scoring Logic
# ---------------------------------------------------------------------------

def _score_colors(
    brand_accent: str,
    colors_found: List[str],
    has_primary_navy: bool,
    off_brand_colors: List[str],
) -> Tuple[float, List[Inconsistency]]:
    """Score colour usage and return issues."""
    issues: List[Inconsistency] = []
    score = 100.0

    # Check primary navy
    if not has_primary_navy:
        score -= 25.0
        issues.append(Inconsistency(
            field="primary_color",
            expected=PRIMARY_NAVY,
            found="not detected",
            severity=Severity.critical,
            platform="website",
        ))

    # Check accent colour present
    accent_present = any(
        normalise_hex(c) == normalise_hex(brand_accent)
        for c in colors_found
    )
    if not accent_present:
        score -= 15.0
        issues.append(Inconsistency(
            field="accent_color",
            expected=brand_accent,
            found="not detected",
            severity=Severity.warning,
            platform="website",
        ))

    # Penalise off-brand colours
    for obc in off_brand_colors:
        score -= 5.0
        issues.append(Inconsistency(
            field="off_brand_color",
            expected="brand palette only",
            found=obc,
            severity=Severity.info,
            platform="website",
        ))

    return max(0.0, score), issues


def _score_fonts(
    missing_fonts: List[str],
    extra_fonts: List[str],
) -> Tuple[float, List[Inconsistency]]:
    """Score font usage and return issues."""
    issues: List[Inconsistency] = []
    score = 100.0

    for mf in missing_fonts:
        score -= 20.0
        issues.append(Inconsistency(
            field="font_missing",
            expected=mf,
            found="not detected",
            severity=Severity.critical,
            platform="website",
        ))

    for ef in extra_fonts:
        score -= 5.0
        issues.append(Inconsistency(
            field="font_extra",
            expected="brand fonts only",
            found=ef,
            severity=Severity.info,
            platform="website",
        ))

    return max(0.0, score), issues


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def audit_visual(company_slug: str, demo: bool = True, css_text: Optional[str] = None) -> BrandCheck:
    """
    Run a visual identity audit for the given company.

    Parameters
    ----------
    company_slug : str
        Key from config.COMPANIES.
    demo : bool
        Use built-in demo data when True.
    css_text : str, optional
        Raw CSS to parse when not in demo mode.

    Returns
    -------
    BrandCheck with score 0-100 and any inconsistencies.
    """
    brand = get_company(company_slug)
    if brand is None:
        return BrandCheck(
            category=AuditCategory.visual,
            score=0,
            details=f"Unknown company: {company_slug}",
        )

    if brand.status == "coming_soon":
        return BrandCheck(
            category=AuditCategory.visual,
            score=0,
            details=f"{brand.official_name} is marked coming_soon; visual audit skipped.",
        )

    all_issues: List[Inconsistency] = []

    if demo:
        scan = DEMO_PAGE_SCANS.get(company_slug, {})
        colors_found = scan.get("hex_colors_found", [])
        has_primary_navy = scan.get("has_primary_navy", False)
        off_brand_colors = scan.get("off_brand_colors", [])
        missing_fonts = scan.get("missing_fonts", [])
        extra_fonts = scan.get("extra_fonts", [])
        pages_scanned = scan.get("pages_scanned", 0)
        pages_with_issues = scan.get("pages_with_issues", 0)
    else:
        if css_text:
            colors_found = extract_hex_colors(css_text)
            fonts_found = extract_font_families(css_text)
            has_primary_navy = any(normalise_hex(c) == normalise_hex(PRIMARY_NAVY) for c in colors_found)
            off_brand_colors = [
                c for c in colors_found
                if normalise_hex(c) not in {
                    normalise_hex(PRIMARY_NAVY),
                    normalise_hex(brand.accent_hex),
                    "#ffffff", "#f5f5f5", "#f0f0f0", "#e8e8e8", "#f8f8f8",
                }
            ]
            missing_fonts = [
                f for f in FONT_FAMILIES.values()
                if not any(f.lower() in found.lower() for found in fonts_found)
            ]
            extra_fonts = [
                f for f in fonts_found
                if not any(
                    brand_f.lower() in f.lower()
                    for brand_f in FONT_FAMILIES.values()
                )
                and f.lower() not in {"sans-serif", "serif", "monospace", "inherit"}
            ]
        else:
            colors_found = []
            has_primary_navy = False
            off_brand_colors = []
            missing_fonts = list(FONT_FAMILIES.values())
            extra_fonts = []
        pages_scanned = 1
        pages_with_issues = 1 if off_brand_colors or missing_fonts else 0

    # Score colours
    color_score, color_issues = _score_colors(
        brand.accent_hex, colors_found, has_primary_navy, off_brand_colors
    )
    all_issues.extend(color_issues)

    # Score fonts
    font_score, font_issues = _score_fonts(missing_fonts, extra_fonts)
    all_issues.extend(font_issues)

    # Combined score (60% colour, 40% font)
    final_score = (color_score * 0.6) + (font_score * 0.4)

    details = (
        f"Visual audit for {brand.official_name}: "
        f"score {final_score:.0f}/100 "
        f"({pages_scanned} pages scanned, {pages_with_issues} with issues, "
        f"{len(all_issues)} total findings)"
    )

    return BrandCheck(
        category=AuditCategory.visual,
        score=round(final_score, 1),
        details=details,
        inconsistencies=all_issues,
    )


def audit_all_visual(demo: bool = True) -> Dict[str, BrandCheck]:
    """Run visual audit for every active company."""
    results: Dict[str, BrandCheck] = {}
    for slug in get_active_companies():
        results[slug] = audit_visual(slug, demo=demo)
    return results
