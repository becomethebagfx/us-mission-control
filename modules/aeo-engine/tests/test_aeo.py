"""
AEO/GEO Content Engine -- Test Suite

Tests for capsule word count validation, schema JSON-LD validity,
optimizer scoring, and query categorization. Uses mock data only.
"""

from __future__ import annotations

import json
import sys
import os

import pytest

# Ensure the aeo-engine package is importable
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config import (
    AEO_SCORING_WEIGHTS,
    CAPSULE_MAX_WORDS,
    CAPSULE_MIN_WORDS,
    COMPANIES,
    GEOGRAPHIC_MODIFIERS,
    PRIMARY_MARKETS,
    TARGET_QUERIES,
    get_company,
    get_active_companies,
    get_all_queries,
    get_queries_for_company,
    expand_query_with_geo,
)
from models import (
    AnswerCapsule,
    CitationReport,
    CitationTrend,
    FAQPair,
    FAQSet,
    OptimizationIssue,
    OptimizationScore,
    QueryIntent,
    SchemaMarkup,
    SchemaType,
    TargetQuery,
)


# ======================================================================
# Config Tests
# ======================================================================


class TestConfig:
    """Tests for config.py."""

    def test_scoring_weights_sum_to_100(self) -> None:
        assert sum(AEO_SCORING_WEIGHTS.values()) == 100

    def test_five_companies_registered(self) -> None:
        assert len(COMPANIES) == 5

    def test_company_slugs(self) -> None:
        expected = {"us_framing", "us_drywall", "us_exteriors", "us_development", "us_interiors"}
        assert set(COMPANIES.keys()) == expected

    def test_us_interiors_is_coming_soon(self) -> None:
        assert COMPANIES["us_interiors"].status == "coming_soon"

    def test_active_companies_excludes_coming_soon(self) -> None:
        active = get_active_companies()
        assert "us_interiors" not in active
        assert len(active) == 4

    def test_get_company_valid_slug(self) -> None:
        company = get_company("us_framing")
        assert company.name == "US Framing"

    def test_get_company_invalid_slug_raises(self) -> None:
        with pytest.raises(KeyError, match="Unknown company slug"):
            get_company("nonexistent_company")

    def test_target_queries_exist_for_all_companies(self) -> None:
        for slug in COMPANIES:
            assert slug in TARGET_QUERIES
            assert len(TARGET_QUERIES[slug]) > 0

    def test_total_queries_at_least_50(self) -> None:
        all_queries = get_all_queries()
        assert len(all_queries) >= 50

    def test_primary_markets_are_four(self) -> None:
        assert len(PRIMARY_MARKETS) == 4

    def test_expand_query_with_geo_no_existing_geo(self) -> None:
        expanded = expand_query_with_geo("best framing contractor")
        assert len(expanded) == len(PRIMARY_MARKETS)
        assert all("best framing contractor" in q for q in expanded)

    def test_expand_query_with_geo_existing_geo_unchanged(self) -> None:
        expanded = expand_query_with_geo("best framing contractor Louisville KY")
        assert len(expanded) == 1
        assert expanded[0] == "best framing contractor Louisville KY"


# ======================================================================
# Capsule Word Count Validation Tests
# ======================================================================


class TestAnswerCapsule:
    """Tests for capsule word count validation (40-60 words)."""

    def _make_text(self, word_count: int) -> str:
        """Generate text with exactly word_count words."""
        words = ["word"] * word_count
        return " ".join(words)

    def test_valid_capsule_40_words(self) -> None:
        text = self._make_text(40)
        capsule = AnswerCapsule(
            content=text,
            word_count=40,
            query="test query",
            company_slug="us_framing",
        )
        assert capsule.word_count == 40

    def test_valid_capsule_50_words(self) -> None:
        text = self._make_text(50)
        capsule = AnswerCapsule(
            content=text,
            word_count=50,
            query="test query",
            company_slug="us_framing",
        )
        assert capsule.word_count == 50

    def test_valid_capsule_60_words(self) -> None:
        text = self._make_text(60)
        capsule = AnswerCapsule(
            content=text,
            word_count=60,
            query="test query",
            company_slug="us_framing",
        )
        assert capsule.word_count == 60

    def test_invalid_capsule_39_words(self) -> None:
        text = self._make_text(39)
        with pytest.raises(Exception, match="(minimum is 40|greater than or equal to 40)"):
            AnswerCapsule(
                content=text,
                word_count=39,
                query="test query",
                company_slug="us_framing",
            )

    def test_invalid_capsule_61_words(self) -> None:
        text = self._make_text(61)
        with pytest.raises(Exception, match="(maximum is 60|less than or equal to 60)"):
            AnswerCapsule(
                content=text,
                word_count=61,
                query="test query",
                company_slug="us_framing",
            )

    def test_invalid_capsule_10_words(self) -> None:
        text = self._make_text(10)
        with pytest.raises(Exception):
            AnswerCapsule(
                content=text,
                word_count=10,
                query="test query",
                company_slug="us_framing",
            )

    def test_invalid_capsule_100_words(self) -> None:
        text = self._make_text(100)
        with pytest.raises(Exception):
            AnswerCapsule(
                content=text,
                word_count=100,
                query="test query",
                company_slug="us_framing",
            )

    def test_mismatched_word_count_raises(self) -> None:
        text = self._make_text(45)
        with pytest.raises(Exception, match="does not match"):
            AnswerCapsule(
                content=text,
                word_count=50,  # Mismatch: says 50 but content has 45
                query="test query",
                company_slug="us_framing",
            )


