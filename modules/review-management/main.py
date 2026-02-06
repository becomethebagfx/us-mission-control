"""
US Construction Marketing - Review Management System CLI.

Commands:
  monitor              Poll platforms for new reviews
  respond              Generate AI-powered responses to reviews
  solicit              Send review request emails (cadence-based)
  analyze-sentiment    Run sentiment analysis on reviews
  curate-testimonials  Select top reviews for marketing
  status               Show system status overview

Global flags:
  --demo / --no-demo   Run in demo mode with mock data (default: demo)
  --company SLUG       Filter to a specific company
  --platform SLUG      Filter to a specific platform
"""

from __future__ import annotations

import json
import logging
import os
import sys

import click

from config import (
    COMPANIES,
    DATA_DIR,
    LOG_FORMAT,
    LOG_LEVEL,
    PLATFORM_CONFIGS,
    SOLICITATIONS_FILE,
    get_active_companies,
    get_company,
)
from models import Platform, ReviewRequest
from review_monitor import poll_reviews, save_reviews
from review_responder import respond_to_reviews, save_responses
from review_solicitor import get_demo_requests, run_solicitation
from sentiment_analyzer import (
    aggregate_by_company,
    aggregate_by_platform,
    analyze_reviews,
    classify_sentiment,
    get_demo_analysis,
)
from testimonial_curator import (
    curate_testimonials,
    print_testimonials,
    save_testimonials,
)

# ---------------------------------------------------------------------------
# Logging setup
# ---------------------------------------------------------------------------

logging.basicConfig(
    level=LOG_LEVEL,
    format=LOG_FORMAT,
    stream=sys.stderr,
)
logger = logging.getLogger("review-management")


# ---------------------------------------------------------------------------
# CLI group
# ---------------------------------------------------------------------------

@click.group()
@click.option(
    "--demo/--no-demo",
    default=True,
    help="Run in demo mode with mock data (default: True).",
)
@click.option(
    "--company",
    default=None,
    type=click.Choice(list(COMPANIES.keys()), case_sensitive=False),
    help="Filter to a specific company.",
)
@click.option(
    "--platform",
    default=None,
    type=click.Choice(list(PLATFORM_CONFIGS.keys()), case_sensitive=False),
    help="Filter to a specific platform.",
)
@click.pass_context
def cli(ctx: click.Context, demo: bool, company: str, platform: str) -> None:
    """US Construction Marketing - Review Management System."""
    ctx.ensure_object(dict)
    ctx.obj["demo"] = demo
    ctx.obj["company"] = company
    ctx.obj["platform"] = platform

    os.makedirs(DATA_DIR, exist_ok=True)

    mode_label = "DEMO" if demo else "LIVE"
    click.echo(f"\n{'=' * 60}")
    click.echo(f"  Review Management System [{mode_label} MODE]")
    click.echo(f"{'=' * 60}")

    if company:
        co = get_company(company)
        click.echo(f"  Company filter: {co.name}")
    if platform:
        click.echo(f"  Platform filter: {platform}")
    click.echo("")


# ---------------------------------------------------------------------------
# Monitor command
# ---------------------------------------------------------------------------

@cli.command()
@click.pass_context
def monitor(ctx: click.Context) -> None:
    """Poll platforms for new reviews."""
    demo = ctx.obj["demo"]
    company = ctx.obj["company"]
    platform = ctx.obj["platform"]

    click.echo("  Polling review platforms...")
    reviews = poll_reviews(company=company, platform=platform, demo=demo)

    if not reviews:
        click.echo("  No new reviews found.")
        return

    click.echo(f"  Found {len(reviews)} reviews:\n")

    for review in reviews:
        stars = "*" * review.rating + " " * (5 - review.rating)
        co = get_company(review.company)
        click.echo(f"  [{stars}] {co.name} / {review.platform.value}")
        click.echo(f"    Author: {review.author}")
        click.echo(f"    Date:   {review.date.strftime('%Y-%m-%d %H:%M')}")
        # Show first 80 chars of review text
        preview = review.text[:80] + ("..." if len(review.text) > 80 else "")
        click.echo(f'    Text:   "{preview}"')
        click.echo("")

    save_reviews(reviews)
    click.echo(f"  Saved {len(reviews)} reviews to {DATA_DIR}/reviews.json")


# ---------------------------------------------------------------------------
# Respond command
# ---------------------------------------------------------------------------

