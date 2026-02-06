"""
Brand Consistency Auditor - Directory Scanner
===============================================
Simulates scanning business directories (Google, Yelp, Facebook, BBB, Angi)
for listing presence, accuracy, and NAP consistency against brand standards.
"""

from __future__ import annotations

from typing import Dict, List, Optional

from config import COMPANIES, DIRECTORIES, get_active_companies, get_company
from models import (
    AuditCategory,
    BrandCheck,
    Inconsistency,
    Platform,
    Severity,
)


# ---------------------------------------------------------------------------
# Demo data: simulated directory scan results
# ---------------------------------------------------------------------------

DEMO_DIRECTORY_RESULTS: Dict[str, List[Platform]] = {
    "us_framing": [
        Platform(
            name="Google Business",
            url="https://business.google.com/us-framing",
            has_listing=True,
            accuracy_score=85.0,
            issues=[
                Inconsistency(
                    field="name",
                    expected="US Framing",
                    found="US Framing LLC",
                    severity=Severity.warning,
                    platform="Google Business",
                ),
            ],
        ),
        Platform(
            name="Yelp",
            url="https://yelp.com/biz/us-framing-pewee-valley",
            has_listing=True,
            accuracy_score=78.0,
            issues=[
                Inconsistency(
                    field="address",
                    expected="P.O. Box 710 Pewee Valley KY 40056",
                    found="PO Box 710 Pewee Valley, KY 40056",
                    severity=Severity.info,
                    platform="Yelp",
                ),
                Inconsistency(
                    field="phone_format",
                    expected="(502) 276-0284",
                    found="502-276-0284",
                    severity=Severity.info,
                    platform="Yelp",
                ),
            ],
        ),
        Platform(
            name="Facebook",
            url="https://facebook.com/usframing",
            has_listing=True,
            accuracy_score=82.0,
            issues=[
                Inconsistency(
                    field="name",
                    expected="US Framing",
                    found="U.S. Framing",
                    severity=Severity.warning,
                    platform="Facebook",
                ),
            ],
        ),
        Platform(
            name="BBB",
            url="https://bbb.org/us-framing",
            has_listing=True,
            accuracy_score=95.0,
            issues=[],
        ),
        Platform(
            name="Angi",
            url="https://angi.com/us-framing",
            has_listing=True,
            accuracy_score=65.0,
            issues=[
                Inconsistency(
                    field="name",
                    expected="US Framing",
                    found="US Framing Inc",
                    severity=Severity.warning,
                    platform="Angi",
                ),
                Inconsistency(
                    field="address",
                    expected="P.O. Box 710 Pewee Valley KY 40056",
                    found="PO Box 710, Pewee Valley Kentucky 40056",
                    severity=Severity.warning,
                    platform="Angi",
                ),
                Inconsistency(
                    field="phone_format",
                    expected="(502) 276-0284",
                    found="5022760284",
                    severity=Severity.info,
                    platform="Angi",
                ),
            ],
        ),
    ],
    "us_drywall": [
        Platform(
            name="Google Business",
            url="https://business.google.com/us-drywall",
            has_listing=True,
            accuracy_score=90.0,
            issues=[
                Inconsistency(
                    field="address",
                    expected="4700 Shelbyville Rd Suite 200 Louisville KY 40207",
                    found="4700 Shelbyville Rd Ste 200 Louisville KY 40207",
                    severity=Severity.info,
                    platform="Google Business",
                ),
            ],
        ),
        Platform(
            name="Yelp",
            url="https://yelp.com/biz/us-drywall-louisville",
            has_listing=True,
            accuracy_score=72.0,
            issues=[
                Inconsistency(
                    field="name",
                    expected="US Drywall",
                    found="US Drywall Services",
                    severity=Severity.warning,
                    platform="Yelp",
                ),
            ],
        ),
        Platform(
            name="Facebook",
            url="https://facebook.com/usdrywall",
            has_listing=True,
            accuracy_score=92.0,
            issues=[],
        ),
        Platform(
            name="BBB",
            url="https://bbb.org/us-drywall",
            has_listing=True,
            accuracy_score=80.0,
            issues=[
                Inconsistency(
                    field="name",
                    expected="US Drywall",
                    found="US Drywall LLC",
                    severity=Severity.warning,
                    platform="BBB",
                ),
            ],
        ),
        Platform(
            name="Angi",
            url="",
            has_listing=False,
            accuracy_score=0.0,
            issues=[
                Inconsistency(
                    field="listing",
                    expected="Active listing",
                    found="No listing found",
                    severity=Severity.critical,
                    platform="Angi",
                ),
            ],
        ),
    ],
    "us_exteriors": [
        Platform(
            name="Google Business",
            url="https://business.google.com/us-exteriors",
            has_listing=True,
            accuracy_score=95.0,
            issues=[],
        ),
        Platform(
            name="Yelp",
            url="https://yelp.com/biz/us-exteriors-louisville",
            has_listing=True,
            accuracy_score=75.0,
            issues=[
                Inconsistency(
                    field="name",
                    expected="US Exteriors",
                    found="US Exteriors LLC",
                    severity=Severity.warning,
                    platform="Yelp",
                ),
            ],
        ),
        Platform(
            name="Facebook",
            url="https://facebook.com/usexteriors",
            has_listing=True,
            accuracy_score=80.0,
            issues=[
                Inconsistency(
                    field="name",
                    expected="US Exteriors",
                    found="U.S. Exteriors",
                    severity=Severity.warning,
                    platform="Facebook",
                ),
            ],
        ),
        Platform(
            name="BBB",
            url="https://bbb.org/us-exteriors",
            has_listing=True,
            accuracy_score=95.0,
            issues=[],
        ),
        Platform(
            name="Angi",
            url="https://angi.com/us-exteriors",
            has_listing=True,
            accuracy_score=90.0,
            issues=[],
        ),
    ],
    "us_development": [
        Platform(
            name="Google Business",
            url="https://business.google.com/us-development",
            has_listing=True,
            accuracy_score=82.0,
            issues=[
                Inconsistency(
                    field="address",
                    expected="4965 US Highway 42 Suite 220 Louisville KY 40222",
                    found="4965 US Hwy 42 Suite 220 Louisville KY 40222",
                    severity=Severity.info,
                    platform="Google Business",
                ),
            ],
        ),
        Platform(
            name="Yelp",
            url="https://yelp.com/biz/us-development-louisville",
            has_listing=True,
            accuracy_score=70.0,
            issues=[
                Inconsistency(
                    field="name",
                    expected="US Development",
                    found="US Development Group",
                    severity=Severity.warning,
                    platform="Yelp",
                ),
            ],
        ),
        Platform(
            name="Facebook",
            url="https://facebook.com/usdevelopment",
            has_listing=True,
            accuracy_score=92.0,
            issues=[],
        ),
        Platform(
            name="BBB",
            url="",
            has_listing=False,
            accuracy_score=0.0,
            issues=[
                Inconsistency(
                    field="listing",
                    expected="Active listing",
                    found="No listing found",
                    severity=Severity.critical,
                    platform="BBB",
                ),
            ],
        ),
        Platform(
            name="Angi",
            url="https://angi.com/us-development",
            has_listing=True,
            accuracy_score=68.0,
            issues=[
                Inconsistency(
                    field="address",
                    expected="4965 US Highway 42 Suite 220 Louisville KY 40222",
                    found="4965 Highway 42 Ste 220 Louisville KY 40222",
                    severity=Severity.warning,
                    platform="Angi",
                ),
            ],
        ),
    ],
}


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def _score_directory_results(platforms: List[Platform]) -> float:
    """
    Compute a directory health score 0-100.

    - Each directory is worth equal share of 100
    - Missing listing = 0 for that directory
    - Present listing = accuracy_score for that directory
    """
    if not platforms:
        return 0.0

    total_dirs = len(platforms)
    per_dir_weight = 100.0 / total_dirs
    score = 0.0

    for p in platforms:
        if p.has_listing and p.accuracy_score is not None:
            score += (p.accuracy_score / 100.0) * per_dir_weight
        # Missing listing contributes 0

    return round(score, 1)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def scan_directories(company_slug: str, demo: bool = True) -> BrandCheck:
    """
    Scan all configured directories for a company's listings.

    Parameters
    ----------
    company_slug : str
        Key from config.COMPANIES.
    demo : bool
        Use built-in demo data when True.

    Returns
    -------
    BrandCheck with score and platform details.
    """
    brand = get_company(company_slug)
    if brand is None:
        return BrandCheck(
            category=AuditCategory.directory,
            score=0,
            details=f"Unknown company: {company_slug}",
        )

    if brand.status == "coming_soon":
        return BrandCheck(
            category=AuditCategory.directory,
            score=0,
            details=f"{brand.official_name} is marked coming_soon; directory scan skipped.",
        )

    if demo:
        platforms = DEMO_DIRECTORY_RESULTS.get(company_slug, [])
    else:
        # Live scanning would go here
        platforms = []

    # Collect all issues
    all_issues: List[Inconsistency] = []
    for p in platforms:
        all_issues.extend(p.issues)

    score = _score_directory_results(platforms)

    listed_count = sum(1 for p in platforms if p.has_listing)
    total_count = len(platforms)
    critical_count = sum(1 for i in all_issues if i.severity == Severity.critical)
    warning_count = sum(1 for i in all_issues if i.severity == Severity.warning)

    details = (
        f"Directory scan for {brand.official_name}: "
        f"score {score:.0f}/100 "
        f"({listed_count}/{total_count} directories listed, "
        f"{critical_count} critical, {warning_count} warnings, "
        f"{len(all_issues)} total issues)"
    )

    return BrandCheck(
        category=AuditCategory.directory,
        score=score,
        details=details,
        inconsistencies=all_issues,
    )


def scan_all_directories(demo: bool = True) -> Dict[str, BrandCheck]:
    """Scan directories for every active company."""
    results: Dict[str, BrandCheck] = {}
    for slug in get_active_companies():
        results[slug] = scan_directories(slug, demo=demo)
    return results


def get_platforms(company_slug: str, demo: bool = True) -> List[Platform]:
    """Return the platform listing objects for a company (used by report generator)."""
    if demo:
        return DEMO_DIRECTORY_RESULTS.get(company_slug, [])
    return []
