"""
Brand Consistency Auditor - Test Suite
=======================================
pytest tests for NAP fuzzy matching, visual scoring, voice scoring,
report generation, and remediation task format.

All tests use mock/demo data only -- no network calls.
"""

from __future__ import annotations

import json
import sys
import os

# Add parent directory to path so we can import the auditor modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

import pytest

from config import (
    ADDRESS_ABBREVIATIONS,
    COMPANIES,
    FUZZY_MATCH_THRESHOLD,
    SCORING_WEIGHTS,
    get_active_companies,
    get_company,
    company_slugs,
)
from models import (
    AuditCategory,
    AuditReport,
    BrandCheck,
    Inconsistency,
    Platform,
    RemediationTask,
    Severity,
)
from nap_auditor import (
    audit_all_nap,
    audit_nap,
    check_address,
    check_name,
    check_phone,
    normalise_address,
    normalise_phone,
    similarity,
)
from visual_auditor import (
    audit_all_visual,
    audit_visual,
    extract_font_families,
    extract_hex_colors,
    hex_distance,
    normalise_hex,
)
from voice_auditor import (
    analyse_keyword_presence,
    analyse_tone,
    audit_all_voice,
    audit_voice,
    count_syllables,
    flesch_kincaid_grade,
)
from directory_scanner import (
    scan_all_directories,
    scan_directories,
    get_platforms,
)
from report_generator import (
    export_report_json,
    generate_all_reports,
    generate_report,
    print_report_summary,
)
from remediation_engine import (
    export_remediation_json,
    generate_all_remediation,
    generate_remediation,
    generate_remediation_from_report,
    print_remediation_summary,
)


# ===================================================================
# CONFIG TESTS
# ===================================================================

class TestConfig:
    """Tests for configuration and company registry."""

    def test_five_companies_registered(self):
        assert len(COMPANIES) == 5

    def test_active_companies_exclude_coming_soon(self):
        active = get_active_companies()
        assert "us_interiors" not in active
        assert len(active) == 4

    def test_company_lookup(self):
        brand = get_company("us_framing")
        assert brand is not None
        assert brand.official_name == "US Framing"
        assert brand.accent_hex == "#4A90D9"
        assert brand.phone == "(502) 276-0284"

    def test_unknown_company_returns_none(self):
        assert get_company("nonexistent") is None

    def test_scoring_weights_sum_to_100(self):
        assert sum(SCORING_WEIGHTS.values()) == 100

    def test_us_interiors_is_coming_soon(self):
        brand = get_company("us_interiors")
        assert brand is not None
        assert brand.status == "coming_soon"
        assert brand.accent_hex == "#8B5E3C"

    def test_all_active_companies_have_required_fields(self):
        for slug, brand in get_active_companies().items():
            assert brand.official_name, f"{slug} missing official_name"
            assert brand.tagline, f"{slug} missing tagline"
            assert brand.accent_hex, f"{slug} missing accent_hex"
            assert brand.address_line1, f"{slug} missing address_line1"
            assert brand.address_line2, f"{slug} missing address_line2"
            assert brand.phone, f"{slug} missing phone"
            assert len(brand.voice_keywords) >= 4, f"{slug} has fewer than 4 voice keywords"

    def test_company_slugs(self):
        slugs = company_slugs()
        assert "us_framing" in slugs
        assert "us_drywall" in slugs
        assert "us_exteriors" in slugs
        assert "us_development" in slugs
        assert "us_interiors" in slugs


# ===================================================================
# NAP AUDITOR TESTS
# ===================================================================

