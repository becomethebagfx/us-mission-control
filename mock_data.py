"""
Mission Control Dashboard — Mock Data Generator
Generates realistic demo data for all dashboard systems.
Uses seed 42 for reproducibility.
"""

import json
import random
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List

from config import config, COMPANIES, ACTIVE_COMPANIES

# ── Constants ───────────────────────────────────────────────────────

DATA_DIR = config.DATA_DIR

# Active company keys for round-robin assignment
_ACTIVE_KEYS = list(ACTIVE_COMPANIES.keys())

# Construction industry realistic data pools
FIRST_NAMES = [
    "James", "Robert", "Michael", "David", "William", "Richard", "Joseph",
    "Thomas", "Christopher", "Daniel", "Matthew", "Anthony", "Mark", "Steven",
    "Andrew", "Paul", "Joshua", "Kenneth", "Kevin", "Brian", "Sarah", "Jennifer",
    "Lisa", "Amanda", "Michelle", "Kimberly", "Emily", "Jessica", "Ashley", "Nicole",
]

LAST_NAMES = [
    "Anderson", "Martinez", "Thompson", "Garcia", "Robinson", "Clark", "Lewis",
    "Walker", "Hall", "Young", "Allen", "King", "Wright", "Scott", "Torres",
    "Nguyen", "Hill", "Green", "Adams", "Baker", "Nelson", "Carter", "Mitchell",
    "Perez", "Roberts", "Turner", "Phillips", "Campbell", "Parker", "Evans",
]

PROJECT_TYPES = [
    "Multi-Family Residential",
    "Mixed-Use Development",
    "Luxury Apartment Complex",
    "Senior Living Facility",
    "Student Housing",
    "Hotel / Hospitality",
    "Retail Center",
    "Medical Office Building",
    "Warehouse / Industrial",
    "Office Renovation",
    "Townhome Community",
    "Assisted Living Center",
    "Condominium Tower",
    "Restaurant Build-Out",
    "Church / Religious Facility",
]

LINKEDIN_POST_TOPICS = [
    ("Project Milestone: {company} Tops Out {units}-Unit Complex",
     "Proud to announce our team just topped out the {units}-unit {type} in {city}. {days} days ahead of schedule with zero recordable incidents. This is what happens when planning meets execution. #ConstructionExcellence"),
    ("Why Pre-Construction Planning Saves Millions",
     "We recently saved a client $2.3M on a {type} project through value engineering during pre-con. The earlier you bring in your trade partners, the better your outcomes. Here is what we learned."),
    ("{company} Team Spotlight: Meet Our Field Leaders",
     "Our field superintendents average 18 years of experience. Today we are highlighting the team behind the {type} in {city}. Their coordination skills are unmatched in the industry."),
    ("3 Lessons from Managing {units} Units Simultaneously",
     "Managing multiple large-scale projects requires systems, not heroics. Here are 3 frameworks we use at {company} to keep {units} units on track across {states} states."),
    ("The Future of Multi-Family Construction",
     "Mass timber, modular builds, and AI-driven scheduling are reshaping our industry. At {company}, we are investing in innovation to deliver better buildings faster. Here is our take on 2026 trends."),
    ("Safety First: {days} Days Without a Recordable Incident",
     "Safety is not a priority at {company} — it is a value. We just hit {days} consecutive days without a recordable incident across all active job sites. Here is how we maintain that standard."),
    ("Client Testimonial: {type} Delivered On Time, On Budget",
     "Nothing beats hearing from satisfied clients. This {type} was delivered 2 weeks early and $400K under budget. Our pre-construction process made the difference. Thank you for trusting us."),
    ("Hiring: {company} Is Growing — {count} New Positions",
     "We are adding {count} new team members to support our expanding project pipeline. If you are passionate about commercial construction and want to work with industry leaders, check out our openings."),
    ("Behind the Build: Time-Lapse of {type} Project",
     "From foundation to finish in 60 seconds. Watch the full time-lapse of our {type} build in {city}. 14 months of precision work captured in one incredible video."),
    ("Industry Report: Multi-Family Starts Up 12% in Southeast",
     "New data shows multi-family construction starts are up 12% in the Southeast region. At {company}, we are seeing this firsthand with our strongest pipeline ever. Here is what is driving the growth."),
]

