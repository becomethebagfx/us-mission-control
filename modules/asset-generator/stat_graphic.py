"""
Visual Asset Generator - Stat Graphic Generator
Generate stat/infographic cards for key construction metrics.
"""

from pathlib import Path
from typing import Optional

from PIL import Image

from config import BRAND_PALETTES, OUTPUT_DIR, PLATFORM_SIZES, get_brand
from models import Asset, AssetStatus, AssetType
from template_engine import TemplateEngine


# ──────────────────────────────────────────────────────────────
# Demo Data
# ──────────────────────────────────────────────────────────────

DEMO_STATS: list[dict[str, str]] = [
    {
        "company": "us_framing",
        "stat_value": "0.78",
        "stat_label": "EMR Safety Rating",
        "stat_description": "Our Experience Modification Rate reflects an unwavering commitment to jobsite safety across every project.",
    },
    {
        "company": "us_framing",
        "stat_value": "2.5M+",
        "stat_label": "Square Feet Framed",
        "stat_description": "Total square footage of steel and wood framing installed across commercial and residential projects.",
    },
    {
        "company": "us_drywall",
        "stat_value": "340+",
        "stat_label": "Projects Completed",
        "stat_description": "Commercial drywall and finishing projects delivered on time, from Level 3 to Level 5 finishes.",
    },
    {
        "company": "us_exteriors",
        "stat_value": "15",
        "stat_label": "Years in Business",
        "stat_description": "A decade and a half of building envelope expertise, from EIFS to metal panels to waterproofing systems.",
    },
    {
        "company": "us_development",
        "stat_value": "$120M+",
        "stat_label": "Projects Under Management",
        "stat_description": "Total value of development projects currently under management across the Southwest.",
    },
    {
        "company": "us_interiors",
        "stat_value": "98%",
        "stat_label": "Client Retention Rate",
        "stat_description": "Repeat business from general contractors and property managers who trust our interior finish quality.",
    },
    {
        "company": "us_drywall",
        "stat_value": "1.2M",
        "stat_label": "Board Feet Installed Annually",
        "stat_description": "Annual drywall installation volume across commercial, healthcare, and hospitality sectors.",
    },
    {
        "company": "us_framing",
        "stat_value": "48hr",
        "stat_label": "Average Bid Turnaround",
        "stat_description": "From plan review to detailed estimate in under two business days. Speed without sacrificing accuracy.",
    },
]


def generate_stat_card(
    company_key: str,
    stat_value: str,
    stat_label: str,
    stat_description: str = "",
    platform: str = "linkedin_post",
    output_dir: Optional[Path] = None,
) -> Asset:
    """Generate a stat/infographic card.

    Args:
        company_key: Company identifier.
        stat_value: The headline metric value (e.g., '0.78', '2.5M+').
        stat_label: Label describing the metric.
        stat_description: Optional longer description.
        platform: Target platform for sizing.
        output_dir: Directory to save the image.

    Returns:
        Asset metadata object.
    """
    engine = TemplateEngine()
    brand = get_brand(company_key)
    size = PLATFORM_SIZES[platform]

    variables = {
        "stat_value": stat_value,
        "stat_label": stat_label,
        "stat_description": stat_description,
    }

    out_dir = output_dir or OUTPUT_DIR / "stat_cards"
    out_dir.mkdir(parents=True, exist_ok=True)

    safe_label = stat_label.lower().replace(" ", "_").replace("/", "_")[:30]
    filename = f"{brand['name_short'].lower()}_stat_{safe_label}_{size['width']}x{size['height']}.png"
    output_path = out_dir / filename

    img = engine.render_to_image(
        template_type="stat_card",
        company_key=company_key,
        variables=variables,
        width=size["width"],
        height=size["height"],
        output_path=output_path,
    )

    file_size = output_path.stat().st_size if output_path.exists() else 0

    asset = Asset(
        company=company_key,
        type=AssetType.STAT_CARD,
        title=f"Stat Card: {stat_value} {stat_label}",
        template="stat_card",
        platform=platform,
        width=size["width"],
        height=size["height"],
        status=AssetStatus.GENERATED,
        file_path=str(output_path),
        file_size_bytes=file_size,
        tags=["stat", "infographic", brand["name_short"].lower(), platform],
        variables=variables,
    )

    return asset


def generate_demo_stats(
    platform: str = "linkedin_post",
    output_dir: Optional[Path] = None,
) -> list[Asset]:
    """Generate sample stat cards for all demo data.

    Args:
        platform: Target platform for sizing.
        output_dir: Directory to save images.

    Returns:
        List of Asset metadata objects.
    """
    assets = []
    for stat in DEMO_STATS:
        asset = generate_stat_card(
            company_key=stat["company"],
            stat_value=stat["stat_value"],
            stat_label=stat["stat_label"],
            stat_description=stat.get("stat_description", ""),
            platform=platform,
            output_dir=output_dir,
        )
        assets.append(asset)
    return assets


if __name__ == "__main__":
    print("Generating demo stat cards...")
    results = generate_demo_stats()
    for asset in results:
        print(f"  {asset.to_summary()}")
        print(f"    File: {asset.file_path}")
    print(f"\nGenerated {len(results)} stat card images.")
