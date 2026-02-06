"""
Testimonial Curator - selects and formats top reviews for marketing.

Ranks reviews by impact using a composite score:
  score * text_length_factor * recency_weight

Selects top 5 per company, formats as quote blocks for website/marketing.
"""

from __future__ import annotations

import json
import logging
import math
import os
from datetime import datetime
from typing import Dict, List, Optional

from config import COMPANIES, DATA_DIR, TESTIMONIALS_FILE, get_company
from models import Review, SentimentTheme, Testimonial

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Scoring constants
# ---------------------------------------------------------------------------

# Ideal review length for marketing (words). Reviews near this length score highest.
IDEAL_LENGTH_WORDS = 40

# How quickly recency decays (higher = faster decay for old reviews)
RECENCY_DECAY_FACTOR = 0.02

# Minimum star rating to consider for testimonials
MIN_RATING_FOR_TESTIMONIAL = 4

# Maximum testimonials per company
TOP_N_PER_COMPANY = 5


# ---------------------------------------------------------------------------
# Scoring functions
# ---------------------------------------------------------------------------

def _word_count(text: str) -> int:
    """Count words in a string."""
    return len(text.split())


def _length_factor(text: str) -> float:
    """
    Score based on text length. Peaks at IDEAL_LENGTH_WORDS.

    Short reviews (<10 words) are penalised.
    Very long reviews get a slight penalty for marketing conciseness.
    """
    wc = _word_count(text)
    if wc < 10:
        return 0.3
    if wc <= IDEAL_LENGTH_WORDS:
        return 0.6 + 0.4 * (wc / IDEAL_LENGTH_WORDS)
    # Slight decay for very long reviews
    over = wc - IDEAL_LENGTH_WORDS
    return max(0.6, 1.0 - over * 0.005)


def _recency_weight(review_date: datetime, now: Optional[datetime] = None) -> float:
    """
    Exponential decay weighting by recency.

    Recent reviews score higher. A review from today = 1.0.
    """
    now = now or datetime.utcnow()
    days_old = max((now - review_date).days, 0)
    return math.exp(-RECENCY_DECAY_FACTOR * days_old)


def _sentiment_factor(review: Review) -> float:
    """
    Boost score based on sentiment analysis results.

    Reviews with detected positive themes get a bonus.
    """
    base = 1.0
    if review.sentiment_score is not None and review.sentiment_score > 0.5:
        base += 0.2
    if review.themes:
        # Bonus for having multiple positive themes mentioned
        base += min(len(review.themes) * 0.05, 0.15)
    return base


def calculate_rank_score(review: Review, now: Optional[datetime] = None) -> float:
    """
    Calculate the composite ranking score for a review.

    score = rating_normalised * length_factor * recency_weight * sentiment_factor

    Args:
        review: The review to score.
        now: Reference time for recency calculation.

    Returns:
        Composite score >= 0.
    """
    # Normalise rating to [0, 1] range
    rating_norm = review.rating / 5.0

    length_f = _length_factor(review.text)
    recency_w = _recency_weight(review.date, now)
    sentiment_f = _sentiment_factor(review)

    score = rating_norm * length_f * recency_w * sentiment_f
    return round(score, 4)


# ---------------------------------------------------------------------------
# Quote formatting
# ---------------------------------------------------------------------------

def _truncate_for_marketing(text: str, max_words: int = 60) -> str:
    """Truncate review text for marketing use, ending at a sentence boundary."""
    words = text.split()
    if len(words) <= max_words:
        return text

    truncated = " ".join(words[:max_words])
    # Try to end at a sentence boundary
    last_period = truncated.rfind(".")
    last_excl = truncated.rfind("!")
    last_boundary = max(last_period, last_excl)

    if last_boundary > len(truncated) * 0.5:
        return truncated[: last_boundary + 1]
    return truncated + "..."


def format_quote_block(review: Review, company_name: str) -> str:
    """
    Format a review as a marketing-ready quote block.

    Example output:
    -----------------------------------------------
    "US Framing did an outstanding job on our
    commercial warehouse project..."

    -- Mike Henderson
       Google Review | 5 Stars
       US Framing
    -----------------------------------------------
    """
    quote_text = _truncate_for_marketing(review.text)
    platform_display = {
        "google": "Google Review",
        "facebook": "Facebook Review",
        "yelp": "Yelp Review",
        "buildingconnected": "BuildingConnected Review",
    }
    platform_name = platform_display.get(review.platform.value, review.platform.value)
    stars = review.rating

    lines = [
        '"{}"'.format(quote_text),
        "",
        "-- {}".format(review.author),
        "   {} | {} Star{}".format(platform_name, stars, "s" if stars != 1 else ""),
        "   {}".format(company_name),
    ]

    return "\n".join(lines)


