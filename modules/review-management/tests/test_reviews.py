"""
Tests for the Review Management System.

Covers: sentiment scoring, response tone matching, solicitation
personalisation, testimonial ranking, and config validation.
All tests use mock data only -- no external APIs or services.
"""

from __future__ import annotations

import sys
import os
from datetime import datetime, timedelta

import pytest

# Ensure the parent package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import (
    COMPANIES,
    PLATFORM_CONFIGS,
    SENTIMENT_NEGATIVE_THRESHOLD,
    SENTIMENT_POSITIVE_THRESHOLD,
    SOLICITATION_CADENCE_DAYS,
    get_active_companies,
    get_company,
)
from models import (
    Platform,
    Review,
    ReviewRequest,
    ReviewResponse,
    SentimentResult,
    SentimentTheme,
    Testimonial,
)
from review_monitor import poll_reviews
from review_responder import (
    RATING_TONE_MAP,
    generate_demo_response,
    respond_to_reviews,
)
from review_solicitor import (
    generate_solicitation_email,
    get_demo_requests,
    get_next_cadence_step,
)
from sentiment_analyzer import (
    analyze_review,
    analyze_reviews,
    classify_sentiment,
)
from testimonial_curator import (
    calculate_rank_score,
    curate_testimonials,
    format_quote_block,
)


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------

@pytest.fixture
def positive_review() -> Review:
    return Review(
        id="test-pos-001",
        platform=Platform.GOOGLE,
        company="us_framing",
        rating=5,
        text=(
            "US Framing did an outstanding job on our commercial warehouse project. "
            "The structural framing was completed ahead of schedule and passed "
            "inspection on the first try. Their crew was professional, clean, "
            "and safety-conscious. Would absolutely recommend."
        ),
        author="Test Reviewer Positive",
        date=datetime.utcnow() - timedelta(days=2),
    )


@pytest.fixture
def negative_review() -> Review:
    return Review(
        id="test-neg-001",
        platform=Platform.GOOGLE,
        company="us_exteriors",
        rating=1,
        text=(
            "Very disappointed. The stucco work started cracking within two months. "
            "We have been trying to reach them for warranty repair and keep getting "
            "the runaround. The original work looked nice but clearly was not done right."
        ),
        author="Test Reviewer Negative",
        date=datetime.utcnow() - timedelta(days=5),
    )


@pytest.fixture
def neutral_review() -> Review:
    return Review(
        id="test-neu-001",
        platform=Platform.YELP,
        company="us_drywall",
        rating=3,
        text=(
            "Decent drywall work but the project took longer than quoted. The finish "
            "quality was good once complete. Pricing was fair."
        ),
        author="Test Reviewer Neutral",
        date=datetime.utcnow() - timedelta(days=10),
    )


@pytest.fixture
def all_reviews(positive_review, negative_review, neutral_review) -> list:
    return [positive_review, negative_review, neutral_review]


@pytest.fixture
def sample_request() -> ReviewRequest:
    return ReviewRequest(
        company="us_framing",
        contact_name="John Smith",
        email="john.smith@example.com",
        project_name="Main Street Office Renovation",
        platform_links={},
    )


# ---------------------------------------------------------------------------
# Config validation tests
# ---------------------------------------------------------------------------

class TestConfig:
    """Validate configuration integrity."""

    def test_all_companies_have_required_fields(self):
        for slug, co in COMPANIES.items():
            assert co.slug == slug
            assert co.name
            assert co.full_name
            assert co.status in ("active", "coming_soon")
            assert len(co.services) > 0
            assert len(co.brand_voice_keywords) >= 3

    def test_five_companies_exist(self):
        assert len(COMPANIES) == 5

    def test_four_active_companies(self):
        active = get_active_companies()
        assert len(active) == 4

    def test_us_interiors_is_coming_soon(self):
        co = get_company("us_interiors")
        assert co.status == "coming_soon"

    def test_get_company_raises_for_unknown(self):
        with pytest.raises(KeyError):
            get_company("nonexistent_company")

    def test_platform_configs_have_required_keys(self):
        required_keys = {"name", "api_base", "auth_type", "enabled", "review_endpoint"}
        for slug, cfg in PLATFORM_CONFIGS.items():
            missing = required_keys - set(cfg.keys())
            assert not missing, f"Platform {slug} missing keys: {missing}"

    def test_sentiment_thresholds_are_symmetric(self):
        assert SENTIMENT_POSITIVE_THRESHOLD == -SENTIMENT_NEGATIVE_THRESHOLD

    def test_solicitation_cadence_is_sorted(self):
        assert SOLICITATION_CADENCE_DAYS == sorted(SOLICITATION_CADENCE_DAYS)

    def test_solicitation_cadence_has_four_steps(self):
        assert len(SOLICITATION_CADENCE_DAYS) == 4


