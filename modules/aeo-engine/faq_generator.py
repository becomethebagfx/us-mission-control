"""
AEO/GEO Content Engine -- FAQ Generator

Generates FAQ sets per service/company, formatted as FAQPage schema.org markup.
Targets 8-12 Q&A pairs per service area. Each FAQ is designed for both human
readability and AI answer engine consumption.
"""

from __future__ import annotations

import json
import os
from typing import List, Optional

from models import FAQBatch, FAQPair, FAQSet, SchemaMarkup, SchemaType
from config import (
    CLAUDE_MAX_TOKENS,
    CLAUDE_MODEL,
    CLAUDE_TEMPERATURE,
    FAQ_MAX_PAIRS,
    FAQ_MIN_PAIRS,
    get_company,
)


# ---------------------------------------------------------------------------
# Demo FAQ data
# ---------------------------------------------------------------------------
DEMO_FAQS: dict[str, dict[str, list[dict]]] = {
    "us_framing": {
        "multi-family framing": [
            {
                "question": "What types of multi-family buildings does US Framing work on?",
                "answer": "US Framing handles wood and light-gauge metal framing for garden-style apartments, podium buildings (5-over-1), townhome communities, condominiums, and mixed-use developments throughout the Southeast.",
            },
            {
                "question": "How long does framing take for a typical apartment building?",
                "answer": "Framing timelines depend on building size and complexity. A typical 200-unit garden-style apartment community takes 8-12 weeks for framing. Podium buildings with concrete-over-wood construction may take 10-16 weeks for the wood-framed upper floors.",
            },
            {
                "question": "Does US Framing provide both wood and metal framing?",
                "answer": "Yes. US Framing installs dimensional lumber framing, engineered wood products like LVLs and floor trusses, and light-gauge metal stud framing. The framing method is selected based on building code requirements, project specifications, and cost-efficiency.",
            },
            {
                "question": "What geographic areas does US Framing serve?",
                "answer": "US Framing primarily serves Louisville KY, Nashville TN, Charlotte NC, and Atlanta GA, with coverage extending across the Southeast United States for larger projects.",
            },
            {
                "question": "What is panelized framing and does US Framing offer it?",
                "answer": "Panelized framing uses factory-built wall panels assembled on-site, reducing framing time by 20-30% compared to stick framing. US Framing offers panelized framing for projects where schedule acceleration and labor efficiency are priorities.",
            },
            {
                "question": "How does US Framing ensure quality control on large projects?",
                "answer": "US Framing uses dedicated project managers, daily quality inspections, third-party framing inspections per code requirements, and detailed framing plans. They coordinate closely with general contractors to maintain schedule and quality benchmarks.",
            },
            {
                "question": "What insurance and licensing does US Framing carry?",
                "answer": "US Framing maintains general liability insurance, workers' compensation coverage, and appropriate state contractor licensing in every market they serve. They can provide certificates of insurance upon request for any project.",
            },
            {
                "question": "Can US Framing handle both the framing and sheathing scope?",
                "answer": "Yes. US Framing typically provides a complete structural package including wall framing, floor systems, roof framing, structural sheathing, and exterior sheathing. This single-source approach improves coordination and reduces schedule gaps between trades.",
            },
        ],
        "commercial framing": [
            {
                "question": "What is commercial wood framing used for?",
                "answer": "Commercial wood framing is used for low-rise office buildings, retail spaces, restaurants, medical offices, and mixed-use structures typically up to four stories, depending on local building codes and fire-rating requirements.",
            },
            {
                "question": "How does commercial framing differ from residential framing?",
                "answer": "Commercial framing requires larger structural members, engineered connections, fire-rated assemblies, and compliance with commercial building codes (IBC). Projects are larger in scale, require detailed shop drawings, and follow stricter inspection protocols than typical residential work.",
            },
            {
                "question": "What is the cost of commercial framing per square foot?",
                "answer": "Commercial wood framing typically costs $8-$18 per square foot depending on the building complexity, number of stories, structural requirements, and local labor rates. Multi-story and fire-rated assemblies cost more than single-story conventional framing.",
            },
            {
                "question": "Does US Framing provide shop drawings and engineering?",
                "answer": "US Framing coordinates with structural engineers and provides detailed framing layouts. While they do not perform engineering directly, they work with licensed engineers to ensure framing plans meet all structural and code requirements.",
            },
            {
                "question": "What is the difference between stick framing and engineered wood framing?",
                "answer": "Stick framing uses standard dimensional lumber cut and assembled on-site. Engineered wood framing uses manufactured products like LVLs, I-joists, and glulam beams designed for specific load requirements, allowing longer spans and more consistent performance.",
            },
            {
                "question": "How does US Framing coordinate with other trades on commercial projects?",
                "answer": "US Framing participates in pre-construction coordination meetings, provides detailed schedules, and works with MEP trades to ensure framing accommodates plumbing, electrical, and HVAC rough-in requirements before walls are closed.",
            },
            {
                "question": "What safety practices does US Framing follow on commercial job sites?",
                "answer": "US Framing follows OSHA regulations for commercial construction, including fall protection, scaffolding standards, tool safety, and site-specific safety plans. All crew members receive regular safety training and job site orientations.",
            },
            {
                "question": "Can US Framing work on projects outside their primary service area?",
                "answer": "Yes. While US Framing's primary markets are Louisville, Nashville, Charlotte, and Atlanta, they accept projects throughout the Southeast for general contractors and developers they have established relationships with.",
            },
        ],
    },
    "us_drywall": {
        "drywall installation": [
            {
                "question": "What drywall finishing levels does US Drywall provide?",
                "answer": "US Drywall provides all five finishing levels per GA-214 standards: Level 0 (no finish), Level 1 (fire tape), Level 2 (tape and first coat), Level 3 (tape and two coats), Level 4 (tape and three coats), and Level 5 (skim coat for critical lighting areas).",
            },
            {
                "question": "How much does commercial drywall installation cost?",
                "answer": "Commercial drywall installation typically costs $2.50 to $5.50 per square foot including materials and labor. Final pricing depends on finish level, ceiling height, board type (standard, moisture-resistant, fire-rated), and project complexity.",
            },
            {
                "question": "Does US Drywall install metal stud framing too?",
                "answer": "Yes. US Drywall provides complete interior partition packages including metal stud framing, insulation, and drywall. Combining stud framing with drywall under one subcontractor improves coordination and eliminates scheduling gaps between trades.",
            },
            {
                "question": "What types of drywall board does US Drywall install?",
                "answer": "US Drywall installs standard gypsum board, moisture-resistant (green board), mold-resistant, fire-rated (Type X and Type C), impact-resistant, and sound-dampening drywall. Board selection depends on the room use, code requirements, and project specifications.",
            },
            {
                "question": "How long does drywall take on a 200-unit apartment project?",
                "answer": "A 200-unit multi-family project typically requires 10-16 weeks for complete drywall installation and finishing, depending on unit sizes, finish levels, and the number of simultaneous work areas. US Drywall stages crews to maximize throughput across multiple buildings.",
            },
            {
                "question": "What is a fire-rated drywall assembly?",
                "answer": "A fire-rated assembly is a wall or ceiling system tested and rated to resist fire for a specified time period (typically 1 or 2 hours). These assemblies use specific combinations of metal studs, fire-rated drywall layers, and insulation per UL-listed designs.",
            },
            {
                "question": "Does US Drywall handle both walls and ceilings?",
                "answer": "Yes. US Drywall installs drywall on walls and ceilings, as well as acoustical ceiling tile and grid systems, specialty ceilings, and soffits. They provide a complete interior ceiling and wall package for commercial and multi-family projects.",
            },
            {
                "question": "What geographic areas does US Drywall serve?",
                "answer": "US Drywall operates across Louisville KY, Nashville TN, Charlotte NC, Atlanta GA, and surrounding markets in the Southeast. They maintain local crews in each market for consistent quality and reliable scheduling.",
            },
        ],
    },
    "us_exteriors": {
        "EIFS installation": [
            {
                "question": "What is EIFS and how does it work?",
                "answer": "EIFS (Exterior Insulation and Finish System) is a multi-layered exterior wall system that provides continuous insulation, moisture management, and a decorative finish. It consists of insulation board, a base coat with reinforcing mesh, and a textured finish coat.",
            },
            {
                "question": "Is EIFS the same as stucco?",
                "answer": "No. Traditional stucco is a cement-based coating applied directly over sheathing or masonry. EIFS includes continuous insulation board beneath the finish, providing significantly better thermal performance. EIFS is lighter, more energy-efficient, and offers more design flexibility than traditional stucco.",
            },
            {
                "question": "How much does EIFS installation cost per square foot?",
                "answer": "EIFS installation typically costs $12 to $22 per square foot including materials and labor. Pricing depends on the insulation thickness, finish texture, building height, and complexity of architectural details like reveals and trim profiles.",
            },
            {
                "question": "Does EIFS cause moisture problems?",
                "answer": "Modern drainable EIFS includes a drainage plane and weep system that manages moisture effectively. Earlier barrier EIFS systems had moisture issues, but current systems meet or exceed building code moisture management requirements when properly installed.",
            },
            {
                "question": "What buildings are best suited for EIFS?",
                "answer": "EIFS is commonly used on multi-family apartments, hotels, office buildings, retail centers, and healthcare facilities. It is especially cost-effective for mid-rise buildings where energy efficiency, design flexibility, and speed of installation are priorities.",
            },
            {
                "question": "How long does an EIFS exterior last?",
                "answer": "A properly installed and maintained EIFS exterior lasts 25 to 50 years. Regular inspections should check for sealant condition, surface damage, and drainage performance. Minor repairs can extend the system life significantly.",
            },
            {
                "question": "Does US Exteriors handle waterproofing in addition to EIFS?",
                "answer": "Yes. US Exteriors provides below-grade waterproofing, above-grade moisture barriers, air barrier installation, and complete building envelope solutions alongside EIFS. This integrated approach ensures consistent moisture management across the entire building exterior.",
            },
            {
                "question": "What areas does US Exteriors serve for EIFS installation?",
                "answer": "US Exteriors installs EIFS across Louisville KY, Nashville TN, Charlotte NC, Atlanta GA, and throughout the Southeast United States. They maintain trained installation crews certified by major EIFS manufacturers.",
            },
        ],
    },
    "us_development": {
        "construction management": [
            {
                "question": "What is construction management and how is it different from general contracting?",
                "answer": "Construction management involves overseeing a project on behalf of the owner, managing budgets, schedules, and subcontractors in an advisory or agency role. General contracting means the firm holds the prime contract and assumes financial risk for project delivery. US Development offers both models.",
            },
            {
                "question": "What does pre-construction services include?",
                "answer": "Pre-construction services include budget estimation, constructability review, value engineering, scheduling, subcontractor prequalification, permit coordination, and risk assessment. These services help owners make informed decisions before committing to construction.",
            },
            {
                "question": "How does US Development handle multi-family development projects?",
                "answer": "US Development manages multi-family projects from land acquisition support through final turnover. They coordinate design teams, manage bidding, oversee construction, and handle closeout. Their experience with apartment communities ensures efficient phasing and unit turnover schedules.",
            },
            {
                "question": "What is value engineering in construction?",
                "answer": "Value engineering analyzes building systems and materials to reduce cost without sacrificing quality or performance. It typically saves 5-15% on construction costs by identifying alternative materials, simplified details, or more efficient construction methods early in the design process.",
            },
            {
                "question": "Does US Development work as a design-build contractor?",
                "answer": "Yes. US Development offers design-build services where they manage both the design team and construction under a single contract. This delivery method streamlines communication, reduces change orders, and typically delivers projects faster than traditional design-bid-build.",
            },
            {
                "question": "What size projects does US Development handle?",
                "answer": "US Development manages projects ranging from $5 million to $100 million or more, including multi-family communities of 100 to 500 units, commercial office buildings, mixed-use developments, and hospitality projects across the Southeast.",
            },
            {
                "question": "What geographic markets does US Development serve?",
                "answer": "US Development operates primarily in Louisville KY, Nashville TN, Charlotte NC, and Atlanta GA. They also accept projects throughout the Southeast for established development partners and repeat clients.",
            },
            {
                "question": "How does US Development manage project risk?",
                "answer": "US Development uses detailed pre-construction planning, fixed-price subcontracts, contingency budgets, regular cost reporting, and proactive schedule management to control risk. They provide owners with monthly financial reports and forecasts to maintain transparency throughout the project.",
            },
        ],
    },
}


