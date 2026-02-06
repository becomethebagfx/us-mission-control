"""
Visual Asset Generator - Tests
Test template rendering, platform dimensions, asset CRUD, brand injection, and config validation.
"""

import json
import sys
import tempfile
from pathlib import Path
from unittest.mock import patch

import pytest

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from config import (
    BRAND_PALETTES,
    COMPANY_KEYS,
    COMPANY_NAMES,
    COMPANY_SHORT_NAMES,
    PLATFORM_SIZES,
    TEMPLATE_TYPES,
    get_brand,
    get_platform,
)
from models import Asset, AssetStatus, AssetType, BrandPalette, PlatformSize, Template


# ──────────────────────────────────────────────────────────────
# Config Validation Tests
# ──────────────────────────────────────────────────────────────


class TestConfig:
    """Test configuration validity."""

    def test_all_five_companies_present(self):
        """All 5 companies must be in the brand palette registry."""
        expected = {"us_framing", "us_drywall", "us_exteriors", "us_development", "us_interiors"}
        assert set(COMPANY_KEYS) == expected

    def test_brand_palette_has_required_fields(self):
        """Each brand palette must have primary, accent, text_light, text_dark."""
        required_fields = {"primary", "accent", "text_light", "text_dark", "font_heading", "font_body", "name_short", "name_full"}
        for key, palette in BRAND_PALETTES.items():
            for field in required_fields:
                assert field in palette, f"Missing '{field}' in palette for {key}"

    def test_primary_color_consistent(self):
        """All companies share the same primary navy color."""
        for key, palette in BRAND_PALETTES.items():
            assert palette["primary"] == "#1B2A4A", f"Primary color mismatch for {key}"

    def test_accent_colors_unique(self):
        """Each company has a distinct accent color."""
        accents = [p["accent"] for p in BRAND_PALETTES.values()]
        assert len(accents) == len(set(accents)), "Accent colors are not unique"

    def test_specific_accent_colors(self):
        """Verify the exact accent color for each company."""
        expected = {
            "us_framing": "#4A90D9",
            "us_drywall": "#B8860B",
            "us_exteriors": "#2D5F2D",
            "us_development": "#C4AF94",
            "us_interiors": "#8B5E3C",
        }
        for key, color in expected.items():
            assert BRAND_PALETTES[key]["accent"] == color, f"Wrong accent for {key}"

    def test_short_names(self):
        """Verify short name codes."""
        expected = {
            "us_framing": "USF",
            "us_drywall": "USD",
            "us_exteriors": "USE",
            "us_development": "USDv",
            "us_interiors": "USI",
        }
        for key, short in expected.items():
            assert BRAND_PALETTES[key]["name_short"] == short

    def test_all_eight_platforms_present(self):
        """All 8 platform sizes must be configured."""
        expected = {
            "linkedin_post", "linkedin_banner", "instagram_post", "instagram_story",
            "facebook_post", "facebook_cover", "gbp_post", "twitter_post",
        }
        assert set(PLATFORM_SIZES.keys()) == expected

    def test_platform_dimensions(self):
        """Verify exact pixel dimensions for each platform."""
        expected = {
            "linkedin_post": (1200, 627),
            "linkedin_banner": (1128, 191),
            "instagram_post": (1080, 1080),
            "instagram_story": (1080, 1920),
            "facebook_post": (1200, 630),
            "facebook_cover": (820, 312),
            "gbp_post": (720, 540),
            "twitter_post": (1200, 675),
        }
        for key, (w, h) in expected.items():
            assert PLATFORM_SIZES[key]["width"] == w, f"Width mismatch for {key}"
            assert PLATFORM_SIZES[key]["height"] == h, f"Height mismatch for {key}"

    def test_platform_has_aspect_ratio(self):
        """Each platform size must include an aspect ratio."""
        for key, info in PLATFORM_SIZES.items():
            assert "aspect_ratio" in info, f"Missing aspect_ratio for {key}"
            assert info["aspect_ratio"] > 0, f"Invalid aspect_ratio for {key}"

    def test_template_types_present(self):
        """All 4 template types must be configured."""
        expected = {"project_showcase", "social_quote", "stat_card", "company_header"}
        assert set(TEMPLATE_TYPES.keys()) == expected

    def test_get_brand_valid(self):
        """get_brand returns palette for valid company key."""
        brand = get_brand("us_framing")
        assert brand["accent"] == "#4A90D9"

    def test_get_brand_invalid(self):
        """get_brand raises KeyError for invalid company key."""
        with pytest.raises(KeyError):
            get_brand("nonexistent_company")

    def test_get_platform_valid(self):
        """get_platform returns size for valid platform key."""
        platform = get_platform("linkedin_post")
        assert platform["width"] == 1200

    def test_get_platform_invalid(self):
        """get_platform raises KeyError for invalid platform key."""
        with pytest.raises(KeyError):
            get_platform("tiktok_post")

    def test_company_names_mapping(self):
        """COMPANY_NAMES maps keys to full names."""
        assert COMPANY_NAMES["us_framing"] == "US Framing"
        assert COMPANY_NAMES["us_development"] == "US Development"

    def test_company_short_names_mapping(self):
        """COMPANY_SHORT_NAMES maps keys to short codes."""
        assert COMPANY_SHORT_NAMES["us_framing"] == "USF"
        assert COMPANY_SHORT_NAMES["us_interiors"] == "USI"


