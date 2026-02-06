"""
GBP Automation Module - API Client
REST client for Google Business Profile API v4.9 with OAuth2,
rate-limit tracking, and demo mode.
"""

import json
import os
import time
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from uuid import uuid4

import httpx

from config import (
    DATA_DIR,
    GBP_BASE_URL,
    PHOTO_ALLOWED_FORMATS,
    PHOTO_MAX_BYTES,
    PHOTO_MIN_BYTES,
    RATE_LIMIT_DAILY,
    RATE_LIMIT_FILE,
)
from models import (
    CallToAction,
    CallToActionType,
    DailyMetric,
    LocalPost,
    Location,
    Photo,
    PhotoCategory,
    PostType,
    Review,
    ReviewReply,
    StarRating,
)


# ---------------------------------------------------------------------------
# Rate-limit bookkeeping
# ---------------------------------------------------------------------------


class RateLimiter:
    """Track daily API call count persisted to a JSON file."""

    def __init__(self, path: str = RATE_LIMIT_FILE) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._state = self._load()

    def _load(self) -> Dict[str, Any]:
        if self._path.exists():
            with open(self._path) as f:
                return json.load(f)
        return {"date": str(date.today()), "count": 0}

    def _save(self) -> None:
        with open(self._path, "w") as f:
            json.dump(self._state, f)

    def check(self) -> bool:
        today = str(date.today())
        if self._state["date"] != today:
            self._state = {"date": today, "count": 0}
            self._save()
        return self._state["count"] < RATE_LIMIT_DAILY

    def increment(self) -> int:
        today = str(date.today())
        if self._state["date"] != today:
            self._state = {"date": today, "count": 0}
        self._state["count"] += 1
        self._save()
        return self._state["count"]

    @property
    def remaining(self) -> int:
        today = str(date.today())
        if self._state["date"] != today:
            return RATE_LIMIT_DAILY
        return max(0, RATE_LIMIT_DAILY - self._state["count"])


# ---------------------------------------------------------------------------
# GBP API Client
# ---------------------------------------------------------------------------


