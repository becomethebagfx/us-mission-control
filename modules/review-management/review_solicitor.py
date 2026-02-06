"""
Review Solicitor - generates personalised review request emails.

Implements a 4-step cadence (Day 0, 3, 7, 14) with tracking.
Each step uses a different template with escalating urgency.
Includes direct review links for Google, Yelp, and Facebook.
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime
from typing import Dict, List, Optional

from config import (
    COMPANIES,
    DATA_DIR,
    SOLICITATION_CADENCE_DAYS,
    SOLICITATION_SUBJECTS,
    SOLICITATIONS_FILE,
    get_company,
)
from models import ReviewRequest, SolicitationRecord

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Email templates per cadence step
# ---------------------------------------------------------------------------

EMAIL_TEMPLATES: Dict[int, str] = {
    0: """\
Hi {contact_name},

Thank you for choosing {company_name} for your {project_name} project! It was a
pleasure working with you, and we hope the results exceeded your expectations.

If you have a moment, we would truly appreciate a quick review of your experience.
Your feedback helps other property owners and general contractors find trusted
partners, and it helps us continue improving.

{review_links}

Thank you again for your trust in {company_name}.

Warm regards,
{sender_name}
{company_name}
{phone}
{website}
""",
    3: """\
Hi {contact_name},

We hope you are enjoying the results of your {project_name} project!

A few days ago, we reached out to ask about your experience with {company_name}.
If you haven't had a chance yet, we'd love to hear your thoughts. A brief review
takes just 2 minutes and makes a huge difference for our team.

{review_links}

Your honest feedback -- whether it is praise or constructive -- helps us
deliver even better results on every project.

Best regards,
{sender_name}
{company_name}
{phone}
""",
    7: """\
Hi {contact_name},

Just a friendly reminder -- we would love to hear about your experience with
{company_name} on the {project_name} project.

Online reviews are one of the most impactful ways you can support a local
construction team. If you have 2 minutes, it would mean the world to us.

{review_links}

Thank you for considering it!

{sender_name}
{company_name}
{phone}
""",
    14: """\
Hi {contact_name},

This is our final follow-up regarding your {project_name} project with
{company_name}. We completely understand if you are busy, but if you do have a
moment, a short review would be greatly appreciated.

{review_links}

No matter what, thank you for choosing {company_name}. We are proud of the work
we delivered, and we hope you are too.

