"""
GBP Automation Module - CLI Entry Point
Click-based CLI with commands for posting, syncing, uploading, and insights.
"""

import sys
from datetime import date, timedelta
from typing import Optional

import click

from config import ACTIVE_COMPANIES, COMPANIES, get_company
from gbp_client import GBPClient
from insights_tracker import InsightsTracker
from location_manager import LocationManager
from models import CallToActionType
from post_generator import (
    generate_company_update,
    generate_project_completion,
    generate_service_highlight,
)


# ---------------------------------------------------------------------------
# Shared options
# ---------------------------------------------------------------------------


def _build_client(demo: bool) -> GBPClient:
    return GBPClient(account_id="demo" if demo else "", demo=demo)


# ---------------------------------------------------------------------------
# CLI Group
# ---------------------------------------------------------------------------


@click.group()
@click.option("--demo", is_flag=True, default=False, help="Run with mock data (no API calls).")
@click.pass_context
def cli(ctx: click.Context, demo: bool) -> None:
    """GBP Automation - Google Business Profile management for US Construction companies."""
    ctx.ensure_object(dict)
    ctx.obj["demo"] = demo
    ctx.obj["client"] = _build_client(demo)


# ---------------------------------------------------------------------------
# Command: post
# ---------------------------------------------------------------------------


@cli.command()
@click.option(
    "--type",
    "post_type",
    type=click.Choice(["project", "service", "update"], case_sensitive=False),
    required=True,
    help="Post type to generate.",
)
@click.option("--company", required=True, help="Company key or slug (e.g. us_framing).")
@click.option("--project", default=None, help="Project name (for project type).")
@click.option("--milestone", default=None, help="Milestone (for project type).")
@click.option("--stats", default=None, help="Stats string (for project type).")
@click.option("--service", default=None, help="Service name (for service type).")
@click.option("--benefits", default=None, help="Benefits list (for service type).")
@click.option("--update-kind", default="news", help="Update kind: news/hiring/event.")
@click.option("--details", default=None, help="Details text (for update type).")
@click.option("--photo-url", default=None, help="Optional photo URL to attach.")
@click.option("--cta-url", default=None, help="Optional CTA URL.")
@click.option("--publish", is_flag=True, default=False, help="Actually publish via API.")
@click.pass_context
def post(
    ctx: click.Context,
    post_type: str,
    company: str,
    project: Optional[str],
    milestone: Optional[str],
    stats: Optional[str],
    service: Optional[str],
    benefits: Optional[str],
    update_kind: str,
    details: Optional[str],
    photo_url: Optional[str],
    cta_url: Optional[str],
    publish: bool,
) -> None:
    """Generate (and optionally publish) a GBP post."""
    demo = ctx.obj["demo"]
    client = ctx.obj["client"]

    co = get_company(company)
    if co is None:
        click.echo(f"Error: Unknown company '{company}'.", err=True)
        click.echo(f"Available: {', '.join(COMPANIES.keys())}", err=True)
        sys.exit(1)
    if co.coming_soon:
        click.echo(f"Warning: {co.name} is marked as 'coming soon'.", err=True)

    company_key = company if company in COMPANIES else next(
        (k for k, v in COMPANIES.items() if v.slug == company), company
    )

    click.echo(f"\nGenerating {post_type} post for {co.name}...")

    if post_type == "project":
        if not all([project, milestone, stats]):
            click.echo("Error: --project, --milestone, and --stats are required for project posts.", err=True)
            sys.exit(1)
        local_post = generate_project_completion(
            company_key=company_key,
            company_name=co.name,
            project_name=project,
            milestone=milestone,
            stats=stats,
            photo_url=photo_url,
            cta_url=cta_url,
            demo=demo,
        )
    elif post_type == "service":
        if not all([service, benefits]):
            click.echo("Error: --service and --benefits are required for service posts.", err=True)
            sys.exit(1)
        local_post = generate_service_highlight(
            company_key=company_key,
            company_name=co.name,
            service_name=service,
            benefits=benefits,
            cta_url=cta_url,
            demo=demo,
        )
    else:  # update
        if not details:
            click.echo("Error: --details is required for update posts.", err=True)
            sys.exit(1)
        local_post = generate_company_update(
            company_key=company_key,
            company_name=co.name,
            update_type=update_kind,
            details=details,
            cta_url=cta_url,
            demo=demo,
        )

    click.echo(f"\n{'='*60}")
    click.echo(f"  Post Type : {local_post.post_type.value}")
    click.echo(f"  Company   : {co.name}")
    word_count = len(local_post.summary.split())
    click.echo(f"  Words     : {word_count}")
    click.echo(f"{'='*60}")
    click.echo(f"\n{local_post.summary}\n")
    if local_post.call_to_action:
        click.echo(f"  CTA: {local_post.call_to_action.action_type.value}")
        if local_post.call_to_action.url:
            click.echo(f"  URL: {local_post.call_to_action.url}")

    if publish:
        mgr = LocationManager(client, demo=demo)
        locations = mgr.get_locations_for_company(company_key)
        if not locations:
            click.echo("No locations found for this company.", err=True)
            sys.exit(1)
        loc = locations[0]
        result = client.create_post(loc.name, local_post)
        click.echo(f"\n  Published: {result.name}")
    else:
        click.echo("\n  (Preview only. Add --publish to post to GBP.)")


