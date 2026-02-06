"""
Brand Consistency Auditor - CLI
================================
Click-based command-line interface for running brand audits,
scanning directories, generating reports, and creating remediation plans.

Usage:
    python main.py full-audit --demo
    python main.py audit-nap --company us_framing --demo
    python main.py audit-visual --demo
    python main.py audit-voice --company us_drywall --demo
    python main.py scan-directories --demo
    python main.py generate-report --company us_framing --demo --output report.json
    python main.py remediate --demo --output tasks.json
    python main.py status
"""

from __future__ import annotations

import json
import sys
from typing import Optional

import click

from config import COMPANIES, SCORING_WEIGHTS, get_active_companies, get_company, company_slugs
from directory_scanner import scan_all_directories, scan_directories
from models import AuditCategory, Severity
from nap_auditor import audit_all_nap, audit_nap
from remediation_engine import (
    export_remediation_json,
    generate_all_remediation,
    generate_remediation,
    print_remediation_summary,
)
from report_generator import (
    export_report_json,
    generate_all_reports,
    generate_report,
    print_report_summary,
)
from visual_auditor import audit_all_visual, audit_visual
from voice_auditor import audit_all_voice, audit_voice


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _resolve_companies(company: Optional[str]):
    """Return a list of company slugs to process."""
    if company:
        if company not in COMPANIES:
            click.echo(f"Error: Unknown company '{company}'. Valid: {', '.join(company_slugs())}")
            sys.exit(1)
        return [company]
    return list(get_active_companies().keys())


def _print_check(slug: str, check):
    """Pretty-print a BrandCheck result."""
    brand = get_company(slug)
    name = brand.official_name if brand else slug

    severity_counts = {}
    for i in check.inconsistencies:
        severity_counts[i.severity.value] = severity_counts.get(i.severity.value, 0) + 1

    bar_filled = int(check.score / 5)
    bar = "#" * bar_filled + "-" * (20 - bar_filled)

    click.echo(f"  {name:20s}  {check.score:5.1f}/100  [{bar}]", nl=False)
    if severity_counts:
        parts = [f"{v} {k}" for k, v in severity_counts.items()]
        click.echo(f"  ({', '.join(parts)})")
    else:
        click.echo("  (clean)")


# ---------------------------------------------------------------------------
# CLI Group
# ---------------------------------------------------------------------------

@click.group()
@click.version_option(version="1.0.0", prog_name="brand-auditor")
def cli():
    """Brand Consistency Auditor for US Construction Marketing.

    Audit NAP data, visual identity, voice/tone, and directory listings
    across the US Construction family of companies.
    """
    pass


# ---------------------------------------------------------------------------
# audit-nap
# ---------------------------------------------------------------------------

@cli.command("audit-nap")
@click.option("--company", "-c", default=None, help="Company slug (e.g. us_framing). Omit for all.")
@click.option("--demo/--live", default=True, help="Use demo data (default) or live scraping.")
@click.option("--verbose", "-v", is_flag=True, help="Show individual issues.")
def audit_nap_cmd(company: Optional[str], demo: bool, verbose: bool):
    """Audit Name-Address-Phone consistency across platforms."""
    slugs = _resolve_companies(company)

    click.echo("")
    click.echo("=" * 60)
    click.echo("  NAP CONSISTENCY AUDIT")
    click.echo("=" * 60)
    click.echo("")

    for slug in slugs:
        result = audit_nap(slug, demo=demo)
        _print_check(slug, result)

        if verbose and result.inconsistencies:
            for issue in result.inconsistencies:
                sev_marker = {"critical": "!!!", "warning": " ! ", "info": " . "}
                marker = sev_marker.get(issue.severity.value, "   ")
                click.echo(f"    {marker} [{issue.platform}] {issue.field}: "
                           f"expected '{issue.expected}' | found '{issue.found}'")
            click.echo("")

    click.echo("")


# ---------------------------------------------------------------------------
# audit-visual
# ---------------------------------------------------------------------------

@cli.command("audit-visual")
@click.option("--company", "-c", default=None, help="Company slug. Omit for all.")
@click.option("--demo/--live", default=True, help="Use demo data (default).")
@click.option("--verbose", "-v", is_flag=True, help="Show individual issues.")
def audit_visual_cmd(company: Optional[str], demo: bool, verbose: bool):
    """Audit visual identity: colours, fonts, brand palette."""
    slugs = _resolve_companies(company)

    click.echo("")
    click.echo("=" * 60)
    click.echo("  VISUAL IDENTITY AUDIT")
    click.echo("=" * 60)
    click.echo("")

    for slug in slugs:
        result = audit_visual(slug, demo=demo)
        _print_check(slug, result)

        if verbose and result.inconsistencies:
            for issue in result.inconsistencies:
                click.echo(f"      {issue.field}: expected '{issue.expected}' | found '{issue.found}'")
            click.echo("")

    click.echo("")


# ---------------------------------------------------------------------------
# audit-voice
# ---------------------------------------------------------------------------

@cli.command("audit-voice")
@click.option("--company", "-c", default=None, help="Company slug. Omit for all.")
@click.option("--demo/--live", default=True, help="Use demo data (default).")
@click.option("--verbose", "-v", is_flag=True, help="Show individual issues.")
def audit_voice_cmd(company: Optional[str], demo: bool, verbose: bool):
    """Audit voice, tone, readability, and keyword usage."""
    slugs = _resolve_companies(company)

    click.echo("")
    click.echo("=" * 60)
    click.echo("  VOICE & TONE AUDIT")
    click.echo("=" * 60)
    click.echo("")

    for slug in slugs:
        result = audit_voice(slug, demo=demo)
        _print_check(slug, result)

        if verbose and result.inconsistencies:
            for issue in result.inconsistencies:
                click.echo(f"      {issue.field}: expected '{issue.expected}' | found '{issue.found}'")
            click.echo("")

    click.echo("")


