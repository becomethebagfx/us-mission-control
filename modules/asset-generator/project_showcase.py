"""
Visual Asset Generator - Project Showcase
Generate project completion graphics with stats overlay.
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

DEMO_PROJECTS: list[dict[str, str]] = [
    {
        "company": "us_framing",
        "project_name": "Meridian Tower - Steel & Wood Framing",
        "sqft": "145,000 sq ft",
        "timeline": "8 months",
        "location": "Austin, TX",
    },
    {
        "company": "us_drywall",
        "project_name": "Lakewood Medical Center - Interior Finishing",
        "sqft": "82,000 sq ft",
        "timeline": "5 months",
        "location": "Denver, CO",
    },
    {
        "company": "us_exteriors",
        "project_name": "Summit Ridge HOA - Full Exterior Renovation",
        "sqft": "24,000 sq ft",
        "timeline": "3 months",
        "location": "Phoenix, AZ",
    },
    {
        "company": "us_development",
        "project_name": "Harbor View Mixed-Use Development",
        "sqft": "310,000 sq ft",
        "timeline": "18 months",
        "location": "San Diego, CA",
    },
    {
        "company": "us_interiors",
        "project_name": "Grandview Corporate Office - Full Buildout",
        "sqft": "56,000 sq ft",
        "timeline": "4 months",
        "location": "Dallas, TX",
    },
]


def generate_project_showcase(
    company_key: str,
    project_name: str,
    sqft: str = "",
    timeline: str = "",
    location: str = "",
    stats: str = "",
    platform: str = "linkedin_post",
    output_dir: Optional[Path] = None,
) -> Asset:
    """Generate a project showcase image.

    Args:
        company_key: Company identifier (e.g., 'us_framing').
        project_name: Name of the completed project.
        sqft: Square footage string.
        timeline: Project timeline string.
        location: Project location.
        stats: Additional stats text.
        platform: Target platform for sizing.
        output_dir: Directory to save the image.

    Returns:
        Asset metadata object.
    """
    engine = TemplateEngine()
    brand = get_brand(company_key)
    size = PLATFORM_SIZES[platform]

    variables = {
        "project_name": project_name,
        "sqft": sqft,
        "timeline": timeline,
        "location": location,
        "stats": stats,
    }

    out_dir = output_dir or OUTPUT_DIR / "project_showcase"
    out_dir.mkdir(parents=True, exist_ok=True)

    safe_name = project_name.lower().replace(" ", "_").replace("-", "_")[:40]
    filename = f"{brand['name_short'].lower()}_{safe_name}_{size['width']}x{size['height']}.png"
    output_path = out_dir / filename

    img = engine.render_to_image(
        template_type="project_showcase",
        company_key=company_key,
        variables=variables,
        width=size["width"],
        height=size["height"],
        output_path=output_path,
    )

    file_size = output_path.stat().st_size if output_path.exists() else 0

    asset = Asset(
        company=company_key,
        type=AssetType.SOCIAL_POST,
        title=f"Project Showcase: {project_name}",
        template="project_showcase",
        platform=platform,
        width=size["width"],
        height=size["height"],
        status=AssetStatus.GENERATED,
        file_path=str(output_path),
        file_size_bytes=file_size,
        tags=["project", "showcase", brand["name_short"].lower(), platform],
        variables=variables,
    )

    return asset


def generate_demo_showcases(
    platform: str = "linkedin_post",
    output_dir: Optional[Path] = None,
) -> list[Asset]:
    """Generate sample project showcases for all demo projects.

    Args:
        platform: Target platform for sizing.
        output_dir: Directory to save images.

    Returns:
        List of Asset metadata objects.
    """
    assets = []
    for project in DEMO_PROJECTS:
        asset = generate_project_showcase(
            company_key=project["company"],
            project_name=project["project_name"],
            sqft=project.get("sqft", ""),
            timeline=project.get("timeline", ""),
            location=project.get("location", ""),
            platform=platform,
            output_dir=output_dir,
        )
        assets.append(asset)
    return assets


if __name__ == "__main__":
    print("Generating demo project showcases...")
    results = generate_demo_showcases()
    for asset in results:
        print(f"  {asset.to_summary()}")
        print(f"    File: {asset.file_path}")
    print(f"\nGenerated {len(results)} project showcase images.")