# ---------------------------------------------------------------------------
# Command: sync-locations
# ---------------------------------------------------------------------------


@cli.command("sync-locations")
@click.option("--company", default=None, help="Filter to a single company.")
@click.pass_context
def sync_locations(ctx: click.Context, company: Optional[str]) -> None:
    """Sync and display GBP locations with NAP verification."""
    demo = ctx.obj["demo"]
    client = ctx.obj["client"]

    mgr = LocationManager(client, demo=demo)
    mgr.sync_locations()

    output = mgr.print_status(company_filter=company)
    click.echo(output)


# ---------------------------------------------------------------------------
# Command: upload-photos
# ---------------------------------------------------------------------------


@cli.command("upload-photos")
@click.option("--company", required=True, help="Company key or slug.")
@click.option("--path", "photo_path", required=True, type=click.Path(exists=True), help="Path to photo file.")
@click.option(
    "--category",
    type=click.Choice(["COVER", "PROFILE", "ADDITIONAL", "POST"], case_sensitive=False),
    default="ADDITIONAL",
    help="Photo category.",
)
@click.option("--resize/--no-resize", default=True, help="Auto-resize to platform spec.")
@click.pass_context
def upload_photos(
    ctx: click.Context,
    company: str,
    photo_path: str,
    category: str,
    resize: bool,
) -> None:
    """Upload a photo to a company's GBP listing."""
    from photo_manager import upload_photo_to_location

    demo = ctx.obj["demo"]
    client = ctx.obj["client"]

    co = get_company(company)
    if co is None:
        click.echo(f"Error: Unknown company '{company}'.", err=True)
        sys.exit(1)

    company_key = company if company in COMPANIES else next(
        (k for k, v in COMPANIES.items() if v.slug == company), company
    )

    mgr = LocationManager(client, demo=demo)
    locations = mgr.get_locations_for_company(company_key)
    if not locations:
        click.echo("No locations found.", err=True)
        sys.exit(1)

    loc = locations[0]
    click.echo(f"Uploading {photo_path} to {loc.title} as {category}...")

    try:
        photo = upload_photo_to_location(
            client=client,
            location_name=loc.name,
            file_path=photo_path,
            company_key=company_key,
            category_hint=category,
            auto_resize=resize,
        )
        click.echo(f"  Uploaded: {photo.name}")
        click.echo(f"  Size: {photo.size_bytes:,} bytes")
        click.echo(f"  Dimensions: {photo.width}x{photo.height}")
        click.echo(f"  Category: {photo.category.value}")
    except Exception as e:
        click.echo(f"Error: {e}", err=True)
        sys.exit(1)


# ---------------------------------------------------------------------------
# Command: insights
# ---------------------------------------------------------------------------


@cli.command()
@click.option("--company", default=None, help="Filter to a single company.")
@click.option("--days", default=30, type=int, help="Number of days to report on.")
@click.option("--poll", "do_poll", is_flag=True, default=False, help="Fetch fresh data from API before reporting.")
@click.pass_context
def insights(
    ctx: click.Context,
    company: Optional[str],
    days: int,
    do_poll: bool,
) -> None:
    """Display GBP performance insights and trends."""
    demo = ctx.obj["demo"]
    client = ctx.obj["client"]

    tracker = InsightsTracker(client, demo=demo)

    if demo:
        click.echo("Generating demo insights data...")
        tracker.generate_demo_data(days=days + 30)

    if do_poll or demo:
        mgr = LocationManager(client, demo=demo)
        locations = mgr.locations
        if company:
            locations = [l for l in locations if l.company_key == company]
        added = tracker.poll(locations, days=days)
        click.echo(f"  Fetched {added} new metric records.")

    reports = tracker.all_reports(days=days)
    if company:
        reports = [r for r in reports if r.company_key == company]

    if not reports:
        click.echo("No insights data found. Try --poll or --demo to fetch data first.")
        return

    for report in reports:
        click.echo(tracker.format_report(report))
        click.echo()


# ---------------------------------------------------------------------------
# Command: status
# ---------------------------------------------------------------------------


@cli.command()
@click.option("--company", default=None, help="Filter to a single company.")
@click.pass_context
def status(ctx: click.Context, company: Optional[str]) -> None:
    """Show overall GBP status: locations, NAP health, rate limits."""
    demo = ctx.obj["demo"]
    client = ctx.obj["client"]

    mgr = LocationManager(client, demo=demo)
    mgr.sync_locations()

    click.echo(mgr.print_status(company_filter=company))

    click.echo(f"\n  API Rate Limit: {client.rate_remaining} / 500 remaining today")

    click.echo(f"\n  Registered Companies:")
    for key, co in COMPANIES.items():
        status_label = "COMING SOON" if co.coming_soon else "ACTIVE"
        click.echo(f"    [{co.accent_color}] {co.name:20s} {status_label}")


# ---------------------------------------------------------------------------
# Entry point
# ---------------------------------------------------------------------------


if __name__ == "__main__":
    cli()
