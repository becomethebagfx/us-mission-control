"""
Brand Consistency Auditor - Report Generator
==============================================
Produces comprehensive brand health reports with weighted scoring,
section breakdowns, recommendations, and JSON export.
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional

from config import COMPANIES, SCORING_WEIGHTS, get_active_companies, get_company
from directory_scanner import get_platforms, scan_directories
from models import (
    AuditCategory,
    AuditReport,
    BrandCheck,
    Inconsistency,
    Severity,
)
from nap_auditor import audit_nap
from visual_auditor import audit_visual
from voice_auditor import audit_voice


# ---------------------------------------------------------------------------
# Recommendation Engine
# ---------------------------------------------------------------------------

def _generate_recommendations(sections: Dict[str, BrandCheck]) -> List[str]:
    """
    Analyse section scores and inconsistencies to produce
    prioritised, actionable recommendations.
    """
    recommendations: List[str] = []

    # NAP recommendations
    nap = sections.get("nap")
    if nap:
        critical_nap = [i for i in nap.inconsistencies if i.severity == Severity.critical]
        warning_nap = [i for i in nap.inconsistencies if i.severity == Severity.warning]

        if critical_nap:
            platforms_affected = sorted(set(i.platform for i in critical_nap if i.platform))
            recommendations.append(
                f"URGENT: Fix critical NAP inconsistencies on {', '.join(platforms_affected)}. "
                f"Incorrect business name or phone number directly harms local SEO rankings."
            )

        name_warnings = [i for i in warning_nap if i.field == "name"]
        if name_warnings:
            variants = sorted(set(i.found for i in name_warnings))
            recommendations.append(
                f"Standardise business name across directories. Found variants: "
                f"{', '.join(repr(v) for v in variants)}. "
                f"Use the exact official name without LLC/Inc suffixes or periods."
            )

        phone_format_issues = [i for i in nap.inconsistencies if i.field == "phone_format"]
        if phone_format_issues:
            recommendations.append(
                "Standardise phone number format to (XXX) XXX-XXXX across all platforms."
            )

        if nap.score < 70:
            recommendations.append(
                "NAP score is below 70. Consider a dedicated NAP cleanup sprint: "
                "update all directory listings to match brand standards exactly."
            )

    # Visual recommendations
    visual = sections.get("visual")
    if visual:
        color_issues = [i for i in visual.inconsistencies if "color" in i.field]
        font_issues = [i for i in visual.inconsistencies if "font" in i.field]

        missing_fonts = [i for i in font_issues if i.field == "font_missing"]
        if missing_fonts:
            fonts = [i.expected for i in missing_fonts]
            recommendations.append(
                f"Add missing brand fonts to website: {', '.join(fonts)}. "
                f"Import via Google Fonts or self-host for consistency."
            )

        off_brand = [i for i in color_issues if i.field == "off_brand_color"]
        if off_brand:
            colors = [i.found for i in off_brand]
            recommendations.append(
                f"Replace off-brand colours ({', '.join(colors)}) with approved palette. "
                f"Create a CSS variables file with brand colours for easy maintenance."
            )

        if visual.score < 70:
            recommendations.append(
                "Visual identity score is below 70. Conduct a full CSS audit to enforce "
                "brand colour palette and font family standards across all pages."
            )

    # Voice recommendations
    voice = sections.get("voice")
    if voice:
        keyword_issues = [i for i in voice.inconsistencies if i.field == "keyword_coverage"]
        tagline_issues = [i for i in voice.inconsistencies if i.field == "tagline"]
        readability_issues = [i for i in voice.inconsistencies if i.field == "readability"]

        if tagline_issues:
            recommendations.append(
                "Add the official brand tagline to the website header or hero section. "
                "Consistent tagline usage reinforces brand positioning."
            )

        if keyword_issues:
            recommendations.append(
                "Increase brand keyword density in website copy. "
                "Ensure core service terms and differentiators appear naturally in page content."
            )

        if readability_issues:
            recommendations.append(
                "Adjust content readability to Grade 8-12 level for B2B audience. "
                "Avoid overly complex or overly simplified language."
            )

    # Directory recommendations
    directory = sections.get("directory")
    if directory:
        missing_listings = [
            i for i in directory.inconsistencies
            if i.field == "listing" and i.severity == Severity.critical
        ]
        if missing_listings:
            platforms = sorted(set(i.platform for i in missing_listings))
            recommendations.append(
                f"Create business listings on: {', '.join(platforms)}. "
                f"Missing directory listings reduce online visibility and local SEO authority."
            )

        if directory.score < 70:
            recommendations.append(
                "Directory presence score is below 70. Prioritise claiming and verifying "
                "business listings across all major directories."
            )

    # Sort by urgency (URGENT first)
    recommendations.sort(key=lambda r: (0 if r.startswith("URGENT") else 1, r))

    return recommendations


# ---------------------------------------------------------------------------
# Score Calculation
# ---------------------------------------------------------------------------

def _weighted_score(sections: Dict[str, BrandCheck]) -> float:
    """
    Calculate the overall weighted score from section scores.
    Uses weights from config.SCORING_WEIGHTS.
    """
    category_to_key = {
        AuditCategory.nap: "nap",
        AuditCategory.visual: "visual",
        AuditCategory.voice: "voice",
        AuditCategory.directory: "directories",
    }

    total = 0.0
    weight_sum = 0

    for section_key, check in sections.items():
        weight_key = category_to_key.get(check.category, section_key)
        weight = SCORING_WEIGHTS.get(weight_key, 0)
        total += check.score * weight
        weight_sum += weight

    if weight_sum == 0:
        return 0.0

    return round(total / weight_sum, 1)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_report(company_slug: str, demo: bool = True) -> AuditReport:
    """
    Run all audits and produce a comprehensive brand health report.

    Parameters
    ----------
    company_slug : str
        Key from config.COMPANIES.
    demo : bool
        Use demo data for all sub-auditors.

    Returns
    -------
    AuditReport with overall score, sections, issues, and recommendations.
    """
    brand = get_company(company_slug)
    if brand is None:
        return AuditReport(
            company=company_slug,
            overall_score=0,
            recommendations=[f"Unknown company: {company_slug}"],
            audit_timestamp=datetime.now(timezone.utc).isoformat(),
        )

    # Run all audits
    nap_result = audit_nap(company_slug, demo=demo)
    visual_result = audit_visual(company_slug, demo=demo)
    voice_result = audit_voice(company_slug, demo=demo)
    directory_result = scan_directories(company_slug, demo=demo)

    sections = {
        "nap": nap_result,
        "visual": visual_result,
        "voice": voice_result,
        "directory": directory_result,
    }

    # Collect all issues
    all_issues: List[Inconsistency] = []
    for check in sections.values():
        all_issues.extend(check.inconsistencies)

    # Calculate weighted score
    overall = _weighted_score(sections)

    # Generate recommendations
    recs = _generate_recommendations(sections)

    # Get platform data
    platforms = get_platforms(company_slug, demo=demo)

    return AuditReport(
        company=company_slug,
        company_name=brand.official_name,
        overall_score=overall,
        sections=sections,
        issues=all_issues,
        recommendations=recs,
        platforms=platforms,
        audit_timestamp=datetime.now(timezone.utc).isoformat(),
    )


def generate_all_reports(demo: bool = True) -> Dict[str, AuditReport]:
    """Generate reports for all active companies."""
    reports: Dict[str, AuditReport] = {}
    for slug in get_active_companies():
        reports[slug] = generate_report(slug, demo=demo)
    return reports


def export_report_json(report: AuditReport, filepath: Optional[str] = None) -> str:
    """
    Serialise an AuditReport to JSON.

    Parameters
    ----------
    report : AuditReport
        The report to serialise.
    filepath : str, optional
        If provided, write JSON to this file path.

    Returns
    -------
    JSON string.
    """
    data = report.model_dump(mode="json")
    json_str = json.dumps(data, indent=2, default=str)

    if filepath:
        with open(filepath, "w") as f:
            f.write(json_str)

    return json_str


def print_report_summary(report: AuditReport) -> str:
    """
    Produce a human-readable summary of an audit report.

    Returns the formatted string (also suitable for terminal output).
    """
    lines: List[str] = []
    lines.append("=" * 70)
    lines.append(f"  BRAND CONSISTENCY AUDIT: {report.company_name or report.company}")
    lines.append(f"  Timestamp: {report.audit_timestamp}")
    lines.append("=" * 70)
    lines.append("")

    # Overall score with visual bar
    bar_filled = int(report.overall_score / 5)
    bar_empty = 20 - bar_filled
    bar = "#" * bar_filled + "-" * bar_empty
    grade = _score_grade(report.overall_score)
    lines.append(f"  OVERALL SCORE: {report.overall_score:.0f}/100  [{bar}]  Grade: {grade}")
    lines.append("")

    # Section scores
    lines.append("  SECTION SCORES:")
    lines.append("  " + "-" * 50)
    for key, check in report.sections.items():
        section_bar_filled = int(check.score / 5)
        section_bar = "#" * section_bar_filled + "-" * (20 - section_bar_filled)
        lines.append(f"    {key.upper():12s}  {check.score:5.1f}/100  [{section_bar}]")
    lines.append("")

    # Issues summary
    critical = sum(1 for i in report.issues if i.severity == Severity.critical)
    warnings = sum(1 for i in report.issues if i.severity == Severity.warning)
    infos = sum(1 for i in report.issues if i.severity == Severity.info)
    lines.append(f"  ISSUES: {len(report.issues)} total")
    lines.append(f"    Critical: {critical}  |  Warnings: {warnings}  |  Info: {infos}")
    lines.append("")

    # Platform listing status
    if report.platforms:
        lines.append("  DIRECTORY LISTINGS:")
        lines.append("  " + "-" * 50)
        for p in report.platforms:
            status = "LISTED" if p.has_listing else "MISSING"
            acc = f"{p.accuracy_score:.0f}%" if p.accuracy_score and p.has_listing else "N/A"
            lines.append(f"    {p.name:20s}  {status:8s}  Accuracy: {acc}")
        lines.append("")

    # Recommendations
    if report.recommendations:
        lines.append("  RECOMMENDATIONS:")
        lines.append("  " + "-" * 50)
        for idx, rec in enumerate(report.recommendations, 1):
            lines.append(f"    {idx}. {rec}")
        lines.append("")

    lines.append("=" * 70)

    return "\n".join(lines)


def _score_grade(score: float) -> str:
    """Map a numeric score to a letter grade."""
    if score >= 90:
        return "A"
    elif score >= 80:
        return "B"
    elif score >= 70:
        return "C"
    elif score >= 60:
        return "D"
    else:
        return "F"