def format_html_testimonial(review: Review, company_name: str) -> str:
    """Format a review as an HTML testimonial card."""
    quote_text = _truncate_for_marketing(review.text)
    stars_html = "".join(
        '<span class="star filled">&#9733;</span>' if i < review.rating
        else '<span class="star">&#9734;</span>'
        for i in range(5)
    )

    return (
        '<div class="testimonial-card">\n'
        '  <div class="stars">{stars}</div>\n'
        '  <blockquote>"{quote}"</blockquote>\n'
        '  <div class="attribution">\n'
        '    <strong>{author}</strong>\n'
        '    <span class="platform">{platform}</span>\n'
        '  </div>\n'
        '</div>'
    ).format(
        stars=stars_html,
        quote=quote_text,
        author=review.author,
        platform=review.platform.value.title(),
    )


# ---------------------------------------------------------------------------
# Curation
# ---------------------------------------------------------------------------

def curate_testimonials(
    reviews: List[Review],
    company: Optional[str] = None,
    top_n: int = TOP_N_PER_COMPANY,
    now: Optional[datetime] = None,
) -> Dict[str, List[Testimonial]]:
    """
    Select and format top testimonials per company.

    Args:
        reviews: All reviews to consider.
        company: Optional filter to a specific company slug.
        top_n: Number of top testimonials per company.
        now: Reference time for recency scoring.

    Returns:
        Dict mapping company slug to list of Testimonial objects.
    """
    # Filter to eligible reviews
    eligible = [
        r for r in reviews
        if r.rating >= MIN_RATING_FOR_TESTIMONIAL
        and (company is None or r.company == company)
    ]

    if not eligible:
        logger.info("No eligible reviews found for testimonial curation")
        return {}

    # Group by company
    by_company: Dict[str, List[Review]] = {}
    for review in eligible:
        by_company.setdefault(review.company, []).append(review)

    results: Dict[str, List[Testimonial]] = {}

    for co_slug, co_reviews in by_company.items():
        co_profile = get_company(co_slug)

        # Score and sort
        scored = []
        for review in co_reviews:
            score = calculate_rank_score(review, now)
            scored.append((review, score))

        scored.sort(key=lambda x: x[1], reverse=True)
        top = scored[:top_n]

        testimonials = []
        for review, score in top:
            formatted = format_quote_block(review, co_profile.name)
            testimonial = Testimonial(
                review=review,
                rank_score=score,
                formatted_quote=formatted,
            )
            testimonials.append(testimonial)

        results[co_slug] = testimonials
        logger.info(
            "Curated %d testimonials for %s (from %d eligible)",
            len(testimonials), co_slug, len(co_reviews),
        )

    return results


def save_testimonials(testimonials: Dict[str, List[Testimonial]]) -> None:
    """Persist curated testimonials to JSON file."""
    os.makedirs(DATA_DIR, exist_ok=True)
    output = {}
    for company, items in testimonials.items():
        output[company] = [t.model_dump(mode="json") for t in items]

    with open(TESTIMONIALS_FILE, "w") as f:
        json.dump(output, f, indent=2, default=str)

    total = sum(len(v) for v in testimonials.values())
    logger.info("Saved %d testimonials across %d companies", total, len(testimonials))


def print_testimonials(testimonials: Dict[str, List[Testimonial]]) -> None:
    """Pretty-print curated testimonials to stdout."""
    for company, items in testimonials.items():
        co_profile = get_company(company)
        print(f"\n{'=' * 60}")
        print(f"  {co_profile.name} - Top Testimonials")
        print(f"{'=' * 60}")

        for i, testimonial in enumerate(items, 1):
            print(f"\n  #{i} (Score: {testimonial.rank_score:.4f})")
            print(f"  {'-' * 50}")
            for line in testimonial.formatted_quote.split("\n"):
                print(f"  {line}")
            print(f"  {'-' * 50}")

    total = sum(len(v) for v in testimonials.values())
    print(f"\n  Total testimonials curated: {total}")
