"""
Brand Consistency Auditor - Remediation Engine
================================================
Generates actionable fix tasks with priority levels, effort estimates,
and step-by-step instructions. Output is JSON-compatible with Monday.com import.
"""

from __future__ import annotations

import json
from typing import Dict, List, Optional

from config import get_active_companies, get_company
from models import (
    AuditCategory,
    AuditReport,
    BrandCheck,
    Inconsistency,
    RemediationTask,
    Severity,
)
from report_generator import generate_report


# ---------------------------------------------------------------------------
# Task Generation from Inconsistencies
# ---------------------------------------------------------------------------

def _nap_remediation(company_slug: str, issues: List[Inconsistency]) -> List[RemediationTask]:
    """Generate remediation tasks for NAP inconsistencies."""
    tasks: List[RemediationTask] = []
    brand = get_company(company_slug)
    if not brand:
        return tasks

    # Group issues by platform
    platform_issues: Dict[str, List[Inconsistency]] = {}
    for issue in issues:
        if issue.platform:
            platform_issues.setdefault(issue.platform, []).append(issue)

    for platform, p_issues in platform_issues.items():
        has_critical = any(i.severity == Severity.critical for i in p_issues)
        name_issues = [i for i in p_issues if i.field == "name"]
        address_issues = [i for i in p_issues if i.field == "address"]
        phone_issues = [i for i in p_issues if i.field in ("phone", "phone_format")]

        steps: List[str] = []
        steps.append(f"Log in to {platform} business manager / owner portal.")

        if name_issues:
            steps.append(
                f"Update business name to exactly: '{brand.official_name}' "
                f"(currently showing: '{name_issues[0].found}')."
            )
        if address_issues:
            steps.append(
                f"Update address to: '{brand.address_line1}, {brand.address_line2}' "
                f"(currently showing: '{address_issues[0].found}')."
            )
        if phone_issues:
            steps.append(
                f"Update phone number to: '{brand.phone}' "
                f"(currently showing: '{phone_issues[0].found}')."
            )

        steps.append("Save changes and verify the listing displays correctly.")
        steps.append("Take a screenshot for documentation.")

        priority = "P1" if has_critical else "P2"
        effort = 15 if len(p_issues) <= 2 else 25

        field_names = sorted(set(i.field for i in p_issues))
        tasks.append(RemediationTask(
            priority=priority,
            effort_minutes=effort,
            description=(
                f"Fix {', '.join(field_names)} on {platform} for {brand.official_name}"
            ),
            steps=steps,
            company=company_slug,
            category=AuditCategory.nap,
            platform=platform,
        ))

    return tasks


def _visual_remediation(company_slug: str, issues: List[Inconsistency]) -> List[RemediationTask]:
    """Generate remediation tasks for visual identity issues."""
    tasks: List[RemediationTask] = []
    brand = get_company(company_slug)
    if not brand:
        return tasks

    # Missing fonts
    missing_fonts = [i for i in issues if i.field == "font_missing"]
    if missing_fonts:
        font_names = [i.expected for i in missing_fonts]
        tasks.append(RemediationTask(
            priority="P2",
            effort_minutes=30,
            description=f"Add missing brand fonts ({', '.join(font_names)}) to {brand.official_name} website",
            steps=[
                f"Open the website CSS / theme configuration for {brand.official_name}.",
                f"Add Google Fonts import for: {', '.join(font_names)}.",
                "Example: @import url('https://fonts.googleapis.com/css2?family=Playfair+Display:wght@400;700&family=Inter:wght@400;500;600&display=swap');",
                "Update heading selectors to use 'Playfair Display' as the primary font.",
                "Update body text selectors to use 'Inter' as the primary font.",
                "Verify font rendering across homepage, about, and service pages.",
                "Take before/after screenshots.",
            ],
            company=company_slug,
            category=AuditCategory.visual,
        ))

    # Off-brand colours
    off_brand = [i for i in issues if i.field == "off_brand_color"]
    if off_brand:
        colors = [i.found for i in off_brand]
        tasks.append(RemediationTask(
            priority="P3",
            effort_minutes=45,
            description=f"Replace {len(colors)} off-brand colour(s) on {brand.official_name} website",
            steps=[
                f"Search CSS files for the following off-brand hex values: {', '.join(colors)}.",
                f"Replace with appropriate brand palette colours:",
                f"  - Primary navy: #1B2A4A",
                f"  - Accent: {brand.accent_hex}",
                f"  - Neutrals: #FFFFFF, #F5F5F5, #333333",
                "Create a CSS custom properties file (:root variables) for brand colours.",
                "Update all colour references to use CSS variables.",
                "Verify visual appearance on key pages.",
            ],
            company=company_slug,
            category=AuditCategory.visual,
        ))

    # Extra (non-brand) fonts
    extra_fonts = [i for i in issues if i.field == "font_extra"]
    if extra_fonts:
        fonts = [i.found for i in extra_fonts]
        tasks.append(RemediationTask(
            priority="P3",
            effort_minutes=20,
            description=f"Remove non-brand fonts ({', '.join(fonts)}) from {brand.official_name} website",
            steps=[
                f"Search CSS for font-family declarations containing: {', '.join(fonts)}.",
                "Replace with the appropriate brand font:",
                "  - Headings: 'Playfair Display', serif",
                "  - Body: 'Inter', sans-serif",
                "Remove any unused @import or <link> tags for non-brand fonts.",
                "Verify font rendering across all pages.",
            ],
            company=company_slug,
            category=AuditCategory.visual,
        ))

    # Missing primary navy
    navy_missing = [i for i in issues if i.field == "primary_color"]
    if navy_missing:
        tasks.append(RemediationTask(
            priority="P1",
            effort_minutes=30,
            description=f"Add primary navy (#1B2A4A) to {brand.official_name} website",
            steps=[
                "Open the main CSS / theme file.",
                "Add #1B2A4A as the primary brand colour in CSS variables.",
                "Apply to: header background, footer background, primary text, CTA buttons.",
                "Ensure sufficient contrast with text elements (WCAG AA minimum).",
                "Verify across homepage, about, services, and contact pages.",
            ],
            company=company_slug,
            category=AuditCategory.visual,
        ))

    return tasks