# ======================================================================
# Schema JSON-LD Validity Tests
# ======================================================================


class TestSchemaMarkup:
    """Tests for schema JSON-LD validation."""

    def test_valid_schema_home_and_construction(self) -> None:
        schema = SchemaMarkup(
            schema_type=SchemaType.HOME_AND_CONSTRUCTION_BUSINESS,
            json_ld={
                "@context": "https://schema.org",
                "@type": "HomeAndConstructionBusiness",
                "name": "US Framing",
                "description": "Framing contractor",
                "telephone": "(502) 555-0101",
            },
            company_slug="us_framing",
        )
        assert schema.schema_type == SchemaType.HOME_AND_CONSTRUCTION_BUSINESS

    def test_valid_schema_faq_page(self) -> None:
        schema = SchemaMarkup(
            schema_type=SchemaType.FAQ_PAGE,
            json_ld={
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "mainEntity": [
                    {
                        "@type": "Question",
                        "name": "What is framing?",
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": "Framing is the structural skeleton of a building.",
                        },
                    }
                ],
            },
        )
        assert schema.schema_type == SchemaType.FAQ_PAGE

    def test_valid_schema_how_to(self) -> None:
        schema = SchemaMarkup(
            schema_type=SchemaType.HOW_TO,
            json_ld={
                "@context": "https://schema.org",
                "@type": "HowTo",
                "name": "Framing Process",
                "step": [
                    {"@type": "HowToStep", "name": "Plan", "text": "Plan the layout."}
                ],
            },
        )
        assert schema.schema_type == SchemaType.HOW_TO

    def test_valid_schema_service(self) -> None:
        schema = SchemaMarkup(
            schema_type=SchemaType.SERVICE,
            json_ld={
                "@context": "https://schema.org",
                "@type": "Service",
                "name": "Wood Framing",
                "provider": {"@type": "Organization", "name": "US Framing"},
            },
        )
        assert schema.schema_type == SchemaType.SERVICE

    def test_valid_schema_local_business(self) -> None:
        schema = SchemaMarkup(
            schema_type=SchemaType.LOCAL_BUSINESS,
            json_ld={
                "@context": "https://schema.org",
                "@type": "LocalBusiness",
                "name": "US Framing - Louisville",
                "address": {
                    "@type": "PostalAddress",
                    "addressLocality": "Louisville",
                    "addressRegion": "KY",
                },
            },
        )
        assert schema.schema_type == SchemaType.LOCAL_BUSINESS

    def test_missing_context_raises(self) -> None:
        with pytest.raises(Exception, match="@context"):
            SchemaMarkup(
                schema_type=SchemaType.FAQ_PAGE,
                json_ld={
                    "@type": "FAQPage",
                    "mainEntity": [],
                },
            )

    def test_missing_type_raises(self) -> None:
        with pytest.raises(Exception, match="@type"):
            SchemaMarkup(
                schema_type=SchemaType.FAQ_PAGE,
                json_ld={
                    "@context": "https://schema.org",
                    "mainEntity": [],
                },
            )

    def test_json_ld_is_serializable(self) -> None:
        schema = SchemaMarkup(
            schema_type=SchemaType.HOME_AND_CONSTRUCTION_BUSINESS,
            json_ld={
                "@context": "https://schema.org",
                "@type": "HomeAndConstructionBusiness",
                "name": "US Framing",
            },
        )
        serialized = json.dumps(schema.json_ld)
        assert isinstance(serialized, str)
        assert "US Framing" in serialized


# ======================================================================
# Schema Generator Tests
# ======================================================================


