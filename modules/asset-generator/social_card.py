"""
Visual Asset Generator - Social Card Generator
Generate quote cards, announcement cards, and tip cards with company branding.
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

DEMO_QUOTES: list[dict[str, str]] = [
    {
        "company": "us_framing",
        "quote_text": "US Framing delivered our steel framing package two weeks ahead of schedule. Their crew coordination was outstanding.",
        "quote_author": "Mike Reynolds",
        "quote_role": "Project Manager, Turner Construction",
    },
    {
        "company": "us_drywall",
        "quote_text": "The quality of finish on this medical facility exceeded every expectation. Level 5 finish throughout, zero punch list items on drywall.",
        "quote_author": "Sarah Chen",
        "quote_role": "Director of Construction, HCA Healthcare",
    },
    {
        "company": "us_exteriors",
        "quote_text": "From EIFS to metal panels, US Exteriors handled the entire building envelope. Their waterproofing detail work is best in class.",
        "quote_author": "David Ortiz",
        "quote_role": "Owner, Ortiz Development Group",
    },
    {
        "company": "us_development",
        "quote_text": "US Development managed our mixed-use project from entitlement through certificate of occupancy. True turnkey execution.",
        "quote_author": "Jennifer Walsh",
        "quote_role": "VP Real Estate, Pacific Investment Partners",
    },
    {
        "company": "us_interiors",
        "quote_text": "The attention to detail on our corporate headquarters was remarkable. Every suite was completed to spec, on time, and within budget.",
        "quote_author": "Robert Kim",
        "quote_role": "Facilities Director, Apex Technologies",
    },
]

DEMO_ANNOUNCEMENTS: list[dict[str, str]] = [
    {
        "company": "us_framing",
        "quote_text": "Now hiring experienced steel framers and lead carpenters across Texas and Colorado. Join a crew that values craftsmanship.",
        "quote_author": "US Framing",
        "quote_role": "Career Opportunities",
    },
    {
        "company": "us_drywall",
        "quote_text": "Proud to announce our expanded service area now covering the entire Southwest region. Same quality, broader reach.",
        "quote_author": "US Drywall",
        "quote_role": "Company Announcement",
    },
]

DEMO_TIPS: list[dict[str, str]] = [
    {
        "company": "us_framing",
        "quote_text": "Pro Tip: Always verify anchor bolt placement before pouring. A 1/4 inch offset at the slab means 2 inches of correction at the roof line.",
        "quote_author": "US Framing",
        "quote_role": "Field Insight",
    },
    {
        "company": "us_exteriors",
        "quote_text": "Moisture management starts at design. Proper flashing details and drainage planes prevent 90% of building envelope failures.",
        "quote_author": "US Exteriors",
        "quote_role": "Technical Insight",
    },
]


def generate_quote_card(
    company_key: str,
    quote_text: str,
    quote_author: str = "",
    quote_role: str = "",
    platform: str = "linkedin_post",
    output_dir: Optional[Path] = None,
) -> Asset:
    """Generate a quote/testimonial card.

    Args:
        company_key: Company identifier.
        quote_text: The quote text to display.
        quote_author: Person who said the quote.
        quote_role: Author's title/role.
        platform: Target platform for sizing.
        output_dir: Directory to save the image.

    Returns:
        Asset metadata object.
    """
    engine = TemplateEngine()
    brand = get_brand(company_key)
    size = PLATFORM_SIZES[platform]

    variables = {
        "quote_text": quote_text,
        "quote_author": quote_author,
        "quote_role": quote_role,
    }

    out_dir = output_dir or OUTPUT_DIR / "social_cards"
    out_dir.mkdir(parents=True, exist_ok=True)

    safe_author = quote_author.lower().replace(" ", "_").replace(",", "")[:30] if quote_author else "card"
    filename = f"{brand['name_short'].lower()}_quote_{safe_author}_{size['width']}x{size['height']}.png"
    output_path = out_dir / filename

    img = engine.render_to_image(
        template_type="social_quote",
        company_key=company_key,
        variables=variables,
        width=size["width"],
        height=size["height"],
        output_path=output_path,
    )

    file_size = output_path.stat().st_size if output_path.exists() else 0

    asset = Asset(
        company=company_key,
        type=AssetType.QUOTE_CARD,
        title=f"Quote Card: {quote_author or 'Anonymous'}",
        template="social_quote",
        platform=platform,
        width=size["width"],
        height=size["height"],
        status=AssetStatus.GENERATED,
        file_path=str(output_path),
        file_size_bytes=file_size,
        tags=["quote", "testimonial", brand["name_short"].lower(), platform],
        variables=variables,
    )

    return asset


def generate_announcement_card(
    company_key: str,
    announcement_text: str,
    title: str = "",
    subtitle: str = "",
    platform: str = "linkedin_post",
    output_dir: Optional[Path] = None,
) -> Asset:
    """Generate an announcement card.

    Args:
        company_key: Company identifier.
        announcement_text: The announcement body text.
        title: Card title (defaults to company name).
        subtitle: Subtitle or category label.
        platform: Target platform for sizing.
        output_dir: Directory to save the image.

    Returns:
        Asset metadata object.
    """
    brand = get_brand(company_key)
    return generate_quote_card(
        company_key=company_key,
        quote_text=announcement_text,
        quote_author=title or brand["name_full"],
        quote_role=subtitle or "Announcement",
        platform=platform,
        output_dir=output_dir,
    )


def generate_tip_card(
    company_key: str,
    tip_text: str,
    category: str = "Field Insight",
    platform: str = "linkedin_post",
    output_dir: Optional[Path] = None,
) -> Asset:
    """Generate a professional tip/insight card.

    Args:
        company_key: Company identifier.
        tip_text: The tip or insight text.
        category: Category label (e.g., 'Field Insight', 'Technical Tip').
        platform: Target platform for sizing.
        output_dir: Directory to save the image.

    Returns:
        Asset metadata object.
    """
    brand = get_brand(company_key)
    return generate_quote_card(
        company_key=company_key,
        quote_text=tip_text,
        quote_author=brand["name_full"],
        quote_role=category,
        platform=platform,
        output_dir=output_dir,
    )


def generate_demo_cards(
    platform: str = "linkedin_post",
    output_dir: Optional[Path] = None,
) -> list[Asset]:
    """Generate sample social cards for all demo data.

    Args:
        platform: Target platform for sizing.
        output_dir: Directory to save images.

    Returns:
        List of Asset metadata objects.
    """
    assets = []

    # Quote cards
    for quote in DEMO_QUOTES:
        asset = generate_quote_card(
            company_key=quote["company"],
            quote_text=quote["quote_text"],
            quote_author=quote.get("quote_author", ""),
            quote_role=quote.get("quote_role", ""),
            platform=platform,
            output_dir=output_dir,
        )
        assets.append(asset)

    # Announcement cards
    for announcement in DEMO_ANNOUNCEMENTS:
        asset = generate_announcement_card(
            company_key=announcement["company"],
            announcement_text=announcement["quote_text"],
            title=announcement.get("quote_author", ""),
            subtitle=announcement.get("quote_role", ""),
            platform=platform,
            output_dir=output_dir,
        )
        assets.append(asset)

    # Tip cards
    for tip in DEMO_TIPS:
        asset = generate_tip_card(
            company_key=tip["company"],
            tip_text=tip["quote_text"],
            category=tip.get("quote_role", "Field Insight"),
            platform=platform,
            output_dir=output_dir,
        )
        assets.append(asset)

    return assets


if __name__ == "__main__":
    print("Generating demo social cards...")
    results = generate_demo_cards()
    for asset in results:
        print(f"  {asset.to_summary()}")
        print(f"    File: {asset.file_path}")
    print(f"\nGenerated {len(results)} social card images.")
