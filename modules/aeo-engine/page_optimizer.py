"""
AEO/GEO Content Engine -- Page Optimizer

Analyzes HTML pages and scores their AEO (Answer Engine Optimization) readiness
on a 0-100 scale. Checks heading structure, capsule presence, schema markup,
robots.txt bot access, answer density, and word count.

Returns per-page optimization reports with specific, actionable recommendations.
"""

from __future__ import annotations

import json
import re
from typing import Any, Dict, List, Optional

from models import OptimizationIssue, OptimizationScore
from config import AEO_SCORING_WEIGHTS, ALLOWED_BOTS, MIN_ANSWER_DENSITY


# ---------------------------------------------------------------------------
# Sample HTML for demo mode
# ---------------------------------------------------------------------------
DEMO_HTML_GOOD = """<!DOCTYPE html>
<html lang="en">
<head>
    <title>Multi-Family Framing Contractor | US Framing</title>
    <meta name="description" content="US Framing is a professional multi-family framing contractor serving Louisville, Nashville, Charlotte, and Atlanta.">
    <script type="application/ld+json">
    {
        "@context": "https://schema.org",
        "@type": "HomeAndConstructionBusiness",
        "name": "US Framing",
        "description": "Professional wood and metal framing contractor specializing in multi-family and commercial projects.",
        "telephone": "(502) 555-0101",
        "aggregateRating": {
            "@type": "AggregateRating",
            "ratingValue": "4.9",
            "reviewCount": "67"
        }
    }
    </script>
</head>
<body>
    <h1>Multi-Family Framing Contractor</h1>
    <p>US Framing is a leading multi-family framing contractor serving Louisville and the Southeast. They specialize in wood and light-gauge metal framing for apartment complexes, condominiums, and mixed-use developments. Their experienced crews deliver precise structural framing on schedule, supporting projects from four-story walk-ups to large podium-style buildings.</p>

    <h2>Our Framing Services</h2>
    <p>We provide complete structural framing packages including wall framing, floor systems, roof framing, and exterior sheathing.</p>

    <h3>Wood Framing</h3>
    <p>Dimensional lumber and engineered wood products for residential and commercial structures up to five stories.</p>

    <h3>Metal Framing</h3>
    <p>Light-gauge metal stud framing for commercial interiors, exterior walls, and fire-rated assemblies.</p>

    <h2>Frequently Asked Questions</h2>
    <h3>How long does framing take for an apartment building?</h3>
    <p>A typical 200-unit garden-style apartment community takes 8-12 weeks for framing. Podium buildings may take 10-16 weeks for the wood-framed upper floors.</p>

    <h3>What areas does US Framing serve?</h3>
    <p>US Framing serves Louisville KY, Nashville TN, Charlotte NC, Atlanta GA, and the broader Southeast region.</p>
</body>
</html>"""


DEMO_HTML_POOR = """<!DOCTYPE html>
<html>
<head>
    <title>US Framing</title>
</head>
<body>
    <div class="hero">
        <h1>Welcome to Our Site</h1>
    </div>
    <div class="content">
        <p>We do framing. Call us for more info.</p>
        <p>Contact: (502) 555-0101</p>
    </div>
</body>
</html>"""


DEMO_ROBOTS_TXT = """User-agent: *
Allow: /

User-agent: GPTBot
Allow: /

User-agent: PerplexityBot
Allow: /

User-agent: Google-Extended
Allow: /

User-agent: ClaudeBot
Allow: /

Sitemap: https://www.usframing.com/sitemap.xml"""


# ---------------------------------------------------------------------------
# Scoring Functions
# ---------------------------------------------------------------------------


