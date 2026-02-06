"""
GBP Automation Module - Post Generator
Generate three types of Google Business Profile posts using Claude AI,
with demo mode fallback returning realistic mock posts.
"""

from datetime import date, datetime, timedelta
from typing import Optional

from models import (
    CallToAction,
    CallToActionType,
    EventSchedule,
    LocalPost,
    OfferDetails,
    PostType,
)


# ---------------------------------------------------------------------------
# Claude AI Post Generation
# ---------------------------------------------------------------------------


def _call_claude(prompt: str) -> str:
    """Call Anthropic Claude to generate post text."""
    import anthropic
    from config import CLAUDE_MAX_TOKENS, CLAUDE_MODEL

    client = anthropic.Anthropic()
    message = client.messages.create(
        model=CLAUDE_MODEL,
        max_tokens=CLAUDE_MAX_TOKENS,
        messages=[{"role": "user", "content": prompt}],
    )
    return message.content[0].text


def _build_system_context(company_name: str) -> str:
    return (
        f"You are a marketing copywriter for {company_name}, a commercial "
        f"construction company in the Dallas-Fort Worth metro. Write in a "
        f"professional yet approachable tone. Use concrete numbers and "
        f"specifics. Target general contractors, property managers, and "
        f"developers. Keep the post between 150 and 300 words. Do NOT "
        f"include hashtags or emojis. Write only the post body text."
    )


# ---------------------------------------------------------------------------
# Post Type 1: Project Completion
# ---------------------------------------------------------------------------


def generate_project_completion(
    company_key: str,
    company_name: str,
    project_name: str,
    milestone: str,
    stats: str,
    photo_url: Optional[str] = None,
    cta_url: Optional[str] = None,
    demo: bool = False,
) -> LocalPost:
    """Generate a project-completion post (milestone, stats, photo).

    Args:
        company_key: Registry key (e.g. ``us_framing``).
        company_name: Display name (e.g. ``US Framing``).
        project_name: Name of the completed project.
        milestone: What was achieved (e.g. ``Structural framing completed``).
        stats: Key statistics (e.g. ``45,000 sq ft in 6 weeks``).
        photo_url: Optional media URL for the post.
        cta_url: Optional URL for the Learn More CTA button.
        demo: If True, skip the AI call and return a mock post.
    """
    if demo:
        summary = (
            f"{company_name} is proud to announce the completion of a major "
            f"milestone on the {project_name} project. Our team successfully "
            f"delivered {milestone}, covering {stats} while maintaining our "
            f"commitment to quality and safety.\n\n"
            f"This project presented unique challenges including tight "
            f"timelines and complex structural requirements. Our experienced "
            f"crews worked with precision, coordinating closely with the "
            f"general contractor to ensure every detail met specifications.\n\n"
            f"Key highlights from this project include zero safety incidents "
            f"throughout the duration of work, ahead-of-schedule completion "
            f"that kept the overall project timeline on track, and quality "
            f"inspections passed on first review without any corrective "
            f"action required.\n\n"
            f"We are grateful for the trust placed in our team and look "
            f"forward to continuing to deliver exceptional results across "
            f"the Dallas-Fort Worth metro area. Contact us to discuss how "
            f"we can bring this same level of expertise to your next "
            f"commercial construction project."
        )
    else:
        prompt = (
            f"{_build_system_context(company_name)}\n\n"
            f"Write a Google Business Profile post celebrating project "
            f"completion.\n"
            f"Project: {project_name}\n"
            f"Milestone: {milestone}\n"
            f"Stats: {stats}\n"
            f"Include a call-to-action inviting readers to contact us for "
            f"their next project."
        )
        summary = _call_claude(prompt)

    cta = CallToAction(
        action_type=CallToActionType.LEARN_MORE,
        url=cta_url or f"https://www.{company_key.replace('_', '')}.com/projects",
    )

    return LocalPost(
        company_key=company_key,
        post_type=PostType.WHATS_NEW,
        summary=summary,
        call_to_action=cta,
        media_url=photo_url,
        created_at=datetime.utcnow(),
    )


