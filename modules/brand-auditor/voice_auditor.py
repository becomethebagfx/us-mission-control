"""
Brand Consistency Auditor - Voice Auditor
===========================================
Scores content against brand voice guidelines using keyword analysis,
readability metrics (simplified Flesch-Kincaid), and tone consistency.
"""

from __future__ import annotations

import math
import re
from typing import Dict, List, Optional, Tuple

from config import COMPANIES, get_active_companies, get_company
from models import AuditCategory, BrandCheck, Inconsistency, Severity


# ---------------------------------------------------------------------------
# Demo data: simulated content analysis results
# ---------------------------------------------------------------------------

DEMO_CONTENT_ANALYSES: Dict[str, Dict[str, object]] = {
    "us_framing": {
        "sample_text": (
            "US Framing is the nation's largest multi-family wood framing group, "
            "delivering precision structural framing at scale nationwide. Our "
            "craftsmanship and reliability set the standard for multi-family "
            "wood construction projects across the country."
        ),
        "keyword_hits": 7,
        "keyword_total": 8,
        "readability_score": 42.5,  # Flesch-Kincaid grade level
        "tone_scores": {
            "professional": 0.92,
            "authoritative": 0.88,
            "approachable": 0.65,
        },
        "tagline_present": True,
        "pages_analysed": 5,
    },
    "us_drywall": {
        "sample_text": (
            "US Drywall provides expert commercial drywall services with a focus "
            "on quality and professional finish. Our team of experienced "
            "craftspeople deliver interior drywall solutions with attention to detail."
        ),
        "keyword_hits": 6,
        "keyword_total": 8,
        "readability_score": 38.2,
        "tone_scores": {
            "professional": 0.85,
            "authoritative": 0.78,
            "approachable": 0.72,
        },
        "tagline_present": True,
        "pages_analysed": 4,
    },
    "us_exteriors": {
        "sample_text": (
            "We offer complete exterior envelope systems built for durability and "
            "protection. Our weatherproofing and cladding solutions ensure your "
            "building's exterior stands up to the elements."
        ),
        "keyword_hits": 5,
        "keyword_total": 8,
        "readability_score": 35.8,
        "tone_scores": {
            "professional": 0.90,
            "authoritative": 0.82,
            "approachable": 0.70,
        },
        "tagline_present": False,
        "pages_analysed": 4,
    },
    "us_development": {
        "sample_text": (
            "US Development delivers turnkey construction management solutions. "
            "We partner with clients for full project oversight and delivery, "
            "ensuring every development is completed on time and on budget."
        ),
        "keyword_hits": 5,
        "keyword_total": 8,
        "readability_score": 40.1,
        "tone_scores": {
            "professional": 0.88,
            "authoritative": 0.85,
            "approachable": 0.68,
        },
        "tagline_present": True,
        "pages_analysed": 3,
    },
}


# ---------------------------------------------------------------------------
# Readability: Simplified Flesch-Kincaid
# ---------------------------------------------------------------------------

def count_syllables(word: str) -> int:
    """Estimate syllable count for an English word."""
    word = word.lower().strip()
    if not word:
        return 0

    # Simple heuristic based on vowel groups
    vowels = "aeiouy"
    count = 0
    prev_vowel = False
    for char in word:
        is_vowel = char in vowels
        if is_vowel and not prev_vowel:
            count += 1
        prev_vowel = is_vowel

    # Adjust for silent e
    if word.endswith("e") and count > 1:
        count -= 1

    return max(1, count)


def flesch_kincaid_grade(text: str) -> float:
    """
    Calculate simplified Flesch-Kincaid Grade Level.

    FK = 0.39 * (words/sentences) + 11.8 * (syllables/words) - 15.59
    """
    sentences = re.split(r"[.!?]+", text)
    sentences = [s.strip() for s in sentences if s.strip()]
    if not sentences:
        return 0.0

    words = re.findall(r"\b[a-zA-Z]+\b", text)
    if not words:
        return 0.0

    total_syllables = sum(count_syllables(w) for w in words)
    num_words = len(words)
    num_sentences = len(sentences)

    grade = 0.39 * (num_words / num_sentences) + 11.8 * (total_syllables / num_words) - 15.59
    return round(max(0.0, grade), 1)


