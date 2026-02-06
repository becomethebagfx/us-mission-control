"""
Brand Consistency Auditor - NAP Auditor
========================================
Checks Name, Address, Phone consistency across platforms using
fuzzy matching (difflib.SequenceMatcher) with configurable threshold.
"""

from __future__ import annotations

import difflib
import re
from typing import Dict, List, Tuple

from config import (
    ADDRESS_ABBREVIATIONS,
    COMPANIES,
    FUZZY_MATCH_THRESHOLD,
    get_active_companies,
    get_company,
)
from models import AuditCategory, BrandCheck, Inconsistency, Severity


# ---------------------------------------------------------------------------
# Demo data: simulated platform listings with realistic inconsistencies
# ---------------------------------------------------------------------------

DEMO_LISTINGS: Dict[str, Dict[str, Dict[str, str]]] = {
    "us_framing": {
        "Google Business": {
            "name": "US Framing LLC",
            "address": "P.O. Box 710, Pewee Valley KY 40056",
            "phone": "(502) 276-0284",
        },
        "Yelp": {
            "name": "US Framing",
            "address": "PO Box 710 Pewee Valley, KY 40056",
            "phone": "502-276-0284",
        },
        "Facebook": {
            "name": "U.S. Framing",
            "address": "P.O. Box 710 Pewee Valley KY 40056",
            "phone": "(502) 276-0284",
        },
        "BBB": {
            "name": "US Framing",
            "address": "P.O. Box 710 Pewee Valley KY 40056",
            "phone": "(502) 276-0284",
        },
        "Angi": {
            "name": "US Framing Inc",
            "address": "PO Box 710, Pewee Valley Kentucky 40056",
            "phone": "5022760284",
        },
    },
    "us_drywall": {
        "Google Business": {
            "name": "US Drywall",
            "address": "4700 Shelbyville Rd Ste 200 Louisville KY 40207",
            "phone": "(502) 555-0180",
        },
        "Yelp": {
            "name": "US Drywall Services",
            "address": "4700 Shelbyville Road Suite 200, Louisville KY 40207",
            "phone": "502-555-0180",
        },
        "Facebook": {
            "name": "US Drywall",
            "address": "4700 Shelbyville Rd Suite 200 Louisville KY 40207",
            "phone": "(502) 555-0180",
        },
        "BBB": {
            "name": "US Drywall LLC",
            "address": "4700 Shelbyville Rd, Suite 200, Louisville, KY 40207",
            "phone": "(502) 555-0180",
        },
        "Angi": {
            "name": "US Drywall",
            "address": "4700 Shelbyville Rd #200 Louisville KY 40207",
            "phone": "5025550180",
        },
    },
    "us_exteriors": {
        "Google Business": {
            "name": "US Exteriors",
            "address": "4700 Shelbyville Rd Suite 210 Louisville KY 40207",
            "phone": "(502) 555-0192",
        },
        "Yelp": {
            "name": "US Exteriors LLC",
            "address": "4700 Shelbyville Road, Ste 210, Louisville KY 40207",
            "phone": "502-555-0192",
        },
        "Facebook": {
            "name": "U.S. Exteriors",
            "address": "4700 Shelbyville Rd Ste 210 Louisville KY 40207",
            "phone": "(502) 555-0192",
        },
        "BBB": {
            "name": "US Exteriors",
            "address": "4700 Shelbyville Rd Suite 210 Louisville KY 40207",
            "phone": "(502) 555-0192",
        },
        "Angi": {
            "name": "US Exteriors",
            "address": "4700 Shelbyville Rd Suite 210, Louisville, KY 40207",
            "phone": "(502) 555-0192",
        },
    },
    "us_development": {
        "Google Business": {
            "name": "US Development",
            "address": "4965 US Hwy 42 Suite 220 Louisville KY 40222",
            "phone": "(502) 555-0195",
        },
        "Yelp": {
            "name": "US Development Group",
            "address": "4965 US Highway 42, Ste 220, Louisville KY 40222",
            "phone": "502-555-0195",
        },
        "Facebook": {
            "name": "US Development",
            "address": "4965 US Highway 42 Suite 220 Louisville KY 40222",
            "phone": "(502) 555-0195",
        },
        "BBB": {
            "name": "US Development LLC",
            "address": "4965 US Highway 42 Suite 220, Louisville, KY 40222",
            "phone": "(502) 555-0195",
        },
        "Angi": {
            "name": "US Development",
            "address": "4965 Highway 42 Ste 220 Louisville KY 40222",
            "phone": "5025550195",
        },
    },
}


# ---------------------------------------------------------------------------
# Normalisation Helpers
# ---------------------------------------------------------------------------

def normalise_phone(phone: str) -> str:
    """Strip a phone number to digits only."""
    return re.sub(r"\D", "", phone)