ARTICLE_TOPICS = [
    "The Complete Guide to Multi-Family Framing",
    "Understanding Fire-Rated Assemblies in Commercial Construction",
    "5 Ways Pre-Construction Planning Reduces Cost Overruns",
    "Mass Timber vs. Traditional Framing: A Cost Comparison",
    "How to Choose the Right Drywall System for Your Project",
    "EIFS Installation Best Practices for 2026",
    "The Role of BIM in Modern Construction Management",
    "Acoustical Ceiling Solutions for Multi-Family Properties",
    "Metal Stud Framing: When and Why to Use It",
    "Exterior Waterproofing Systems Explained",
    "Construction Safety Programs That Actually Work",
    "Value Engineering Without Sacrificing Quality",
    "The GC's Guide to Trade Partner Management",
    "Understanding Moisture Barriers in Building Envelopes",
    "How AI Is Changing Construction Scheduling",
    "Owner's Representation: What It Is and When You Need It",
    "Sustainable Building Materials in Commercial Construction",
    "Managing Punch Lists Efficiently on Large Projects",
]

CITIES = [
    "Louisville, KY", "Nashville, TN", "Charlotte, NC", "Atlanta, GA",
    "Austin, TX", "Denver, CO", "Raleigh, NC", "Tampa, FL",
    "Phoenix, AZ", "Dallas, TX", "Orlando, FL", "San Antonio, TX",
    "Columbus, OH", "Indianapolis, IN", "Jacksonville, FL",
]

AEO_QUERIES = [
    "best multi-family framing contractor",
    "commercial drywall companies near me",
    "exterior building envelope services",
    "construction management companies Kentucky",
    "wood framing vs steel framing multi-family",
    "fire rated drywall assembly contractors",
    "EIFS installation companies southeast",
    "pre-construction planning services",
    "multi-family construction cost per unit",
    "commercial acoustical ceiling installers",
    "general contractor multi-family development",
    "construction takeover services",
    "mass timber construction contractors",
    "drywall finishing levels explained",
    "building envelope waterproofing contractors",
]

REVIEW_TEXTS_POSITIVE = [
    "Excellent work on our {type} project. The team was professional, on time, and the quality exceeded our expectations.",
    "We have used {company} on three projects now and they consistently deliver outstanding results. Highly recommend.",
    "The attention to detail on our {type} was impressive. They caught issues early and resolved them before they became problems.",
    "Best trade partner we have worked with. Communication was excellent throughout the entire project lifecycle.",
    "From pre-construction through final punch list, {company} was a true partner. They made our job easier.",
    "{company} completed our {type} ahead of schedule. Their field team is experienced and well-organized.",
    "Top-notch safety record and quality workmanship. We plan to use them on every future project in the region.",
    "Responsive, reliable, and results-driven. {company} is the real deal in commercial construction.",
]

REVIEW_TEXTS_NEGATIVE = [
    "Communication could have been better during the project. Some delays were not communicated promptly.",
    "Quality was decent but they struggled to stay on schedule for our {type} project.",
]

HASHTAGS = [
    "#Construction", "#CommercialConstruction", "#MultiFamily",
    "#Framing", "#Drywall", "#BuildingEnvelope", "#ConstructionLife",
    "#GeneralContractor", "#ProjectManagement", "#PreConstruction",
    "#SafetyFirst", "#ConstructionIndustry", "#BuildingTogether",
    "#CommercialRealEstate", "#ConstructionManagement", "#Innovation",
    "#Sustainability", "#MassTimber", "#BIM", "#ConstructionTech",
]

ASSET_TYPES = [
    ("social_post", "1200x1200"),
    ("cover_photo", "1584x396"),
    ("og_image", "1200x630"),
    ("flyer", "2550x3300"),
]


# ── Helpers ─────────────────────────────────────────────────────────

def _company_for_index(i: int) -> str:
    """Return an active company key via round-robin with some randomness."""
    return random.choice(_ACTIVE_KEYS)