class TestSchemaGenerator:
    """Tests for schema_generator.py."""

    def test_generate_home_and_construction_business(self) -> None:
        from schema_generator import generate_home_and_construction_business

        schema = generate_home_and_construction_business("us_framing")
        assert schema.schema_type == SchemaType.HOME_AND_CONSTRUCTION_BUSINESS
        assert schema.json_ld["@context"] == "https://schema.org"
        assert schema.json_ld["name"] == "US Framing"
        assert "aggregateRating" in schema.json_ld

    def test_generate_faq_page(self) -> None:
        from schema_generator import generate_faq_page

        qa = [
            {"question": "What is framing?", "answer": "Structural skeleton of buildings."},
            {"question": "How long does it take?", "answer": "8-12 weeks typically."},
        ]
        schema = generate_faq_page(qa, company_slug="us_framing")
        assert schema.schema_type == SchemaType.FAQ_PAGE
        assert len(schema.json_ld["mainEntity"]) == 2

    def test_generate_how_to(self) -> None:
        from schema_generator import generate_how_to

        schema = generate_how_to(
            name="Framing Process",
            description="How we frame buildings.",
            steps=[
                {"name": "Plan", "text": "Create framing plans."},
                {"name": "Build", "text": "Frame the structure."},
            ],
            company_slug="us_framing",
        )
        assert schema.schema_type == SchemaType.HOW_TO
        assert len(schema.json_ld["step"]) == 2

    def test_generate_service(self) -> None:
        from schema_generator import generate_service

        schema = generate_service(
            service_name="Wood Framing",
            description="Professional wood framing services.",
            company_slug="us_framing",
        )
        assert schema.schema_type == SchemaType.SERVICE
        assert schema.json_ld["name"] == "Wood Framing"

    def test_generate_local_business(self) -> None:
        from schema_generator import generate_local_business

        schema = generate_local_business("us_framing", "Nashville TN")
        assert schema.schema_type == SchemaType.LOCAL_BUSINESS
        assert "Nashville" in schema.json_ld["name"]

    def test_generate_all_schemas_produces_multiple(self) -> None:
        from schema_generator import generate_all_schemas

        batch = generate_all_schemas("us_framing")
        # At least: 1 HCB + 8 services + 4 local + 1 howto = 14
        assert len(batch.schemas) >= 10

    def test_validate_json_ld_valid(self) -> None:
        from schema_generator import validate_json_ld

        schema = SchemaMarkup(
            schema_type=SchemaType.HOME_AND_CONSTRUCTION_BUSINESS,
            json_ld={
                "@context": "https://schema.org",
                "@type": "HomeAndConstructionBusiness",
                "name": "US Framing",
                "description": "Framing contractor",
                "telephone": "(502) 555-0101",
            },
        )
        issues = validate_json_ld(schema)
        assert len(issues) == 0

    def test_validate_json_ld_missing_field(self) -> None:
        from schema_generator import validate_json_ld

        schema = SchemaMarkup(
            schema_type=SchemaType.HOME_AND_CONSTRUCTION_BUSINESS,
            json_ld={
                "@context": "https://schema.org",
                "@type": "HomeAndConstructionBusiness",
                "name": "US Framing",
                # Missing description and telephone
            },
        )
        issues = validate_json_ld(schema)
        assert len(issues) > 0
        assert any("description" in i or "telephone" in i for i in issues)

    def test_render_json_ld_script_tag(self) -> None:
        from schema_generator import render_json_ld_script_tag

        schema = SchemaMarkup(
            schema_type=SchemaType.FAQ_PAGE,
            json_ld={
                "@context": "https://schema.org",
                "@type": "FAQPage",
                "mainEntity": [],
            },
        )
        tag = render_json_ld_script_tag(schema)
        assert tag.startswith('<script type="application/ld+json">')
        assert tag.endswith("</script>")
        assert "FAQPage" in tag


# ======================================================================
# Optimizer Scoring Tests (0-100 range)
# ======================================================================