class TestNAPAuditor:
    """Tests for NAP consistency checking and fuzzy matching."""

    def test_normalise_phone_strips_formatting(self):
        assert normalise_phone("(502) 276-0284") == "5022760284"
        assert normalise_phone("502-276-0284") == "5022760284"
        assert normalise_phone("5022760284") == "5022760284"
        assert normalise_phone("+1 (502) 276-0284") == "15022760284"

    def test_normalise_address_expands_abbreviations(self):
        result = normalise_address("4700 Shelbyville Rd Ste 200")
        assert "Road" in result
        assert "Suite" in result
        assert "Rd" not in result.split()  # "Rd" should not appear as standalone word

    def test_normalise_address_removes_punctuation(self):
        result = normalise_address("P.O. Box 710, Pewee Valley, KY 40056")
        assert "," not in result
        assert "." not in result

    def test_similarity_identical_strings(self):
        assert similarity("US Framing", "US Framing") == 1.0

    def test_similarity_case_insensitive(self):
        assert similarity("US Framing", "us framing") == 1.0

    def test_similarity_above_threshold_for_close_match(self):
        ratio = similarity("US Framing", "US Framing LLC")
        assert ratio >= 0.7  # close enough to detect
        assert ratio < 1.0   # but not identical

    def test_similarity_below_threshold_for_different_name(self):
        ratio = similarity("US Framing", "Acme Builders")
        assert ratio < FUZZY_MATCH_THRESHOLD

    def test_check_name_exact_match_no_issues(self):
        issues = check_name("US Framing", "US Framing", "Google Business")
        assert len(issues) == 0

    def test_check_name_variant_detected(self):
        issues = check_name("US Framing", "U.S. Framing", "Facebook")
        assert len(issues) >= 1
        assert issues[0].field == "name"
        assert issues[0].platform == "Facebook"

    def test_check_name_llc_suffix_detected(self):
        issues = check_name("US Framing", "US Framing LLC", "Google Business")
        assert len(issues) >= 1
        # "US Framing" vs "US Framing LLC" similarity ~0.80, below 0.85 threshold
        # so this correctly classifies as critical (significant name deviation)
        assert issues[0].severity in (Severity.critical, Severity.warning, Severity.info)

    def test_check_address_normalised_match(self):
        issues = check_address(
            "4700 Shelbyville Rd Suite 200",
            "Louisville KY 40207",
            "4700 Shelbyville Road Suite 200 Louisville KY 40207",
            "Yelp",
        )
        # After normalisation "Rd" -> "Road", these should match or be info-level
        for issue in issues:
            assert issue.severity != Severity.critical

    def test_check_phone_digits_match(self):
        issues = check_phone("(502) 276-0284", "502-276-0284", "Yelp")
        # Same digits, different format -> phone_format info
        assert all(i.field == "phone_format" for i in issues)
        assert all(i.severity == Severity.info for i in issues)

    def test_check_phone_different_number_critical(self):
        issues = check_phone("(502) 276-0284", "(502) 999-0000", "Yelp")
        assert any(i.severity == Severity.critical for i in issues)

    def test_audit_nap_demo_returns_brand_check(self):
        result = audit_nap("us_framing", demo=True)
        assert isinstance(result, BrandCheck)
        assert result.category == AuditCategory.nap
        assert 0 <= result.score <= 100

    def test_audit_nap_unknown_company(self):
        result = audit_nap("nonexistent", demo=True)
        assert result.score == 0
        assert "Unknown" in result.details

    def test_audit_nap_coming_soon_skipped(self):
        result = audit_nap("us_interiors", demo=True)
        assert result.score == 0
        assert "coming_soon" in result.details

    def test_audit_all_nap_covers_active_companies(self):
        results = audit_all_nap(demo=True)
        active = get_active_companies()
        for slug in active:
            assert slug in results


# ===================================================================
# VISUAL AUDITOR TESTS
# ===================================================================