def _score_heading_structure(html: str) -> tuple[int, list[OptimizationIssue]]:
    """Score heading structure (0-100). Checks H1 presence, H2/H3 hierarchy."""
    issues: list[OptimizationIssue] = []
    score = 100

    h1_matches = re.findall(r"<h1[^>]*>(.*?)</h1>", html, re.IGNORECASE | re.DOTALL)
    h2_matches = re.findall(r"<h2[^>]*>(.*?)</h2>", html, re.IGNORECASE | re.DOTALL)
    h3_matches = re.findall(r"<h3[^>]*>(.*?)</h3>", html, re.IGNORECASE | re.DOTALL)

    if len(h1_matches) == 0:
        score -= 40
        issues.append(
            OptimizationIssue(
                category="heading_structure",
                severity="critical",
                message="No H1 tag found on the page.",
                recommendation="Add a single, descriptive H1 tag that includes the primary service keyword.",
            )
        )
    elif len(h1_matches) > 1:
        score -= 20
        issues.append(
            OptimizationIssue(
                category="heading_structure",
                severity="medium",
                message=f"Multiple H1 tags found ({len(h1_matches)}). Pages should have exactly one H1.",
                recommendation="Consolidate to a single H1 and demote others to H2.",
            )
        )

    if len(h2_matches) == 0:
        score -= 30
        issues.append(
            OptimizationIssue(
                category="heading_structure",
                severity="high",
                message="No H2 tags found. Pages need section headings for AI parsing.",
                recommendation="Add H2 headings for each major section (Services, FAQ, Process, etc.).",
            )
        )

    if len(h3_matches) == 0 and len(h2_matches) > 0:
        score -= 10
        issues.append(
            OptimizationIssue(
                category="heading_structure",
                severity="low",
                message="No H3 sub-headings found. Deeper structure helps AI engines parse content.",
                recommendation="Add H3 headings under H2 sections for specific topics or FAQ questions.",
            )
        )

    # Check for generic/non-descriptive H1
    if h1_matches:
        h1_text = h1_matches[0].strip().lower()
        generic_h1s = ["welcome", "home", "about us", "our company", "hello"]
        if any(h1_text.startswith(g) for g in generic_h1s):
            score -= 20
            issues.append(
                OptimizationIssue(
                    category="heading_structure",
                    severity="high",
                    message=f"H1 is generic: '{h1_matches[0].strip()}'. AI engines need descriptive headings.",
                    recommendation="Replace with a keyword-rich H1 like 'Multi-Family Framing Contractor Louisville KY'.",
                )
            )

    return max(score, 0), issues


def _score_capsule_presence(html: str) -> tuple[int, list[OptimizationIssue]]:
    """Score for presence of answer-capsule-style content (40-60 word paragraphs)."""
    issues: list[OptimizationIssue] = []

    # Extract paragraph text
    paragraphs = re.findall(r"<p[^>]*>(.*?)</p>", html, re.IGNORECASE | re.DOTALL)
    paragraph_texts = [re.sub(r"<[^>]+>", "", p).strip() for p in paragraphs]
    paragraph_texts = [p for p in paragraph_texts if p]

    if not paragraph_texts:
        issues.append(
            OptimizationIssue(
                category="capsule_presence",
                severity="critical",
                message="No paragraph content found on the page.",
                recommendation="Add substantive paragraph content answering key customer questions.",
            )
        )
        return 0, issues

    # Count capsule-length paragraphs (40-60 words)
    capsule_count = 0
    near_capsule_count = 0
    for text in paragraph_texts:
        wc = len(text.split())
        if 40 <= wc <= 60:
            capsule_count += 1
        elif 30 <= wc <= 80:
            near_capsule_count += 1

    total_paras = len(paragraph_texts)
    score = 0

    if capsule_count >= 3:
        score = 100
    elif capsule_count == 2:
        score = 80
    elif capsule_count == 1:
        score = 60
    elif near_capsule_count >= 2:
        score = 40
        issues.append(
            OptimizationIssue(
                category="capsule_presence",
                severity="medium",
                message=f"Found {near_capsule_count} near-capsule paragraphs but no exact 40-60 word capsules.",
                recommendation="Refine paragraphs to be exactly 40-60 words, self-contained, and directly answering a question.",
            )
        )
    else:
        score = 10
        issues.append(
            OptimizationIssue(
                category="capsule_presence",
                severity="high",
                message="No answer capsules (40-60 word self-contained paragraphs) found.",
                recommendation="Add 2-3 answer capsules that directly answer common customer questions in 40-60 words each.",
            )
        )

    return score, issues