# ──────────────────────────────────────────────────────────────
# Model Tests
# ──────────────────────────────────────────────────────────────


class TestModels:
    """Test Pydantic models."""

    def test_asset_creation(self):
        """Asset can be created with required fields."""
        asset = Asset(
            company="us_framing",
            type=AssetType.SOCIAL_POST,
            title="Test Asset",
            width=1200,
            height=627,
        )
        assert asset.company == "us_framing"
        assert asset.type == AssetType.SOCIAL_POST
        assert asset.width == 1200
        assert asset.height == 627
        assert asset.status == AssetStatus.GENERATED
        assert len(asset.id) == 12

    def test_asset_dimensions_property(self):
        """Asset dimensions property returns formatted string."""
        asset = Asset(
            company="us_drywall",
            type=AssetType.STAT_CARD,
            title="Test",
            width=1080,
            height=1080,
        )
        assert asset.dimensions == "1080x1080"

    def test_asset_summary(self):
        """Asset summary includes key information."""
        asset = Asset(
            company="us_framing",
            type=AssetType.QUOTE_CARD,
            title="Test Quote",
            width=1200,
            height=627,
        )
        summary = asset.to_summary()
        assert "Test Quote" in summary
        assert "us_framing" in summary
        assert "1200x627" in summary

    def test_asset_tags_default_empty(self):
        """Asset tags default to empty list."""
        asset = Asset(
            company="us_framing",
            type=AssetType.SOCIAL_POST,
            title="Test",
            width=100,
            height=100,
        )
        assert asset.tags == []

    def test_asset_with_tags(self):
        """Asset can be created with tags."""
        asset = Asset(
            company="us_framing",
            type=AssetType.SOCIAL_POST,
            title="Test",
            width=100,
            height=100,
            tags=["project", "showcase", "linkedin"],
        )
        assert len(asset.tags) == 3
        assert "project" in asset.tags

    def test_brand_palette_model(self):
        """BrandPalette validates color fields."""
        palette = BrandPalette(primary="#1B2A4A", accent="#4A90D9")
        assert palette.primary == "#1B2A4A"
        assert palette.text_light == "#FFFFFF"

    def test_platform_size_model(self):
        """PlatformSize computes aspect ratio."""
        size = PlatformSize(name="Test", width=1200, height=627)
        assert size.aspect_ratio == pytest.approx(1200 / 627, rel=1e-4)
        assert size.dimensions_tuple == (1200, 627)

    def test_template_model(self):
        """Template stores name and variables."""
        tmpl = Template(
            name="Test Template",
            html_path="test.html",
            variables=["company_name", "accent_color"],
        )
        assert tmpl.name == "Test Template"
        assert len(tmpl.variables) == 2

    def test_asset_type_enum_values(self):
        """AssetType enum has all expected values."""
        assert AssetType.SOCIAL_POST.value == "social_post"
        assert AssetType.COVER_PHOTO.value == "cover_photo"
        assert AssetType.OG_IMAGE.value == "og_image"
        assert AssetType.FLYER.value == "flyer"
        assert AssetType.STAT_CARD.value == "stat_card"
        assert AssetType.QUOTE_CARD.value == "quote_card"

    def test_asset_status_enum_values(self):
        """AssetStatus enum has all expected values."""
        assert AssetStatus.GENERATED.value == "generated"
        assert AssetStatus.APPROVED.value == "approved"
        assert AssetStatus.REJECTED.value == "rejected"

    def test_asset_serialization(self):
        """Asset can be serialized to dict."""
        asset = Asset(
            company="us_framing",
            type=AssetType.SOCIAL_POST,
            title="Serialize Test",
            width=1200,
            height=627,
            tags=["test"],
        )
        data = asset.model_dump(mode="json")
        assert data["company"] == "us_framing"
        assert data["type"] == "social_post"
        assert data["tags"] == ["test"]