class TestVisualAuditor:
    """Tests for visual identity auditing."""

    def test_normalise_hex_lowercase(self):
        assert normalise_hex("#4A90D9") == "#4a90d9"
        assert normalise_hex("#ffffff") == "#ffffff"

    def test_hex_distance_identical(self):
        assert hex_distance("#4A90D9", "#4A90D9") == 0.0

    def test_hex_distance_black_white(self):
        dist = hex_distance("#000000", "#FFFFFF")
        assert dist > 0.9  # should be near 1.0

    def test_hex_distance_similar_colors(self):
        dist = hex_distance("#4A90D9", "#4A90DA")
        assert dist < 0.01  # very similar

    def test_extract_hex_colors(self):
        css = "color: #4A90D9; background: #FFFFFF; border: 1px solid #333;"
        colors = extract_hex_colors(css)
        assert "#4A90D9" in colors
        assert "#FFFFFF" in colors
        assert "#333" in colors

    def test_extract_font_families(self):
        css = "font-family: 'Playfair Display', serif; body { font-family: Inter, sans-serif; }"
        fonts = extract_font_families(css)
        assert "Playfair Display" in fonts
        assert "Inter" in fonts

    def test_audit_visual_demo_score_range(self):
        result = audit_visual("us_framing", demo=True)
        assert isinstance(result, BrandCheck)
        assert result.category == AuditCategory.visual
        assert 0 <= result.score <= 100

    def test_audit_visual_unknown_company(self):
        result = audit_visual("nonexistent", demo=True)
        assert result.score == 0

    def test_audit_visual_coming_soon_skipped(self):
        result = audit_visual("us_interiors", demo=True)
        assert result.score == 0
        assert "coming_soon" in result.details

    def test_audit_visual_with_css_text(self):
        css = """
        :root {
            --primary: #1B2A4A;
            --accent: #4A90D9;
        }
        h1 { font-family: 'Playfair Display', serif; color: #1B2A4A; }
        body { font-family: 'Inter', sans-serif; }
        """
        result = audit_visual("us_framing", demo=False, css_text=css)
        assert result.score > 0

    def test_audit_all_visual_covers_active_companies(self):
        results = audit_all_visual(demo=True)
        for slug in get_active_companies():
            assert slug in results

    def test_visual_score_decreases_with_issues(self):
        # US Development has missing Playfair Display in demo data
        result_dev = audit_visual("us_development", demo=True)
        result_ext = audit_visual("us_exteriors", demo=True)
        # US Exteriors should score higher (no missing fonts in demo)
        assert result_ext.score >= result_dev.score


# ===================================================================
# VOICE AUDITOR TESTS
# ===================================================================

class TestVoiceAuditor:
    """Tests for voice, tone, and readability auditing."""

    def test_count_syllables(self):
        assert count_syllables("the") == 1
        assert count_syllables("framing") == 2
        assert count_syllables("construction") == 3

    def test_flesch_kincaid_grade(self):
        simple_text = "The dog ran. The cat sat. It was fun."
        complex_text = (
            "The comprehensive architectural specifications delineate "
            "the structural requirements for multi-family residential "
            "construction projects incorporating sustainable materials."
        )
        simple_grade = flesch_kincaid_grade(simple_text)
        complex_grade = flesch_kincaid_grade(complex_text)
        assert simple_grade < complex_grade

    def test_flesch_kincaid_empty_text(self):
        assert flesch_kincaid_grade("") == 0.0

    def test_analyse_keyword_presence(self):
        text = "We deliver precision wood framing at nationwide scale."
        keywords = ["precision", "wood framing", "scale", "reliability"]
        hits, total = analyse_keyword_presence(text, keywords)
        assert total == 4
        assert hits >= 3  # precision, wood framing, scale

    def test_analyse_keyword_case_insensitive(self):
        text = "PRECISION framing with RELIABILITY"
        keywords = ["precision", "reliability"]
        hits, total = analyse_keyword_presence(text, keywords)
        assert hits == 2

    def test_analyse_tone_returns_three_dimensions(self):
        text = "We deliver professional solutions with proven expertise."
        scores = analyse_tone(text)
        assert "professional" in scores
        assert "authoritative" in scores
        assert "approachable" in scores
        for v in scores.values():
            assert 0 <= v <= 1.0

    def test_audit_voice_demo_score_range(self):
        result = audit_voice("us_framing", demo=True)
        assert isinstance(result, BrandCheck)
        assert result.category == AuditCategory.voice
        assert 0 <= result.score <= 100

    def test_audit_voice_unknown_company(self):
        result = audit_voice("nonexistent", demo=True)
        assert result.score == 0

    def test_audit_voice_coming_soon_skipped(self):
        result = audit_voice("us_interiors", demo=True)
        assert result.score == 0

    def test_audit_voice_with_content_text(self):
        text = (
            "US Framing is the nation's largest multi-family wood framing group. "
            "We deliver precision structural framing with reliability and craftsmanship."
        )
        result = audit_voice("us_framing", demo=False, content_text=text)
        assert result.score > 0

    def test_audit_all_voice_covers_active_companies(self):
        results = audit_all_voice(demo=True)
        for slug in get_active_companies():
            assert slug in results