# ---------------------------------------------------------------------------
# scan-directories
# ---------------------------------------------------------------------------

@cli.command("scan-directories")
@click.option("--company", "-c", default=None, help="Company slug. Omit for all.")
@click.option("--demo/--live", default=True, help="Use demo data (default).")
@click.option("--verbose", "-v", is_flag=True, help="Show individual platform details.")
def scan_directories_cmd(company: Optional[str], demo: bool, verbose: bool):
    """Scan business directories for listing presence and accuracy."""
    slugs = _resolve_companies(company)

    click.echo("")
    click.echo("=" * 60)
    click.echo("  DIRECTORY LISTING SCAN")
    click.echo("=" * 60)
    click.echo("")

    for slug in slugs:
        result = scan_directories(slug, demo=demo)
        _print_check(slug, result)

        if verbose and result.inconsistencies:
            for issue in result.inconsistencies:
                sev_marker = {"critical": "!!!", "warning": " ! ", "info": " . "}
                marker = sev_marker.get(issue.severity.value, "   ")
                click.echo(f"    {marker} [{issue.platform}] {issue.field}: {issue.found}")
            click.echo("")

    click.echo("")


# ---------------------------------------------------------------------------
# full-audit
# ---------------------------------------------------------------------------

@cli.command("full-audit")
@click.option("--company", "-c", default=None, help="Company slug. Omit for all.")
@click.option("--demo/--live", default=True, help="Use demo data (default).")
@click.option("--output", "-o", default=None, help="Output JSON file path.")
def full_audit_cmd(company: Optional[str], demo: bool, output: Optional[str]):
    """Run a complete brand consistency audit (all categories)."""
    slugs = _resolve_companies(company)

    click.echo("")
    click.echo("=" * 60)
    click.echo("  FULL BRAND CONSISTENCY AUDIT")
    click.echo("=" * 60)
    click.echo("")

    for slug in slugs:
        report = generate_report(slug, demo=demo)
        click.echo(print_report_summary(report))
        click.echo("")

        if output and len(slugs) == 1:
            export_report_json(report, output)
            click.echo(f"  Report exported to: {output}")
            click.echo("")


# ---------------------------------------------------------------------------
# generate-report
# ---------------------------------------------------------------------------

@cli.command("generate-report")
@click.option("--company", "-c", default=None, help="Company slug. Omit for all.")
@click.option("--demo/--live", default=True, help="Use demo data (default).")
@click.option("--output", "-o", default=None, help="Output JSON file path.")
def generate_report_cmd(company: Optional[str], demo: bool, output: Optional[str]):
    """Generate a comprehensive brand health report."""
    slugs = _resolve_companies(company)

    for slug in slugs:
        report = generate_report(slug, demo=demo)
        click.echo(print_report_summary(report))

        if output:
            if len(slugs) == 1:
                filepath = output
            else:
                filepath = output.replace(".json", f"_{slug}.json")

            export_report_json(report, filepath)
            click.echo(f"  Exported to: {filepath}")

        click.echo("")


# ---------------------------------------------------------------------------
# remediate
# ---------------------------------------------------------------------------

@cli.command("remediate")
@click.option("--company", "-c", default=None, help="Company slug. Omit for all.")
@click.option("--demo/--live", default=True, help="Use demo data (default).")
@click.option("--output", "-o", default=None, help="Output JSON file path (Monday.com format).")
def remediate_cmd(company: Optional[str], demo: bool, output: Optional[str]):
    """Generate remediation tasks with priorities and step-by-step instructions."""
    slugs = _resolve_companies(company)

    all_tasks = []
    for slug in slugs:
        tasks = generate_remediation(slug, demo=demo)
        all_tasks.extend(tasks)
        click.echo(print_remediation_summary(tasks))
        click.echo("")

    if output:
        export_remediation_json(all_tasks, output)
        click.echo(f"  Remediation plan exported to: {output}")
        click.echo(f"  Total tasks: {len(all_tasks)}")
        click.echo(f"  Total effort: {sum(t.effort_minutes for t in all_tasks)} minutes")
        click.echo("")


# ---------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------

@cli.command("status")
def status_cmd():
    """Show registered companies and audit configuration."""
    click.echo("")
    click.echo("=" * 60)
    click.echo("  BRAND AUDITOR STATUS")
    click.echo("=" * 60)
    click.echo("")

    click.echo("  REGISTERED COMPANIES:")
    click.echo("  " + "-" * 50)
    for slug, brand in COMPANIES.items():
        status_label = "ACTIVE" if brand.status == "active" else "COMING SOON"
        click.echo(f"    {brand.official_name:20s}  [{slug:16s}]  {status_label}")
        if brand.status == "active":
            click.echo(f"      Accent: {brand.accent_hex}  |  Phone: {brand.phone}")
            addr = f"{brand.address_line1}, {brand.address_line2}" if brand.address_line1 else "N/A"
            click.echo(f"      Address: {addr}")
        click.echo("")

    click.echo("  SCORING WEIGHTS:")
    click.echo("  " + "-" * 50)
    for category, weight in SCORING_WEIGHTS.items():
        click.echo(f"    {category.upper():12s}  {weight}%")
    click.echo("")

    click.echo("  DIRECTORIES MONITORED:")
    click.echo("  " + "-" * 50)
    from config import DIRECTORIES
    for d in DIRECTORIES:
        click.echo(f"    - {d}")
    click.echo("")

    click.echo("  FUZZY MATCH THRESHOLD: 0.85")
    click.echo("")
    click.echo("=" * 60)


# ---------------------------------------------------------------------------
# Entry Point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    cli()