def normalise_address(address: str) -> str:
    """
    Expand common abbreviations and remove punctuation / extra whitespace
    so that fuzzy matching can focus on real differences.
    """
    result = address

    # Remove commas and periods
    result = result.replace(",", " ").replace(".", " ")

    # Expand abbreviations (whole-word only)
    for abbr, full in ADDRESS_ABBREVIATIONS.items():
        result = re.sub(rf"\b{re.escape(abbr)}\b", full, result)

    # Collapse whitespace
    result = re.sub(r"\s+", " ", result).strip()

    return result


def similarity(a: str, b: str) -> float:
    """Return SequenceMatcher ratio between two strings."""
    return difflib.SequenceMatcher(None, a.lower(), b.lower()).ratio()


# ---------------------------------------------------------------------------
# Core Audit Logic
# ---------------------------------------------------------------------------

def check_name(expected: str, found: str, platform: str) -> List[Inconsistency]:
    """Compare a business name against the brand standard."""
    issues: List[Inconsistency] = []
    ratio = similarity(expected, found)

    if expected.lower() != found.lower():
        if ratio < FUZZY_MATCH_THRESHOLD:
            severity = Severity.critical
        elif ratio < 0.95:
            severity = Severity.warning
        else:
            severity = Severity.info

        issues.append(Inconsistency(
            field="name",
            expected=expected,
            found=found,
            severity=severity,
            platform=platform,
        ))

    return issues


def check_address(expected_line1: str, expected_line2: str, found: str, platform: str) -> List[Inconsistency]:
    """Compare an address against the brand standard after normalisation."""
    issues: List[Inconsistency] = []
    canonical = f"{expected_line1} {expected_line2}"
    norm_expected = normalise_address(canonical)
    norm_found = normalise_address(found)
    ratio = similarity(norm_expected, norm_found)

    if ratio < 1.0:
        if ratio < FUZZY_MATCH_THRESHOLD:
            severity = Severity.critical
        elif ratio < 0.95:
            severity = Severity.warning
        else:
            severity = Severity.info

        issues.append(Inconsistency(
            field="address",
            expected=canonical,
            found=found,
            severity=severity,
            platform=platform,
        ))

    return issues


def check_phone(expected: str, found: str, platform: str) -> List[Inconsistency]:
    """Compare phone numbers after stripping to digits."""
    issues: List[Inconsistency] = []
    norm_expected = normalise_phone(expected)
    norm_found = normalise_phone(found)

    if norm_expected != norm_found:
        issues.append(Inconsistency(
            field="phone",
            expected=expected,
            found=found,
            severity=Severity.critical,
            platform=platform,
        ))
    elif expected != found:
        issues.append(Inconsistency(
            field="phone_format",
            expected=expected,
            found=found,
            severity=Severity.info,
            platform=platform,
        ))

    return issues


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def audit_nap(company_slug: str, demo: bool = True) -> BrandCheck:
    """
    Run a full NAP audit for the given company.

    Parameters
    ----------
    company_slug : str
        Key from config.COMPANIES.
    demo : bool
        When True, use built-in demo listings rather than live scraping.

    Returns
    -------
    BrandCheck with score and inconsistency list.
    """
    brand = get_company(company_slug)
    if brand is None:
        return BrandCheck(
            category=AuditCategory.nap,
            score=0,
            details=f"Unknown company: {company_slug}",
        )

    if brand.status == "coming_soon":
        return BrandCheck(
            category=AuditCategory.nap,
            score=0,
            details=f"{brand.official_name} is marked coming_soon; NAP audit skipped.",
        )

    if demo:
        listings = DEMO_LISTINGS.get(company_slug, {})
    else:
        # Live scraping would go here
        listings = {}

    all_issues: List[Inconsistency] = []

    for platform_name, listing in listings.items():
        all_issues.extend(check_name(brand.official_name, listing.get("name", ""), platform_name))
        all_issues.extend(check_address(
            brand.address_line1,
            brand.address_line2,
            listing.get("address", ""),
            platform_name,
        ))
        all_issues.extend(check_phone(brand.phone, listing.get("phone", ""), platform_name))

    # Score: start at 100, deduct per issue
    deductions = {
        Severity.critical: 15,
        Severity.warning: 8,
        Severity.info: 2,
    }
    total_deduction = sum(deductions.get(i.severity, 0) for i in all_issues)
    score = max(0.0, 100.0 - total_deduction)

    critical_count = sum(1 for i in all_issues if i.severity == Severity.critical)
    warning_count = sum(1 for i in all_issues if i.severity == Severity.warning)
    info_count = sum(1 for i in all_issues if i.severity == Severity.info)

    details = (
        f"NAP audit for {brand.official_name}: "
        f"{len(all_issues)} issues found across {len(listings)} platforms "
        f"({critical_count} critical, {warning_count} warnings, {info_count} info)"
    )

    return BrandCheck(
        category=AuditCategory.nap,
        score=score,
        details=details,
        inconsistencies=all_issues,
    )


def audit_all_nap(demo: bool = True) -> Dict[str, BrandCheck]:
    """Run NAP audit for every active company."""
    results: Dict[str, BrandCheck] = {}
    for slug in get_active_companies():
        results[slug] = audit_nap(slug, demo=demo)
    return results
