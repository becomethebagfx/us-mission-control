"""
Review Monitor - polls review platforms for new reviews.

In demo mode, returns realistic mock reviews for all active companies.
In live mode, would call platform APIs and normalise responses.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timedelta
from typing import Dict, List, Optional
from uuid import uuid4

from config import (
    DATA_DIR,
    PLATFORM_CONFIGS,
    TIMESTAMPS_FILE,
    get_active_companies,
)
from models import Platform, Review, SentimentTheme

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Timestamp persistence
# ---------------------------------------------------------------------------

def _load_timestamps() -> Dict[str, str]:
    """Load last-check timestamps from JSON file."""
    if os.path.exists(TIMESTAMPS_FILE):
        with open(TIMESTAMPS_FILE, "r") as f:
            return json.load(f)
    return {}


def _save_timestamps(timestamps: Dict[str, str]) -> None:
    """Persist last-check timestamps to JSON file."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(TIMESTAMPS_FILE, "w") as f:
        json.dump(timestamps, f, indent=2)


def _get_last_check(company: str, platform: str) -> Optional[datetime]:
    """Get the last check timestamp for a company/platform pair."""
    timestamps = _load_timestamps()
    key = f"{company}:{platform}"
    if key in timestamps:
        return datetime.fromisoformat(timestamps[key])
    return None


def _set_last_check(company: str, platform: str, when: datetime) -> None:
    """Set the last check timestamp for a company/platform pair."""
    timestamps = _load_timestamps()
    key = f"{company}:{platform}"
    timestamps[key] = when.isoformat()
    _save_timestamps(timestamps)


# ---------------------------------------------------------------------------
# Demo / mock data
# ---------------------------------------------------------------------------

MOCK_REVIEWS: List[dict] = [
    # US Framing reviews
    {
        "company": "us_framing",
        "platform": "google",
        "rating": 5,
        "text": (
            "US Framing did an outstanding job on our commercial warehouse project. "
            "The structural framing was completed two days ahead of schedule and "
            "passed inspection on the first try. Their crew was professional, clean, "
            "and safety-conscious. Would absolutely recommend."
        ),
        "author": "Mike Henderson",
    },
    {
        "company": "us_framing",
        "platform": "yelp",
        "rating": 4,
        "text": (
            "Good framing work on our office renovation. The metal framing was solid "
            "and the crew kept the site tidy. Only reason for 4 stars is communication "
            "could have been slightly better about schedule changes."
        ),
        "author": "Sarah Mitchell",
    },
    {
        "company": "us_framing",
        "platform": "google",
        "rating": 2,
        "text": (
            "Framing work was okay but they left a lot of debris behind and we had "
            "to call twice about cleanup. The actual structural work seems fine but "
            "the job site management was disappointing."
        ),
        "author": "Tony Russo",
    },
    # US Drywall reviews
    {
        "company": "us_drywall",
        "platform": "google",
        "rating": 5,
        "text": (
            "Absolutely flawless finish on our new office space. The level-5 finish "
            "they delivered was perfect for our paint-only walls. Dust was controlled "
            "throughout the process. The team was meticulous."
        ),
        "author": "Jennifer Park",
    },
    {
        "company": "us_drywall",
        "platform": "facebook",
        "rating": 5,
        "text": (
            "US Drywall transformed our retail space. Seamless walls, perfectly smooth "
            "surfaces, and they finished right on time. Their attention to detail is "
            "unmatched in the industry."
        ),
        "author": "Carlos Mendez",
    },
    {
        "company": "us_drywall",
        "platform": "yelp",
        "rating": 3,
        "text": (
            "Decent drywall work but the project took longer than quoted. The finish "
            "quality was good once complete. Pricing was fair. Would consider using "
            "them again for a less time-sensitive project."
        ),
        "author": "Linda Chen",
    },
    # US Exteriors reviews
    {
        "company": "us_exteriors",
        "platform": "google",
        "rating": 5,
        "text": (
            "Our building's new facade looks incredible. US Exteriors handled the "
            "stucco and siding work flawlessly. The curb appeal improvement is "
            "dramatic. They also waterproofed the entire exterior. Couldn't be happier."
        ),
        "author": "David Kim",
    },
    {
        "company": "us_exteriors",
        "platform": "facebook",
        "rating": 4,
        "text": (
            "Good exterior renovation work. The siding installation was clean and "
            "the final look is very professional. They were a bit over the initial "
            "estimate but explained the additional waterproofing needed."
        ),
        "author": "Rachel Thompson",
    },
    {
        "company": "us_exteriors",
        "platform": "google",
        "rating": 1,
        "text": (
            "Very disappointed. The stucco work started cracking within two months. "
            "We have been trying to reach them for warranty repair and keep getting "
            "the runaround. The original work looked nice but clearly was not done right."
        ),
        "author": "James Wright",
    },
    # US Development reviews
    {
        "company": "us_development",
        "platform": "google",
        "rating": 5,
        "text": (
            "US Development managed our full tenant improvement project from start "
            "to finish. Their project management was transparent with weekly updates "
            "and they came in under budget. True turnkey experience."
        ),
        "author": "Amanda Foster",
    },
    {
        "company": "us_development",
        "platform": "yelp",
        "rating": 4,
        "text": (
            "Solid general contracting work on our retail buildout. The milestone "
            "tracking was helpful and the team communicated well. Minor punch list "
            "items took a bit long to resolve but overall a great experience."
        ),
        "author": "Robert Garcia",
    },
    {
        "company": "us_development",
        "platform": "facebook",
        "rating": 2,
        "text": (
            "The project went significantly over the original timeline. While the "
            "final quality was acceptable, the delays caused us to miss our grand "
            "opening date. Communication about schedule slips was not proactive enough."
        ),
        "author": "Patricia Long",
    },
]