All the best,
{sender_name}
{company_name}
{phone}
{website}
""",
}


# ---------------------------------------------------------------------------
# Review link formatting
# ---------------------------------------------------------------------------

DEFAULT_REVIEW_LINKS: Dict[str, Dict[str, str]] = {
    "us_framing": {
        "google": "https://g.page/r/usframing/review",
        "yelp": "https://www.yelp.com/writeareview/biz/us-framing",
        "facebook": "https://facebook.com/usframing/reviews",
    },
    "us_drywall": {
        "google": "https://g.page/r/usdrywall/review",
        "yelp": "https://www.yelp.com/writeareview/biz/us-drywall",
        "facebook": "https://facebook.com/usdrywall/reviews",
    },
    "us_exteriors": {
        "google": "https://g.page/r/usexteriors/review",
        "yelp": "https://www.yelp.com/writeareview/biz/us-exteriors",
        "facebook": "https://facebook.com/usexteriors/reviews",
    },
    "us_development": {
        "google": "https://g.page/r/usdevelopment/review",
        "yelp": "https://www.yelp.com/writeareview/biz/us-development",
        "facebook": "https://facebook.com/usdevelopment/reviews",
    },
    "us_interiors": {
        "google": "https://g.page/r/usinteriors/review",
        "yelp": "https://www.yelp.com/writeareview/biz/us-interiors",
        "facebook": "https://facebook.com/usinteriors/reviews",
    },
}


def _format_review_links(company_slug: str, custom_links: Optional[dict] = None) -> str:
    """Format review platform links as a readable block."""
    links = custom_links or DEFAULT_REVIEW_LINKS.get(company_slug, {})
    if not links:
        return "Please visit our profiles to leave a review."

    lines = ["Leave a review on any of these platforms:"]
    platform_names = {
        "google": "Google",
        "yelp": "Yelp",
        "facebook": "Facebook",
    }
    for platform, url in links.items():
        name = platform_names.get(platform, platform.title())
        lines.append(f"  * {name}: {url}")

    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Solicitation tracking
# ---------------------------------------------------------------------------

def _load_solicitations() -> List[dict]:
    """Load solicitation records from JSON file."""
    if os.path.exists(SOLICITATIONS_FILE):
        with open(SOLICITATIONS_FILE, "r") as f:
            return json.load(f)
    return []


def _save_solicitations(records: List[dict]) -> None:
    """Persist solicitation records to JSON file."""
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(SOLICITATIONS_FILE, "w") as f:
        json.dump(records, f, indent=2, default=str)


def _find_existing_record(
    records: List[dict], email: str, company: str
) -> Optional[dict]:
    """Find an existing solicitation record by email and company."""
    for rec in records:
        req = rec.get("request", {})
        if req.get("email") == email and req.get("company") == company:
            return rec
    return None


# ---------------------------------------------------------------------------
# Email generation
# ---------------------------------------------------------------------------

def generate_solicitation_email(
    request: ReviewRequest,
    cadence_day: int,
) -> dict:
    """
    Generate a single solicitation email for a given cadence step.

    Args:
        request: The review request details.
        cadence_day: Which day in the cadence (0, 3, 7, or 14).

    Returns:
        Dict with 'subject', 'body', 'to', 'from_name', 'from_email' keys.
    """
    if cadence_day not in EMAIL_TEMPLATES:
        raise ValueError(
            f"Invalid cadence_day {cadence_day}. Must be one of {SOLICITATION_CADENCE_DAYS}"
        )

    company = get_company(request.company)
    review_links = _format_review_links(
        request.company,
        request.platform_links if request.platform_links else None,
    )

    subject = SOLICITATION_SUBJECTS[cadence_day].format(company_name=company.name)
    body = EMAIL_TEMPLATES[cadence_day].format(
        contact_name=request.contact_name,
        company_name=company.name,
        project_name=request.project_name,
        review_links=review_links,
        sender_name=company.review_request_sender_name,
        phone=company.phone,
        website=company.website,
    )

    return {
        "subject": subject,
        "body": body,
        "to": request.email,
        "from_name": company.review_request_sender_name,
        "from_email": company.review_request_sender_email,
        "cadence_day": cadence_day,
        "company": request.company,
        "generated_at": datetime.utcnow().isoformat(),
    }


# ---------------------------------------------------------------------------
# Cadence management
# ---------------------------------------------------------------------------

def get_next_cadence_step(request: ReviewRequest) -> Optional[int]:
    """
    Determine the next cadence step for a solicitation request.

    Returns:
        The next cadence day, or None if all steps have been sent.
    """
    records = _load_solicitations()
    existing = _find_existing_record(records, request.email, request.company)

    if existing:
        steps_sent = existing.get("steps_sent", [])
        if existing.get("review_received", False):
            return None
        for day in SOLICITATION_CADENCE_DAYS:
            if day not in steps_sent:
                return day
        return None

    return SOLICITATION_CADENCE_DAYS[0]


def record_solicitation_sent(request: ReviewRequest, cadence_day: int) -> None:
    """Record that a solicitation step was sent."""
    records = _load_solicitations()
    existing = _find_existing_record(records, request.email, request.company)

    if existing:
        if cadence_day not in existing["steps_sent"]:
            existing["steps_sent"].append(cadence_day)
        existing["last_sent_at"] = datetime.utcnow().isoformat()
    else:
        record = SolicitationRecord(
            request=request,
            steps_sent=[cadence_day],
            last_sent_at=datetime.utcnow(),
        )
        records.append(record.model_dump(mode="json"))

    _save_solicitations(records)


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def run_solicitation(
    requests: List[ReviewRequest],
    demo: bool = True,
) -> List[dict]:
    """
    Process solicitation requests, generating the next email in the cadence.

    Args:
        requests: List of ReviewRequest objects to process.
        demo: If True, generate but do not send emails.

    Returns:
        List of generated email dicts.
    """
    generated_emails: List[dict] = []

    for request in requests:
        next_step = get_next_cadence_step(request)
        if next_step is None:
            logger.info(
                "All cadence steps complete for %s at %s, skipping",
                request.contact_name,
                request.company,
            )
            continue

        logger.info(
            "Generating Day %d email for %s (%s / %s)",
            next_step,
            request.contact_name,
            request.company,
            request.project_name,
        )

        email = generate_solicitation_email(request, next_step)
        generated_emails.append(email)

        if demo:
            logger.info("[DEMO] Would send email to %s: %s", request.email, email["subject"])
        else:
            # In live mode, integrate with email service (SendGrid, SES, etc.)
            logger.info("Sending email to %s via email service...", request.email)
            pass

        record_solicitation_sent(request, next_step)

    return generated_emails


def get_demo_requests() -> List[ReviewRequest]:
    """Generate sample review requests for demo mode."""
    return [
        ReviewRequest(
            company="us_framing",
            contact_name="Mike Henderson",
            email="mike.henderson@example.com",
            project_name="Riverside Commercial Warehouse",
            platform_links={},
        ),
        ReviewRequest(
            company="us_drywall",
            contact_name="Jennifer Park",
            email="jennifer.park@example.com",
            project_name="Downtown Office Suite 400",
            platform_links={},
        ),
        ReviewRequest(
            company="us_exteriors",
            contact_name="David Kim",
            email="david.kim@example.com",
            project_name="Oakwood Plaza Facade Renovation",
            platform_links={},
        ),
        ReviewRequest(
            company="us_development",
            contact_name="Amanda Foster",
            email="amanda.foster@example.com",
            project_name="Elm Street Tenant Improvement",
            platform_links={},
        ),
    ]