def _voice_remediation(company_slug: str, issues: List[Inconsistency]) -> List[RemediationTask]:
    """Generate remediation tasks for voice/tone issues."""
    tasks: List[RemediationTask] = []
    brand = get_company(company_slug)
    if not brand:
        return tasks

    # Missing tagline
    tagline_issues = [i for i in issues if i.field == "tagline"]
    if tagline_issues and brand.tagline:
        tasks.append(RemediationTask(
            priority="P2",
            effort_minutes=15,
            description=f"Add brand tagline to {brand.official_name} website",
            steps=[
                f"Add the tagline '{brand.tagline}' to the website header or hero section.",
                "Ensure it appears on the homepage above the fold.",
                "Consider adding it to the meta description for SEO.",
                "Verify it renders correctly on desktop and mobile.",
            ],
            company=company_slug,
            category=AuditCategory.voice,
        ))

    # Low keyword coverage
    keyword_issues = [i for i in issues if i.field == "keyword_coverage"]
    if keyword_issues:
        tasks.append(RemediationTask(
            priority="P2",
            effort_minutes=60,
            description=f"Improve brand keyword density for {brand.official_name} website copy",
            steps=[
                f"Review the following brand keywords: {', '.join(brand.voice_keywords)}.",
                "Audit homepage, about page, and service pages for keyword usage.",
                "Naturally integrate missing keywords into page headings and body copy.",
                "Aim for at least 50% keyword coverage across main pages.",
                "Do not keyword-stuff; maintain natural, professional tone.",
                "Review and approve copy changes with marketing team.",
            ],
            company=company_slug,
            category=AuditCategory.voice,
        ))

    # Readability issues
    readability_issues = [i for i in issues if i.field == "readability"]
    if readability_issues:
        tasks.append(RemediationTask(
            priority="P3",
            effort_minutes=45,
            description=f"Adjust content readability for {brand.official_name}",
            steps=[
                "Target Grade 8-12 reading level for B2B construction audience.",
                "Shorten sentences longer than 25 words.",
                "Replace jargon with clear, industry-standard terms.",
                "Use active voice and concrete examples.",
                "Re-test readability after edits using Flesch-Kincaid.",
            ],
            company=company_slug,
            category=AuditCategory.voice,
        ))

    # Low tone scores
    tone_issues = [i for i in issues if i.field.startswith("tone_")]
    if tone_issues:
        dimensions = [i.field.replace("tone_", "") for i in tone_issues]
        tasks.append(RemediationTask(
            priority="P3",
            effort_minutes=30,
            description=f"Strengthen {', '.join(dimensions)} tone for {brand.official_name}",
            steps=[
                f"Low scores detected in: {', '.join(dimensions)}.",
                "Review website copy for tone alignment.",
                "Professional: Use industry terms, cite certifications, reference project scale.",
                "Authoritative: Include stats, leadership claims, track record evidence.",
                "Approachable: Add partnership language, team references, client testimonials.",
                "Apply changes to homepage, about page, and service pages.",
            ],
            company=company_slug,
            category=AuditCategory.voice,
        ))

    return tasks