def _generate_mock_reviews(
    company: Optional[str] = None,
    platform: Optional[str] = None,
) -> List[Review]:
    """Generate mock Review objects from the static dataset."""
    reviews = []
    now = datetime.utcnow()

    for i, mock in enumerate(MOCK_REVIEWS):
        if company and mock["company"] != company:
            continue
        if platform and mock["platform"] != platform:
            continue

        review_date = now - timedelta(hours=(len(MOCK_REVIEWS) - i) * 8)
        review = Review(
            id=f"{mock['platform']}-{uuid4().hex[:8]}",
            platform=Platform(mock["platform"]),
            company=mock["company"],
            rating=mock["rating"],
            text=mock["text"],
            author=mock["author"],
            date=review_date,
        )
        reviews.append(review)

    return reviews


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def poll_reviews(
    company: Optional[str] = None,
    platform: Optional[str] = None,
    demo: bool = True,
) -> List[Review]:
    """
    Poll review platforms for new reviews.

    Args:
        company: Filter to a specific company slug. None = all active companies.
        platform: Filter to a specific platform. None = all enabled platforms.
        demo: If True, return mock reviews. If False, call live APIs.

    Returns:
        List of new Review objects found since last check.
    """
    if demo:
        logger.info("Running in DEMO mode - returning mock reviews")
        reviews = _generate_mock_reviews(company=company, platform=platform)
        logger.info("Found %d mock reviews", len(reviews))
        return reviews

    # --- Live mode (stub - would call real APIs) ---
    logger.info("Running in LIVE mode - polling platform APIs")
    all_reviews: List[Review] = []
    active_companies = get_active_companies()

    if company:
        if company not in active_companies:
            logger.warning("Company '%s' is not active, skipping", company)
            return []
        target_companies = {company: active_companies[company]}
    else:
        target_companies = active_companies

    target_platforms = (
        [platform] if platform else
        [p for p, cfg in PLATFORM_CONFIGS.items() if cfg["enabled"]]
    )

    for co_slug, co_profile in target_companies.items():
        for plat in target_platforms:
            last_check = _get_last_check(co_slug, plat)
            logger.info(
                "Checking %s on %s (last check: %s)",
                co_slug, plat, last_check or "never",
            )

            # In live mode, you would:
            # 1. Build auth headers from PLATFORM_CONFIGS[plat]
            # 2. GET the review endpoint
            # 3. Filter by date > last_check
            # 4. Normalise response into Review objects
            # 5. Append to all_reviews

            _set_last_check(co_slug, plat, datetime.utcnow())

    return all_reviews


def detect_new_reviews(
    reviews: List[Review],
    company: Optional[str] = None,
    platform: Optional[str] = None,
) -> List[Review]:
    """
    Filter a list of reviews to only those newer than the last check.

    Args:
        reviews: Full review list to filter.
        company: Company slug to check timestamp for.
        platform: Platform slug to check timestamp for.

    Returns:
        Reviews that are newer than the stored last-check timestamp.
    """
    new_reviews = []
    for review in reviews:
        co = company or review.company
        plat = platform or review.platform.value
        last_check = _get_last_check(co, plat)

        if last_check is None or review.date > last_check:
            new_reviews.append(review)

    return new_reviews


def save_reviews(reviews: List[Review]) -> None:
    """Persist reviews to the local JSON store."""
    os.makedirs(DATA_DIR, exist_ok=True)
    existing: List[dict] = []
    reviews_file = os.path.join(DATA_DIR, "reviews.json")

    if os.path.exists(reviews_file):
        with open(reviews_file, "r") as f:
            existing = json.load(f)

    existing_ids = {r["id"] for r in existing}
    for review in reviews:
        if review.id not in existing_ids:
            existing.append(review.model_dump(mode="json"))

    with open(reviews_file, "w") as f:
        json.dump(existing, f, indent=2, default=str)

    logger.info("Saved %d reviews (total: %d)", len(reviews), len(existing))
