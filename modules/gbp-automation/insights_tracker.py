"""
GBP Automation Module - Insights Tracker
Poll getDailyMetrics, store to JSON, and compute weekly/monthly trends.
"""

import json
import random
from datetime import date, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional

from config import ACTIVE_COMPANIES, DATA_DIR, INSIGHTS_FILE
from models import DailyMetric, InsightReport


# ---------------------------------------------------------------------------
# Storage
# ---------------------------------------------------------------------------


class InsightsStore:
    """Persist daily metrics to a JSON file and load them back."""

    def __init__(self, path: str = INSIGHTS_FILE) -> None:
        self._path = Path(path)
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._data: Dict[str, List[Dict[str, Any]]] = self._load()

    def _load(self) -> Dict[str, List[Dict[str, Any]]]:
        if self._path.exists() and self._path.stat().st_size > 0:
            with open(self._path) as f:
                return json.load(f)
        return {}

    def _save(self) -> None:
        with open(self._path, "w") as f:
            json.dump(self._data, f, indent=2, default=str)

    def store_metrics(self, metrics: List[DailyMetric]) -> int:
        """Append daily metrics to the store. Returns count of new records."""
        added = 0
        for m in metrics:
            key = f"{m.company_key}:{m.location_name}"
            existing_dates = {
                r["date"] for r in self._data.get(key, [])
            }
            if str(m.date) not in existing_dates:
                self._data.setdefault(key, []).append(
                    {
                        "location_name": m.location_name,
                        "company_key": m.company_key,
                        "date": str(m.date),
                        "views": m.views,
                        "search_impressions": m.search_impressions,
                        "clicks": m.clicks,
                        "calls": m.calls,
                        "direction_requests": m.direction_requests,
                        "website_clicks": m.website_clicks,
                    }
                )
                added += 1
        self._save()
        return added

    def get_metrics(
        self,
        company_key: str,
        location_name: str,
        start_date: Optional[date] = None,
        end_date: Optional[date] = None,
    ) -> List[DailyMetric]:
        """Retrieve stored metrics for a location, optionally filtered by date range."""
        key = f"{company_key}:{location_name}"
        records = self._data.get(key, [])
        metrics: List[DailyMetric] = []
        for r in records:
            d = date.fromisoformat(r["date"])
            if start_date and d < start_date:
                continue
            if end_date and d > end_date:
                continue
            metrics.append(
                DailyMetric(
                    location_name=r["location_name"],
                    company_key=r["company_key"],
                    date=d,
                    views=r.get("views", 0),
                    search_impressions=r.get("search_impressions", 0),
                    clicks=r.get("clicks", 0),
                    calls=r.get("calls", 0),
                    direction_requests=r.get("direction_requests", 0),
                    website_clicks=r.get("website_clicks", 0),
                )
            )
        metrics.sort(key=lambda m: m.date)
        return metrics

    def list_locations(self) -> List[str]:
        """Return all stored location keys."""
        return list(self._data.keys())


# ---------------------------------------------------------------------------
# Aggregation & Trends
# ---------------------------------------------------------------------------

METRIC_FIELDS = [
    "views",
    "search_impressions",
    "clicks",
    "calls",
    "direction_requests",
    "website_clicks",
]


def aggregate_metrics(
    metrics: List[DailyMetric],
    company_key: str,
    location_name: str,
) -> InsightReport:
    """Sum daily metrics into an InsightReport with trend calculations."""
    if not metrics:
        today = date.today()
        return InsightReport(
            company_key=company_key,
            location_name=location_name,
            start_date=today,
            end_date=today,
        )

    sorted_m = sorted(metrics, key=lambda m: m.date)
    start = sorted_m[0].date
    end = sorted_m[-1].date

    totals = {f: 0 for f in METRIC_FIELDS}
    for m in sorted_m:
        for f in METRIC_FIELDS:
            totals[f] += getattr(m, f, 0)

    # Week-over-week trends
    trends = compute_weekly_trends(sorted_m)

    return InsightReport(
        company_key=company_key,
        location_name=location_name,
        start_date=start,
        end_date=end,
        total_views=totals["views"],
        total_search_impressions=totals["search_impressions"],
        total_clicks=totals["clicks"],
        total_calls=totals["calls"],
        total_direction_requests=totals["direction_requests"],
        total_website_clicks=totals["website_clicks"],
        daily_metrics=sorted_m,
        trends=trends,
    )


def compute_weekly_trends(metrics: List[DailyMetric]) -> Dict[str, float]:
    """Compare the most recent 7 days against the prior 7 days.

    Returns a dict of metric_name -> percentage change.
    """
    if len(metrics) < 8:
        return {}

    sorted_m = sorted(metrics, key=lambda m: m.date)
    recent = sorted_m[-7:]
    prior = sorted_m[-14:-7] if len(sorted_m) >= 14 else sorted_m[:7]

    trends: Dict[str, float] = {}
    for field in METRIC_FIELDS:
        recent_sum = sum(getattr(m, field, 0) for m in recent)
        prior_sum = sum(getattr(m, field, 0) for m in prior)
        if prior_sum > 0:
            pct = round(((recent_sum - prior_sum) / prior_sum) * 100, 1)
        elif recent_sum > 0:
            pct = 100.0
        else:
            pct = 0.0
        trends[field] = pct
    return trends


