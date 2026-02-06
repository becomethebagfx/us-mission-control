"""
Visual Asset Generator - CLI
Command-line interface for generating, resizing, and managing visual assets.
"""

import sys
from pathlib import Path

import click

# Ensure the package directory is on the path
sys.path.insert(0, str(Path(__file__).parent))

from config import BRAND_PALETTES, COMPANY_KEYS, COMPANY_NAMES, OUTPUT_DIR, PLATFORM_SIZES
from models import AssetStatus, AssetType


# ──────────────────────────────────────────────────────────────
# CLI Group
# ──────────────────────────────────────────────────────────────


@click.group()
@click.version_option(version="1.0.0", prog_name="asset-generator")
def cli():
    """US Construction Marketing - Visual Asset Generator

    Generate branded visual assets for all 5 companies across
    8 social media platforms.
    """
    pass


# ──────────────────────────────────────────────────────────────
# Generate Command
# ──────────────────────────────────────────────────────────────


@cli.command()
@click.option(
    "--template",
    type=click.Choice(["project_showcase", "social_quote", "stat_card", "company_header"]),
    required=True,
    help="Template type to generate.",
)
@click.option(
    "--company",
    type=click.Choice(COMPANY_KEYS),
    required=True,
    help="Company brand to apply.",
)
@click.option(
    "--platform",
    type=click.Choice(list(PLATFORM_SIZES.keys())),
    default="linkedin_post",
    help="Target platform for sizing.",
)
@click.option("--title", default="", help="Asset title or project name.")
@click.option("--value", default="", help="Stat value (for stat_card template).")
@click.option("--label", default="", help="Stat label (for stat_card template).")
@click.option("--quote", default="", help="Quote text (for social_quote template).")
@click.option("--author", default="", help="Quote author (for social_quote template).")
@click.option("--tagline", default="", help="Tagline (for company_header template).")
@click.option("--sqft", default="", help="Square footage (for project_showcase).")
@click.option("--timeline", default="", help="Timeline (for project_showcase).")
@click.option("--location", default="", help="Location (for project_showcase).")
@click.option("--demo", is_flag=True, help="Generate demo assets with sample data.")
@click.option("--output", type=click.Path(), default=None, help="Custom output directory.")
def generate(template, company, platform, title, value, label, quote, author, tagline, sqft, timeline, location, demo, output):
    """Generate a branded visual asset."""
    from asset_library import AssetLibrary

    output_dir = Path(output) if output else None
    library = AssetLibrary()

    if demo:
        _generate_demo(template, platform, output_dir, library)
        return

    if template == "project_showcase":
        from project_showcase import generate_project_showcase

        project_name = title or "Untitled Project"
        asset = generate_project_showcase(
            company_key=company,
            project_name=project_name,
            sqft=sqft,
            timeline=timeline,
            location=location,
            platform=platform,
            output_dir=output_dir,
        )
        library.add(asset)
        click.echo(f"Generated: {asset.to_summary()}")
        click.echo(f"  File: {asset.file_path}")

    elif template == "social_quote":
        from social_card import generate_quote_card

        quote_text = quote or "Enter your quote text here."
        asset = generate_quote_card(
            company_key=company,
            quote_text=quote_text,
            quote_author=author,
            platform=platform,
            output_dir=output_dir,
        )
        library.add(asset)
        click.echo(f"Generated: {asset.to_summary()}")
        click.echo(f"  File: {asset.file_path}")

    elif template == "stat_card":
        from stat_graphic import generate_stat_card

        stat_value = value or "0"
        stat_label = label or "Metric"
        asset = generate_stat_card(
            company_key=company,
            stat_value=stat_value,
            stat_label=stat_label,
            platform=platform,
            output_dir=output_dir,
        )
        library.add(asset)
        click.echo(f"Generated: {asset.to_summary()}")
        click.echo(f"  File: {asset.file_path}")

    elif template == "company_header":
        from template_engine import TemplateEngine
        from models import Asset, AssetType, AssetStatus

        engine = TemplateEngine()
        brand = BRAND_PALETTES[company]
        size = PLATFORM_SIZES[platform]
        out_dir = output_dir or OUTPUT_DIR / "headers"
        out_dir.mkdir(parents=True, exist_ok=True)

        variables = {
            "tagline": tagline or "Building Excellence",
        }

        filename = f"{brand['name_short'].lower()}_header_{size['width']}x{size['height']}.png"
        output_path = out_dir / filename

        engine.render_to_image(
            template_type="company_header",
            company_key=company,
            variables=variables,
            width=size["width"],
            height=size["height"],
            output_path=output_path,
        )

        file_size = output_path.stat().st_size if output_path.exists() else 0
        asset = Asset(
            company=company,
            type=AssetType.COVER_PHOTO,
            title=f"Header: {brand['name_full']}",
            template="company_header",
            platform=platform,
            width=size["width"],
            height=size["height"],
            status=AssetStatus.GENERATED,
            file_path=str(output_path),
            file_size_bytes=file_size,
            tags=["header", "banner", brand["name_short"].lower(), platform],
            variables=variables,
        )
        library.add(asset)
        click.echo(f"Generated: {asset.to_summary()}")
        click.echo(f"  File: {asset.file_path}")