# ---------------------------------------------------------------------------
# Post Type 2: Service Highlight
# ---------------------------------------------------------------------------


def generate_service_highlight(
    company_key: str,
    company_name: str,
    service_name: str,
    benefits: str,
    cta_type: CallToActionType = CallToActionType.CALL,
    cta_url: Optional[str] = None,
    demo: bool = False,
) -> LocalPost:
    """Generate a service-highlight post.

    Args:
        company_key: Registry key.
        company_name: Display name.
        service_name: Name of the service (e.g. ``Metal Stud Framing``).
        benefits: Comma-separated benefits.
        cta_type: CTA button type (CALL, LEARN_MORE, BOOK).
        cta_url: Optional URL for the CTA button.
        demo: If True, return a mock post.
    """
    if demo:
        summary = (
            f"Looking for reliable {service_name.lower()} services in "
            f"Dallas-Fort Worth? {company_name} brings over a decade of "
            f"commercial construction experience to every single job we "
            f"take on across the region.\n\n"
            f"Our {service_name.lower()} services deliver: {benefits}. "
            f"Whether you are building a new multi-family residential complex, "
            f"renovating a commercial office space, or managing a large-scale "
            f"retail development project, our experienced crews have the "
            f"expertise and equipment to meet your exact specifications "
            f"on time and within budget.\n\n"
            f"What truly sets us apart from other contractors is our "
            f"unwavering commitment to clear and transparent communication, "
            f"detailed project scheduling, and consistent quality across every "
            f"project we deliver. We understand that subcontractor reliability "
            f"directly impacts your bottom line and project timeline, which "
            f"is exactly why we treat every single deadline as non-negotiable "
            f"and every inspection as an opportunity to demonstrate our "
            f"commitment to excellence.\n\n"
            f"Our entire team is fully licensed, bonded, insured, and "
            f"OSHA-certified for commercial construction. We proudly "
            f"serve the entire DFW metro area including Dallas, Fort Worth, "
            f"Arlington, Plano, Frisco, McKinney, and all surrounding areas.\n\n"
            f"Call us today to discuss your upcoming project requirements "
            f"and receive a detailed, no-obligation proposal within 48 hours. "
            f"We look forward to earning your trust and delivering "
            f"exceptional results on your next project."
        )
    else:
        prompt = (
            f"{_build_system_context(company_name)}\n\n"
            f"Write a Google Business Profile post highlighting a specific "
            f"service.\n"
            f"Service: {service_name}\n"
            f"Key Benefits: {benefits}\n"
            f"Include a strong call-to-action to contact us."
        )
        summary = _call_claude(prompt)

    cta = CallToAction(
        action_type=cta_type,
        url=cta_url,
    )

    return LocalPost(
        company_key=company_key,
        post_type=PostType.WHATS_NEW,
        summary=summary,
        call_to_action=cta,
        created_at=datetime.utcnow(),
    )


# ---------------------------------------------------------------------------
# Post Type 3: Company Update
# ---------------------------------------------------------------------------


