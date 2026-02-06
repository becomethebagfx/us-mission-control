"""
GBP Automation Module - Test Suite
Tests for post_generator, photo_manager, location_manager,
insights_tracker, and config validation.
All tests use mock data -- no real API calls.
"""

import json
import os
import sys
import tempfile
from datetime import date, timedelta
from pathlib import Path

import pytest

# Ensure the package root is importable
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from config import (
    ACTIVE_COMPANIES,
    COMPANIES,
    GBP_API_VERSION,
    GBP_BASE_URL,
    OAUTH_SCOPES,
    PHOTO_ALLOWED_FORMATS,
    PHOTO_MAX_BYTES,
    PHOTO_MIN_BYTES,
    PHOTO_SPECS,
    RATE_LIMIT_DAILY,
    get_company,
)
from gbp_client import GBPClient
from insights_tracker import (
    InsightsStore,
    InsightsTracker,
    aggregate_metrics,
    compute_monthly_totals,
    compute_weekly_trends,
)
from location_manager import (
    LocationManager,
    normalize_address,
    normalize_phone,
    verify_nap,
)
from models import (
    CallToAction,
    CallToActionType,
    DailyMetric,
    InsightReport,
    LocalPost,
    Location,
    Photo,
    PhotoCategory,
    PostType,
    StarRating,
)
from photo_manager import (
    PhotoValidationError,
    categorize_photo,
    validate_format,
    validate_size,
)
from post_generator import (
    generate_company_update,
    generate_project_completion,
    generate_service_highlight,
)


# =====================================================================
# Config Validation
# =====================================================================


class TestConfig:
    def test_api_version(self):
        assert GBP_API_VERSION == "v4.9"
        assert GBP_API_VERSION in GBP_BASE_URL

    def test_base_url_format(self):
        assert GBP_BASE_URL.startswith("https://mybusiness.googleapis.com/")

    def test_oauth_scopes_nonempty(self):
        assert len(OAUTH_SCOPES) >= 1
        assert "business.manage" in OAUTH_SCOPES[0]

    def test_rate_limit(self):
        assert RATE_LIMIT_DAILY == 500

    def test_photo_specs_dimensions(self):
        assert PHOTO_SPECS["COVER"]["width"] == 1024
        assert PHOTO_SPECS["COVER"]["height"] == 576
        assert PHOTO_SPECS["PROFILE"]["width"] == 720
        assert PHOTO_SPECS["PROFILE"]["height"] == 720
        assert PHOTO_SPECS["POST"]["width"] == 720
        assert PHOTO_SPECS["POST"]["height"] == 540

    def test_photo_size_limits(self):
        assert PHOTO_MIN_BYTES == 10 * 1024
        assert PHOTO_MAX_BYTES == 5 * 1024 * 1024

    def test_allowed_formats(self):
        assert "JPEG" in PHOTO_ALLOWED_FORMATS
        assert "JPG" in PHOTO_ALLOWED_FORMATS
        assert "PNG" in PHOTO_ALLOWED_FORMATS

    def test_five_companies_registered(self):
        assert len(COMPANIES) == 5

    def test_company_names(self):
        expected = {"US Framing", "US Drywall", "US Exteriors", "US Development", "US Interiors"}
        actual = {co.name for co in COMPANIES.values()}
        assert actual == expected

    def test_accent_colors(self):
        expected_colors = {
            "us_framing": "#4A90D9",
            "us_drywall": "#B8860B",
            "us_exteriors": "#2D5F2D",
            "us_development": "#C4AF94",
            "us_interiors": "#8B5E3C",
        }
        for key, expected in expected_colors.items():
            assert COMPANIES[key].accent_color == expected

    def test_us_interiors_coming_soon(self):
        assert COMPANIES["us_interiors"].coming_soon is True

    def test_active_companies_excludes_coming_soon(self):
        assert "us_interiors" not in ACTIVE_COMPANIES
        assert len(ACTIVE_COMPANIES) == 4

    def test_get_company_by_key(self):
        co = get_company("us_framing")
        assert co is not None
        assert co.name == "US Framing"

    def test_get_company_by_slug(self):
        co = get_company("us-drywall")
        assert co is not None
        assert co.name == "US Drywall"

    def test_get_company_unknown(self):
        assert get_company("nonexistent") is None