def _directory_remediation(company_slug: str, issues: List[Inconsistency]) -> List[RemediationTask]:
    """Generate remediation tasks for directory listing issues."""
    tasks: List[RemediationTask] = []
    brand = get_company(company_slug)
    if not brand:
        return tasks

    # Missing listings
    missing = [i for i in issues if i.field == "listing" and i.severity == Severity.critical]
    for m in missing:
        tasks.append(RemediationTask(
            priority="P1",
            effort_minutes=30,
            description=f"Create {m.platform} listing for {brand.official_name}",
            steps=[
                f"Go to {m.platform} and create a new business listing.",
                f"Business Name: {brand.official_name}",
                f"Address: {brand.address_line1}, {brand.address_line2}",
                f"Phone: {brand.phone}",
                "Upload brand-consistent logo and cover photo.",
                "Add business description using brand tagline and voice keywords.",
                "Select appropriate business categories.",
                "Verify ownership if required.",
                "Take a screenshot of the completed listing.",
            ],
            company=company_slug,
            category=AuditCategory.directory,
            platform=m.platform,
        ))

    return tasks


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def generate_remediation(company_slug: str, demo: bool = True) -> List[RemediationTask]:
    """
    Generate all remediation tasks for a company based on a full audit.

    Parameters
    ----------
    company_slug : str
        Key from config.COMPANIES.
    demo : bool
        Use demo data for the underlying audit.

    Returns
    -------
    List of RemediationTask sorted by priority.
    """
    report = generate_report(company_slug, demo=demo)
    return generate_remediation_from_report(report)


def generate_remediation_from_report(report: AuditReport) -> List[RemediationTask]:
    """
    Generate remediation tasks from an existing AuditReport.

    Returns
    -------
    List of RemediationTask sorted by priority.
    """
    all_tasks: List[RemediationTask] = []

    for section_key, check in report.sections.items():
        issues = check.inconsistencies
        if check.category == AuditCategory.nap:
            all_tasks.extend(_nap_remediation(report.company, issues))
        elif check.category == AuditCategory.visual:
            all_tasks.extend(_visual_remediation(report.company, issues))
        elif check.category == AuditCategory.voice:
            all_tasks.extend(_voice_remediation(report.company, issues))
        elif check.category == AuditCategory.directory:
            all_tasks.extend(_directory_remediation(report.company, issues))

    # Sort: P1 first, then P2, then P3
    priority_order = {"P1": 0, "P2": 1, "P3": 2}
    all_tasks.sort(key=lambda t: priority_order.get(t.priority, 9))

    return all_tasks


def generate_all_remediation(demo: bool = True) -> Dict[str, List[RemediationTask]]:
    """Generate remediation tasks for all active companies."""
    results: Dict[str, List[RemediationTask]] = {}
    for slug in get_active_companies():
        results[slug] = generate_remediation(slug, demo=demo)
    return results


def export_remediation_json(
    tasks: List[RemediationTask],
    filepath: Optional[str] = None,
) -> str:
    """
    Serialise remediation tasks to JSON (Monday.com-compatible format).

    Parameters
    ----------
    tasks : list
        Tasks to serialise.
    filepath : str, optional
        If provided, write JSON to this file.

    Returns
    -------
    JSON string.
    """
    monday_items = []
    for idx, task in enumerate(tasks, 1):
        monday_items.append({
            "id": idx,
            "name": task.description,
            "group": f"{task.category.value}_fixes",
            "column_values": {
                "priority": {"label": task.priority},
                "status": {"label": "To Do"},
                "effort_minutes": task.effort_minutes,
                "company": task.company,
                "platform": task.platform,
                "category": task.category.value,
            },
            "subitems": [
                {"name": step} for step in task.steps
            ],
        })

    data = {
        "board_name": "Brand Consistency Remediation",
        "items": monday_items,
        "total_tasks": len(tasks),
        "total_effort_minutes": sum(t.effort_minutes for t in tasks),
        "priority_breakdown": {
            "P1": sum(1 for t in tasks if t.priority == "P1"),
            "P2": sum(1 for t in tasks if t.priority == "P2"),
            "P3": sum(1 for t in tasks if t.priority == "P3"),
        },
    }

    json_str = json.dumps(data, indent=2)

    if filepath:
        with open(filepath, "w") as f:
            f.write(json_str)

    return json_str


def print_remediation_summary(tasks: List[RemediationTask]) -> str:
    """
    Produce a human-readable summary of remediation tasks.

    Returns the formatted string.
    """
    lines: List[str] = []
    lines.append("=" * 70)
    lines.append("  REMEDIATION PLAN")
    lines.append("=" * 70)
    lines.append("")

    p1 = [t for t in tasks if t.priority == "P1"]
    p2 = [t for t in tasks if t.priority == "P2"]
    p3 = [t for t in tasks if t.priority == "P3"]

    lines.append(f"  Total Tasks: {len(tasks)}")
    lines.append(f"  Total Effort: {sum(t.effort_minutes for t in tasks)} minutes")
    lines.append(f"  P1 (Critical): {len(p1)}  |  P2 (Important): {len(p2)}  |  P3 (Minor): {len(p3)}")
    lines.append("")

    for priority_label, priority_tasks in [("P1 - CRITICAL", p1), ("P2 - IMPORTANT", p2), ("P3 - MINOR", p3)]:
        if priority_tasks:
            lines.append(f"  --- {priority_label} ---")
            for idx, task in enumerate(priority_tasks, 1):
                lines.append(f"    {idx}. [{task.effort_minutes}min] {task.description}")
                for step_idx, step in enumerate(task.steps, 1):
                    lines.append(f"       {step_idx}. {step}")
                lines.append("")

    lines.append("=" * 70)

    return "\n".join(lines)