def _company_info(key: str) -> Dict[str, Any]:
    return ACTIVE_COMPANIES[key]


def _random_date(start_days_ago: int, end_days_ago: int = 0) -> str:
    """Return an ISO date string between start_days_ago and end_days_ago relative to now."""
    now = datetime.now()
    start = now - timedelta(days=start_days_ago)
    end = now - timedelta(days=end_days_ago)
    delta = (end - start).total_seconds()
    random_seconds = random.uniform(0, delta)
    dt = start + timedelta(seconds=random_seconds)
    return dt.isoformat(timespec="seconds")


def _future_date(min_days: int, max_days: int) -> str:
    """Return an ISO datetime string in the future."""
    now = datetime.now()
    dt = now + timedelta(
        days=random.randint(min_days, max_days),
        hours=random.randint(8, 17),
        minutes=random.choice([0, 15, 30, 45]),
    )
    return dt.isoformat(timespec="seconds")


def _future_datetime_pair(min_days: int, max_days: int, duration_hours: float = 1.0) -> tuple:
    """Return a (start, end) ISO datetime pair."""
    now = datetime.now()
    start_dt = now + timedelta(
        days=random.randint(min_days, max_days),
        hours=random.randint(8, 17),
        minutes=random.choice([0, 15, 30, 45]),
    )
    end_dt = start_dt + timedelta(hours=duration_hours)
    return start_dt.isoformat(timespec="seconds"), end_dt.isoformat(timespec="seconds")


def _random_phone() -> str:
    return f"({random.randint(200, 999)}) {random.randint(200, 999)}-{random.randint(1000, 9999)}"


def _random_email(first: str, last: str) -> str:
    domains = ["gmail.com", "outlook.com", "yahoo.com", "constructionco.com", "builderfirm.com"]
    return f"{first.lower()}.{last.lower()}@{random.choice(domains)}"


def _write_json(filename: str, data: Any) -> Path:
    """Write data to a JSON file in DATA_DIR."""
    filepath = DATA_DIR / filename
    with open(filepath, "w") as f:
        json.dump(data, f, indent=2, default=str)
    return filepath


# ── Data Generators ─────────────────────────────────────────────────

def generate_posts() -> List[Dict[str, Any]]:
    """Generate 25 LinkedIn posts across active companies."""
    statuses_pool = (
        ["scheduled"] * 10 + ["draft"] * 5 + ["published"] * 8 + ["rejected"] * 2
    )
    random.shuffle(statuses_pool)

    posts = []
    for i in range(25):
        key = _ACTIVE_KEYS[i % len(_ACTIVE_KEYS)]
        co = _company_info(key)
        topic_template = random.choice(LINKEDIN_POST_TOPICS)
        title_tpl, content_tpl = topic_template

        replacements = {
            "company": co["name"],
            "units": str(random.randint(80, 400)),
            "type": random.choice(PROJECT_TYPES),
            "city": random.choice(CITIES),
            "days": str(random.randint(30, 365)),
            "states": str(random.randint(3, 12)),
            "count": str(random.randint(5, 25)),
        }

        title = title_tpl.format(**replacements)
        content = content_tpl.format(**replacements)
        # Trim or pad content to 150-300 chars
        if len(content) > 300:
            content = content[:297] + "..."
        elif len(content) < 150:
            content = content + " Learn more about our approach to quality construction."

        status = statuses_pool[i]

        if status == "scheduled":
            scheduled_date = _future_date(1, 30)
        elif status == "published":
            scheduled_date = _random_date(60, 1)
        else:
            scheduled_date = None

        engagement = {
            "likes": random.randint(0, 250) if status == "published" else 0,
            "comments": random.randint(0, 45) if status == "published" else 0,
            "shares": random.randint(0, 30) if status == "published" else 0,
        }

        post = {
            "id": f"post-{i + 1:03d}",
            "company": co["name"],
            "company_slug": co["slug"],
            "title": title,
            "content": content,
            "status": status,
            "scheduled_date": scheduled_date,
            "hashtags": random.sample(HASHTAGS, random.randint(3, 6)),
            "platform": "linkedin",
            "engagement": engagement,
            "created_at": _random_date(90, 1),
        }
        posts.append(post)

    return posts