# =====================================================================
# Post Generator
# =====================================================================


class TestPostGenerator:
    def test_project_completion_word_count(self):
        post = generate_project_completion(
            company_key="us_framing",
            company_name="US Framing",
            project_name="The Summit Tower",
            milestone="Structural framing completed",
            stats="45,000 sq ft in 6 weeks",
            demo=True,
        )
        word_count = len(post.summary.split())
        assert 150 <= word_count <= 300, (
            f"Project completion post has {word_count} words, expected 150-300"
        )

    def test_project_completion_fields(self):
        post = generate_project_completion(
            company_key="us_framing",
            company_name="US Framing",
            project_name="The Summit Tower",
            milestone="Structural framing completed",
            stats="45,000 sq ft in 6 weeks",
            photo_url="https://example.com/photo.jpg",
            demo=True,
        )
        assert post.company_key == "us_framing"
        assert post.post_type == PostType.WHATS_NEW
        assert post.call_to_action is not None
        assert post.call_to_action.action_type == CallToActionType.LEARN_MORE
        assert post.media_url == "https://example.com/photo.jpg"
        assert post.created_at is not None

    def test_service_highlight_word_count(self):
        post = generate_service_highlight(
            company_key="us_drywall",
            company_name="US Drywall",
            service_name="Level 5 Finish",
            benefits="flawless smooth finish, fast turnaround, competitive pricing",
            demo=True,
        )
        word_count = len(post.summary.split())
        assert 150 <= word_count <= 300, (
            f"Service highlight post has {word_count} words, expected 150-300"
        )

    def test_service_highlight_cta(self):
        post = generate_service_highlight(
            company_key="us_drywall",
            company_name="US Drywall",
            service_name="Level 5 Finish",
            benefits="smooth finish, fast turnaround",
            cta_type=CallToActionType.CALL,
            demo=True,
        )
        assert post.call_to_action.action_type == CallToActionType.CALL

    def test_company_update_news_word_count(self):
        post = generate_company_update(
            company_key="us_development",
            company_name="US Development",
            update_type="news",
            details="We have expanded into the Austin market.",
            demo=True,
        )
        word_count = len(post.summary.split())
        assert 150 <= word_count <= 300, (
            f"Company update post has {word_count} words, expected 150-300"
        )

    def test_company_update_hiring(self):
        post = generate_company_update(
            company_key="us_exteriors",
            company_name="US Exteriors",
            update_type="hiring",
            details="Seeking experienced siding installers.",
            demo=True,
        )
        word_count = len(post.summary.split())
        assert 150 <= word_count <= 300
        assert post.post_type == PostType.WHATS_NEW

    def test_company_update_event(self):
        post = generate_company_update(
            company_key="us_framing",
            company_name="US Framing",
            update_type="event",
            details="Join us at the DFW Construction Expo.",
            event_start=date.today() + timedelta(days=14),
            demo=True,
        )
        assert post.post_type == PostType.EVENT
        assert post.event is not None
        assert post.event.start_date == date.today() + timedelta(days=14)


# =====================================================================
# Photo Manager
# =====================================================================