# ---------------------------------------------------------------------------
# Keyword & Voice Analysis
# ---------------------------------------------------------------------------

def analyse_keyword_presence(text: str, keywords: List[str]) -> Tuple[int, int]:
    """
    Count how many brand keywords appear in the text.

    Returns
    -------
    (hits, total) where hits <= total == len(keywords).
    """
    text_lower = text.lower()
    hits = sum(1 for kw in keywords if kw.lower() in text_lower)
    return hits, len(keywords)


def analyse_tone(text: str) -> Dict[str, float]:
    """
    Simple tone analysis based on word-list heuristics.
    Returns scores 0-1 for professional, authoritative, approachable.
    """
    text_lower = text.lower()
    words = re.findall(r"\b[a-zA-Z]+\b", text_lower)
    total = max(len(words), 1)

    professional_words = {
        "expertise", "professional", "solutions", "deliver", "quality",
        "precision", "standards", "compliance", "ensure", "industry",
        "certified", "management", "strategic", "performance", "efficiency",
    }
    authoritative_words = {
        "leading", "largest", "premier", "proven", "trusted",
        "nationwide", "established", "recognized", "guarantee", "standard",
        "excellence", "superior", "comprehensive", "definitive", "authority",
    }
    approachable_words = {
        "partner", "team", "together", "help", "support",
        "community", "family", "care", "welcome", "friendly",
        "accessible", "easy", "simple", "understand", "guide",
    }

    prof_count = sum(1 for w in words if w in professional_words)
    auth_count = sum(1 for w in words if w in authoritative_words)
    appr_count = sum(1 for w in words if w in approachable_words)

    # Scale: more keyword-dense = higher score, capped at 1.0
    scale_factor = 15.0  # calibration factor
    return {
        "professional": min(1.0, prof_count / total * scale_factor),
        "authoritative": min(1.0, auth_count / total * scale_factor),
        "approachable": min(1.0, appr_count / total * scale_factor),
    }


# ---------------------------------------------------------------------------
# Scoring
# ---------------------------------------------------------------------------