def generate_articles() -> List[Dict[str, Any]]:
    """Generate 18 content library articles."""
    statuses_pool = (
        ["draft"] * 4 + ["review"] * 4 + ["approved"] * 4 + ["published"] * 6
    )
    random.shuffle(statuses_pool)

    tags_pool = [
        "framing", "drywall", "exteriors", "construction management",
        "pre-construction", "safety", "BIM", "mass timber", "sustainability",
        "multi-family", "commercial", "fire-rated", "acoustical",
        "waterproofing", "value engineering", "innovation", "cost control",
    ]

    articles = []
    for i in range(18):
        key = _ACTIVE_KEYS[i % len(_ACTIVE_KEYS)]
        co = _company_info(key)
        status = statuses_pool[i]

        created = _random_date(120, 10)
        published_at = _random_date(10, 0) if status == "published" else None

        article = {
            "id": f"article-{i + 1:03d}",
            "company": co["name"],
            "company_slug": co["slug"],
            "title": ARTICLE_TOPICS[i],
            "topic": ARTICLE_TOPICS[i].split(":")[0] if ":" in ARTICLE_TOPICS[i] else ARTICLE_TOPICS[i],
            "word_count": random.randint(800, 2500),
            "status": status,
            "aeo_score": random.randint(35, 95),
            "created_at": created,
            "published_at": published_at,
            "tags": random.sample(tags_pool, random.randint(2, 5)),
        }
        articles.append(article)

    return articles


def generate_leads() -> List[Dict[str, Any]]:
    """Generate 30 reactivation leads."""
    statuses_pool = (
        ["new"] * 8 + ["contacted"] * 8 + ["engaged"] * 6
        + ["converted"] * 5 + ["dead"] * 3
    )
    random.shuffle(statuses_pool)

    leads = []
    for i in range(30):
        key = _ACTIVE_KEYS[i % len(_ACTIVE_KEYS)]
        co = _company_info(key)
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)
        status = statuses_pool[i]

        lead = {
            "id": f"lead-{i + 1:03d}",
            "company": co["name"],
            "company_slug": co["slug"],
            "name": f"{first} {last}",
            "email": _random_email(first, last),
            "phone": _random_phone(),
            "project_type": random.choice(PROJECT_TYPES),
            "deal_value": random.randint(10, 500) * 1000,
            "score": random.randint(10, 100),
            "status": status,
            "last_contact": _random_date(90, 0),
            "sequence_step": random.randint(0, 4),
            "created_at": _random_date(180, 30),
        }
        leads.append(lead)

    return leads


def generate_events() -> List[Dict[str, Any]]:
    """Generate 40 calendar events spread across the next 30 days."""
    event_types = [
        ("post", 0.5),
        ("meeting", 1.0),
        ("deadline", 0.0),
        ("milestone", 0.0),
    ]

    events = []
    for i in range(40):
        key = _ACTIVE_KEYS[i % len(_ACTIVE_KEYS)]
        co = _company_info(key)
        etype, default_dur = random.choice(event_types)

        if etype == "post":
            title = f"{co['name']} — LinkedIn Post: {random.choice(LINKEDIN_POST_TOPICS)[0][:40].format(company=co['name'], units='200', type='Apartment', city='Louisville', days='90', states='5', count='10')}..."
            duration = 0.5
        elif etype == "meeting":
            meeting_types = [
                "Weekly Status Call", "Pre-Con Kickoff", "Client Review",
                "Trade Partner Coordination", "Safety Standup", "Pipeline Review",
                "Marketing Strategy Session", "Budget Review",
            ]
            title = f"{co['name']} — {random.choice(meeting_types)}"
            duration = random.choice([0.5, 1.0, 1.5, 2.0])
        elif etype == "deadline":
            deadline_types = [
                "Proposal Due", "Permit Submission", "Content Calendar Finalized",
                "Monthly Report Due", "GBP Update Deadline",
            ]
            title = f"{co['name']} — {random.choice(deadline_types)}"
            duration = 0.0
        else:
            milestone_types = [
                "Project Topping Out", "Grand Opening", "100-Day Safety Milestone",
                "Website Launch", "First LinkedIn Campaign",
            ]
            title = f"{co['name']} — {random.choice(milestone_types)}"
            duration = 0.0

        start, end = _future_datetime_pair(0, 30, duration if duration > 0 else 1.0)
        if duration == 0.0:
            end = start  # Milestones and deadlines are single-point events

        event = {
            "id": f"event-{i + 1:03d}",
            "title": title,
            "start": start,
            "end": end,
            "company": co["name"],
            "company_slug": co["slug"],
            "type": etype,
            "color": co["accent_color"],
        }
        events.append(event)

    return events