class TestOptimizer:
    """Tests for page_optimizer.py scoring."""

    def test_optimizer_score_range_good_page(self) -> None:
        from page_optimizer import optimize_page, DEMO_HTML_GOOD, DEMO_ROBOTS_TXT

        result = optimize_page(
            html=DEMO_HTML_GOOD,
            robots_txt=DEMO_ROBOTS_TXT,
            page_url="https://example.com/good",
        )
        assert 0 <= result.score <= 100
        assert result.score >= 50  # Good page should score well

    def test_optimizer_score_range_poor_page(self) -> None:
        from page_optimizer import optimize_page, DEMO_HTML_POOR

        result = optimize_page(
            html=DEMO_HTML_POOR,
            robots_txt="",
            page_url="https://example.com/poor",
        )
        assert 0 <= result.score <= 100
        assert result.score < 50  # Poor page should score low

    def test_optimizer_breakdown_has_all_categories(self) -> None:
        from page_optimizer import optimize_page, DEMO_HTML_GOOD

        result = optimize_page(html=DEMO_HTML_GOOD)
        for category in AEO_SCORING_WEIGHTS:
            assert category in result.breakdown
            assert 0 <= result.breakdown[category] <= 100

    def test_optimizer_issues_are_list(self) -> None:
        from page_optimizer import optimize_page, DEMO_HTML_POOR

        result = optimize_page(html=DEMO_HTML_POOR)
        assert isinstance(result.issues, list)
        # Poor page should have at least one issue
        assert len(result.issues) > 0

    def test_optimizer_recommendations_exist_for_poor_page(self) -> None:
        from page_optimizer import optimize_page, DEMO_HTML_POOR

        result = optimize_page(html=DEMO_HTML_POOR)
        assert len(result.recommendations) > 0

    def test_optimizer_empty_html_scores_zero_or_low(self) -> None:
        from page_optimizer import optimize_page

        result = optimize_page(html="")
        assert result.score <= 20

    def test_optimizer_demo_returns_two_results(self) -> None:
        from page_optimizer import optimize_page_demo

        results = optimize_page_demo()
        assert len(results) == 2
        # First should be good, second should be poor
        assert results[0].score > results[1].score


# ======================================================================
# Query Categorization Tests
# ======================================================================


class TestQueryCategorization:
    """Tests for query intent classification."""

    def test_transactional_query_best(self) -> None:
        from query_researcher import _classify_intent

        intent = _classify_intent("best framing contractor Louisville")
        assert intent == QueryIntent.TRANSACTIONAL

    def test_transactional_query_cost(self) -> None:
        from query_researcher import _classify_intent

        intent = _classify_intent("commercial drywall cost per square foot")
        assert intent == QueryIntent.TRANSACTIONAL

    def test_transactional_query_near_me(self) -> None:
        from query_researcher import _classify_intent

        intent = _classify_intent("drywall companies near me")
        assert intent == QueryIntent.TRANSACTIONAL

    def test_informational_query_how(self) -> None:
        from query_researcher import _classify_intent

        intent = _classify_intent("how long does framing take for apartments")
        assert intent == QueryIntent.INFORMATIONAL

    def test_informational_query_what(self) -> None:
        from query_researcher import _classify_intent

        intent = _classify_intent("what is EIFS exterior system")
        assert intent == QueryIntent.INFORMATIONAL

    def test_informational_query_vs(self) -> None:
        from query_researcher import _classify_intent

        intent = _classify_intent("wood framing vs metal framing")
        assert intent == QueryIntent.INFORMATIONAL

    def test_informational_query_explained(self) -> None:
        from query_researcher import _classify_intent

        intent = _classify_intent("drywall finishing levels explained")
        assert intent == QueryIntent.INFORMATIONAL


# ======================================================================
# Target Query Model Tests
# ======================================================================


class TestTargetQuery:
    """Tests for the TargetQuery model."""

    def test_valid_target_query(self) -> None:
        q = TargetQuery(
            query="best framing contractor Louisville KY",
            company_slug="us_framing",
            intent=QueryIntent.TRANSACTIONAL,
            priority=8,
        )
        assert q.priority == 8

    def test_priority_range_validation(self) -> None:
        with pytest.raises(Exception):
            TargetQuery(
                query="test query text",
                company_slug="us_framing",
                priority=11,  # Exceeds max of 10
            )

    def test_priority_min_validation(self) -> None:
        with pytest.raises(Exception):
            TargetQuery(
                query="test query text",
                company_slug="us_framing",
                priority=0,  # Below min of 1
            )

    def test_query_min_length(self) -> None:
        with pytest.raises(Exception):
            TargetQuery(query="hi", company_slug="us_framing")


# ======================================================================
# Optimization Score Model Tests
# ======================================================================


class TestOptimizationScore:
    """Tests for OptimizationScore model validation."""

    def test_valid_score(self) -> None:
        score = OptimizationScore(
            page_url="https://example.com",
            score=75,
        )
        assert score.score == 75

    def test_score_zero(self) -> None:
        score = OptimizationScore(page_url="https://example.com", score=0)
        assert score.score == 0

    def test_score_100(self) -> None:
        score = OptimizationScore(page_url="https://example.com", score=100)
        assert score.score == 100

    def test_score_over_100_raises(self) -> None:
        with pytest.raises(Exception):
            OptimizationScore(page_url="https://example.com", score=101)

    def test_score_negative_raises(self) -> None:
        with pytest.raises(Exception):
            OptimizationScore(page_url="https://example.com", score=-1)