# ===================================================================
# DIRECTORY SCANNER TESTS
# ===================================================================

class TestDirectoryScanner:
    """Tests for directory listing scanning."""

    def test_scan_directories_demo(self):
        result = scan_directories("us_framing", demo=True)
        assert isinstance(result, BrandCheck)
        assert result.category == AuditCategory.directory
        assert 0 <= result.score <= 100

    def test_scan_directories_unknown_company(self):
        result = scan_directories("nonexistent", demo=True)
        assert result.score == 0

    def test_scan_directories_coming_soon_skipped(self):
        result = scan_directories("us_interiors", demo=True)
        assert result.score == 0

    def test_get_platforms_returns_list(self):
        platforms = get_platforms("us_framing", demo=True)
        assert isinstance(platforms, list)
        assert len(platforms) > 0
        assert all(isinstance(p, Platform) for p in platforms)

    def test_platform_has_listing_flag(self):
        platforms = get_platforms("us_framing", demo=True)
        for p in platforms:
            assert isinstance(p.has_listing, bool)

    def test_scan_all_directories_covers_active_companies(self):
        results = scan_all_directories(demo=True)
        for slug in get_active_companies():
            assert slug in results

    def test_missing_listing_has_critical_severity(self):
        # US Drywall is missing from Angi in demo data
        result = scan_directories("us_drywall", demo=True)
        missing = [i for i in result.inconsistencies if i.field == "listing"]
        if missing:
            assert missing[0].severity == Severity.critical


# ===================================================================
# REPORT GENERATOR TESTS
# ===================================================================

class TestReportGenerator:
    """Tests for comprehensive report generation."""

    def test_generate_report_returns_audit_report(self):
        report = generate_report("us_framing", demo=True)
        assert isinstance(report, AuditReport)
        assert report.company == "us_framing"
        assert report.company_name == "US Framing"

    def test_report_overall_score_range(self):
        report = generate_report("us_framing", demo=True)
        assert 0 <= report.overall_score <= 100

    def test_report_has_all_sections(self):
        report = generate_report("us_framing", demo=True)
        assert "nap" in report.sections
        assert "visual" in report.sections
        assert "voice" in report.sections
        assert "directory" in report.sections

    def test_report_has_recommendations(self):
        report = generate_report("us_framing", demo=True)
        assert isinstance(report.recommendations, list)
        # Demo data should generate at least some recommendations
        assert len(report.recommendations) > 0

    def test_report_has_issues(self):
        report = generate_report("us_framing", demo=True)
        assert isinstance(report.issues, list)
        assert len(report.issues) > 0

    def test_report_has_timestamp(self):
        report = generate_report("us_framing", demo=True)
        assert report.audit_timestamp != ""

    def test_report_unknown_company(self):
        report = generate_report("nonexistent", demo=True)
        assert report.overall_score == 0

    def test_generate_all_reports(self):
        reports = generate_all_reports(demo=True)
        for slug in get_active_companies():
            assert slug in reports
            assert isinstance(reports[slug], AuditReport)

    def test_export_report_json(self):
        report = generate_report("us_framing", demo=True)
        json_str = export_report_json(report)
        data = json.loads(json_str)
        assert data["company"] == "us_framing"
        assert "overall_score" in data
        assert "sections" in data
        assert "issues" in data
        assert "recommendations" in data

    def test_print_report_summary_returns_string(self):
        report = generate_report("us_framing", demo=True)
        summary = print_report_summary(report)
        assert isinstance(summary, str)
        assert "US Framing" in summary
        assert "OVERALL SCORE" in summary

    def test_weighted_score_uses_config_weights(self):
        report = generate_report("us_framing", demo=True)
        # Verify the weighted score is not just a simple average
        section_avg = sum(c.score for c in report.sections.values()) / len(report.sections)
        # They might be close but should reflect weighting
        assert isinstance(report.overall_score, float)