def generate_tokens() -> List[Dict[str, Any]]:
    """Generate token status for each active company."""
    now = datetime.now()
    token_scenarios = [
        # (linkedin_status, days_until_expiry)
        ("active", 45),
        ("active", 30),
        ("expiring", 5),
        ("expired", -10),
    ]
    random.shuffle(token_scenarios)

    tokens = []
    for i, key in enumerate(_ACTIVE_KEYS):
        co = _company_info(key)
        scenario = token_scenarios[i % len(token_scenarios)]
        li_status, days_offset = scenario

        expires_at = (now + timedelta(days=days_offset)).isoformat(timespec="seconds")
        last_refreshed = (now - timedelta(days=random.randint(1, 15))).isoformat(timespec="seconds")

        token = {
            "company": co["name"],
            "company_slug": co["slug"],
            "linkedin_token": {
                "status": li_status,
                "expires_at": expires_at,
                "last_refreshed": last_refreshed,
            },
            "monday_token": {
                "status": "active" if random.random() > 0.25 else "disconnected",
                "connected": random.random() > 0.25,
            },
        }
        tokens.append(token)

    return tokens


def generate_gbp() -> Dict[str, Any]:
    """Generate Google Business Profile data."""
    locations = []
    gbp_posts = []

    for i, key in enumerate(_ACTIVE_KEYS):
        co = _company_info(key)
        if not co.get("address"):
            continue

        location = {
            "company": co["name"],
            "company_slug": co["slug"],
            "name": f"{co['name']} — Headquarters",
            "address": co["address"],
            "phone": co["phone"],
            "rating": round(random.uniform(4.5, 5.0), 1),
            "review_count": random.randint(15, 120),
            "verified": True,
            "insights": {
                "views": random.randint(500, 5000),
                "clicks": random.randint(50, 800),
                "calls": random.randint(10, 150),
                "directions": random.randint(20, 300),
            },
        }
        locations.append(location)

        # GBP posts per location
        post_types = ["whats_new", "event", "offer"]
        for j in range(random.randint(2, 5)):
            gbp_post = {
                "id": f"gbp-post-{i + 1}-{j + 1:02d}",
                "company": co["name"],
                "location": location["name"],
                "title": f"{co['name']} — {random.choice(['Project Update', 'Team Spotlight', 'Now Hiring', 'Safety Milestone', 'New Service Offering'])}",
                "type": random.choice(post_types),
                "status": random.choice(["published", "published", "draft"]),
                "created_at": _random_date(60, 0),
            }
            gbp_posts.append(gbp_post)

    return {"locations": locations, "posts": gbp_posts}