@cli.command()
@click.pass_context
def respond(ctx: click.Context) -> None:
    """Generate AI-powered responses to reviews."""
    demo = ctx.obj["demo"]
    company = ctx.obj["company"]
    platform = ctx.obj["platform"]

    click.echo("  Fetching reviews to respond to...")
    reviews = poll_reviews(company=company, platform=platform, demo=demo)

    if not reviews:
        click.echo("  No reviews to respond to.")
        return

    click.echo(f"  Generating responses for {len(reviews)} reviews...\n")
    responses = respond_to_reviews(reviews, demo=demo)

    for resp in responses:
        review = next((r for r in reviews if r.id == resp.review_id), None)
        if review:
            co = get_company(review.company)
            click.echo(f"  Review by {review.author} ({review.rating}/5) - {co.name}")
            click.echo(f"  Tone: {resp.tone} | Brand Voice: {resp.brand_voice_score:.0%}")
            click.echo(f"  Response:")
            # Wrap response text
            for line in resp.response_text.split("\n"):
                click.echo(f"    {line}")
            click.echo("")

    save_responses(responses)
    click.echo(f"  Saved {len(responses)} responses to {DATA_DIR}/responses.json")


# ---------------------------------------------------------------------------
# Solicit command
# ---------------------------------------------------------------------------

@cli.command()
@click.pass_context
def solicit(ctx: click.Context) -> None:
    """Send review request emails (cadence-based)."""
    demo = ctx.obj["demo"]
    company = ctx.obj["company"]

    if demo:
        requests = get_demo_requests()
        if company:
            requests = [r for r in requests if r.company == company]
    else:
        click.echo("  Live solicitation requires project completion data source.")
        click.echo("  Use --demo for sample emails.")
        return

    click.echo(f"  Processing {len(requests)} review requests...\n")
    emails = run_solicitation(requests, demo=demo)

    if not emails:
        click.echo("  All cadence steps already completed for these requests.")
        return

    for email in emails:
        co = get_company(email["company"])
        click.echo(f"  To: {email['to']}")
        click.echo(f"  From: {email['from_name']} <{email['from_email']}>")
        click.echo(f"  Subject: {email['subject']}")
        click.echo(f"  Company: {co.name}")
        click.echo(f"  Cadence Day: {email['cadence_day']}")
        click.echo(f"  --- Email Preview ---")
        # Show first 200 chars
        preview = email["body"][:200] + ("..." if len(email["body"]) > 200 else "")
        for line in preview.split("\n"):
            click.echo(f"  {line}")
        click.echo(f"  --- End Preview ---\n")

    click.echo(f"  Generated {len(emails)} solicitation emails")


# ---------------------------------------------------------------------------
# Analyze sentiment command
# ---------------------------------------------------------------------------

@cli.command("analyze-sentiment")
@click.pass_context
def analyze_sentiment(ctx: click.Context) -> None:
    """Run sentiment analysis on reviews."""
    demo = ctx.obj["demo"]
    company = ctx.obj["company"]
    platform = ctx.obj["platform"]

    click.echo("  Fetching reviews for sentiment analysis...")
    reviews = poll_reviews(company=company, platform=platform, demo=demo)

    if not reviews:
        click.echo("  No reviews to analyse.")
        return

    click.echo(f"  Analysing {len(reviews)} reviews...\n")
    analysis = get_demo_analysis(reviews)

    # Per-review results
    click.echo("  Individual Review Scores:")
    click.echo(f"  {'Author':<20} {'Rating':>6} {'Score':>8} {'Class':>10}  Themes")
    click.echo(f"  {'-' * 75}")

    for review, result in zip(reviews, analysis["results"]):
        classification = classify_sentiment(result.score)
        themes_str = ", ".join(t.value for t in result.themes) or "none"
        click.echo(
            f"  {review.author:<20} {review.rating:>6} {result.score:>8.4f} "
            f"{classification:>10}  {themes_str}"
        )

    # Company aggregates
    click.echo(f"\n  Company Aggregates:")
    click.echo(
        f"  {'Company':<20} {'Avg':>6} {'Total':>6} "
        f"{'Pos':>5} {'Neu':>5} {'Neg':>5}  Top Themes"
    )
    click.echo(f"  {'-' * 75}")

    for slug, agg in analysis["by_company"].items():
        co = get_company(slug)
        themes_str = ", ".join(t.value for t in agg.top_themes) or "none"
        click.echo(
            f"  {co.name:<20} {agg.avg_score:>6.4f} {agg.total_reviews:>6} "
            f"{agg.positive_count:>5} {agg.neutral_count:>5} "
            f"{agg.negative_count:>5}  {themes_str}"
        )

    # Platform aggregates
    click.echo(f"\n  Platform Aggregates:")
    click.echo(
        f"  {'Platform':<20} {'Avg':>6} {'Total':>6} "
        f"{'Pos':>5} {'Neu':>5} {'Neg':>5}  Top Themes"
    )
    click.echo(f"  {'-' * 75}")

    for plat, agg in analysis["by_platform"].items():
        themes_str = ", ".join(t.value for t in agg.top_themes) or "none"
        click.echo(
            f"  {plat:<20} {agg.avg_score:>6.4f} {agg.total_reviews:>6} "
            f"{agg.positive_count:>5} {agg.neutral_count:>5} "
            f"{agg.negative_count:>5}  {themes_str}"
        )


