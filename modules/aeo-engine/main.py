"""
AEO/GEO Content Engine -- CLI

Command-line interface for the AEO/GEO Content Engine.
Provides commands for query research, capsule generation, FAQ generation,
schema generation, page optimization, and citation monitoring.

Usage:
    python main.py --help
    python main.py research-queries --demo --company us_framing
    python main.py generate-capsules --demo
    python main.py generate-faq --demo --company us_drywall
    python main.py generate-schema --company us_framing
    python main.py optimize-pages --demo
    python main.py monitor-citations --company us_framing
    python main.py status
"""

from __future__ import annotations

import json
import sys
from typing import Optional

import click

from config import COMPANIES, TARGET_QUERIES, get_company, get_active_companies
from models import SchemaType


# ---------------------------------------------------------------------------
# CLI Group
# ---------------------------------------------------------------------------
@click.group()
@click.option("--demo", is_flag=True, default=False, help="Use demo data instead of AI")
@click.option(
    "--company",
    type=click.Choice(list(COMPANIES.keys()) + ["all"], case_sensitive=False),
    default="all",
    help="Filter to a specific company or 'all'",
)
@click.pass_context
def cli(ctx: click.Context, demo: bool, company: str) -> None:
    """AEO/GEO Content Engine for US Construction Marketing.

    Generates answer capsules, FAQ sets, schema markup, and monitors
    AI citation visibility for the US Construction family of companies.
    """
    ctx.ensure_object(dict)
    ctx.obj["demo"] = demo
    ctx.obj["company"] = company


# ---------------------------------------------------------------------------
# research-queries
# ---------------------------------------------------------------------------
@cli.command("research-queries")
@click.pass_context
def research_queries_cmd(ctx: click.Context) -> None:
    """Discover and rank target queries by search intent."""
    from query_researcher import research_queries

    demo = ctx.obj["demo"]
    company_filter = ctx.obj["company"]

    slugs = _resolve_company_slugs(company_filter)
    total = 0

    for slug in slugs:
        company = get_company(slug)
        click.echo(f"\n{'='*60}")
        click.echo(f"  {company.name} -- Query Research")
        click.echo(f"{'='*60}")

        queries = research_queries(slug, demo=demo)
        for q in queries:
            click.echo(
                f"  [{q.priority:2d}] [{q.intent.value:15s}] {q.query}"
            )
        click.echo(f"  Total: {len(queries)} queries discovered")
        total += len(queries)

    click.echo(f"\nGrand total: {total} queries across {len(slugs)} companies")


# ---------------------------------------------------------------------------
# generate-capsules
# ---------------------------------------------------------------------------
@cli.command("generate-capsules")
@click.pass_context
def generate_capsules_cmd(ctx: click.Context) -> None:
    """Generate 40-60 word answer capsules for target queries."""
    from capsule_generator import generate_capsules

    demo = ctx.obj["demo"]
    company_filter = ctx.obj["company"]

    slugs = _resolve_company_slugs(company_filter)

    for slug in slugs:
        company = get_company(slug)
        click.echo(f"\n{'='*60}")
        click.echo(f"  {company.name} -- Answer Capsules")
        click.echo(f"{'='*60}")

        batch = generate_capsules(slug, demo=demo)
        for capsule in batch.capsules:
            click.echo(f"\n  Query: {capsule.query}")
            click.echo(f"  Words: {capsule.word_count}")
            click.echo(f"  Capsule: {capsule.content}")
            click.echo(f"  Source: {capsule.source_attribution}")

        if batch.errors:
            click.echo(f"\n  Errors ({len(batch.errors)}):")
            for err in batch.errors:
                click.echo(f"    - {err}")

        click.echo(f"\n  Generated: {len(batch.capsules)} capsules, {len(batch.errors)} errors")