def _generate_demo(template: str, platform: str, output_dir, library):
    """Generate demo assets for a given template type."""
    from asset_library import AssetLibrary

    if template == "project_showcase":
        from project_showcase import generate_demo_showcases

        assets = generate_demo_showcases(platform=platform, output_dir=output_dir)
    elif template == "social_quote":
        from social_card import generate_demo_cards

        assets = generate_demo_cards(platform=platform, output_dir=output_dir)
    elif template == "stat_card":
        from stat_graphic import generate_demo_stats

        assets = generate_demo_stats(platform=platform, output_dir=output_dir)
    elif template == "company_header":
        # Generate headers for all companies
        from template_engine import TemplateEngine
        from models import Asset, AssetType, AssetStatus

        engine = TemplateEngine()
        assets = []
        taglines = {
            "us_framing": "Precision Framing, On Time",
            "us_drywall": "Flawless Finishes, Every Surface",
            "us_exteriors": "Protecting What You Build",
            "us_development": "From Vision to Reality",
            "us_interiors": "Crafting Exceptional Spaces",
        }
        for company_key in COMPANY_KEYS:
            brand = BRAND_PALETTES[company_key]
            size = PLATFORM_SIZES[platform]
            out_dir = output_dir or OUTPUT_DIR / "headers"
            out_dir.mkdir(parents=True, exist_ok=True)

            variables = {"tagline": taglines.get(company_key, "Building Excellence")}
            filename = f"{brand['name_short'].lower()}_header_{size['width']}x{size['height']}.png"
            output_path = out_dir / filename

            engine.render_to_image(
                template_type="company_header",
                company_key=company_key,
                variables=variables,
                width=size["width"],
                height=size["height"],
                output_path=output_path,
            )

            file_size = output_path.stat().st_size if output_path.exists() else 0
            asset = Asset(
                company=company_key,
                type=AssetType.COVER_PHOTO,
                title=f"Header: {brand['name_full']}",
                template="company_header",
                platform=platform,
                width=size["width"],
                height=size["height"],
                status=AssetStatus.GENERATED,
                file_path=str(output_path),
                file_size_bytes=file_size,
                tags=["header", "banner", brand["name_short"].lower(), platform],
                variables=variables,
            )
            assets.append(asset)
    else:
        click.echo(f"Unknown template: {template}")
        return

    for asset in assets:
        library.add(asset)
        click.echo(f"  {asset.to_summary()}")
        click.echo(f"    File: {asset.file_path}")

    click.echo(f"\nGenerated {len(assets)} demo {template} assets.")


# ──────────────────────────────────────────────────────────────
# Resize Command
# ──────────────────────────────────────────────────────────────


@cli.command()
@click.argument("source", type=click.Path(exists=True))
@click.option(
    "--platform",
    type=click.Choice(list(PLATFORM_SIZES.keys())),
    default=None,
    help="Target platform. If omitted, resizes for all platforms.",
)
@click.option("--output", type=click.Path(), default=None, help="Custom output directory.")
def resize(source, platform, output):
    """Resize an image for social media platforms."""
    from platform_sizer import resize_for_all_platforms, resize_for_platform

    output_dir = Path(output) if output else None

    if platform:
        output_path = resize_for_platform(source, platform, output_dir=output_dir)
        click.echo(f"Resized for {platform}: {output_path}")
    else:
        results = resize_for_all_platforms(source, output_dir=output_dir)
        click.echo(f"Resized for {len(results)} platforms:")
        for plat, path in results.items():
            click.echo(f"  {plat}: {path}")