# ---------------------------------------------------------------------------
# Sentiment analysis tests
# ---------------------------------------------------------------------------

class TestSentimentAnalysis:
    """Verify sentiment scores stay in [-1, 1] and themes are detected."""

    def test_positive_review_score_in_range(self, positive_review):
        result = analyze_review(positive_review)
        assert -1.0 <= result.score <= 1.0

    def test_negative_review_score_in_range(self, negative_review):
        result = analyze_review(negative_review)
        assert -1.0 <= result.score <= 1.0

    def test_neutral_review_score_in_range(self, neutral_review):
        result = analyze_review(neutral_review)
        assert -1.0 <= result.score <= 1.0

    def test_positive_review_classified_positive(self, positive_review):
        result = analyze_review(positive_review)
        assert result.score > 0, f"Expected positive score, got {result.score}"

    def test_negative_review_classified_negative(self, negative_review):
        result = analyze_review(negative_review)
        assert result.score < 0, f"Expected negative score, got {result.score}"

    def test_sentiment_result_has_themes(self, positive_review):
        result = analyze_review(positive_review)
        assert isinstance(result.themes, list)

    def test_positive_review_detects_timeliness(self, positive_review):
        result = analyze_review(positive_review)
        assert SentimentTheme.TIMELINESS in result.themes

    def test_positive_review_detects_safety(self, positive_review):
        result = analyze_review(positive_review)
        assert SentimentTheme.SAFETY in result.themes

    def test_negative_review_detects_quality(self, negative_review):
        result = analyze_review(negative_review)
        assert SentimentTheme.QUALITY in result.themes

    def test_negative_review_detects_communication(self, negative_review):
        result = analyze_review(negative_review)
        assert SentimentTheme.COMMUNICATION in result.themes

    def test_classify_sentiment_positive(self):
        assert classify_sentiment(0.5) == "positive"

    def test_classify_sentiment_negative(self):
        assert classify_sentiment(-0.5) == "negative"

    def test_classify_sentiment_neutral(self):
        assert classify_sentiment(0.0) == "neutral"

    def test_batch_analysis_returns_correct_count(self, all_reviews):
        results = analyze_reviews(all_reviews)
        assert len(results) == len(all_reviews)

    def test_all_scores_in_valid_range(self, all_reviews):
        results = analyze_reviews(all_reviews)
        for result in results:
            assert -1.0 <= result.score <= 1.0
            assert result.magnitude >= 0.0

    def test_magnitude_is_non_negative(self, positive_review):
        result = analyze_review(positive_review)
        assert result.magnitude >= 0.0

    def test_sentiment_result_model_validation(self):
        result = SentimentResult(score=0.5, magnitude=0.8, themes=[SentimentTheme.QUALITY])
        assert result.score == 0.5
        assert result.magnitude == 0.8
        assert SentimentTheme.QUALITY in result.themes

    def test_score_clamped_to_range(self):
        """SentimentResult should reject scores outside [-1, 1]."""
        with pytest.raises(Exception):
            SentimentResult(score=1.5, magnitude=0.5, themes=[])
        with pytest.raises(Exception):
            SentimentResult(score=-1.5, magnitude=0.5, themes=[])


# ---------------------------------------------------------------------------
# Response tone matching tests
# ---------------------------------------------------------------------------