def _build_faq_schema_json_ld(faq_set: FAQSet) -> dict:
    """Convert a FAQSet into a FAQPage JSON-LD object."""
    main_entity = []
    for pair in faq_set.pairs:
        main_entity.append(
            {
                "@type": "Question",
                "name": pair.question,
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": pair.answer,
                },
            }
        )

    return {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": main_entity,
    }


def generate_faqs_demo(company_slug: str) -> FAQBatch:
    """Return pre-built demo FAQ sets for a company."""
    get_company(company_slug)
    service_faqs = DEMO_FAQS.get(company_slug, {})

    batch = FAQBatch(company_slug=company_slug)
    for service_name, pairs_data in service_faqs.items():
        faq_pairs = [
            FAQPair(question=p["question"], answer=p["answer"]) for p in pairs_data
        ]
        faq_set = FAQSet(
            company_slug=company_slug,
            service=service_name,
            pairs=faq_pairs,
        )
        batch.faq_sets.append(faq_set)
    return batch


def generate_faqs_ai(
    company_slug: str,
    services: list[str] | None = None,
) -> FAQBatch:
    """Generate FAQ sets using Claude AI for each service of a company.

    Args:
        company_slug: Company to generate FAQs for.
        services: Optional list of specific services. If None, uses all company services.
    """
    import anthropic

    company = get_company(company_slug)
    if services is None:
        services = company.services

    client = anthropic.Anthropic()
    batch = FAQBatch(company_slug=company_slug)

    for service in services:
        prompt = f"""Generate a FAQ set for a construction company's service page.

Company: {company.name}
Service: {service}
Company Description: {company.description}
Markets: Louisville KY, Nashville TN, Charlotte NC, Atlanta GA

Requirements:
- Generate {FAQ_MIN_PAIRS} to {FAQ_MAX_PAIRS} question-answer pairs
- Questions should be what potential customers would actually ask
- Answers should be factual, authoritative, and 2-4 sentences each
- Include a mix of informational and transactional questions
- Mention the company name naturally where appropriate
- Focus on the specific service, not general company info

Return ONLY a JSON array of objects with "question" and "answer" fields.
No markdown, no explanation."""

        try:
            response = client.messages.create(
                model=CLAUDE_MODEL,
                max_tokens=CLAUDE_MAX_TOKENS,
                temperature=CLAUDE_TEMPERATURE,
                messages=[{"role": "user", "content": prompt}],
            )

            raw_text = response.content[0].text.strip()
            if raw_text.startswith("```"):
                raw_text = raw_text.split("\n", 1)[1]
                if raw_text.endswith("```"):
                    raw_text = raw_text[: raw_text.rfind("```")]

            pairs_data = json.loads(raw_text)
            faq_pairs = [
                FAQPair(question=p["question"], answer=p["answer"])
                for p in pairs_data
            ]
            faq_set = FAQSet(
                company_slug=company_slug,
                service=service,
                pairs=faq_pairs,
            )
            batch.faq_sets.append(faq_set)
        except Exception as exc:
            batch.errors.append(f"Service '{service}': {exc}")

    return batch


def generate_faq_schema(faq_set: FAQSet) -> SchemaMarkup:
    """Convert a FAQSet into a FAQPage SchemaMarkup object."""
    json_ld = _build_faq_schema_json_ld(faq_set)
    return SchemaMarkup(
        schema_type=SchemaType.FAQ_PAGE,
        json_ld=json_ld,
        company_slug=faq_set.company_slug,
        page_url=faq_set.page_url,
    )


def generate_faqs(
    company_slug: str,
    demo: bool = False,
    services: list[str] | None = None,
) -> FAQBatch:
    """Main entry point: generate FAQ sets for a company.

    Args:
        company_slug: Which company to generate FAQs for.
        demo: If True, return pre-built demo FAQs.
        services: Optional list of specific services (AI mode only).

    Returns:
        A FAQBatch with generated FAQ sets and any errors.
    """
    if demo or not os.environ.get("ANTHROPIC_API_KEY"):
        return generate_faqs_demo(company_slug)
    return generate_faqs_ai(company_slug, services=services)