# ---------------------------------------------------------------------------
# generate-faq
# ---------------------------------------------------------------------------
@cli.command("generate-faq")
@click.option("--schema", "include_schema", is_flag=True, help="Include FAQPage JSON-LD output")
@click.pass_context
def generate_faq_cmd(ctx: click.Context, include_schema: bool) -> None:
    """Generate FAQ sets per service/company."""
    from faq_generator import generate_faqs, generate_faq_schema

    demo = ctx.obj["demo"]
    company_filter = ctx.obj["company"]

    slugs = _resolve_company_slugs(company_filter)

    for slug in slugs:
        company = get_company(slug)
        click.echo(f"\n{'='*60}")
        click.echo(f"  {company.name} -- FAQ Sets")
        click.echo(f"{'='*60}")

        batch = generate_faqs(slug, demo=demo)
        for faq_set in batch.faq_sets:
            click.echo(f"\n  Service: {faq_set.service}")
            click.echo(f"  Q&A Pairs: {len(faq_set.pairs)}")
            for i, pair in enumerate(faq_set.pairs, 1):
                click.echo(f"\n    Q{i}: {pair.question}")
                click.echo(f"    A{i}: {pair.answer}")

            if include_schema:
                schema = generate_faq_schema(faq_set)
                click.echo(f"\n  FAQPage JSON-LD:")
                click.echo(json.dumps(schema.json_ld, indent=2))

        if batch.errors:
            click.echo(f"\n  Errors ({len(batch.errors)}):")
            for err in batch.errors:
                click.echo(f"    - {err}")

        click.echo(f"\n  Generated: {len(batch.faq_sets)} FAQ sets")


# ---------------------------------------------------------------------------
# generate-schema
# ---------------------------------------------------------------------------
@cli.command("generate-schema")
@click.option(
    "--type",
    "schema_type",
    type=click.Choice([t.value for t in SchemaType], case_sensitive=False),
    default=None,
    help="Generate only a specific schema type",
)
@click.pass_context
def generate_schema_cmd(ctx: click.Context, schema_type: Optional[str]) -> None:
    """Generate JSON-LD schema markup for companies."""
    from schema_generator import generate_all_schemas, validate_json_ld, render_json_ld_script_tag

    company_filter = ctx.obj["company"]
    slugs = _resolve_company_slugs(company_filter)

    for slug in slugs:
        company = get_company(slug)
        click.echo(f"\n{'='*60}")
        click.echo(f"  {company.name} -- Schema Markup")
        click.echo(f"{'='*60}")

        batch = generate_all_schemas(slug)

        for schema in batch.schemas:
            if schema_type and schema.schema_type.value != schema_type:
                continue

            # Validate
            issues = validate_json_ld(schema)
            status = "VALID" if not issues else "ISSUES"

            click.echo(f"\n  Type: {schema.schema_type.value} [{status}]")

            if issues:
                for issue in issues:
                    click.echo(f"    Issue: {issue}")

            click.echo(render_json_ld_script_tag(schema))

        if batch.errors:
            click.echo(f"\n  Errors ({len(batch.errors)}):")
            for err in batch.errors:
                click.echo(f"    - {err}")

        click.echo(f"\n  Generated: {len(batch.schemas)} schemas")


# ---------------------------------------------------------------------------
# optimize-pages
# ---------------------------------------------------------------------------
@cli.command("optimize-pages")
@click.pass_context
def optimize_pages_cmd(ctx: click.Context) -> None:
    """Analyze HTML pages and score AEO readiness."""
    from page_optimizer import optimize_page_demo, optimize_page

    demo = ctx.obj["demo"]

    click.echo(f"\n{'='*60}")
    click.echo(f"  Page Optimizer -- AEO Readiness Analysis")
    click.echo(f"{'='*60}")

    if demo:
        results = optimize_page_demo()
    else:
        click.echo("  Live page analysis requires page URLs. Using demo mode.")
        results = optimize_page_demo()

    for result in results:
        click.echo(f"\n  Page: {result.page_url}")
        click.echo(f"  Overall Score: {result.score}/100")
        click.echo(f"  Breakdown:")
        for category, score in result.breakdown.items():
            click.echo(f"    {category:25s}: {score:3d}/100")

        if result.issues:
            click.echo(f"\n  Issues ({len(result.issues)}):")
            for issue in result.issues:
                click.echo(f"    [{issue.severity.upper():8s}] {issue.message}")

        if result.recommendations:
            click.echo(f"\n  Recommendations:")
            for i, rec in enumerate(result.recommendations, 1):
                click.echo(f"    {i}. {rec}")