# ---------------------------------------------------------------------------
# Curate testimonials command
# ---------------------------------------------------------------------------

@cli.command("curate-testimonials")
@click.pass_context
def curate_testimonials_cmd(ctx: click.Context) -> None:
    """Select top reviews for marketing use."""
    demo = ctx.obj["demo"]
    company = ctx.obj["company"]
    platform = ctx.obj["platform"]

    click.echo("  Fetching reviews for testimonial curation...")
    reviews = poll_reviews(company=company, platform=platform, demo=demo)

    if not reviews:
        click.echo("  No reviews available.")
        return

    # Run sentiment analysis first (needed for scoring)
    click.echo(f"  Running sentiment analysis on {len(reviews)} reviews...")
    analyze_reviews(reviews)

    click.echo("  Curating top testimonials...\n")
    testimonials = curate_testimonials(reviews, company=company)

    if not testimonials:
        click.echo("  No eligible testimonials found (minimum 4 stars required).")
        return

    print_testimonials(testimonials)
    save_testimonials(testimonials)
    click.echo(f"\n  Saved testimonials to {DATA_DIR}/testimonials.json")


# ---------------------------------------------------------------------------
# Status command
# ---------------------------------------------------------------------------

@cli.command()
@click.pass_context
def status(ctx: click.Context) -> None:
    """Show system status overview."""
    click.echo("  System Status")
    click.echo(f"  {'-' * 50}\n")

    # Companies
    active = get_active_companies()
    click.echo(f"  Companies: {len(COMPANIES)} total, {len(active)} active")
    for slug, co in COMPANIES.items():
        status_badge = "[ACTIVE]" if co.status == "active" else "[COMING SOON]"
        click.echo(f"    {status_badge:>14} {co.name} ({slug})")

    # Platforms
    enabled = [p for p, cfg in PLATFORM_CONFIGS.items() if cfg["enabled"]]
    click.echo(f"\n  Platforms: {len(PLATFORM_CONFIGS)} configured, {len(enabled)} enabled")
    for slug, cfg in PLATFORM_CONFIGS.items():
        status_badge = "[ON]" if cfg["enabled"] else "[OFF]"
        click.echo(f"    {status_badge:>6} {cfg['name']} ({slug})")

    # Data files
    click.echo(f"\n  Data Directory: {DATA_DIR}/")
    if os.path.exists(DATA_DIR):
        for fname in sorted(os.listdir(DATA_DIR)):
            fpath = os.path.join(DATA_DIR, fname)
            if os.path.isfile(fpath):
                size = os.path.getsize(fpath)
                click.echo(f"    {fname:<30} {size:>8} bytes")
    else:
        click.echo("    (no data directory yet)")

    # Solicitation status
    if os.path.exists(SOLICITATIONS_FILE):
        with open(SOLICITATIONS_FILE, "r") as f:
            solicitations = json.load(f)
        click.echo(f"\n  Solicitations: {len(solicitations)} tracked")
        for sol in solicitations:
            req = sol.get("request", {})
            steps = sol.get("steps_sent", [])
            received = sol.get("review_received", False)
            status_label = "REVIEW RECEIVED" if received else f"Step {len(steps)}/4"
            click.echo(
                f"    {req.get('contact_name', 'Unknown'):<25} "
                f"{req.get('company', ''):<15} {status_label}"
            )
    else:
        click.echo("\n  Solicitations: none tracked yet")

    click.echo(f"\n{'=' * 60}\n")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    cli()