class TestPhotoManager:
    def _make_temp_file(self, suffix: str, size: int) -> str:
        """Create a temporary file with the given suffix and size."""
        fd, path = tempfile.mkstemp(suffix=suffix)
        with os.fdopen(fd, "wb") as f:
            f.write(b"\x00" * size)
        return path

    def test_validate_format_jpeg(self):
        path = self._make_temp_file(".jpg", 20_000)
        try:
            fmt = validate_format(path)
            assert fmt.value in ("JPEG", "JPG")
        finally:
            os.unlink(path)

    def test_validate_format_png(self):
        path = self._make_temp_file(".png", 20_000)
        try:
            fmt = validate_format(path)
            assert fmt.value == "PNG"
        finally:
            os.unlink(path)

    def test_validate_format_invalid(self):
        path = self._make_temp_file(".gif", 20_000)
        try:
            with pytest.raises(PhotoValidationError, match="Unsupported format"):
                validate_format(path)
        finally:
            os.unlink(path)

    def test_validate_format_bmp_rejected(self):
        path = self._make_temp_file(".bmp", 20_000)
        try:
            with pytest.raises(PhotoValidationError):
                validate_format(path)
        finally:
            os.unlink(path)

    def test_validate_size_valid(self):
        path = self._make_temp_file(".jpg", 50_000)
        try:
            size = validate_size(path)
            assert size == 50_000
        finally:
            os.unlink(path)

    def test_validate_size_too_small(self):
        path = self._make_temp_file(".jpg", 5_000)
        try:
            with pytest.raises(PhotoValidationError, match="too small"):
                validate_size(path)
        finally:
            os.unlink(path)

    def test_validate_size_too_large(self):
        path = self._make_temp_file(".jpg", 6 * 1024 * 1024)
        try:
            with pytest.raises(PhotoValidationError, match="too large"):
                validate_size(path)
        finally:
            os.unlink(path)

    def test_validate_size_boundary_min(self):
        path = self._make_temp_file(".jpg", PHOTO_MIN_BYTES)
        try:
            size = validate_size(path)
            assert size == PHOTO_MIN_BYTES
        finally:
            os.unlink(path)

    def test_validate_size_boundary_max(self):
        path = self._make_temp_file(".jpg", PHOTO_MAX_BYTES)
        try:
            size = validate_size(path)
            assert size == PHOTO_MAX_BYTES
        finally:
            os.unlink(path)

    def test_categorize_with_hint(self):
        assert categorize_photo("test.jpg", hint="cover") == PhotoCategory.COVER
        assert categorize_photo("test.jpg", hint="profile") == PhotoCategory.PROFILE
        assert categorize_photo("test.jpg", hint="post") == PhotoCategory.POST

    def test_categorize_default(self):
        assert categorize_photo("test.jpg") == PhotoCategory.ADDITIONAL

    def test_categorize_invalid_hint_falls_back(self):
        assert categorize_photo("test.jpg", hint="invalid") == PhotoCategory.ADDITIONAL


# =====================================================================
# Location Manager
# =====================================================================


class TestLocationManager:
    def test_normalize_phone(self):
        assert normalize_phone("+1-214-555-0101") == "12145550101"
        assert normalize_phone("(214) 555-0101") == "2145550101"
        assert normalize_phone("214.555.0101") == "2145550101"

    def test_normalize_address(self):
        assert normalize_address("123 Builder Blvd") == "123 builder blvd"
        assert normalize_address("123 Builder Boulevard") == "123 builder blvd"
        assert normalize_address("456 Finish Ave, Suite 200") == "456 finish ave ste 200"

    def test_nap_verification_pass(self):
        from config import COMPANIES

        co = COMPANIES["us_framing"]
        location = Location(
            name="accounts/test/locations/1",
            title="US Framing",
            phone_number="+1-214-555-0101",
            address_lines=["123 Builder Blvd"],
            city="Dallas",
            state="TX",
            postal_code="75201",
            company_key="us_framing",
        )
        results = verify_nap(location, co)
        assert len(results) == 3
        for r in results:
            assert r.matches is True, f"NAP check failed: {r.message}"

    def test_nap_verification_name_mismatch(self):
        from config import COMPANIES

        co = COMPANIES["us_framing"]
        location = Location(
            name="accounts/test/locations/1",
            title="US Framing LLC",
            phone_number="+1-214-555-0101",
            address_lines=["123 Builder Blvd"],
            city="Dallas",
            state="TX",
            postal_code="75201",
            company_key="us_framing",
        )
        results = verify_nap(location, co)
        name_result = next(r for r in results if r.field == "name")
        assert name_result.matches is False

    def test_nap_verification_phone_mismatch(self):
        from config import COMPANIES

        co = COMPANIES["us_drywall"]
        location = Location(
            name="accounts/test/locations/2",
            title="US Drywall",
            phone_number="+1-214-999-9999",
            address_lines=["456 Finish Ave"],
            city="Dallas",
            state="TX",
            postal_code="75202",
            company_key="us_drywall",
        )
        results = verify_nap(location, co)
        phone_result = next(r for r in results if r.field == "phone")
        assert phone_result.matches is False

    def test_demo_locations_count(self):
        locs = LocationManager.demo_locations()
        assert len(locs) == len(ACTIVE_COMPANIES)

    def test_demo_locations_company_keys(self):
        locs = LocationManager.demo_locations()
        keys = {l.company_key for l in locs}
        assert keys == set(ACTIVE_COMPANIES.keys())

    def test_location_manager_sync_demo(self):
        client = GBPClient(demo=True)
        mgr = LocationManager(client, demo=True)
        locs = mgr.sync_locations()
        assert len(locs) == len(ACTIVE_COMPANIES)

    def test_location_manager_filter_company(self):
        client = GBPClient(demo=True)
        mgr = LocationManager(client, demo=True)
        mgr.sync_locations()
        framing = mgr.get_locations_for_company("us_framing")
        assert len(framing) == 1
        assert framing[0].title == "US Framing"

    def test_nap_summary_demo(self):
        client = GBPClient(demo=True)
        mgr = LocationManager(client, demo=True)
        mgr.sync_locations()
        total, mismatches, msgs = mgr.nap_summary()
        assert total > 0
        assert mismatches == 0  # demo data should be consistent