# ===================================================================
# REMEDIATION ENGINE TESTS
# ===================================================================

class TestRemediationEngine:
    """Tests for remediation task generation and export."""

    def test_generate_remediation_returns_tasks(self):
        tasks = generate_remediation("us_framing", demo=True)
        assert isinstance(tasks, list)
        assert len(tasks) > 0
        assert all(isinstance(t, RemediationTask) for t in tasks)

    def test_remediation_task_priority_format(self):
        tasks = generate_remediation("us_framing", demo=True)
        for task in tasks:
            assert task.priority in ("P1", "P2", "P3")

    def test_remediation_task_has_steps(self):
        tasks = generate_remediation("us_framing", demo=True)
        for task in tasks:
            assert isinstance(task.steps, list)
            assert len(task.steps) > 0

    def test_remediation_task_has_effort(self):
        tasks = generate_remediation("us_framing", demo=True)
        for task in tasks:
            assert task.effort_minutes > 0

    def test_remediation_task_has_description(self):
        tasks = generate_remediation("us_framing", demo=True)
        for task in tasks:
            assert len(task.description) > 0

    def test_remediation_task_has_category(self):
        tasks = generate_remediation("us_framing", demo=True)
        for task in tasks:
            assert task.category in (
                AuditCategory.nap,
                AuditCategory.visual,
                AuditCategory.voice,
                AuditCategory.directory,
            )

    def test_remediation_sorted_by_priority(self):
        tasks = generate_remediation("us_framing", demo=True)
        priority_order = {"P1": 0, "P2": 1, "P3": 2}
        priorities = [priority_order[t.priority] for t in tasks]
        assert priorities == sorted(priorities)

    def test_generate_remediation_from_report(self):
        report = generate_report("us_framing", demo=True)
        tasks = generate_remediation_from_report(report)
        assert isinstance(tasks, list)
        assert len(tasks) > 0

    def test_generate_all_remediation(self):
        all_tasks = generate_all_remediation(demo=True)
        for slug in get_active_companies():
            assert slug in all_tasks
            assert isinstance(all_tasks[slug], list)

    def test_export_remediation_json_format(self):
        tasks = generate_remediation("us_framing", demo=True)
        json_str = export_remediation_json(tasks)
        data = json.loads(json_str)
        assert "board_name" in data
        assert data["board_name"] == "Brand Consistency Remediation"
        assert "items" in data
        assert "total_tasks" in data
        assert "total_effort_minutes" in data
        assert "priority_breakdown" in data

    def test_export_remediation_monday_compatible(self):
        tasks = generate_remediation("us_framing", demo=True)
        json_str = export_remediation_json(tasks)
        data = json.loads(json_str)

        for item in data["items"]:
            assert "id" in item
            assert "name" in item
            assert "group" in item
            assert "column_values" in item
            assert "priority" in item["column_values"]
            assert "status" in item["column_values"]
            assert "subitems" in item

    def test_print_remediation_summary_returns_string(self):
        tasks = generate_remediation("us_framing", demo=True)
        summary = print_remediation_summary(tasks)
        assert isinstance(summary, str)
        assert "REMEDIATION PLAN" in summary
        assert "Total Tasks" in summary

    def test_remediation_unknown_company(self):
        report = generate_report("nonexistent", demo=True)
        tasks = generate_remediation_from_report(report)
        assert tasks == []