def generate_company_update(
    company_key: str,
    company_name: str,
    update_type: str,
    details: str,
    event_start: Optional[date] = None,
    event_end: Optional[date] = None,
    cta_url: Optional[str] = None,
    demo: bool = False,
) -> LocalPost:
    """Generate a company-update post (news, hiring, events).

    Args:
        company_key: Registry key.
        company_name: Display name.
        update_type: Category -- ``news``, ``hiring``, or ``event``.
        details: Description of the update.
        event_start: Optional event start date.
        event_end: Optional event end date.
        cta_url: Optional CTA URL.
        demo: If True, return a mock post.
    """
    if demo:
        if update_type == "hiring":
            summary = (
                f"{company_name} is growing and we are actively looking for "
                f"skilled professionals to join our expanding team. {details}\n\n"
                f"We offer highly competitive pay rates, comprehensive benefits "
                f"including full health insurance coverage and a generous "
                f"401(k) retirement plan with company match, paid training "
                f"and professional certification opportunities, and a "
                f"supportive team environment where your skills and "
                f"experience are truly valued every single day.\n\n"
                f"As one of the fastest-growing commercial construction "
                f"companies in the Dallas-Fort Worth metropolitan area, we "
                f"provide real career advancement opportunities that smaller "
                f"firms simply cannot match. Many of our current project "
                f"leads and supervisors started as crew members and grew "
                f"their careers within the company through hard work and "
                f"dedication to their craft.\n\n"
                f"We believe in investing in our people because they are "
                f"the foundation of everything we build. Our training "
                f"programs keep your skills sharp and your certifications "
                f"current, ensuring you stay competitive in the industry.\n\n"
                f"If you are experienced in commercial construction and want "
                f"to work with a company that genuinely respects your craft "
                f"and values your contributions, we want to hear from you. "
                f"Apply today or share this posting with someone who would "
                f"be a great fit for our growing team."
            )
        elif update_type == "event":
            summary = (
                f"{company_name} is excited to announce an upcoming event "
                f"that we believe will be valuable for construction "
                f"professionals across the region. {details}\n\n"
                f"This is an excellent opportunity to connect directly with "
                f"our experienced team, learn about our latest capabilities "
                f"and service offerings, and explore how we can support "
                f"your next commercial construction project. Whether you "
                f"are a general contractor managing multiple job sites, a "
                f"real estate developer planning your next build, or a "
                f"property manager overseeing renovation work, we look "
                f"forward to meeting you in person.\n\n"
                f"Our leadership team and senior project managers will be "
                f"available throughout the event to discuss project "
                f"timelines, capacity planning, resource allocation, and "
                f"long-term partnership opportunities. We will also "
                f"showcase detailed case studies from some of our most "
                f"recently completed projects throughout the entire "
                f"Dallas-Fort Worth metropolitan area.\n\n"
                f"Mark your calendar, save the date, and reach out to our "
                f"team to reserve your spot at this event. We look forward "
                f"to seeing you there and building lasting professional "
                f"relationships together."
            )
        else:
            summary = (
                f"{company_name} has exciting news to share with our clients "
                f"and partners across the Dallas-Fort Worth region. "
                f"{details}\n\n"
                f"This important development reflects our ongoing and "
                f"unwavering commitment to providing the highest quality "
                f"commercial construction services in the competitive DFW "
                f"market. We continuously invest in our talented people, "
                f"our proven processes, and our modern equipment to ensure "
                f"every single project meets the exacting standards our "
                f"clients have come to expect from our team.\n\n"
                f"Over the past year, we have significantly expanded our "
                f"service area coverage, added new specialized capabilities "
                f"and technical expertise, and strengthened our project "
                f"management processes with industry-leading tools. These "
                f"strategic investments allow us to confidently take on "
                f"larger, more complex commercial projects while still "
                f"maintaining the personalized attention and responsive "
                f"communication that defines our approach.\n\n"
                f"Stay tuned for more updates as we continue to grow and "
                f"evolve. Contact us today to learn how these developments "
                f"can directly benefit your next construction project and "
                f"help you achieve your building goals on time and "
                f"within budget."
            )
    else:
        prompt = (
            f"{_build_system_context(company_name)}\n\n"
            f"Write a Google Business Profile post about a company update.\n"
            f"Update type: {update_type}\n"
            f"Details: {details}\n"
            f"Include a call-to-action appropriate for the update type."
        )
        summary = _call_claude(prompt)

    post_type = PostType.WHATS_NEW
    event_schedule = None
    if update_type == "event" and event_start:
        post_type = PostType.EVENT
        event_schedule = EventSchedule(
            start_date=event_start,
            end_date=event_end or event_start + timedelta(days=1),
        )

    cta_action = {
        "hiring": CallToActionType.LEARN_MORE,
        "event": CallToActionType.BOOK,
        "news": CallToActionType.LEARN_MORE,
    }.get(update_type, CallToActionType.LEARN_MORE)

    cta = CallToAction(
        action_type=cta_action,
        url=cta_url or f"https://www.{company_key.replace('_', '')}.com",
    )

    return LocalPost(
        company_key=company_key,
        post_type=post_type,
        summary=summary,
        call_to_action=cta,
        event=event_schedule,
        created_at=datetime.utcnow(),
    )