def generate_aeo() -> Dict[str, Any]:
    """Generate AEO/GEO optimization data."""
    queries_data = []
    capsules_data = []
    pages_data = []

    for i, query in enumerate(AEO_QUERIES):
        key = _ACTIVE_KEYS[i % len(_ACTIVE_KEYS)]
        co = _company_info(key)

        queries_data.append({
            "query": query,
            "company": co["name"],
            "position": random.randint(1, 20),
            "score": random.randint(20, 100),
            "trend": random.choice(["up", "up", "down", "stable", "stable"]),
        })

        # Some queries have capsules
        if random.random() > 0.3:
            words = random.randint(40, 60)
            capsule_content = (
                f"{co['name']} is a leading provider of {query.replace('best ', '').replace(' near me', '')} "
                f"services, specializing in multi-family and commercial construction projects across the Southeast. "
                f"With decades of experience and a commitment to safety, quality, and on-time delivery, "
                f"the team delivers exceptional results on every project."
            )
            # Trim to approximate word count
            capsule_words = capsule_content.split()
            if len(capsule_words) > words:
                capsule_words = capsule_words[:words]
            capsule_content = " ".join(capsule_words)

            capsules_data.append({
                "id": f"capsule-{i + 1:03d}",
                "company": co["name"],
                "query": query,
                "content": capsule_content,
                "word_count": len(capsule_content.split()),
                "status": random.choice(["active", "active", "draft", "review"]),
            })

    # AEO page scores
    for key in _ACTIVE_KEYS:
        co = _company_info(key)
        if co.get("website"):
            page_paths = ["/", "/services", "/about", "/projects", "/contact"]
            for path in page_paths:
                score = random.randint(30, 95)
                issues = []
                if score < 60:
                    possible_issues = [
                        "Missing structured data",
                        "Answer capsule too long (>60 words)",
                        "Missing FAQ schema",
                        "No speakable markup",
                        "Missing HomeAndConstructionBusiness schema",
                    ]
                    issues = random.sample(possible_issues, random.randint(1, 3))

                pages_data.append({
                    "url": f"{co['website']}{path}",
                    "company": co["name"],
                    "aeo_score": score,
                    "issues": issues,
                })

    return {"queries": queries_data, "capsules": capsules_data, "pages": pages_data}


def generate_reviews() -> Dict[str, Any]:
    """Generate review data across platforms."""
    platforms = ["google", "yelp", "facebook"]
    reviews = []

    for i in range(35):
        key = _ACTIVE_KEYS[i % len(_ACTIVE_KEYS)]
        co = _company_info(key)
        platform = random.choice(platforms)
        first = random.choice(FIRST_NAMES)
        last = random.choice(LAST_NAMES)

        # Mostly positive reviews
        if random.random() > 0.15:
            rating = random.choice([4, 4, 5, 5, 5])
            text_tpl = random.choice(REVIEW_TEXTS_POSITIVE)
        else:
            rating = random.choice([2, 3])
            text_tpl = random.choice(REVIEW_TEXTS_NEGATIVE)

        text = text_tpl.format(
            company=co["name"],
            type=random.choice(PROJECT_TYPES),
        )

        review_date = _random_date(180, 1)
        has_reply = random.random() > 0.3
        reply = None
        reply_date = None
        if has_reply:
            reply = f"Thank you for your feedback, {first}! We appreciate your trust in {co['name']} and look forward to working with you again."
            # Reply date is 1-7 days after review
            review_dt = datetime.fromisoformat(review_date)
            reply_dt = review_dt + timedelta(days=random.randint(1, 7))
            reply_date = reply_dt.isoformat(timespec="seconds")

        review = {
            "id": f"review-{i + 1:03d}",
            "company": co["name"],
            "platform": platform,
            "rating": rating,
            "text": text,
            "author": f"{first} {last[0]}.",
            "date": review_date,
            "reply": reply,
            "reply_date": reply_date,
        }
        reviews.append(review)

    # Compute summary
    total = len(reviews)
    avg_rating = round(sum(r["rating"] for r in reviews) / total, 2)
    by_platform: Dict[str, Dict[str, Any]] = {}
    by_company: Dict[str, Dict[str, Any]] = {}

    for r in reviews:
        # By platform
        p = r["platform"]
        if p not in by_platform:
            by_platform[p] = {"count": 0, "total_rating": 0}
        by_platform[p]["count"] += 1
        by_platform[p]["total_rating"] += r["rating"]

        # By company
        c = r["company"]
        if c not in by_company:
            by_company[c] = {"count": 0, "total_rating": 0}
        by_company[c]["count"] += 1
        by_company[c]["total_rating"] += r["rating"]

    # Calculate averages
    for k in by_platform:
        by_platform[k]["average_rating"] = round(
            by_platform[k]["total_rating"] / by_platform[k]["count"], 2
        )
        del by_platform[k]["total_rating"]

    for k in by_company:
        by_company[k]["average_rating"] = round(
            by_company[k]["total_rating"] / by_company[k]["count"], 2
        )
        del by_company[k]["total_rating"]

    summary = {
        "total": total,
        "average_rating": avg_rating,
        "by_platform": by_platform,
        "by_company": by_company,
    }

    return {"reviews": reviews, "summary": summary}