def compute_monthly_totals(
    metrics: List[DailyMetric],
) -> Dict[str, Dict[str, int]]:
    """Group daily metrics by YYYY-MM and sum each field.

    Returns ``{"2026-01": {"views": N, ...}, ...}``.
    """
    monthly: Dict[str, Dict[str, int]] = {}
    for m in metrics:
        month_key = m.date.strftime("%Y-%m")
        if month_key not in monthly:
            monthly[month_key] = {f: 0 for f in METRIC_FIELDS}
        for f in METRIC_FIELDS:
            monthly[month_key][f] += getattr(m, f, 0)
    return monthly


# ---------------------------------------------------------------------------
# Polling / Sync
# ---------------------------------------------------------------------------


class InsightsTracker:
    """High-level tracker that polls the GBP API and stores results."""

    def __init__(self, client, demo: bool = False) -> None:
        self.client = client
        self.demo = demo
        self.store = InsightsStore()

    def poll(
        self,
        locations: List,
        days: int = 30,
    ) -> int:
        """Fetch the last ``days`` of metrics for each location and store them.

        Returns the total number of new records stored.
        """
        end = date.today()
        start = end - timedelta(days=days)
        total_added = 0

        for loc in locations:
            metrics = self.client.get_daily_metrics(
                loc.name, loc.company_key, start, end
            )
            added = self.store.store_metrics(metrics)
            total_added += added
        return total_added

    def report(
        self,
        company_key: str,
        location_name: str,
        days: int = 30,
    ) -> InsightReport:
        """Build an aggregated insight report from stored data."""
        end = date.today()
        start = end - timedelta(days=days)
        metrics = self.store.get_metrics(
            company_key, location_name, start, end
        )
        return aggregate_metrics(metrics, company_key, location_name)

    def all_reports(self, days: int = 30) -> List[InsightReport]:
        """Build reports for every stored location."""
        reports: List[InsightReport] = []
        for loc_key in self.store.list_locations():
            company_key, location_name = loc_key.split(":", 1)
            reports.append(self.report(company_key, location_name, days))
        return reports

    # -- Demo ---------------------------------------------------------------

    def generate_demo_data(self, days: int = 60) -> int:
        """Populate the store with realistic demo trend data for all active companies."""
        end = date.today()
        start = end - timedelta(days=days)
        total = 0

        for i, (key, co) in enumerate(ACTIVE_COMPANIES.items(), start=1):
            location_name = f"accounts/demo/locations/{1000 + i}"
            metrics = self.client.get_daily_metrics(
                location_name, key, start, end
            )
            added = self.store.store_metrics(metrics)
            total += added
        return total

    # -- Display helpers ----------------------------------------------------

    def format_report(self, report: InsightReport) -> str:
        """Return a human-readable report string."""
        lines: List[str] = []
        company = ACTIVE_COMPANIES.get(report.company_key)
        name = company.name if company else report.company_key
        lines.append(f"{'='*60}")
        lines.append(f"  {name} - Insights Report")
        lines.append(f"  {report.start_date} to {report.end_date}")
        lines.append(f"{'='*60}")
        lines.append(f"  Views              : {report.total_views:,}")
        lines.append(f"  Search Impressions : {report.total_search_impressions:,}")
        lines.append(f"  Clicks             : {report.total_clicks:,}")
        lines.append(f"  Calls              : {report.total_calls:,}")
        lines.append(f"  Direction Requests : {report.total_direction_requests:,}")
        lines.append(f"  Website Clicks     : {report.total_website_clicks:,}")
        lines.append(f"  Total Engagement   : {report.total_engagement:,}")

        if report.trends:
            lines.append(f"\n  Week-over-Week Trends:")
            for metric, pct in report.trends.items():
                arrow = "+" if pct >= 0 else ""
                label = metric.replace("_", " ").title()
                lines.append(f"    {label:25s}: {arrow}{pct}%")

        monthly = compute_monthly_totals(report.daily_metrics)
        if monthly:
            lines.append(f"\n  Monthly Breakdown:")
            for month, vals in sorted(monthly.items()):
                total_eng = (
                    vals["clicks"]
                    + vals["calls"]
                    + vals["direction_requests"]
                    + vals["website_clicks"]
                )
                lines.append(
                    f"    {month}: {vals['views']:,} views, "
                    f"{total_eng:,} engagements"
                )

        lines.append(f"{'='*60}")
        return "\n".join(lines)