# ──────────────────────────────────────────────────────────────
# Template Engine Tests
# ──────────────────────────────────────────────────────────────


class TestTemplateEngine:
    """Test template rendering and brand injection."""

    def test_inject_brand_colors(self):
        """inject_brand adds all brand colors to variables."""
        from template_engine import TemplateEngine

        engine = TemplateEngine()
        variables = {"project_name": "Test Project"}
        result = engine.inject_brand("us_framing", variables)

        assert result["company_name"] == "US Framing"
        assert result["primary_color"] == "#1B2A4A"
        assert result["accent_color"] == "#4A90D9"
        assert result["project_name"] == "Test Project"

    def test_inject_brand_preserves_custom_vars(self):
        """Custom variables are not overwritten by brand injection."""
        from template_engine import TemplateEngine

        engine = TemplateEngine()
        variables = {"company_name": "Custom Name"}
        result = engine.inject_brand("us_framing", variables)

        # Custom overrides brand
        assert result["company_name"] == "Custom Name"

    def test_html_rendering(self):
        """HTML templates render with Jinja2 variables."""
        from template_engine import TemplateEngine

        engine = TemplateEngine()
        templates = engine.list_templates()
        assert len(templates) >= 4

        html = engine.render_html("stat_card.html", {
            "stat_value": "42",
            "stat_label": "Projects",
            "company_name": "US Framing",
            "company_short": "USF",
            "accent_color": "#4A90D9",
            "primary_color": "#1B2A4A",
        })
        assert "42" in html
        assert "Projects" in html
        assert "#4A90D9" in html

    def test_render_to_image_creates_file(self):
        """render_to_image creates a PNG file."""
        from template_engine import TemplateEngine

        engine = TemplateEngine()

        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "test_output.png"
            img = engine.render_to_image(
                template_type="stat_card",
                company_key="us_framing",
                variables={"stat_value": "99", "stat_label": "Score"},
                width=600,
                height=400,
                output_path=output_path,
            )
            assert output_path.exists()
            assert img.size == (600, 400)

    def test_render_all_template_types(self):
        """All 4 template types render without error."""
        from template_engine import TemplateEngine

        engine = TemplateEngine()

        templates_and_vars = {
            "project_showcase": {"project_name": "Test", "sqft": "1000", "timeline": "3mo", "location": "TX"},
            "social_quote": {"quote_text": "Great work!", "quote_author": "John"},
            "stat_card": {"stat_value": "42", "stat_label": "Projects"},
            "company_header": {"tagline": "Building Excellence"},
        }

        for template_type, variables in templates_and_vars.items():
            img = engine.render_to_image(
                template_type=template_type,
                company_key="us_drywall",
                variables=variables,
                width=800,
                height=400,
            )
            assert img.size == (800, 400), f"Wrong size for {template_type}"

    def test_hex_to_rgb(self):
        """hex_to_rgb converts hex to RGB tuple."""
        from template_engine import hex_to_rgb

        assert hex_to_rgb("#1B2A4A") == (27, 42, 74)
        assert hex_to_rgb("#FFFFFF") == (255, 255, 255)
        assert hex_to_rgb("000000") == (0, 0, 0)

    def test_get_contrast_color(self):
        """get_contrast_color returns appropriate text color."""
        from template_engine import get_contrast_color

        assert get_contrast_color("#1B2A4A") == "#FFFFFF"  # Dark bg -> white text
        assert get_contrast_color("#FFFFFF") == "#1B2A4A"  # Light bg -> dark text


# ──────────────────────────────────────────────────────────────
# Asset Library (CRUD) Tests
# ──────────────────────────────────────────────────────────────


