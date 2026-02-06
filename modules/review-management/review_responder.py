"""
Review Responder - generates brand-voice-matched replies using Claude AI.

Produces different response tones depending on star rating:
  5-star: enthusiastic thanks
  4-star: grateful with acknowledgment
  3-star: appreciative with improvement note
  1-2 star: empathetic with resolution offer

In demo mode, generates realistic responses without calling the API.
"""

from __future__ import annotations

import json
import logging
import os
from typing import List, Optional

from config import AI_MODEL_CONFIG, DATA_DIR, COMPANIES, get_company
from models import Review, ReviewResponse

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Rating-to-tone mapping and prompt templates
# ---------------------------------------------------------------------------

RATING_TONE_MAP = {
    5: "enthusiastic",
    4: "grateful",
    3: "appreciative",
    2: "empathetic",
    1: "empathetic",
}

RESPONSE_TEMPLATES = {
    "enthusiastic": (
        "Write an enthusiastic, heartfelt thank-you response. Express genuine "
        "excitement about the positive feedback. Reference specific details the "
        "reviewer mentioned. Keep it warm and professional. 2-3 sentences."
    ),
    "grateful": (
        "Write a grateful response that thanks the reviewer warmly. Acknowledge "
        "the positive aspects they mentioned. If they noted any minor concern, "
        "briefly address it with a constructive note. 2-3 sentences."
    ),
    "appreciative": (
        "Write an appreciative response that thanks the reviewer for their honest "
        "feedback. Acknowledge both the positive and the area for improvement they "
        "mentioned. Show that you take their feedback seriously. 3-4 sentences."
    ),
    "empathetic": (
        "Write an empathetic, professional response that sincerely apologises for "
        "the reviewer's negative experience. Acknowledge their specific concerns "
        "without being defensive. Offer a concrete resolution path (direct contact "
        "with a manager, a follow-up call, warranty review). Include a direct "
        "contact method. 4-5 sentences."
    ),
}


# ---------------------------------------------------------------------------
# Demo response generator
# ---------------------------------------------------------------------------

DEMO_RESPONSES = {
    "enthusiastic": [
        (
            "Thank you so much, {author}! We are thrilled to hear about your "
            "experience with {project_ref}. Our team takes tremendous pride in "
            "delivering {brand_keyword} results, and your kind words mean the "
            "world to us. We look forward to working with you again!"
        ),
        (
            "Wow, {author}, what an incredible review! Knowing that our work on "
            "{project_ref} exceeded your expectations is exactly why we do what "
            "we do. Thank you for trusting {company_name} with your project!"
        ),
    ],
    "grateful": [
        (
            "Thank you for the wonderful feedback, {author}! We're glad the work "
            "on {project_ref} met your expectations. We appreciate you noting "
            "{detail_note}, and we'll keep striving for {brand_keyword} results. "
            "Thanks for choosing {company_name}!"
        ),
    ],
    "appreciative": [
        (
            "Thank you for your honest review, {author}. We're pleased that "
            "{positive_note} met your standards. We hear your feedback about "
            "{improvement_note} and are taking it to heart. At {company_name}, "
            "continuous improvement is core to our mission. We appreciate your trust."
        ),
    ],
    "empathetic": [
        (
            "{author}, we sincerely apologise for falling short of the {brand_keyword} "
            "standards we set for ourselves. Your concerns about {concern_note} are "
            "completely valid, and we want to make this right. Our project manager "
            "will reach out within 24 hours to discuss a resolution. In the meantime, "
            "please don't hesitate to call us directly at {phone}."
        ),
    ],
}


def _extract_review_details(review: Review) -> dict:
    """Extract key details from a review for template filling."""
    text_lower = review.text.lower()

    positive_note = "the quality of our work"
    improvement_note = "the area you mentioned"
    concern_note = "the issue you experienced"
    detail_note = "those details"
    project_ref = "your project"

    if "schedule" in text_lower or "time" in text_lower:
        if review.rating >= 4:
            positive_note = "we met your timeline expectations"
        else:
            improvement_note = "the scheduling"
            concern_note = "the timeline challenges"
    if "clean" in text_lower or "debris" in text_lower or "dust" in text_lower:
        if review.rating >= 4:
            positive_note = "our site cleanliness"
            detail_note = "the cleanliness of the worksite"
        else:
            improvement_note = "worksite cleanliness"
            concern_note = "the cleanup issues"
    if "finish" in text_lower or "quality" in text_lower or "flawless" in text_lower:
        positive_note = "the finish quality"
        detail_note = "the quality details"
    if "communication" in text_lower:
        if review.rating >= 4:
            positive_note = "our communication"
        else:
            improvement_note = "our communication process"
            concern_note = "the communication gaps"
    if "budget" in text_lower or "price" in text_lower or "estimate" in text_lower:
        if review.rating >= 4:
            positive_note = "we delivered within budget"
        else:
            improvement_note = "the pricing transparency"
            concern_note = "the cost overruns"
    if "warehouse" in text_lower or "office" in text_lower or "retail" in text_lower:
        for word in ["warehouse", "office", "retail", "building", "space"]:
            if word in text_lower:
                project_ref = f"your {word} project"
                break

    return {
        "positive_note": positive_note,
        "improvement_note": improvement_note,
        "concern_note": concern_note,
        "detail_note": detail_note,
        "project_ref": project_ref,
    }