def _score_schema_markup(html: str) -> tuple[int, list[OptimizationIssue]]:
    """Score schema.org JSON-LD markup presence and quality."""
    issues: list[OptimizationIssue] = []

    ld_blocks = re.findall(
        r'<script[^>]*type=["\']application/ld\+json["\'][^>]*>(.*?)</script>',
        html,
        re.IGNORECASE | re.DOTALL,
    )

    if not ld_blocks:
        issues.append(
            OptimizationIssue(
                category="schema_markup",
                severity="critical",
                message="No JSON-LD schema markup found on the page.",
                recommendation="Add HomeAndConstructionBusiness, FAQPage, and/or Service JSON-LD schema.",
            )
        )
        return 0, issues

    score = 50  # Base score for having any schema
    valid_schemas: list[str] = []

    for block in ld_blocks:
        try:
            data = json.loads(block.strip())
            schema_type = data.get("@type", "unknown")
            valid_schemas.append(schema_type)

            if data.get("@context") != "https://schema.org":
                issues.append(
                    OptimizationIssue(
                        category="schema_markup",
                        severity="medium",
                        message=f"Schema @context is not 'https://schema.org' in {schema_type}.",
                        recommendation="Set @context to 'https://schema.org'.",
                    )
                )

            # Bonus for construction-relevant types
            if schema_type in [
                "HomeAndConstructionBusiness",
                "LocalBusiness",
                "FAQPage",
                "Service",
                "HowTo",
            ]:
                score += 15

        except json.JSONDecodeError:
            issues.append(
                OptimizationIssue(
                    category="schema_markup",
                    severity="high",
                    message="Invalid JSON in a JSON-LD script block.",
                    recommendation="Fix the JSON syntax in the schema markup.",
                )
            )

    # Check for key schema types
    desired_types = {"HomeAndConstructionBusiness", "FAQPage"}
    present_types = set(valid_schemas)
    missing = desired_types - present_types
    if missing:
        issues.append(
            OptimizationIssue(
                category="schema_markup",
                severity="medium",
                message=f"Missing recommended schema types: {', '.join(missing)}.",
                recommendation=f"Add {', '.join(missing)} JSON-LD schema to the page.",
            )
        )

    return min(score, 100), issues


def _score_bot_access(robots_txt: str) -> tuple[int, list[OptimizationIssue]]:
    """Score robots.txt configuration for AI bot access."""
    issues: list[OptimizationIssue] = []

    if not robots_txt.strip():
        issues.append(
            OptimizationIssue(
                category="bot_access",
                severity="high",
                message="No robots.txt content provided or file is empty.",
                recommendation="Create a robots.txt that explicitly allows GPTBot, PerplexityBot, ClaudeBot, and Google-Extended.",
            )
        )
        return 30, issues  # Empty robots.txt allows all by default, partial credit

    score = 40  # Base score for having a robots.txt
    robots_lower = robots_txt.lower()

    for bot in ALLOWED_BOTS:
        bot_lower = bot.lower()
        if bot_lower in robots_lower:
            # Check if it's allowed or disallowed
            # Simple heuristic: look for "User-agent: BotName" followed by "Allow" or "Disallow"
            bot_section = robots_txt[robots_lower.find(bot_lower) :]
            if "disallow: /" in bot_section.lower().split("\n\n")[0]:
                issues.append(
                    OptimizationIssue(
                        category="bot_access",
                        severity="critical",
                        message=f"{bot} is explicitly disallowed in robots.txt.",
                        recommendation=f"Change 'Disallow: /' to 'Allow: /' for {bot}.",
                    )
                )
                score -= 15
            else:
                score += 12  # Points for each allowed bot
        else:
            issues.append(
                OptimizationIssue(
                    category="bot_access",
                    severity="medium",
                    message=f"{bot} not mentioned in robots.txt.",
                    recommendation=f"Add 'User-agent: {bot}\\nAllow: /' to robots.txt.",
                )
            )

    return min(max(score, 0), 100), issues


def _score_answer_density(html: str) -> tuple[int, list[OptimizationIssue]]:
    """Score the ratio of answer-like sentences to total content."""
    issues: list[OptimizationIssue] = []

    # Extract text content
    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    text = " ".join(text.split())

    sentences = [s.strip() for s in re.split(r"[.!?]+", text) if s.strip()]
    if not sentences:
        issues.append(
            OptimizationIssue(
                category="answer_density",
                severity="critical",
                message="No readable sentence content found.",
                recommendation="Add substantive content that directly answers customer questions.",
            )
        )
        return 0, issues

    # Heuristic: answer-like sentences contain factual, specific information
    answer_signals = [
        r"\d+",  # Contains numbers (costs, timelines, measurements)
        r"(?:provides?|offers?|serves?|includes?|specializ)",  # Service language
        r"(?:typically|usually|approximately|about|ranges?)",  # Authoritative hedging
        r"(?:installed?|built|constructed|managed|delivered)",  # Action verbs
    ]

    answer_count = 0
    for sentence in sentences:
        if len(sentence.split()) < 5:
            continue
        if any(re.search(pattern, sentence, re.IGNORECASE) for pattern in answer_signals):
            answer_count += 1

    density = answer_count / len(sentences) if sentences else 0

    if density >= MIN_ANSWER_DENSITY * 5:
        score = 100
    elif density >= MIN_ANSWER_DENSITY * 3:
        score = 75
    elif density >= MIN_ANSWER_DENSITY:
        score = 50
    else:
        score = 20
        issues.append(
            OptimizationIssue(
                category="answer_density",
                severity="high",
                message=f"Low answer density ({density:.1%}). Content lacks specific, factual answers.",
                recommendation="Add specific details: costs, timelines, service areas, and process steps.",
            )
        )

    return score, issues