class TestAssetLibrary:
    """Test asset library CRUD operations."""

    def _make_library(self, tmpdir: str):
        """Create a library with a temp database."""
        from asset_library import AssetLibrary

        db_path = Path(tmpdir) / "test_assets.json"
        return AssetLibrary(db_path=db_path)

    def _make_asset(self, **overrides) -> Asset:
        """Create a test asset with defaults."""
        defaults = {
            "company": "us_framing",
            "type": AssetType.SOCIAL_POST,
            "title": "Test Asset",
            "width": 1200,
            "height": 627,
            "tags": ["test"],
        }
        defaults.update(overrides)
        return Asset(**defaults)

    def test_add_and_get(self):
        """Add an asset and retrieve it by ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lib = self._make_library(tmpdir)
            asset = self._make_asset()
            asset_id = lib.add(asset)

            retrieved = lib.get(asset_id)
            assert retrieved is not None
            assert retrieved.title == "Test Asset"
            assert retrieved.company == "us_framing"

    def test_get_nonexistent(self):
        """Getting a nonexistent ID returns None."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lib = self._make_library(tmpdir)
            assert lib.get("nonexistent_id") is None

    def test_delete(self):
        """Delete removes an asset."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lib = self._make_library(tmpdir)
            asset = self._make_asset()
            asset_id = lib.add(asset)

            assert lib.delete(asset_id) is True
            assert lib.get(asset_id) is None

    def test_delete_nonexistent(self):
        """Delete returns False for nonexistent ID."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lib = self._make_library(tmpdir)
            assert lib.delete("nonexistent") is False

    def test_list_all(self):
        """list_all returns all assets."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lib = self._make_library(tmpdir)
            for i in range(3):
                lib.add(self._make_asset(title=f"Asset {i}"))

            all_assets = lib.list_all()
            assert len(all_assets) == 3

    def test_search_by_company(self):
        """Search filters by company."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lib = self._make_library(tmpdir)
            lib.add(self._make_asset(company="us_framing"))
            lib.add(self._make_asset(company="us_drywall"))
            lib.add(self._make_asset(company="us_framing"))

            results = lib.search(company="us_framing")
            assert len(results) == 2

    def test_search_by_type(self):
        """Search filters by asset type."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lib = self._make_library(tmpdir)
            lib.add(self._make_asset(type=AssetType.SOCIAL_POST))
            lib.add(self._make_asset(type=AssetType.STAT_CARD))
            lib.add(self._make_asset(type=AssetType.SOCIAL_POST))

            results = lib.search(asset_type=AssetType.SOCIAL_POST)
            assert len(results) == 2

    def test_search_by_tags(self):
        """Search filters by tags (any match)."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lib = self._make_library(tmpdir)
            lib.add(self._make_asset(tags=["project", "showcase"]))
            lib.add(self._make_asset(tags=["quote", "testimonial"]))
            lib.add(self._make_asset(tags=["project", "stat"]))

            results = lib.search(tags=["project"])
            assert len(results) == 2

    def test_search_by_query(self):
        """Search filters by text query in title."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lib = self._make_library(tmpdir)
            lib.add(self._make_asset(title="Meridian Tower Project"))
            lib.add(self._make_asset(title="Lakewood Medical Center"))
            lib.add(self._make_asset(title="Meridian Plaza"))

            results = lib.search(query="meridian")
            assert len(results) == 2

    def test_update_status(self):
        """Update changes asset status."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lib = self._make_library(tmpdir)
            asset = self._make_asset()
            asset_id = lib.add(asset)

            updated = lib.update(asset_id, status=AssetStatus.APPROVED)
            assert updated is not None
            assert updated.status == AssetStatus.APPROVED

    def test_approve_and_reject(self):
        """Approve and reject convenience methods work."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lib = self._make_library(tmpdir)
            asset = self._make_asset()
            asset_id = lib.add(asset)

            lib.approve(asset_id)
            assert lib.get(asset_id).status == AssetStatus.APPROVED

            lib.reject(asset_id)
            assert lib.get(asset_id).status == AssetStatus.REJECTED

    def test_stats(self):
        """Stats returns counts by company, type, status."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lib = self._make_library(tmpdir)
            lib.add(self._make_asset(company="us_framing", type=AssetType.SOCIAL_POST))
            lib.add(self._make_asset(company="us_drywall", type=AssetType.STAT_CARD))
            lib.add(self._make_asset(company="us_framing", type=AssetType.QUOTE_CARD))

            stats = lib.stats()
            assert stats["total"] == 3
            assert stats["by_company"]["us_framing"] == 2
            assert stats["by_company"]["us_drywall"] == 1

    def test_persistence(self):
        """Library persists data across instances."""
        with tempfile.TemporaryDirectory() as tmpdir:
            db_path = Path(tmpdir) / "persist_test.json"

            from asset_library import AssetLibrary

            lib1 = AssetLibrary(db_path=db_path)
            asset = self._make_asset(title="Persist Test")
            asset_id = lib1.add(asset)

            # New instance reads persisted data
            lib2 = AssetLibrary(db_path=db_path)
            retrieved = lib2.get(asset_id)
            assert retrieved is not None
            assert retrieved.title == "Persist Test"

    def test_count_property(self):
        """count property returns total assets."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lib = self._make_library(tmpdir)
            assert lib.count == 0
            lib.add(self._make_asset())
            assert lib.count == 1

    def test_by_company_shortcut(self):
        """by_company convenience method works."""
        with tempfile.TemporaryDirectory() as tmpdir:
            lib = self._make_library(tmpdir)
            lib.add(self._make_asset(company="us_exteriors"))
            lib.add(self._make_asset(company="us_exteriors"))
            lib.add(self._make_asset(company="us_interiors"))

            results = lib.by_company("us_exteriors")
            assert len(results) == 2


# ──────────────────────────────────────────────────────────────
# Platform Sizer Tests
# ──────────────────────────────────────────────────────────────


class TestPlatformSizer:
    """Test platform resizing logic."""

    def test_safe_zone_calculation(self):
        """Safe zone returns correct boundaries."""
        from platform_sizer import get_safe_zone

        zone = get_safe_zone(1200, 627, pct=0.10)
        assert zone["left"] == 120
        assert zone["top"] == 62
        assert zone["right"] == 1080
        assert zone["bottom"] == 565
        assert zone["inner_width"] == 960
        assert zone["inner_height"] == 503

    def test_safe_zone_custom_pct(self):
        """Safe zone respects custom percentage."""
        from platform_sizer import get_safe_zone

        zone = get_safe_zone(1000, 1000, pct=0.20)
        assert zone["left"] == 200
        assert zone["top"] == 200

    def test_resize_for_platform(self):
        """Resize creates file with correct dimensions."""
        from platform_sizer import resize_for_platform
        from PIL import Image

        with tempfile.TemporaryDirectory() as tmpdir:
            # Create source image
            source = Path(tmpdir) / "source.png"
            img = Image.new("RGB", (2000, 2000), (100, 100, 100))
            img.save(str(source))

            output = resize_for_platform(
                source_path=source,
                platform_key="instagram_post",
                output_dir=Path(tmpdir),
            )
            result_img = Image.open(output)
            assert result_img.size == (1080, 1080)

    def test_resize_for_all_platforms(self):
        """Resize for all platforms creates 8 files."""
        from platform_sizer import resize_for_all_platforms
        from PIL import Image

        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source.png"
            img = Image.new("RGB", (2000, 2000), (100, 100, 100))
            img.save(str(source))

            results = resize_for_all_platforms(
                source_path=source,
                output_dir=Path(tmpdir),
            )
            assert len(results) == 8
            for platform_key, path in results.items():
                assert Path(path).exists()

    def test_resize_nonexistent_source(self):
        """Resize raises FileNotFoundError for missing source."""
        from platform_sizer import resize_for_platform

        with pytest.raises(FileNotFoundError):
            resize_for_platform("/nonexistent/image.png", "linkedin_post")

    def test_resize_invalid_platform(self):
        """Resize raises KeyError for invalid platform."""
        from platform_sizer import resize_for_platform
        from PIL import Image

        with tempfile.TemporaryDirectory() as tmpdir:
            source = Path(tmpdir) / "source.png"
            img = Image.new("RGB", (100, 100), (0, 0, 0))
            img.save(str(source))

            with pytest.raises(KeyError):
                resize_for_platform(source, "invalid_platform")

    def test_list_platform_sizes(self):
        """list_platform_sizes returns all platforms."""
        from platform_sizer import list_platform_sizes

        sizes = list_platform_sizes()
        assert len(sizes) == 8
        keys = {s["key"] for s in sizes}
        assert "linkedin_post" in keys
        assert "instagram_story" in keys

    def test_visualize_safe_zones(self):
        """visualize_safe_zones creates an image."""
        from platform_sizer import visualize_safe_zones

        img = visualize_safe_zones(1200, 627)
        assert img.size == (1200, 627)


# ──────────────────────────────────────────────────────────────
# Brand Color Injection Tests
# ──────────────────────────────────────────────────────────────


class TestBrandInjection:
    """Test brand color injection across all companies."""

    @pytest.mark.parametrize("company_key", COMPANY_KEYS)
    def test_inject_brand_for_each_company(self, company_key):
        """Every company can have its brand injected into variables."""
        from template_engine import TemplateEngine

        engine = TemplateEngine()
        result = engine.inject_brand(company_key, {})

        expected_brand = BRAND_PALETTES[company_key]
        assert result["accent_color"] == expected_brand["accent"]
        assert result["primary_color"] == expected_brand["primary"]
        assert result["company_name"] == expected_brand["name_full"]

    @pytest.mark.parametrize("company_key", COMPANY_KEYS)
    def test_render_image_for_each_company(self, company_key):
        """Every company can render an image without error."""
        from template_engine import TemplateEngine

        engine = TemplateEngine()
        img = engine.render_to_image(
            template_type="stat_card",
            company_key=company_key,
            variables={"stat_value": "100", "stat_label": "Test"},
            width=400,
            height=300,
        )
        assert img.size == (400, 300)
