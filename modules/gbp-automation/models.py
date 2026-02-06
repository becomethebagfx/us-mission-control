"""
GBP Automation Module - Data Models
Pydantic models for Google Business Profile entities.
"""

from datetime import date, datetime
from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field, field_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------


class PostType(str, Enum):
    WHATS_NEW = "STANDARD"
    EVENT = "EVENT"
    OFFER = "OFFER"


class PhotoCategory(str, Enum):
    COVER = "COVER"
    PROFILE = "PROFILE"
    ADDITIONAL = "ADDITIONAL"
    POST = "POST"


class MediaFormat(str, Enum):
    JPEG = "JPEG"
    JPG = "JPG"
    PNG = "PNG"


class CallToActionType(str, Enum):
    LEARN_MORE = "LEARN_MORE"
    CALL = "CALL"
    BOOK = "BOOK"
    ORDER = "ORDER"
    SHOP = "SHOP"
    SIGN_UP = "SIGN_UP"
    GET_OFFER = "GET_OFFER"


class StarRating(int, Enum):
    ONE = 1
    TWO = 2
    THREE = 3
    FOUR = 4
    FIVE = 5


# ---------------------------------------------------------------------------
# Location
# ---------------------------------------------------------------------------


class Location(BaseModel):
    """A Google Business Profile location (listing)."""

    name: str = Field(
        ..., description="GBP resource name, e.g. accounts/123/locations/456"
    )
    store_code: Optional[str] = None
    title: str = Field(..., description="Business name shown on Google")
    phone_number: str = ""
    address_lines: List[str] = Field(default_factory=list)
    city: str = ""
    state: str = ""
    postal_code: str = ""
    country: str = "US"
    website_url: Optional[str] = None
    primary_category: Optional[str] = None
    labels: List[str] = Field(default_factory=list)
    company_key: str = Field(
        ..., description="Key into config.COMPANIES registry"
    )

    @property
    def full_address(self) -> str:
        parts = self.address_lines + [
            f"{self.city}, {self.state} {self.postal_code}",
        ]
        return ", ".join(p for p in parts if p)


# ---------------------------------------------------------------------------
# Posts
# ---------------------------------------------------------------------------


class CallToAction(BaseModel):
    action_type: CallToActionType = CallToActionType.LEARN_MORE
    url: Optional[str] = None


class EventSchedule(BaseModel):
    start_date: date
    end_date: date
    start_time: Optional[str] = None  # HH:MM
    end_time: Optional[str] = None


class OfferDetails(BaseModel):
    coupon_code: Optional[str] = None
    redeem_online_url: Optional[str] = None
    terms_conditions: Optional[str] = None


class LocalPost(BaseModel):
    """A GBP local post (What's New, Event, or Offer)."""

    name: Optional[str] = Field(
        None,
        description="GBP resource name once created",
    )
    company_key: str
    post_type: PostType = PostType.WHATS_NEW
    summary: str = Field(
        ...,
        min_length=10,
        max_length=1500,
        description="Post body text (150-300 words recommended)",
    )
    call_to_action: Optional[CallToAction] = None
    media_url: Optional[str] = None
    event: Optional[EventSchedule] = None
    offer: Optional[OfferDetails] = None
    created_at: Optional[datetime] = None

    @field_validator("summary")
    @classmethod
    def check_word_count(cls, v: str) -> str:
        words = len(v.split())
        if words < 10:
            raise ValueError(
                f"Post summary too short ({words} words). Aim for 150-300."
            )
        return v


# ---------------------------------------------------------------------------
# Reviews
# ---------------------------------------------------------------------------


class Review(BaseModel):
    """A customer review on a GBP listing."""

    name: str = Field(
        ..., description="GBP resource name for the review"
    )
    reviewer_name: str = ""
    star_rating: StarRating = StarRating.FIVE
    comment: Optional[str] = None
    create_time: Optional[datetime] = None
    update_time: Optional[datetime] = None


class ReviewReply(BaseModel):
    """A reply to a customer review."""

    review_name: str = Field(
        ..., description="Resource name of the review being replied to"
    )
    comment: str = Field(
        ..., min_length=1, max_length=4096, description="Reply text"
    )
    update_time: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Photos
# ---------------------------------------------------------------------------


class Photo(BaseModel):
    """A photo uploaded to a GBP listing."""

    name: Optional[str] = Field(
        None, description="GBP resource name once uploaded"
    )
    company_key: str
    category: PhotoCategory = PhotoCategory.ADDITIONAL
    media_format: MediaFormat = MediaFormat.JPEG
    source_url: Optional[str] = None
    local_path: Optional[str] = None
    width: Optional[int] = None
    height: Optional[int] = None
    size_bytes: Optional[int] = None
    uploaded_at: Optional[datetime] = None


# ---------------------------------------------------------------------------
# Insights / Metrics
# ---------------------------------------------------------------------------


class DailyMetric(BaseModel):
    """A single day of performance metrics for one location."""

    location_name: str
    company_key: str
    date: date
    views: int = 0
    search_impressions: int = 0
    clicks: int = 0
    calls: int = 0
    direction_requests: int = 0
    website_clicks: int = 0


class InsightReport(BaseModel):
    """Aggregated insight report over a date range."""

    company_key: str
    location_name: str
    start_date: date
    end_date: date
    total_views: int = 0
    total_search_impressions: int = 0
    total_clicks: int = 0
    total_calls: int = 0
    total_direction_requests: int = 0
    total_website_clicks: int = 0
    daily_metrics: List[DailyMetric] = Field(default_factory=list)
    trends: Dict[str, float] = Field(
        default_factory=dict,
        description="Metric name -> week-over-week % change",
    )

    @property
    def total_engagement(self) -> int:
        return (
            self.total_clicks
            + self.total_calls
            + self.total_direction_requests
            + self.total_website_clicks
        )
