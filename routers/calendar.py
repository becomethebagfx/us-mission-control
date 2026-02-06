"""
Mission Control Dashboard — Calendar Router
Provides FullCalendar-compatible event data from the events JSON store.
"""

from fastapi import APIRouter, Query
import json
from config import config
from typing import Optional

router = APIRouter()


@router.get("/events")
async def get_events(
    company: Optional[str] = Query(None),
    type: Optional[str] = Query(None),
):
    """Get calendar events in FullCalendar format."""
    if config.EVENTS_FILE.exists():
        events = json.loads(config.EVENTS_FILE.read_text())
    else:
        events = []

    if company:
        events = [e for e in events if e.get("company_slug") == company]
    if type:
        events = [e for e in events if e.get("type") == type]

    # Transform to FullCalendar format
    fc_events = []
    for e in events:
        fc_events.append(
            {
                "id": e.get("id"),
                "title": e.get("title"),
                "start": e.get("start"),
                "end": e.get("end"),
                "color": e.get("color", "#1B2A4A"),
                "extendedProps": {
                    "company": e.get("company"),
                    "company_slug": e.get("company_slug"),
                    "type": e.get("type"),
                },
            }
        )

    return fc_events