def generate_brand_audit() -> Dict[str, Any]:
    """Generate brand audit results for each active company."""
    audits = []
    for key in _ACTIVE_KEYS:
        co = _company_info(key)

        categories = {
            "logo_consistency": random.randint(60, 100),
            "color_accuracy": random.randint(55, 100),
            "messaging_alignment": random.randint(50, 100),
            "contact_info_accuracy": random.randint(70, 100),
        }
        overall = round(sum(categories.values()) / len(categories))

        possible_issues = [
            "Logo appears pixelated on mobile",
            "Accent color inconsistent between website and LinkedIn banner",
            "Tagline differs across platforms",
            "Phone number mismatch on Google Business Profile",
            "Email address not listed on LinkedIn company page",
            "Website footer shows outdated address",
            "Social media bio exceeds character limit on some platforms",
            "Missing favicon on website",
            "Inconsistent capitalization in company name",
        ]

        issue_count = 0 if overall > 85 else random.randint(1, 4)
        issues = random.sample(possible_issues, min(issue_count, len(possible_issues)))

        audit = {
            "company": co["name"],
            "company_slug": co["slug"],
            "overall_score": overall,
            "categories": categories,
            "issues": issues,
            "last_audited": _random_date(30, 0),
        }
        audits.append(audit)

    return {"audits": audits}


def generate_assets() -> Dict[str, Any]:
    """Generate visual asset data."""
    assets = []
    asset_titles = [
        "Q1 Project Showcase",
        "Team Photo Banner",
        "Service Highlight Card",
        "Client Testimonial Graphic",
        "Safety Milestone Post",
        "Hiring Announcement",
        "Project Time-Lapse Thumbnail",
        "Monthly Newsletter Header",
        "Open Graph Preview Image",
        "LinkedIn Company Cover",
        "Before/After Project Comparison",
        "Infographic — Construction Process",
    ]

    idx = 0
    for key in _ACTIVE_KEYS:
        co = _company_info(key)
        num_assets = random.randint(3, 5)
        for j in range(num_assets):
            atype, dimensions = random.choice(ASSET_TYPES)
            title = random.choice(asset_titles)

            asset = {
                "id": f"asset-{idx + 1:03d}",
                "company": co["name"],
                "type": atype,
                "title": f"{co['name']} — {title}",
                "dimensions": dimensions,
                "status": random.choice(["generated", "generated", "approved", "rejected"]),
                "created_at": _random_date(60, 0),
                "url": f"/static/assets/{co['slug']}/{atype}-{j + 1}.png",
            }
            assets.append(asset)
            idx += 1

    return {"assets": assets}


# ── Main Entry Point ────────────────────────────────────────────────

def seed_all_mock_data() -> Dict[str, Path]:
    """
    Generate and write all mock data JSON files to the data/ directory.
    Returns a dict mapping filename to its written file path.
    """
    random.seed(42)

    DATA_DIR.mkdir(exist_ok=True)

    generators = {
        "posts.json": generate_posts,
        "articles.json": generate_articles,
        "leads.json": generate_leads,
        "events.json": generate_events,
        "tokens.json": generate_tokens,
        "gbp.json": generate_gbp,
        "aeo.json": generate_aeo,
        "reviews.json": generate_reviews,
        "brand_audit.json": generate_brand_audit,
        "assets.json": generate_assets,
    }

    written: Dict[str, Path] = {}
    for filename, gen_func in generators.items():
        data = gen_func()
        filepath = _write_json(filename, data)
        written[filename] = filepath
        print(f"  Wrote {filename} -> {filepath}")

    return written


if __name__ == "__main__":
    print("Seeding mock data for Mission Control dashboard...")
    files = seed_all_mock_data()
    print(f"\nDone. {len(files)} files written to {DATA_DIR}/")
