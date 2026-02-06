"""
Pydantic models and enums for the Review Management System.

Covers reviews, responses, solicitations, sentiment analysis,
and testimonial curation across all platforms and companies.
"""

from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Platform(str, Enum):
    """Supported review platforms."""

    GOOGLE = "google"
    FACEBOOK = "facebook"
    YELP = "yelp"
    BUILDING_CONNECTED = "buildingconnected"


class SentimentTheme(str, Enum):
    """Thematic categories extracted from review text."""

    QUALITY = "quality"
    TIMELINESS = "timeliness"
    SAFETY = "safety"
    COMMUNICATION = "communication"
    PRICE = "price"
    CLEANUP = "cleanup"


class SolicitationStep(int, Enum):
    """Which step in the 4-step solicitation cadence."""

    DAY_0 = 0
    DAY_3 = 3
    DAY_7 = 7
    DAY_14 = 14


# ---------------------------------------------------------------------------
# Core review model
# ---------------------------------------------------------------------------

class Review(BaseModel):
    """A single customer review from any platform, normalised."""

    id: str = Field(..., description="Unique review identifier (platform-prefixed)")
    platform: Platform
    company: str = Field(..., description="Company slug from COMPANIES registry")
    rating: int = Field(..., ge=1, le=5, description="Star rating 1-5")
    text: str = Field(..., description="Full review text")
    author: str = Field(..., description="Reviewer display name")
    date: datetime = Field(default_factory=datetime.utcnow, description="Review timestamp")
    reply: Optional[str] = Field(None, description="Our reply text if already responded")
    sentiment_score: Optional[float] = Field(
        None, ge=-1.0, le=1.0, description="Sentiment score in [-1, 1]"
    )
    themes: List[SentimentTheme] = Field(
        default_factory=list, description="Extracted thematic tags"
    )

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


# ---------------------------------------------------------------------------
# Review request (solicitation input)
# ---------------------------------------------------------------------------

class ReviewRequest(BaseModel):
    """Input for generating a review solicitation email."""

    company: str = Field(..., description="Company slug")
    contact_name: str = Field(..., description="Customer contact name")
    email: str = Field(..., description="Customer email address")
    project_name: str = Field(..., description="Name / address of completed project")
    platform_links: dict = Field(
        default_factory=dict,
        description="Mapping of platform slug to direct review URL",
    )


# ---------------------------------------------------------------------------
# Review response (AI-generated reply)
# ---------------------------------------------------------------------------

class ReviewResponse(BaseModel):
    """AI-generated response to a customer review."""

    review_id: str = Field(..., description="ID of the review being responded to")
    response_text: str = Field(..., description="Generated reply text")
    tone: str = Field(
        ...,
        description="Tone label: enthusiastic | grateful | appreciative | empathetic",
    )
    brand_voice_score: float = Field(
        ...,
        ge=0.0,
        le=1.0,
        description="How well the response matches company brand voice (0-1)",
    )


# ---------------------------------------------------------------------------
# Sentiment analysis result
# ---------------------------------------------------------------------------

class SentimentResult(BaseModel):
    """Output of sentiment analysis on a single review."""

    score: float = Field(..., ge=-1.0, le=1.0, description="Overall sentiment score")
    magnitude: float = Field(
        ..., ge=0.0, description="Strength / intensity of sentiment"
    )
    themes: List[SentimentTheme] = Field(
        default_factory=list, description="Detected thematic tags"
    )


# ---------------------------------------------------------------------------
# Testimonial (curated for marketing)
# ---------------------------------------------------------------------------

class Testimonial(BaseModel):
    """A curated testimonial selected from high-impact reviews."""

    review: Review = Field(..., description="The underlying review")
    rank_score: float = Field(
        ..., ge=0.0, description="Composite ranking score (higher = better)"
    )
    formatted_quote: str = Field(
        ..., description="Marketing-ready quote block with attribution"
    )


# ---------------------------------------------------------------------------
# Solicitation tracking record
# ---------------------------------------------------------------------------

class SolicitationRecord(BaseModel):
    """Tracks which solicitation steps have been sent for a request."""

    request: ReviewRequest
    steps_sent: List[int] = Field(
        default_factory=list,
        description="Cadence days that have been sent (e.g. [0, 3])",
    )
    created_at: datetime = Field(default_factory=datetime.utcnow)
    last_sent_at: Optional[datetime] = None
    review_received: bool = False

    class Config:
        json_encoders = {datetime: lambda v: v.isoformat()}


# ---------------------------------------------------------------------------
# Aggregate sentiment report
# ---------------------------------------------------------------------------

class SentimentAggregate(BaseModel):
    """Aggregated sentiment scores for a company or platform."""

    entity: str = Field(..., description="Company slug or platform name")
    avg_score: float = Field(..., ge=-1.0, le=1.0)
    total_reviews: int = Field(..., ge=0)
    positive_count: int = Field(0)
    neutral_count: int = Field(0)
    negative_count: int = Field(0)
    top_themes: List[SentimentTheme] = Field(default_factory=list)