class TestResponseToneMatching:
    """Verify response tones match star ratings."""

    def test_five_star_gets_enthusiastic_tone(self, positive_review):
        response = generate_demo_response(positive_review)
        assert response.tone == "enthusiastic"

    def test_one_star_gets_empathetic_tone(self, negative_review):
        response = generate_demo_response(negative_review)
        assert response.tone == "empathetic"

    def test_three_star_gets_appreciative_tone(self, neutral_review):
        response = generate_demo_response(neutral_review)
        assert response.tone == "appreciative"

    def test_four_star_gets_grateful_tone(self):
        review = Review(
            id="test-4star",
            platform=Platform.FACEBOOK,
            company="us_drywall",
            rating=4,
            text="Good work, mostly happy with the result. Minor issues.",
            author="Four Star Reviewer",
            date=datetime.utcnow(),
        )
        response = generate_demo_response(review)
        assert response.tone == "grateful"

    def test_two_star_gets_empathetic_tone(self):
        review = Review(
            id="test-2star",
            platform=Platform.YELP,
            company="us_development",
            rating=2,
            text="The project went significantly over timeline. Disappointed.",
            author="Two Star Reviewer",
            date=datetime.utcnow(),
        )
        response = generate_demo_response(review)
        assert response.tone == "empathetic"

    def test_response_contains_author_name(self, positive_review):
        response = generate_demo_response(positive_review)
        assert positive_review.author in response.response_text

    def test_response_brand_voice_score_in_range(self, positive_review):
        response = generate_demo_response(positive_review)
        assert 0.0 <= response.brand_voice_score <= 1.0

    def test_negative_response_offers_resolution(self, negative_review):
        response = generate_demo_response(negative_review)
        text_lower = response.response_text.lower()
        has_resolution = any(
            word in text_lower
            for word in ["call", "reach out", "contact", "phone", "resolve", "right"]
        )
        assert has_resolution, "Negative review response should offer resolution"

    def test_response_model_validation(self):
        resp = ReviewResponse(
            review_id="test-123",
            response_text="Thank you for your review!",
            tone="enthusiastic",
            brand_voice_score=0.85,
        )
        assert resp.review_id == "test-123"
        assert resp.brand_voice_score == 0.85

    def test_rating_tone_map_covers_all_ratings(self):
        for rating in range(1, 6):
            assert rating in RATING_TONE_MAP

    def test_batch_respond_skips_already_replied(self):
        review = Review(
            id="test-replied",
            platform=Platform.GOOGLE,
            company="us_framing",
            rating=5,
            text="Great work!",
            author="Already Replied",
            date=datetime.utcnow(),
            reply="Thanks for the review!",
        )
        responses = respond_to_reviews([review], demo=True)
        assert len(responses) == 0


# ---------------------------------------------------------------------------
# Solicitation personalisation tests
# ---------------------------------------------------------------------------

class TestSolicitationPersonalisation:
    """Verify emails are personalised and cadence is tracked."""

    def test_email_contains_contact_name(self, sample_request):
        email = generate_solicitation_email(sample_request, cadence_day=0)
        assert sample_request.contact_name in email["body"]

    def test_email_contains_project_name(self, sample_request):
        email = generate_solicitation_email(sample_request, cadence_day=0)
        assert sample_request.project_name in email["body"]

    def test_email_contains_company_name(self, sample_request):
        email = generate_solicitation_email(sample_request, cadence_day=0)
        co = get_company(sample_request.company)
        assert co.name in email["body"]

    def test_email_has_review_links(self, sample_request):
        email = generate_solicitation_email(sample_request, cadence_day=0)
        assert "google" in email["body"].lower() or "yelp" in email["body"].lower()

    def test_all_cadence_steps_generate_different_subjects(self, sample_request):
        subjects = set()
        for day in SOLICITATION_CADENCE_DAYS:
            email = generate_solicitation_email(sample_request, cadence_day=day)
            subjects.add(email["subject"])
        assert len(subjects) == 4, "Each cadence step should have a unique subject"

    def test_invalid_cadence_day_raises(self, sample_request):
        with pytest.raises(ValueError):
            generate_solicitation_email(sample_request, cadence_day=99)

    def test_email_from_matches_company(self, sample_request):
        email = generate_solicitation_email(sample_request, cadence_day=0)
        co = get_company(sample_request.company)
        assert email["from_email"] == co.review_request_sender_email

    def test_email_to_matches_request(self, sample_request):
        email = generate_solicitation_email(sample_request, cadence_day=0)
        assert email["to"] == sample_request.email

    def test_demo_requests_cover_four_companies(self):
        requests = get_demo_requests()
        companies = {r.company for r in requests}
        assert len(companies) == 4
        assert "us_interiors" not in companies  # coming_soon

    def test_day_14_email_is_final_follow_up(self, sample_request):
        email = generate_solicitation_email(sample_request, cadence_day=14)
        assert "final" in email["body"].lower()


# ---------------------------------------------------------------------------
# Testimonial ranking tests
# ---------------------------------------------------------------------------