def _compute_voice_score(
    keyword_hits: int,
    keyword_total: int,
    readability_grade: float,
    tone_scores: Dict[str, float],
    tagline_present: bool,
) -> Tuple[float, List[Inconsistency]]:
    """
    Combine keyword, readability, tone, and tagline checks into a single 0-100 score.
    """
    issues: List[Inconsistency] = []

    # Keyword score (30% of total)
    if keyword_total > 0:
        keyword_pct = keyword_hits / keyword_total
    else:
        keyword_pct = 0.0
    keyword_score = keyword_pct * 100

    if keyword_pct < 0.5:
        issues.append(Inconsistency(
            field="keyword_coverage",
            expected=f">= 50% of {keyword_total} brand keywords",
            found=f"{keyword_hits}/{keyword_total} ({keyword_pct:.0%})",
            severity=Severity.warning,
            platform="website",
        ))

    # Readability score (20% of total) - target 8-12 grade level for B2B
    if 8.0 <= readability_grade <= 12.0:
        readability_score = 100.0
    elif readability_grade < 8.0:
        readability_score = max(0, 100 - (8.0 - readability_grade) * 15)
        issues.append(Inconsistency(
            field="readability",
            expected="Grade 8-12 (B2B appropriate)",
            found=f"Grade {readability_grade} (too simple)",
            severity=Severity.info,
            platform="website",
        ))
    else:
        readability_score = max(0, 100 - (readability_grade - 12.0) * 15)
        issues.append(Inconsistency(
            field="readability",
            expected="Grade 8-12 (B2B appropriate)",
            found=f"Grade {readability_grade} (too complex)",
            severity=Severity.warning,
            platform="website",
        ))

    # Tone score (30% of total) - average of tone dimensions
    tone_avg = sum(tone_scores.values()) / max(len(tone_scores), 1)
    tone_score = tone_avg * 100

    for dimension, value in tone_scores.items():
        if value < 0.5:
            issues.append(Inconsistency(
                field=f"tone_{dimension}",
                expected=f"{dimension} >= 0.50",
                found=f"{value:.2f}",
                severity=Severity.warning,
                platform="website",
            ))

    # Tagline score (20% of total)
    tagline_score = 100.0 if tagline_present else 0.0
    if not tagline_present:
        issues.append(Inconsistency(
            field="tagline",
            expected="Brand tagline present on website",
            found="not detected",
            severity=Severity.warning,
            platform="website",
        ))

    # Weighted total
    final = (
        keyword_score * 0.30
        + readability_score * 0.20
        + tone_score * 0.30
        + tagline_score * 0.20
    )

    return round(min(100.0, max(0.0, final)), 1), issues


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def audit_voice(company_slug: str, demo: bool = True, content_text: Optional[str] = None) -> BrandCheck:
    """
    Run a voice / tone audit for the given company.

    Parameters
    ----------
    company_slug : str
        Key from config.COMPANIES.
    demo : bool
        Use built-in demo data when True.
    content_text : str, optional
        Raw page text to analyse when not in demo mode.

    Returns
    -------
    BrandCheck with score 0-100 and findings.
    """
    brand = get_company(company_slug)
    if brand is None:
        return BrandCheck(
            category=AuditCategory.voice,
            score=0,
            details=f"Unknown company: {company_slug}",
        )

    if brand.status == "coming_soon":
        return BrandCheck(
            category=AuditCategory.voice,
            score=0,
            details=f"{brand.official_name} is marked coming_soon; voice audit skipped.",
        )

    if demo:
        analysis = DEMO_CONTENT_ANALYSES.get(company_slug, {})
        keyword_hits = analysis.get("keyword_hits", 0)
        keyword_total = analysis.get("keyword_total", len(brand.voice_keywords))
        readability = analysis.get("readability_score", 0.0)
        tone_scores = analysis.get("tone_scores", {})
        tagline_present = analysis.get("tagline_present", False)
        pages_analysed = analysis.get("pages_analysed", 0)
    else:
        if content_text:
            keyword_hits, keyword_total = analyse_keyword_presence(content_text, brand.voice_keywords)
            readability = flesch_kincaid_grade(content_text)
            tone_scores = analyse_tone(content_text)
            tagline_present = brand.tagline.lower() in content_text.lower() if brand.tagline else False
            pages_analysed = 1
        else:
            keyword_hits, keyword_total = 0, len(brand.voice_keywords)
            readability = 0.0
            tone_scores = {"professional": 0, "authoritative": 0, "approachable": 0}
            tagline_present = False
            pages_analysed = 0

    score, issues = _compute_voice_score(
        keyword_hits, keyword_total, readability, tone_scores, tagline_present
    )

    details = (
        f"Voice audit for {brand.official_name}: "
        f"score {score:.0f}/100 "
        f"(keywords {keyword_hits}/{keyword_total}, readability grade {readability}, "
        f"{pages_analysed} pages analysed, {len(issues)} findings)"
    )

    return BrandCheck(
        category=AuditCategory.voice,
        score=score,
        details=details,
        inconsistencies=issues,
    )


def audit_all_voice(demo: bool = True) -> Dict[str, BrandCheck]:
    """Run voice audit for every active company."""
    results: Dict[str, BrandCheck] = {}
    for slug in get_active_companies():
        results[slug] = audit_voice(slug, demo=demo)
    return results