def _calculate_brand_voice_score(response_text: str, company_slug: str) -> float:
    """Score how well a response matches the company's brand voice (0-1)."""
    company = get_company(company_slug)
    keywords = company.brand_voice_keywords
    text_lower = response_text.lower()

    matches = sum(1 for kw in keywords if kw.lower() in text_lower)
    base_score = min(matches / max(len(keywords) * 0.3, 1), 1.0)

    # Professional tone bonus
    professional_markers = [
        "thank", "appreciate", "team", "pride", "trust",
        "experience", "standards", "quality",
    ]
    tone_matches = sum(1 for m in professional_markers if m in text_lower)
    tone_bonus = min(tone_matches * 0.05, 0.2)

    return round(min(base_score + tone_bonus, 1.0), 2)


def generate_demo_response(review: Review) -> ReviewResponse:
    """Generate a realistic demo response without calling Claude API."""
    tone = RATING_TONE_MAP.get(review.rating, "appreciative")
    company = get_company(review.company)
    details = _extract_review_details(review)

    templates = DEMO_RESPONSES.get(tone, DEMO_RESPONSES["appreciative"])
    template = templates[hash(review.id) % len(templates)]

    brand_keyword = company.brand_voice_keywords[
        hash(review.id) % len(company.brand_voice_keywords)
    ]

    response_text = template.format(
        author=review.author,
        company_name=company.name,
        brand_keyword=brand_keyword,
        phone=company.phone,
        **details,
    )

    brand_voice_score = _calculate_brand_voice_score(response_text, review.company)

    return ReviewResponse(
        review_id=review.id,
        response_text=response_text,
        tone=tone,
        brand_voice_score=brand_voice_score,
    )


# ---------------------------------------------------------------------------
# Live AI response generation
# ---------------------------------------------------------------------------

def generate_ai_response(review: Review) -> ReviewResponse:
    """
    Generate a review response using Claude AI.

    Requires the `anthropic` package and a valid ANTHROPIC_API_KEY env var.
    """
    try:
        import anthropic
    except ImportError:
        logger.warning("anthropic package not installed, falling back to demo mode")
        return generate_demo_response(review)

    api_key = os.environ.get("ANTHROPIC_API_KEY")
    if not api_key:
        logger.warning("ANTHROPIC_API_KEY not set, falling back to demo mode")
        return generate_demo_response(review)

    company = get_company(review.company)
    tone = RATING_TONE_MAP.get(review.rating, "appreciative")
    tone_instruction = RESPONSE_TEMPLATES[tone]

    prompt = (
        f"Company: {company.full_name}\n"
        f"Brand voice keywords: {', '.join(company.brand_voice_keywords)}\n"
        f"Company tagline: {company.tagline}\n"
        f"Company phone: {company.phone}\n\n"
        f"Review from {review.author} ({review.rating}/5 stars):\n"
        f'"{review.text}"\n\n'
        f"Instructions: {tone_instruction}\n\n"
        f"Write the response directly. Do not include any meta-commentary."
    )

    client = anthropic.Anthropic(api_key=api_key)
    message = client.messages.create(
        model=AI_MODEL_CONFIG["model"],
        max_tokens=AI_MODEL_CONFIG["max_tokens"],
        temperature=AI_MODEL_CONFIG["temperature"],
        system=AI_MODEL_CONFIG["system_prompt"],
        messages=[{"role": "user", "content": prompt}],
    )

    response_text = message.content[0].text.strip()
    brand_voice_score = _calculate_brand_voice_score(response_text, review.company)

    return ReviewResponse(
        review_id=review.id,
        response_text=response_text,
        tone=tone,
        brand_voice_score=brand_voice_score,
    )


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

def respond_to_reviews(
    reviews: List[Review],
    demo: bool = True,
) -> List[ReviewResponse]:
    """
    Generate responses for a list of reviews.

    Args:
        reviews: Reviews to respond to.
        demo: If True, use template-based demo responses. If False, use Claude AI.

    Returns:
        List of ReviewResponse objects.
    """
    responses: List[ReviewResponse] = []

    for review in reviews:
        if review.reply:
            logger.info("Review %s already has a reply, skipping", review.id)
            continue

        logger.info(
            "Generating %s response for %s review by %s (%d stars)",
            "demo" if demo else "AI",
            review.company,
            review.author,
            review.rating,
        )

        if demo:
            response = generate_demo_response(review)
        else:
            response = generate_ai_response(review)

        responses.append(response)
        logger.info(
            "Generated response (tone=%s, brand_voice=%.2f)",
            response.tone,
            response.brand_voice_score,
        )

    return responses


def save_responses(responses: List[ReviewResponse]) -> None:
    """Persist responses to the local JSON store."""
    os.makedirs(DATA_DIR, exist_ok=True)
    existing: List[dict] = []
    responses_file = os.path.join(DATA_DIR, "responses.json")

    if os.path.exists(responses_file):
        with open(responses_file, "r") as f:
            existing = json.load(f)

    existing_ids = {r["review_id"] for r in existing}
    for resp in responses:
        if resp.review_id not in existing_ids:
            existing.append(resp.model_dump(mode="json"))

    with open(responses_file, "w") as f:
        json.dump(existing, f, indent=2)

    logger.info("Saved %d responses (total: %d)", len(responses), len(existing))