class TestTestimonialRanking:
    """Verify testimonials are ranked and formatted correctly."""

    def test_higher_rating_scores_higher(self):
        review_5 = Review(
            id="rank-5",
            platform=Platform.GOOGLE,
            company="us_framing",
            rating=5,
            text="Excellent work on our project. Professional and reliable team.",
            author="Rank Test 5",
            date=datetime.utcnow(),
        )
        review_4 = Review(
            id="rank-4",
            platform=Platform.GOOGLE,
            company="us_framing",
            rating=4,
            text="Good work on our project. Professional and reliable team.",
            author="Rank Test 4",
            date=datetime.utcnow(),
        )
        score_5 = calculate_rank_score(review_5)
        score_4 = calculate_rank_score(review_4)
        assert score_5 > score_4

    def test_recent_review_scores_higher_than_old(self):
        now = datetime.utcnow()
        review_new = Review(
            id="rank-new",
            platform=Platform.GOOGLE,
            company="us_framing",
            rating=5,
            text="Outstanding work on our commercial project. Great quality.",
            author="Recent Reviewer",
            date=now,
        )
        review_old = Review(
            id="rank-old",
            platform=Platform.GOOGLE,
            company="us_framing",
            rating=5,
            text="Outstanding work on our commercial project. Great quality.",
            author="Old Reviewer",
            date=now - timedelta(days=180),
        )
        score_new = calculate_rank_score(review_new, now=now)
        score_old = calculate_rank_score(review_old, now=now)
        assert score_new > score_old

    def test_rank_score_is_non_negative(self, positive_review):
        score = calculate_rank_score(positive_review)
        assert score >= 0.0

    def test_curate_excludes_low_ratings(self, all_reviews):
        # Run sentiment analysis first
        analyze_reviews(all_reviews)
        testimonials = curate_testimonials(all_reviews)
        for company, items in testimonials.items():
            for t in items:
                assert t.review.rating >= 4

    def test_curate_returns_dict_by_company(self, all_reviews):
        analyze_reviews(all_reviews)
        testimonials = curate_testimonials(all_reviews)
        assert isinstance(testimonials, dict)
        for key in testimonials:
            assert key in COMPANIES

    def test_curate_respects_company_filter(self, all_reviews):
        analyze_reviews(all_reviews)
        testimonials = curate_testimonials(all_reviews, company="us_framing")
        for key in testimonials:
            assert key == "us_framing"

    def test_quote_block_contains_author(self, positive_review):
        formatted = format_quote_block(positive_review, "US Framing")
        assert positive_review.author in formatted

    def test_quote_block_contains_platform(self, positive_review):
        formatted = format_quote_block(positive_review, "US Framing")
        assert "Google" in formatted

    def test_quote_block_contains_stars(self, positive_review):
        formatted = format_quote_block(positive_review, "US Framing")
        assert "5 Star" in formatted

    def test_testimonial_model_validation(self, positive_review):
        formatted = format_quote_block(positive_review, "US Framing")
        testimonial = Testimonial(
            review=positive_review,
            rank_score=0.95,
            formatted_quote=formatted,
        )
        assert testimonial.rank_score == 0.95


# ---------------------------------------------------------------------------
# Monitor tests
# ---------------------------------------------------------------------------

class TestMonitor:
    """Verify the review monitor works in demo mode."""

    def test_demo_poll_returns_reviews(self):
        reviews = poll_reviews(demo=True)
        assert len(reviews) > 0

    def test_demo_poll_filters_by_company(self):
        reviews = poll_reviews(company="us_framing", demo=True)
        for review in reviews:
            assert review.company == "us_framing"

    def test_demo_poll_filters_by_platform(self):
        reviews = poll_reviews(platform="google", demo=True)
        for review in reviews:
            assert review.platform == Platform.GOOGLE

    def test_demo_reviews_have_valid_fields(self):
        reviews = poll_reviews(demo=True)
        for review in reviews:
            assert review.id
            assert review.author
            assert review.text
            assert 1 <= review.rating <= 5
            assert review.company in COMPANIES


# ---------------------------------------------------------------------------
# Model validation tests
# ---------------------------------------------------------------------------

class TestModels:
    """Verify Pydantic model constraints."""

    def test_review_rating_min_max(self):
        with pytest.raises(Exception):
            Review(
                id="invalid",
                platform=Platform.GOOGLE,
                company="us_framing",
                rating=0,
                text="Bad",
                author="Test",
            )
        with pytest.raises(Exception):
            Review(
                id="invalid",
                platform=Platform.GOOGLE,
                company="us_framing",
                rating=6,
                text="Bad",
                author="Test",
            )

    def test_sentiment_score_bounds(self):
        with pytest.raises(Exception):
            SentimentResult(score=2.0, magnitude=0.5, themes=[])

    def test_platform_enum_values(self):
        assert Platform.GOOGLE.value == "google"
        assert Platform.FACEBOOK.value == "facebook"
        assert Platform.YELP.value == "yelp"
        assert Platform.BUILDING_CONNECTED.value == "buildingconnected"

    def test_sentiment_theme_enum_values(self):
        expected = {"quality", "timeliness", "safety", "communication", "price", "cleanup"}
        actual = {t.value for t in SentimentTheme}
        assert actual == expected

    def test_review_request_model(self):
        req = ReviewRequest(
            company="us_framing",
            contact_name="Test Person",
            email="test@example.com",
            project_name="Test Project",
            platform_links={"google": "https://g.page/r/test/review"},
        )
        assert req.company == "us_framing"
        assert req.platform_links["google"] == "https://g.page/r/test/review"