# ======================================================================
# Citation Report Model Tests
# ======================================================================


class TestCitationReport:
    """Tests for CitationReport model."""

    def test_valid_citation_report(self) -> None:
        report = CitationReport(
            query="best framing contractor",
            company_slug="us_framing",
            platform="ChatGPT",
            position=2,
            score=65,
            trend=CitationTrend.UP,
        )
        assert report.score == 65
        assert report.trend == CitationTrend.UP

    def test_score_range_validation(self) -> None:
        with pytest.raises(Exception):
            CitationReport(
                query="test",
                company_slug="us_framing",
                score=101,
            )

    def test_position_must_be_positive(self) -> None:
        with pytest.raises(Exception):
            CitationReport(
                query="test",
                company_slug="us_framing",
                position=0,
            )


# ======================================================================
# Citation Monitor Tests
# ======================================================================


class TestCitationMonitor:
    """Tests for citation_monitor.py."""

    def test_monitor_query_returns_reports(self) -> None:
        from citation_monitor import monitor_query

        reports = monitor_query("best framing contractor", "us_framing")
        assert len(reports) == 4  # 4 platforms
        for r in reports:
            assert 0 <= r.score <= 100

    def test_monitor_company_returns_batch(self) -> None:
        from citation_monitor import monitor_company

        batch = monitor_company("us_framing")
        assert batch.company_slug == "us_framing"
        assert len(batch.reports) > 0
        assert 0 <= batch.average_score <= 100

    def test_monitor_deterministic_scores(self) -> None:
        from citation_monitor import monitor_query

        reports1 = monitor_query("test query", "us_framing")
        reports2 = monitor_query("test query", "us_framing")
        for r1, r2 in zip(reports1, reports2):
            assert r1.score == r2.score
            assert r1.trend == r2.trend

    def test_citation_summary(self) -> None:
        from citation_monitor import monitor_company, get_citation_summary

        batch = monitor_company("us_framing")
        summary = get_citation_summary(batch)
        assert "company" in summary
        assert "overall_average_score" in summary
        assert "platform_breakdown" in summary
        assert "trend_distribution" in summary


# ======================================================================
# Demo Mode Tests
# ======================================================================


class TestDemoMode:
    """Tests for demo mode across all modules."""

    def test_query_researcher_demo(self) -> None:
        from query_researcher import research_queries

        queries = research_queries("us_framing", demo=True)
        assert len(queries) > 0
        for q in queries:
            assert isinstance(q, TargetQuery)

    def test_capsule_generator_demo(self) -> None:
        from capsule_generator import generate_capsules

        batch = generate_capsules("us_framing", demo=True)
        assert len(batch.capsules) > 0
        for capsule in batch.capsules:
            assert 40 <= capsule.word_count <= 60

    def test_faq_generator_demo(self) -> None:
        from faq_generator import generate_faqs

        batch = generate_faqs("us_framing", demo=True)
        assert len(batch.faq_sets) > 0
        for faq_set in batch.faq_sets:
            assert len(faq_set.pairs) >= 1

    def test_faq_schema_generation(self) -> None:
        from faq_generator import generate_faqs, generate_faq_schema

        batch = generate_faqs("us_framing", demo=True)
        for faq_set in batch.faq_sets:
            schema = generate_faq_schema(faq_set)
            assert schema.schema_type == SchemaType.FAQ_PAGE
            assert "@context" in schema.json_ld
            assert "@type" in schema.json_ld


# ======================================================================
# FAQSet Model Tests
# ======================================================================


class TestFAQSet:
    """Tests for FAQSet and FAQPair models."""

    def test_valid_faq_set(self) -> None:
        faq = FAQSet(
            company_slug="us_framing",
            service="wood framing",
            pairs=[
                FAQPair(
                    question="What is wood framing?",
                    answer="Wood framing is the structural skeleton of a building made from lumber.",
                ),
            ],
        )
        assert len(faq.pairs) == 1

    def test_faq_pair_question_min_length(self) -> None:
        with pytest.raises(Exception):
            FAQPair(question="Why?", answer="This is a valid answer to the question.")

    def test_faq_pair_answer_min_length(self) -> None:
        with pytest.raises(Exception):
            FAQPair(question="What is framing construction?", answer="Framing.")

    def test_faq_set_requires_at_least_one_pair(self) -> None:
        with pytest.raises(Exception):
            FAQSet(company_slug="us_framing", service="wood framing", pairs=[])