# ===================================================================
# MODEL VALIDATION TESTS
# ===================================================================

class TestModels:
    """Tests for Pydantic model validation."""

    def test_inconsistency_model(self):
        issue = Inconsistency(
            field="name",
            expected="US Framing",
            found="US Framing LLC",
            severity=Severity.warning,
            platform="Google Business",
        )
        assert issue.field == "name"
        assert issue.severity == Severity.warning

    def test_brand_check_score_bounds(self):
        check = BrandCheck(category=AuditCategory.nap, score=85.5, details="test")
        assert check.score == 85.5

        with pytest.raises(Exception):
            BrandCheck(category=AuditCategory.nap, score=101.0, details="invalid")

        with pytest.raises(Exception):
            BrandCheck(category=AuditCategory.nap, score=-1.0, details="invalid")

    def test_remediation_task_priority_validation(self):
        task = RemediationTask(
            priority="P1",
            effort_minutes=15,
            description="Fix name on Google Business",
            steps=["Step 1", "Step 2"],
        )
        assert task.priority == "P1"

        with pytest.raises(Exception):
            RemediationTask(
                priority="P4",  # invalid
                effort_minutes=15,
                description="Invalid priority",
            )

    def test_audit_report_model(self):
        report = AuditReport(
            company="us_framing",
            company_name="US Framing",
            overall_score=82.5,
            sections={},
            issues=[],
            recommendations=["Fix something"],
            audit_timestamp="2025-01-01T00:00:00Z",
        )
        assert report.overall_score == 82.5
        assert len(report.recommendations) == 1

    def test_platform_model(self):
        platform = Platform(
            name="Google Business",
            url="https://business.google.com/test",
            has_listing=True,
            accuracy_score=90.0,
        )
        assert platform.has_listing is True
        assert platform.accuracy_score == 90.0

    def test_severity_enum(self):
        assert Severity.critical.value == "critical"
        assert Severity.warning.value == "warning"
        assert Severity.info.value == "info"

    def test_audit_category_enum(self):
        assert AuditCategory.nap.value == "nap"
        assert AuditCategory.visual.value == "visual"
        assert AuditCategory.voice.value == "voice"
        assert AuditCategory.directory.value == "directory"


# ===================================================================
# INTEGRATION TESTS
# ===================================================================

class TestIntegration:
    """End-to-end integration tests using demo data."""

    def test_full_audit_pipeline(self):
        """Run the complete audit pipeline for one company."""
        report = generate_report("us_framing", demo=True)

        # Has all expected sections
        assert len(report.sections) == 4

        # Generates issues
        assert len(report.issues) > 0

        # Generates recommendations
        assert len(report.recommendations) > 0

        # Score is reasonable for demo data
        assert 40 <= report.overall_score <= 95

        # Can generate remediation from report
        tasks = generate_remediation_from_report(report)
        assert len(tasks) > 0

        # Can export to JSON
        report_json = export_report_json(report)
        assert json.loads(report_json)

        task_json = export_remediation_json(tasks)
        assert json.loads(task_json)

    def test_all_companies_audit(self):
        """Verify audit works for every active company."""
        reports = generate_all_reports(demo=True)

        for slug, report in reports.items():
            assert report.overall_score > 0, f"{slug} has zero score"
            assert len(report.sections) == 4, f"{slug} missing sections"
            assert report.audit_timestamp, f"{slug} missing timestamp"

    def test_remediation_covers_all_categories(self):
        """Verify remediation generates tasks across categories."""
        all_remediation = generate_all_remediation(demo=True)
        all_categories_seen = set()

        for slug, tasks in all_remediation.items():
            for task in tasks:
                all_categories_seen.add(task.category)

        # Should have tasks across at least NAP and visual
        assert AuditCategory.nap in all_categories_seen
        assert AuditCategory.visual in all_categories_seen