# ---------------------------------------------------------------------------
# monitor-citations
# ---------------------------------------------------------------------------
@cli.command("monitor-citations")
@click.option(
    "--platform",
    type=click.Choice(["ChatGPT", "Perplexity", "Gemini", "Claude", "all"]),
    default="all",
    help="Filter to a specific AI platform",
)
@click.pass_context
def monitor_citations_cmd(ctx: click.Context, platform: str) -> None:
    """Monitor AI citation visibility for target queries."""
    from citation_monitor import monitor_company, get_citation_summary

    company_filter = ctx.obj["company"]
    slugs = _resolve_company_slugs(company_filter)

    platforms = None if platform == "all" else [platform]

    for slug in slugs:
        company = get_company(slug)
        click.echo(f"\n{'='*60}")
        click.echo(f"  {company.name} -- Citation Monitor")
        click.echo(f"{'='*60}")

        batch = monitor_company(slug, platforms=platforms)
        summary = get_citation_summary(batch)

        click.echo(f"\n  Overall Average Score: {summary['overall_average_score']}/100")
        click.echo(f"  Queries Monitored: {summary['total_queries_monitored']}")

        click.echo(f"\n  Platform Breakdown:")
        for plat, stats in summary["platform_breakdown"].items():
            click.echo(
                f"    {plat:12s}: avg {stats['average_score']:5.1f}/100 | "
                f"citation rate {stats['citation_rate']:5.1f}% | "
                f"{stats['queries_monitored']} queries"
            )

        click.echo(f"\n  Trends: "
                    f"up={summary['trend_distribution']['up']} | "
                    f"stable={summary['trend_distribution']['stable']} | "
                    f"down={summary['trend_distribution']['down']}")

        # Show top cited queries
        cited = [r for r in batch.reports if r.position is not None]
        cited.sort(key=lambda r: r.score, reverse=True)
        if cited:
            click.echo(f"\n  Top Cited Queries:")
            for r in cited[:5]:
                click.echo(
                    f"    [{r.platform:12s}] score={r.score:3d} pos={r.position} "
                    f"trend={r.trend.value:6s} | {r.query[:60]}"
                )


# ---------------------------------------------------------------------------
# status
# ---------------------------------------------------------------------------
@cli.command("status")
@click.pass_context
def status_cmd(ctx: click.Context) -> None:
    """Show engine status: companies, queries, and configuration."""
    click.echo(f"\n{'='*60}")
    click.echo(f"  AEO/GEO Content Engine -- Status")
    click.echo(f"{'='*60}")

    click.echo(f"\n  Companies:")
    for slug, company in COMPANIES.items():
        status_icon = "ACTIVE" if company.status == "active" else "COMING SOON"
        query_count = len(TARGET_QUERIES.get(slug, []))
        click.echo(
            f"    {company.name:20s} [{status_icon:11s}] "
            f"services={len(company.services)} queries={query_count}"
        )

    total_queries = sum(len(q) for q in TARGET_QUERIES.values())
    click.echo(f"\n  Total Target Queries: {total_queries}")
    click.echo(f"  Active Companies: {len(get_active_companies())}")
    click.echo(f"  Total Companies: {len(COMPANIES)}")

    # Check for API key
    import os

    has_key = bool(os.environ.get("ANTHROPIC_API_KEY"))
    click.echo(f"\n  Anthropic API Key: {'configured' if has_key else 'not set (demo mode only)'}")

    from config import CLAUDE_MODEL, AEO_SCORING_WEIGHTS

    click.echo(f"  Claude Model: {CLAUDE_MODEL}")
    click.echo(f"\n  AEO Scoring Weights:")
    for category, weight in AEO_SCORING_WEIGHTS.items():
        click.echo(f"    {category:25s}: {weight}%")


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------
def _resolve_company_slugs(company_filter: str) -> list[str]:
    """Resolve company filter to a list of slugs."""
    if company_filter == "all":
        return list(COMPANIES.keys())
    return [company_filter]


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    cli()