# =====================================================================
# Insights Tracker
# =====================================================================


class TestInsightsTracker:
    def _make_metrics(self, days: int = 30) -> list:
        metrics = []
        for i in range(days):
            d = date.today() - timedelta(days=days - 1 - i)
            metrics.append(
                DailyMetric(
                    location_name="accounts/test/locations/1",
                    company_key="us_framing",
                    date=d,
                    views=100 + i,
                    search_impressions=200 + i * 2,
                    clicks=10 + i,
                    calls=3,
                    direction_requests=5,
                    website_clicks=8,
                )
            )
        return metrics

    def test_aggregate_totals(self):
        metrics = self._make_metrics(30)
        report = aggregate_metrics(metrics, "us_framing", "accounts/test/locations/1")
        assert report.total_views == sum(m.views for m in metrics)
        assert report.total_clicks == sum(m.clicks for m in metrics)
        assert report.total_calls == sum(m.calls for m in metrics)
        assert report.start_date == metrics[0].date
        assert report.end_date == metrics[-1].date

    def test_aggregate_engagement(self):
        metrics = self._make_metrics(7)
        report = aggregate_metrics(metrics, "us_framing", "accounts/test/locations/1")
        expected_engagement = (
            report.total_clicks
            + report.total_calls
            + report.total_direction_requests
            + report.total_website_clicks
        )
        assert report.total_engagement == expected_engagement

    def test_weekly_trends(self):
        metrics = self._make_metrics(14)
        trends = compute_weekly_trends(metrics)
        # With incrementing values, recent week should be higher
        assert "views" in trends
        assert trends["views"] > 0

    def test_weekly_trends_too_few_days(self):
        metrics = self._make_metrics(5)
        trends = compute_weekly_trends(metrics)
        assert trends == {}

    def test_monthly_totals(self):
        metrics = self._make_metrics(60)
        monthly = compute_monthly_totals(metrics)
        assert len(monthly) >= 2  # should span at least 2 months

    def test_insights_store_roundtrip(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            store = InsightsStore(path=path)
            metrics = self._make_metrics(7)
            added = store.store_metrics(metrics)
            assert added == 7

            # Duplicate insert should add 0
            added2 = store.store_metrics(metrics)
            assert added2 == 0

            # Retrieve
            retrieved = store.get_metrics(
                "us_framing",
                "accounts/test/locations/1",
                date.today() - timedelta(days=10),
                date.today(),
            )
            assert len(retrieved) == 7
        finally:
            os.unlink(path)

    def test_insights_store_date_filtering(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = f.name
        try:
            store = InsightsStore(path=path)
            metrics = self._make_metrics(30)
            store.store_metrics(metrics)

            # Only last 7 days
            recent = store.get_metrics(
                "us_framing",
                "accounts/test/locations/1",
                date.today() - timedelta(days=6),
                date.today(),
            )
            assert len(recent) == 7
        finally:
            os.unlink(path)

    def test_demo_data_generation(self):
        client = GBPClient(demo=True)
        tracker = InsightsTracker(client, demo=True)
        # Use a temp file for storage
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            tracker.store = InsightsStore(path=f.name)
        try:
            added = tracker.generate_demo_data(days=14)
            assert added > 0
            reports = tracker.all_reports(days=14)
            assert len(reports) == len(ACTIVE_COMPANIES)
            for report in reports:
                assert report.total_views > 0
        finally:
            os.unlink(tracker.store._path)

    def test_aggregate_empty(self):
        report = aggregate_metrics([], "us_framing", "test/loc")
        assert report.total_views == 0
        assert report.total_engagement == 0


# =====================================================================
# GBP Client (Demo Mode)
# =====================================================================


class TestGBPClientDemo:
    def test_list_locations_demo(self):
        client = GBPClient(demo=True)
        locations = client.list_locations()
        assert len(locations) == len(ACTIVE_COMPANIES)

    def test_get_location_demo(self):
        client = GBPClient(demo=True)
        loc = client.get_location("accounts/demo/locations/1001")
        assert loc.name == "accounts/demo/locations/1001"

    def test_create_post_demo(self):
        client = GBPClient(demo=True)
        post = LocalPost(
            company_key="us_framing",
            post_type=PostType.WHATS_NEW,
            summary="This is a test post for US Framing. " * 15,
        )
        result = client.create_post("accounts/demo/locations/1001", post)
        assert result.name is not None
        assert "localPosts" in result.name

    def test_update_post_demo(self):
        client = GBPClient(demo=True)
        result = client.update_post(
            "accounts/demo/locations/1001/localPosts/abc",
            {"summary": "Updated summary text for the post content here."},
            ["summary"],
        )
        assert result["updateMask"] == ["summary"]

    def test_delete_post_demo(self):
        client = GBPClient(demo=True)
        assert client.delete_post("accounts/demo/locations/1001/localPosts/abc") is True

    def test_list_reviews_demo(self):
        client = GBPClient(demo=True)
        reviews = client.list_reviews("accounts/demo/locations/1001")
        assert len(reviews) == 3
        assert all(r.star_rating in (StarRating.FOUR, StarRating.FIVE) for r in reviews)

    def test_reply_to_review_demo(self):
        client = GBPClient(demo=True)
        reply = client.reply_to_review(
            "accounts/demo/locations/1001/reviews/r001",
            "Thank you for the kind words!",
        )
        assert reply.comment == "Thank you for the kind words!"

    def test_get_daily_metrics_demo(self):
        client = GBPClient(demo=True)
        metrics = client.get_daily_metrics(
            "accounts/demo/locations/1001",
            "us_framing",
            date.today() - timedelta(days=7),
            date.today(),
        )
        assert len(metrics) == 8  # inclusive range
        assert all(m.views > 0 for m in metrics)

    def test_rate_limiter_remaining(self):
        client = GBPClient(demo=True)
        assert client.rate_remaining == 500


# =====================================================================
# Models
# =====================================================================


class TestModels:
    def test_location_full_address(self):
        loc = Location(
            name="test",
            title="Test Co",
            address_lines=["123 Main St"],
            city="Dallas",
            state="TX",
            postal_code="75201",
            company_key="test",
        )
        assert "123 Main St" in loc.full_address
        assert "Dallas, TX 75201" in loc.full_address

    def test_post_summary_too_short(self):
        with pytest.raises(ValueError):
            LocalPost(
                company_key="us_framing",
                post_type=PostType.WHATS_NEW,
                summary="Too short",
            )

    def test_insight_report_engagement(self):
        report = InsightReport(
            company_key="us_framing",
            location_name="test",
            start_date=date.today(),
            end_date=date.today(),
            total_clicks=10,
            total_calls=5,
            total_direction_requests=3,
            total_website_clicks=7,
        )
        assert report.total_engagement == 25