def _score_word_count(html: str) -> tuple[int, list[OptimizationIssue]]:
    """Score total word count of page content."""
    issues: list[OptimizationIssue] = []

    text = re.sub(r"<script[^>]*>.*?</script>", "", html, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<style[^>]*>.*?</style>", "", text, flags=re.DOTALL | re.IGNORECASE)
    text = re.sub(r"<[^>]+>", "", text)
    words = text.split()
    wc = len(words)

    if wc >= 1500:
        score = 100
    elif wc >= 1000:
        score = 85
    elif wc >= 600:
        score = 70
    elif wc >= 300:
        score = 50
    elif wc >= 100:
        score = 25
    else:
        score = 5

    if wc < 600:
        issues.append(
            OptimizationIssue(
                category="word_count",
                severity="high" if wc < 300 else "medium",
                message=f"Page has only {wc} words. AI engines prefer substantive content (600+ words).",
                recommendation="Expand content to 600-1500 words with service details, FAQs, and process information.",
            )
        )

    return score, issues


# ---------------------------------------------------------------------------
# Main Optimizer
# ---------------------------------------------------------------------------


def optimize_page(
    html: str,
    robots_txt: str = "",
    page_url: str = "",
    company_slug: str = "",
) -> OptimizationScore:
    """Analyze an HTML page and score its AEO readiness (0-100).

    Args:
        html: The full HTML content of the page.
        robots_txt: The robots.txt content for the site.
        page_url: URL of the page being analyzed.
        company_slug: Company the page belongs to.

    Returns:
        An OptimizationScore with overall score, per-category breakdown, issues, and recommendations.
    """
    all_issues: list[OptimizationIssue] = []
    breakdown: dict[str, int] = {}

    # Run each scoring function
    heading_score, heading_issues = _score_heading_structure(html)
    breakdown["heading_structure"] = heading_score
    all_issues.extend(heading_issues)

    capsule_score, capsule_issues = _score_capsule_presence(html)
    breakdown["capsule_presence"] = capsule_score
    all_issues.extend(capsule_issues)

    schema_score, schema_issues = _score_schema_markup(html)
    breakdown["schema_markup"] = schema_score
    all_issues.extend(schema_issues)

    bot_score, bot_issues = _score_bot_access(robots_txt)
    breakdown["bot_access"] = bot_score
    all_issues.extend(bot_issues)

    density_score, density_issues = _score_answer_density(html)
    breakdown["answer_density"] = density_score
    all_issues.extend(density_issues)

    wc_score, wc_issues = _score_word_count(html)
    breakdown["word_count"] = wc_score
    all_issues.extend(wc_issues)

    # Calculate weighted overall score
    overall = 0
    for category, weight in AEO_SCORING_WEIGHTS.items():
        category_score = breakdown.get(category, 0)
        overall += (category_score * weight) / 100

    overall = int(round(overall))
    overall = max(0, min(100, overall))

    # Generate prioritized recommendations from issues
    severity_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
    sorted_issues = sorted(
        all_issues, key=lambda i: severity_order.get(i.severity, 4)
    )
    recommendations = [
        f"[{i.severity.upper()}] {i.recommendation}"
        for i in sorted_issues
        if i.recommendation
    ]

    return OptimizationScore(
        page_url=page_url or "unknown",
        score=overall,
        breakdown=breakdown,
        issues=sorted_issues,
        recommendations=recommendations,
        company_slug=company_slug,
    )


def optimize_page_demo() -> list[OptimizationScore]:
    """Run the optimizer on demo HTML pages and return results."""
    results = []

    # Good page
    good_result = optimize_page(
        html=DEMO_HTML_GOOD,
        robots_txt=DEMO_ROBOTS_TXT,
        page_url="https://www.usframing.com/services/multi-family-framing",
        company_slug="us_framing",
    )
    results.append(good_result)

    # Poor page
    poor_result = optimize_page(
        html=DEMO_HTML_POOR,
        robots_txt="",
        page_url="https://www.usframing.com/old-homepage",
        company_slug="us_framing",
    )
    results.append(poor_result)

    return results