class GBPClient:
    """Google Business Profile REST API client.

    Set ``demo=True`` to return realistic mock data without hitting the API.
    In production, supply a valid OAuth2 access token or credentials path.
    """

    def __init__(
        self,
        account_id: str = "",
        access_token: Optional[str] = None,
        credentials_path: Optional[str] = None,
        demo: bool = False,
    ) -> None:
        self.account_id = account_id
        self.demo = demo
        self._rate = RateLimiter()

        if not demo:
            self._token = access_token or os.getenv("GBP_ACCESS_TOKEN", "")
            self._client = httpx.Client(
                base_url=GBP_BASE_URL,
                headers={
                    "Authorization": f"Bearer {self._token}",
                    "Content-Type": "application/json",
                },
                timeout=30.0,
            )
        else:
            self._client = None  # type: ignore[assignment]

    # -- helpers -------------------------------------------------------------

    def _request(
        self,
        method: str,
        path: str,
        *,
        json_body: Optional[Dict] = None,
        params: Optional[Dict] = None,
    ) -> Dict[str, Any]:
        if not self._rate.check():
            raise RuntimeError(
                f"Daily rate limit ({RATE_LIMIT_DAILY}) reached. "
                f"Try again tomorrow."
            )
        self._rate.increment()
        resp = self._client.request(
            method, path, json=json_body, params=params
        )
        resp.raise_for_status()
        return resp.json()

    @property
    def rate_remaining(self) -> int:
        return self._rate.remaining

    # -----------------------------------------------------------------------
    # Locations
    # -----------------------------------------------------------------------

    def list_locations(self) -> List[Location]:
        """Return all locations for the account."""
        if self.demo:
            return self._demo_locations()
        data = self._request(
            "GET",
            f"/accounts/{self.account_id}/locations",
            params={"readMask": "name,title,phoneNumbers,storefrontAddress,websiteUri,labels"},
        )
        locations: List[Location] = []
        for loc in data.get("locations", []):
            addr = loc.get("storefrontAddress", {})
            locations.append(
                Location(
                    name=loc["name"],
                    title=loc.get("title", ""),
                    phone_number=(loc.get("phoneNumbers", {}).get("primaryPhone", "")),
                    address_lines=addr.get("addressLines", []),
                    city=addr.get("locality", ""),
                    state=addr.get("administrativeArea", ""),
                    postal_code=addr.get("postalCode", ""),
                    country=addr.get("regionCode", "US"),
                    website_url=loc.get("websiteUri"),
                    labels=loc.get("labels", []),
                    company_key=self._company_key_from_labels(loc.get("labels", [])),
                )
            )
        return locations

    def get_location(self, location_name: str) -> Location:
        """Get a single location by resource name."""
        if self.demo:
            locs = self._demo_locations()
            for loc in locs:
                if loc.name == location_name:
                    return loc
            return locs[0]
        data = self._request("GET", f"/{location_name}")
        addr = data.get("storefrontAddress", {})
        return Location(
            name=data["name"],
            title=data.get("title", ""),
            phone_number=(data.get("phoneNumbers", {}).get("primaryPhone", "")),
            address_lines=addr.get("addressLines", []),
            city=addr.get("locality", ""),
            state=addr.get("administrativeArea", ""),
            postal_code=addr.get("postalCode", ""),
            country=addr.get("regionCode", "US"),
            website_url=data.get("websiteUri"),
            labels=data.get("labels", []),
            company_key=self._company_key_from_labels(data.get("labels", [])),
        )

    # -----------------------------------------------------------------------
    # Posts
    # -----------------------------------------------------------------------

    def create_post(self, location_name: str, post: LocalPost) -> LocalPost:
        """Create a new local post on a location."""
        if self.demo:
            post.name = f"{location_name}/localPosts/{uuid4().hex[:12]}"
            post.created_at = datetime.utcnow()
            return post

        body: Dict[str, Any] = {
            "topicType": post.post_type.value,
            "summary": post.summary,
            "languageCode": "en-US",
        }
        if post.call_to_action:
            cta: Dict[str, Any] = {"actionType": post.call_to_action.action_type.value}
            if post.call_to_action.url:
                cta["url"] = post.call_to_action.url
            body["callToAction"] = cta
        if post.media_url:
            body["media"] = [
                {"mediaFormat": "PHOTO", "sourceUrl": post.media_url}
            ]
        if post.event:
            body["event"] = {
                "title": post.summary[:80],
                "schedule": {
                    "startDate": {
                        "year": post.event.start_date.year,
                        "month": post.event.start_date.month,
                        "day": post.event.start_date.day,
                    },
                    "endDate": {
                        "year": post.event.end_date.year,
                        "month": post.event.end_date.month,
                        "day": post.event.end_date.day,
                    },
                },
            }
        if post.offer:
            body["offer"] = {}
            if post.offer.coupon_code:
                body["offer"]["couponCode"] = post.offer.coupon_code
            if post.offer.redeem_online_url:
                body["offer"]["redeemOnlineUrl"] = post.offer.redeem_online_url
            if post.offer.terms_conditions:
                body["offer"]["termsConditions"] = post.offer.terms_conditions

        data = self._request(
            "POST", f"/{location_name}/localPosts", json_body=body
        )
        post.name = data.get("name")
        post.created_at = datetime.utcnow()
        return post

    def update_post(
        self,
        post_name: str,
        updates: Dict[str, Any],
        update_mask: List[str],
    ) -> Dict[str, Any]:
        """Patch an existing post using updateMask."""
        if self.demo:
            return {"name": post_name, **updates, "updateMask": update_mask}
        return self._request(
            "PATCH",
            f"/{post_name}",
            json_body=updates,
            params={"updateMask": ",".join(update_mask)},
        )

    def delete_post(self, post_name: str) -> bool:
        """Delete a local post."""
        if self.demo:
            return True
        self._request("DELETE", f"/{post_name}")
        return True

    # -----------------------------------------------------------------------
    # Photos
    # -----------------------------------------------------------------------

    def upload_photo(
        self,
        location_name: str,
        photo_path: str,
        category: str = "ADDITIONAL",
    ) -> Photo:
        """Upload a photo after validating size and format."""
        path = Path(photo_path)
        if not path.exists():
            raise FileNotFoundError(f"Photo not found: {photo_path}")

        ext = path.suffix.lstrip(".").upper()
        if ext not in PHOTO_ALLOWED_FORMATS:
            raise ValueError(
                f"Unsupported format '{ext}'. "
                f"Allowed: {', '.join(sorted(PHOTO_ALLOWED_FORMATS))}"
            )

        size = path.stat().st_size
        if size < PHOTO_MIN_BYTES:
            raise ValueError(
                f"Photo too small ({size:,} bytes). Minimum {PHOTO_MIN_BYTES:,} bytes."
            )
        if size > PHOTO_MAX_BYTES:
            raise ValueError(
                f"Photo too large ({size:,} bytes). Maximum {PHOTO_MAX_BYTES:,} bytes."
            )

        if self.demo:
            return Photo(
                name=f"{location_name}/photos/{uuid4().hex[:12]}",
                company_key="demo",
                category=PhotoCategory(category),
                local_path=photo_path,
                size_bytes=size,
                uploaded_at=datetime.utcnow(),
            )

        with open(photo_path, "rb") as f:
            image_data = f.read()

        self._rate.increment()
        resp = self._client.post(
            f"/{location_name}/photos",
            content=image_data,
            headers={
                "Content-Type": f"image/{ext.lower()}",
            },
            params={"category": category},
        )
        resp.raise_for_status()
        data = resp.json()
        return Photo(
            name=data.get("name"),
            company_key="",
            category=PhotoCategory(category),
            local_path=photo_path,
            size_bytes=size,
            uploaded_at=datetime.utcnow(),
        )

    # -----------------------------------------------------------------------
    # Reviews
    # -----------------------------------------------------------------------

    def list_reviews(
        self, location_name: str, page_size: int = 50
    ) -> List[Review]:
        """List reviews for a location."""
        if self.demo:
            return self._demo_reviews(location_name)
        data = self._request(
            "GET",
            f"/{location_name}/reviews",
            params={"pageSize": page_size},
        )
        reviews: List[Review] = []
        for r in data.get("reviews", []):
            reviews.append(
                Review(
                    name=r["name"],
                    reviewer_name=r.get("reviewer", {}).get("displayName", ""),
                    star_rating=StarRating(
                        {"ONE": 1, "TWO": 2, "THREE": 3, "FOUR": 4, "FIVE": 5}.get(
                            r.get("starRating", "FIVE"), 5
                        )
                    ),
                    comment=r.get("comment"),
                    create_time=r.get("createTime"),
                )
            )
        return reviews

    def reply_to_review(self, review_name: str, comment: str) -> ReviewReply:
        """Reply to a customer review."""
        if self.demo:
            return ReviewReply(
                review_name=review_name,
                comment=comment,
                update_time=datetime.utcnow(),
            )
        self._request(
            "PUT",
            f"/{review_name}/reply",
            json_body={"comment": comment},
        )
        return ReviewReply(
            review_name=review_name,
            comment=comment,
            update_time=datetime.utcnow(),
        )

    # -----------------------------------------------------------------------
    # Insights / Metrics
    # -----------------------------------------------------------------------

    def get_daily_metrics(
        self,
        location_name: str,
        company_key: str,
        start_date: date,
        end_date: date,
    ) -> List[DailyMetric]:
        """Fetch daily performance metrics for a location."""
        if self.demo:
            return self._demo_daily_metrics(
                location_name, company_key, start_date, end_date
            )

        body = {
            "locationNames": [location_name],
            "basicRequest": {
                "metricRequests": [
                    {"metric": "QUERIES_DIRECT"},
                    {"metric": "QUERIES_INDIRECT"},
                    {"metric": "VIEWS_MAPS"},
                    {"metric": "VIEWS_SEARCH"},
                    {"metric": "ACTIONS_WEBSITE"},
                    {"metric": "ACTIONS_PHONE"},
                    {"metric": "ACTIONS_DRIVING_DIRECTIONS"},
                ],
                "timeRange": {
                    "startTime": f"{start_date}T00:00:00Z",
                    "endTime": f"{end_date}T23:59:59Z",
                },
            },
        }
        data = self._request(
            "POST",
            f"/{location_name}:reportInsights",
            json_body=body,
        )
        metrics: List[DailyMetric] = []
        for entry in data.get("locationMetrics", [{}])[0].get(
            "metricValues", []
        ):
            for dv in entry.get("dimensionalValues", []):
                d = dv.get("timeDimension", {}).get("timeRange", {}).get("startTime", "")[:10]
                if not d:
                    continue
                metrics.append(
                    DailyMetric(
                        location_name=location_name,
                        company_key=company_key,
                        date=date.fromisoformat(d),
                        views=int(dv.get("value", 0)),
                    )
                )
        return metrics

    # -----------------------------------------------------------------------
    # Demo helpers
    # -----------------------------------------------------------------------

    @staticmethod
    def _company_key_from_labels(labels: List[str]) -> str:
        for label in labels:
            if label.startswith("company:"):
                return label.split(":", 1)[1]
        return "unknown"

    @staticmethod
    def _demo_locations() -> List[Location]:
        from config import ACTIVE_COMPANIES

        locations: List[Location] = []
        for i, (key, co) in enumerate(ACTIVE_COMPANIES.items(), start=1):
            locations.append(
                Location(
                    name=f"accounts/demo/locations/{1000 + i}",
                    store_code=co.slug,
                    title=co.name,
                    phone_number=co.phone,
                    address_lines=[co.address.split(",")[0]],
                    city="Dallas",
                    state="TX",
                    postal_code="75201",
                    website_url=f"https://www.{co.slug}.com",
                    primary_category="General Contractor",
                    labels=[f"company:{key}"],
                    company_key=key,
                )
            )
        return locations

    @staticmethod
    def _demo_reviews(location_name: str) -> List[Review]:
        return [
            Review(
                name=f"{location_name}/reviews/r001",
                reviewer_name="John S.",
                star_rating=StarRating.FIVE,
                comment="Incredible framing work on our commercial project. On time and on budget.",
                create_time=datetime.utcnow() - timedelta(days=3),
            ),
            Review(
                name=f"{location_name}/reviews/r002",
                reviewer_name="Maria G.",
                star_rating=StarRating.FOUR,
                comment="Professional crew. Minor scheduling hiccup but quality was top-notch.",
                create_time=datetime.utcnow() - timedelta(days=10),
            ),
            Review(
                name=f"{location_name}/reviews/r003",
                reviewer_name="David L.",
                star_rating=StarRating.FIVE,
                comment="Best subcontractor we have worked with in DFW. Highly recommend.",
                create_time=datetime.utcnow() - timedelta(days=21),
            ),
        ]

    @staticmethod
    def _demo_daily_metrics(
        location_name: str,
        company_key: str,
        start_date: date,
        end_date: date,
    ) -> List[DailyMetric]:
        import random

        random.seed(hash(location_name) + hash(str(start_date)))
        metrics: List[DailyMetric] = []
        current = start_date
        while current <= end_date:
            day_of_week = current.weekday()
            weekday_boost = 1.0 if day_of_week < 5 else 0.6
            metrics.append(
                DailyMetric(
                    location_name=location_name,
                    company_key=company_key,
                    date=current,
                    views=int(random.randint(40, 120) * weekday_boost),
                    search_impressions=int(random.randint(80, 250) * weekday_boost),
                    clicks=int(random.randint(5, 25) * weekday_boost),
                    calls=int(random.randint(1, 8) * weekday_boost),
                    direction_requests=int(random.randint(2, 12) * weekday_boost),
                    website_clicks=int(random.randint(3, 15) * weekday_boost),
                )
            )
            current += timedelta(days=1)
        return metrics
