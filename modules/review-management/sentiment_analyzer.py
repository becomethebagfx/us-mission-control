"""
Sentiment Analyzer - dual scoring with VADER-style + keyword analysis.

Extracts thematic tags (quality, timeliness, safety, communication, price, cleanup)
and provides per-company and per-platform aggregation.
Score range: -1.0 to 1.0.
"""

from __future__ import annotations

import logging
import re
from collections import Counter, defaultdict
from typing import Dict, List, Optional, Tuple

from config import SENTIMENT_NEGATIVE_THRESHOLD, SENTIMENT_POSITIVE_THRESHOLD
from models import (
    Platform,
    Review,
    SentimentAggregate,
    SentimentResult,
    SentimentTheme,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Keyword lexicons for theme detection
# ---------------------------------------------------------------------------

THEME_KEYWORDS: Dict[SentimentTheme, List[str]] = {
    SentimentTheme.QUALITY: [
        "quality", "craftsmanship", "workmanship", "finish", "flawless",
        "perfect", "solid", "professional", "meticulous", "attention to detail",
        "level-5", "seamless", "sloppy", "poor quality", "defect", "crack",
        "cracking", "inferior", "subpar", "rough",
    ],
    SentimentTheme.TIMELINESS: [
        "on time", "on-time", "schedule", "ahead of schedule", "early",
        "delayed", "late", "behind schedule", "overtime", "deadline",
        "timeline", "on-schedule", "slow", "fast", "quick", "took longer",
        "missed", "grand opening",
    ],
    SentimentTheme.SAFETY: [
        "safety", "safe", "accident", "injury", "osha", "ppe",
        "safety-conscious", "hazard", "dangerous", "incident", "secure",
        "safety-first", "compliant", "code",
    ],
    SentimentTheme.COMMUNICATION: [
        "communication", "communicated", "responsive", "updates", "informed",
        "transparent", "hard to reach", "no response", "ghosted", "ignored",
        "callback", "weekly updates", "proactive", "runaround",
    ],
    SentimentTheme.PRICE: [
        "price", "cost", "budget", "estimate", "expensive", "affordable",
        "overcharge", "value", "fair price", "under budget", "over budget",
        "over the initial estimate", "pricing", "invoice", "bid",
    ],
    SentimentTheme.CLEANUP: [
        "clean", "cleanup", "debris", "mess", "tidy", "dust", "swept",
        "hauled away", "left behind", "cluttered", "organized", "neat",
        "dust-controlled", "clean worksite",
    ],
}


# ---------------------------------------------------------------------------
# Sentiment word lists (simplified VADER-style approach)
# ---------------------------------------------------------------------------

POSITIVE_WORDS = {
    "outstanding", "excellent", "amazing", "fantastic", "wonderful",
    "incredible", "perfect", "flawless", "great", "love", "best",
    "recommend", "impressed", "happy", "pleased", "thrilled",
    "exceeded", "exceptional", "superb", "brilliant", "top-notch",
    "professional", "meticulous", "seamless", "beautiful", "solid",
    "reliable", "trustworthy", "transformed", "dramatic", "helpful",
    "couldn't be happier", "absolutely", "pride", "true",
}

NEGATIVE_WORDS = {
    "disappointed", "terrible", "awful", "horrible", "worst",
    "poor", "bad", "hate", "angry", "frustrated", "unacceptable",
    "unprofessional", "sloppy", "careless", "rude", "overpriced",
    "runaround", "cracking", "delayed", "missed", "defect",
    "debris", "ignored", "ghosted", "subpar", "disappointing",
    "not done right", "falling short", "very disappointed",
}

INTENSIFIERS = {
    "very", "extremely", "incredibly", "absolutely", "truly",
    "completely", "totally", "really", "so", "highly",
}

NEGATORS = {
    "not", "no", "never", "neither", "nor", "hardly",
    "barely", "didn't", "doesn't", "won't", "wouldn't",
    "couldn't", "shouldn't", "isn't", "wasn't", "aren't",
}


# ---------------------------------------------------------------------------
# Core analysis functions
# ---------------------------------------------------------------------------

def _tokenize(text: str) -> List[str]:
    """Simple word tokenizer that preserves multi-word phrases."""
    return re.findall(r"[a-z'-]+", text.lower())


def _vader_style_score(text: str) -> Tuple[float, float]:
    """
    Calculate a VADER-inspired sentiment score.

    Returns:
        (score, magnitude) where score is in [-1, 1] and magnitude >= 0.
    """
    tokens = _tokenize(text)
    text_lower = text.lower()

    positive_hits = 0.0
    negative_hits = 0.0

    # Single word matching
    for i, token in enumerate(tokens):
        is_negated = False
        if i > 0 and tokens[i - 1] in NEGATORS:
            is_negated = True
        if i > 1 and tokens[i - 2] in NEGATORS:
            is_negated = True

        intensity = 1.0
        if i > 0 and tokens[i - 1] in INTENSIFIERS:
            intensity = 1.5

        if token in POSITIVE_WORDS:
            if is_negated:
                negative_hits += 0.75 * intensity
            else:
                positive_hits += 1.0 * intensity
        elif token in NEGATIVE_WORDS:
            if is_negated:
                positive_hits += 0.5 * intensity
            else:
                negative_hits += 1.0 * intensity

    # Multi-word phrase matching
    for phrase in POSITIVE_WORDS:
        if " " in phrase and phrase in text_lower:
            positive_hits += 1.5

    for phrase in NEGATIVE_WORDS:
        if " " in phrase and phrase in text_lower:
            negative_hits += 1.5

    total = positive_hits + negative_hits
    if total == 0:
        return 0.0, 0.0

    score = (positive_hits - negative_hits) / total
    magnitude = total / max(len(tokens), 1)

    return round(max(-1.0, min(1.0, score)), 4), round(magnitude, 4)


def _keyword_score(text: str, rating: int) -> float:
    """
    Calculate sentiment score from keyword density and star rating.

    Blends text analysis with the explicit star rating signal.
    """
    tokens = _tokenize(text)
    text_lower = text.lower()

    pos_count = sum(1 for t in tokens if t in POSITIVE_WORDS)
    neg_count = sum(1 for t in tokens if t in NEGATIVE_WORDS)

    for phrase in POSITIVE_WORDS:
        if " " in phrase and phrase in text_lower:
            pos_count += 1
    for phrase in NEGATIVE_WORDS:
        if " " in phrase and phrase in text_lower:
            neg_count += 1

    word_count = max(len(tokens), 1)
    keyword_ratio = (pos_count - neg_count) / word_count

    # Star rating mapped to [-1, 1]: 1->-1, 2->-0.5, 3->0, 4->0.5, 5->1
    rating_score = (rating - 3) / 2.0

    # Blend: 40% keyword, 60% rating
    blended = 0.4 * keyword_ratio * 5 + 0.6 * rating_score
    return round(max(-1.0, min(1.0, blended)), 4)


def _detect_themes(text: str) -> List[SentimentTheme]:
    """Detect thematic tags present in the review text."""
    text_lower = text.lower()
    detected: List[SentimentTheme] = []

    for theme, keywords in THEME_KEYWORDS.items():
        for keyword in keywords:
            if keyword in text_lower:
                detected.append(theme)
                break

    return detected


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def analyze_review(review: Review) -> SentimentResult:
    """
    Perform dual sentiment analysis on a single review.

    Combines VADER-style text scoring with keyword-rating blending.
    Extracts thematic tags.

    Args:
        review: The Review to analyse.

    Returns:
        SentimentResult with score, magnitude, and themes.
    """
    vader_score, vader_magnitude = _vader_style_score(review.text)
    keyword_sc = _keyword_score(review.text, review.rating)
    themes = _detect_themes(review.text)

    # Final score: average of VADER and keyword scores
    final_score = round((vader_score + keyword_sc) / 2.0, 4)
    final_score = max(-1.0, min(1.0, final_score))

    result = SentimentResult(
        score=final_score,
        magnitude=vader_magnitude,
        themes=themes,
    )

    # Update the review object in place
    review.sentiment_score = final_score
    review.themes = themes

    logger.info(
        "Analyzed review %s: score=%.4f, magnitude=%.4f, themes=%s",
        review.id, final_score, vader_magnitude,
        [t.value for t in themes],
    )

    return result


def analyze_reviews(reviews: List[Review]) -> List[SentimentResult]:
    """Analyse a batch of reviews."""
    return [analyze_review(r) for r in reviews]


def classify_sentiment(score: float) -> str:
    """Classify a sentiment score as positive, negative, or neutral."""
    if score >= SENTIMENT_POSITIVE_THRESHOLD:
        return "positive"
    elif score <= SENTIMENT_NEGATIVE_THRESHOLD:
        return "negative"
    else:
        return "neutral"


def aggregate_by_company(reviews: List[Review]) -> Dict[str, SentimentAggregate]:
    """Aggregate sentiment scores grouped by company."""
    groups: Dict[str, List[Review]] = defaultdict(list)
    for review in reviews:
        groups[review.company].append(review)

    results: Dict[str, SentimentAggregate] = {}
    for company, company_reviews in groups.items():
        scores = [
            r.sentiment_score for r in company_reviews
            if r.sentiment_score is not None
        ]
        if not scores:
            continue

        all_themes: List[SentimentTheme] = []
        for r in company_reviews:
            all_themes.extend(r.themes)
        theme_counts = Counter(all_themes)
        top_themes = [t for t, _ in theme_counts.most_common(3)]

        avg_score = round(sum(scores) / len(scores), 4)
        pos = sum(1 for s in scores if s >= SENTIMENT_POSITIVE_THRESHOLD)
        neg = sum(1 for s in scores if s <= SENTIMENT_NEGATIVE_THRESHOLD)
        neu = len(scores) - pos - neg

        results[company] = SentimentAggregate(
            entity=company,
            avg_score=avg_score,
            total_reviews=len(scores),
            positive_count=pos,
            neutral_count=neu,
            negative_count=neg,
            top_themes=top_themes,
        )

    return results


def aggregate_by_platform(reviews: List[Review]) -> Dict[str, SentimentAggregate]:
    """Aggregate sentiment scores grouped by platform."""
    groups: Dict[str, List[Review]] = defaultdict(list)
    for review in reviews:
        groups[review.platform.value].append(review)

    results: Dict[str, SentimentAggregate] = {}
    for platform, platform_reviews in groups.items():
        scores = [
            r.sentiment_score for r in platform_reviews
            if r.sentiment_score is not None
        ]
        if not scores:
            continue

        all_themes: List[SentimentTheme] = []
        for r in platform_reviews:
            all_themes.extend(r.themes)
        theme_counts = Counter(all_themes)
        top_themes = [t for t, _ in theme_counts.most_common(3)]

        avg_score = round(sum(scores) / len(scores), 4)
        pos = sum(1 for s in scores if s >= SENTIMENT_POSITIVE_THRESHOLD)
        neg = sum(1 for s in scores if s <= SENTIMENT_NEGATIVE_THRESHOLD)
        neu = len(scores) - pos - neg

        results[platform] = SentimentAggregate(
            entity=platform,
            avg_score=avg_score,
            total_reviews=len(scores),
            positive_count=pos,
            neutral_count=neu,
            negative_count=neg,
            top_themes=top_themes,
        )

    return results


def get_demo_analysis(reviews: List[Review]) -> dict:
    """
    Run full demo analysis: analyse all reviews, aggregate by company and platform.

    Returns:
        Dict with 'results', 'by_company', 'by_platform' keys.
    """
    results = analyze_reviews(reviews)
    by_company = aggregate_by_company(reviews)
    by_platform = aggregate_by_platform(reviews)

    return {
        "results": results,
        "by_company": by_company,
        "by_platform": by_platform,
    }