# ──────────────────────────────────────────────────────────────
# Library Command Group
# ──────────────────────────────────────────────────────────────


@cli.group()
def library():
    """Manage the asset library."""
    pass


@library.command("list")
@click.option("--company", type=click.Choice(COMPANY_KEYS), default=None, help="Filter by company.")
@click.option("--type", "asset_type", type=click.Choice([t.value for t in AssetType]), default=None, help="Filter by type.")
@click.option("--platform", type=click.Choice(list(PLATFORM_SIZES.keys())), default=None, help="Filter by platform.")
@click.option("--status", type=click.Choice([s.value for s in AssetStatus]), default=None, help="Filter by status.")
def library_list(company, asset_type, platform, status):
    """List assets in the library."""
    from asset_library import AssetLibrary

    lib = AssetLibrary()
    assets = lib.search(
        company=company,
        asset_type=AssetType(asset_type) if asset_type else None,
        platform=platform,
        status=AssetStatus(status) if status else None,
    )

    if not assets:
        click.echo("No assets found matching criteria.")
        return

    click.echo(f"Found {len(assets)} assets:\n")
    for asset in assets:
        click.echo(f"  {asset.to_summary()}")
        if asset.file_path:
            click.echo(f"    File: {asset.file_path}")


@library.command("search")
@click.argument("query")
def library_search(query):
    """Search assets by text query."""
    from asset_library import AssetLibrary

    lib = AssetLibrary()
    assets = lib.search(query=query)

    if not assets:
        click.echo(f"No assets matching '{query}'.")
        return

    click.echo(f"Found {len(assets)} assets matching '{query}':\n")
    for asset in assets:
        click.echo(f"  {asset.to_summary()}")


@library.command("delete")
@click.argument("asset_id")
@click.confirmation_option(prompt="Are you sure you want to delete this asset?")
def library_delete(asset_id):
    """Delete an asset by ID."""
    from asset_library import AssetLibrary

    lib = AssetLibrary()
    if lib.delete(asset_id):
        click.echo(f"Deleted asset {asset_id}")
    else:
        click.echo(f"Asset {asset_id} not found.")


# ──────────────────────────────────────────────────────────────
# Status Command
# ──────────────────────────────────────────────────────────────


@cli.command()
def status():
    """Show asset library status and statistics."""
    from asset_library import AssetLibrary

    lib = AssetLibrary()
    stats = lib.stats()

    click.echo("=" * 50)
    click.echo("  VISUAL ASSET GENERATOR - STATUS")
    click.echo("=" * 50)
    click.echo(f"\n  Total Assets: {stats['total']}")
    click.echo(f"  Total Size:   {stats['total_size_mb']} MB")

    if stats["by_company"]:
        click.echo("\n  By Company:")
        for company, count in sorted(stats["by_company"].items()):
            name = COMPANY_NAMES.get(company, company)
            click.echo(f"    {name}: {count}")

    if stats["by_type"]:
        click.echo("\n  By Type:")
        for atype, count in sorted(stats["by_type"].items()):
            click.echo(f"    {atype}: {count}")

    if stats["by_status"]:
        click.echo("\n  By Status:")
        for status_val, count in sorted(stats["by_status"].items()):
            click.echo(f"    {status_val}: {count}")

    click.echo("\n  Output Directory: " + str(OUTPUT_DIR))
    click.echo("\n  Available Companies:")
    for key in COMPANY_KEYS:
        brand = BRAND_PALETTES[key]
        click.echo(f"    {brand['name_full']} ({brand['name_short']}) - accent: {brand['accent']}")

    click.echo("\n  Available Platforms:")
    for key, info in PLATFORM_SIZES.items():
        click.echo(f"    {key}: {info['name']} ({info['width']}x{info['height']})")

    click.echo("")


# ──────────────────────────────────────────────────────────────
# Entry Point
# ──────────────────────────────────────────────────────────────

if __name__ == "__main__":
    cli()
