"""
AEO/GEO Content Engine -- Schema Generator

Auto-generates valid JSON-LD structured data for:
  - HomeAndConstructionBusiness
  - FAQPage
  - HowTo (service process documentation)
  - Service (individual service offerings)
  - LocalBusiness (geo-targeted)

All output is validated for correct JSON-LD structure before returning.
"""

from __future__ import annotations

import json
from typing import Any, Dict, List, Optional

from models import SchemaMarkup, SchemaType, SchemaBatch
from config import COMPANIES, GEOGRAPHIC_MODIFIERS, PRIMARY_MARKETS, get_company


# ---------------------------------------------------------------------------
# Schema Generators
# ---------------------------------------------------------------------------


def generate_home_and_construction_business(
    company_slug: str,
) -> SchemaMarkup:
    """Generate HomeAndConstructionBusiness JSON-LD for a company.

    Includes name, description, phone, address, services, and aggregate rating.
    """
    company = get_company(company_slug)

    json_ld: Dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "HomeAndConstructionBusiness",
        "name": company.name,
        "description": company.description,
        "telephone": company.phone,
        "address": {
            "@type": "PostalAddress",
            "addressLocality": company.address.split(",")[0].strip(),
            "addressRegion": company.address.split(",")[-1].strip().split()[0]
            if "," in company.address
            else "",
            "addressCountry": "US",
        },
        "url": f"https://www.{company.domain}",
        "areaServed": [
            {"@type": "City", "name": market} for market in PRIMARY_MARKETS
        ],
        "hasOfferCatalog": {
            "@type": "OfferCatalog",
            "name": f"{company.name} Services",
            "itemListElement": [
                {
                    "@type": "Offer",
                    "itemOffered": {
                        "@type": "Service",
                        "name": service,
                    },
                }
                for service in company.services
            ],
        },
    }

    if company.aggregate_rating > 0 and company.review_count > 0:
        json_ld["aggregateRating"] = {
            "@type": "AggregateRating",
            "ratingValue": str(company.aggregate_rating),
            "reviewCount": str(company.review_count),
            "bestRating": "5",
            "worstRating": "1",
        }

    return SchemaMarkup(
        schema_type=SchemaType.HOME_AND_CONSTRUCTION_BUSINESS,
        json_ld=json_ld,
        company_slug=company_slug,
    )


def generate_faq_page(
    questions_and_answers: List[Dict[str, str]],
    company_slug: str = "",
    page_url: str = "",
) -> SchemaMarkup:
    """Generate FAQPage JSON-LD from a list of Q&A dicts.

    Each dict must have 'question' and 'answer' keys.
    """
    main_entity = []
    for qa in questions_and_answers:
        main_entity.append(
            {
                "@type": "Question",
                "name": qa["question"],
                "acceptedAnswer": {
                    "@type": "Answer",
                    "text": qa["answer"],
                },
            }
        )

    json_ld: Dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "FAQPage",
        "mainEntity": main_entity,
    }

    return SchemaMarkup(
        schema_type=SchemaType.FAQ_PAGE,
        json_ld=json_ld,
        company_slug=company_slug,
        page_url=page_url,
    )


def generate_how_to(
    name: str,
    description: str,
    steps: List[Dict[str, str]],
    company_slug: str = "",
    total_time: str = "",
    estimated_cost: str = "",
) -> SchemaMarkup:
    """Generate HowTo JSON-LD for a service process.

    Args:
        name: Title of the process (e.g. "Multi-Family Framing Process").
        description: Overview of the process.
        steps: List of dicts with 'name' and 'text' keys for each step.
        company_slug: Optional company slug.
        total_time: Optional ISO 8601 duration (e.g. "P8W" for 8 weeks).
        estimated_cost: Optional cost description.
    """
    how_to_steps = []
    for i, step in enumerate(steps, 1):
        how_to_steps.append(
            {
                "@type": "HowToStep",
                "position": str(i),
                "name": step["name"],
                "text": step["text"],
            }
        )

    json_ld: Dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "HowTo",
        "name": name,
        "description": description,
        "step": how_to_steps,
    }

    if total_time:
        json_ld["totalTime"] = total_time
    if estimated_cost:
        json_ld["estimatedCost"] = {
            "@type": "MonetaryAmount",
            "currency": "USD",
            "value": estimated_cost,
        }

    return SchemaMarkup(
        schema_type=SchemaType.HOW_TO,
        json_ld=json_ld,
        company_slug=company_slug,
    )


def generate_service(
    service_name: str,
    description: str,
    company_slug: str,
    area_served: List[str] | None = None,
    price_range: str = "",
) -> SchemaMarkup:
    """Generate Service JSON-LD for an individual service offering.

    Args:
        service_name: Name of the service.
        description: Description of what the service provides.
        company_slug: Company offering the service.
        area_served: List of geographic areas served.
        price_range: Optional price range string.
    """
    company = get_company(company_slug)
    area_served = area_served or PRIMARY_MARKETS

    json_ld: Dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "Service",
        "name": service_name,
        "description": description,
        "provider": {
            "@type": "HomeAndConstructionBusiness",
            "name": company.name,
            "url": f"https://www.{company.domain}",
        },
        "areaServed": [
            {"@type": "City", "name": area} for area in area_served
        ],
        "serviceType": service_name,
    }

    if price_range:
        json_ld["priceRange"] = price_range

    return SchemaMarkup(
        schema_type=SchemaType.SERVICE,
        json_ld=json_ld,
        company_slug=company_slug,
    )


def generate_local_business(
    company_slug: str,
    target_city: str,
) -> SchemaMarkup:
    """Generate LocalBusiness JSON-LD geo-targeted to a specific city.

    Args:
        company_slug: Company to generate for.
        target_city: The target city (e.g. "Nashville TN").
    """
    company = get_company(company_slug)

    city_parts = target_city.rsplit(" ", 1)
    city_name = city_parts[0] if len(city_parts) > 1 else target_city
    state = city_parts[1] if len(city_parts) > 1 else ""

    json_ld: Dict[str, Any] = {
        "@context": "https://schema.org",
        "@type": "LocalBusiness",
        "name": f"{company.name} - {city_name}",
        "description": f"{company.description} Serving {target_city} and surrounding areas.",
        "telephone": company.phone,
        "address": {
            "@type": "PostalAddress",
            "addressLocality": city_name,
            "addressRegion": state,
            "addressCountry": "US",
        },
        "url": f"https://www.{company.domain}",
        "areaServed": {
            "@type": "City",
            "name": target_city,
        },
        "hasOfferCatalog": {
            "@type": "OfferCatalog",
            "name": f"{company.name} Services in {city_name}",
            "itemListElement": [
                {
                    "@type": "Offer",
                    "itemOffered": {
                        "@type": "Service",
                        "name": svc,
                    },
                }
                for svc in company.services
            ],
        },
    }

    if company.aggregate_rating > 0 and company.review_count > 0:
        json_ld["aggregateRating"] = {
            "@type": "AggregateRating",
            "ratingValue": str(company.aggregate_rating),
            "reviewCount": str(company.review_count),
            "bestRating": "5",
            "worstRating": "1",
        }

    return SchemaMarkup(
        schema_type=SchemaType.LOCAL_BUSINESS,
        json_ld=json_ld,
        company_slug=company_slug,
    )


# ---------------------------------------------------------------------------
# Batch Generation
# ---------------------------------------------------------------------------


def generate_all_schemas(company_slug: str) -> SchemaBatch:
    """Generate all schema types for a company.

    Returns a SchemaBatch containing:
      - 1 HomeAndConstructionBusiness schema
      - 1 Service schema per company service
      - 1 LocalBusiness schema per primary market
      - 1 HowTo schema (general process)
    """
    company = get_company(company_slug)
    batch = SchemaBatch(company_slug=company_slug)

    # HomeAndConstructionBusiness
    try:
        hcb = generate_home_and_construction_business(company_slug)
        batch.schemas.append(hcb)
    except Exception as exc:
        batch.errors.append(f"HomeAndConstructionBusiness: {exc}")

    # Service schemas for each service
    for service in company.services:
        try:
            svc = generate_service(
                service_name=service,
                description=f"{company.name} provides professional {service} services for commercial and multi-family construction projects.",
                company_slug=company_slug,
            )
            batch.schemas.append(svc)
        except Exception as exc:
            batch.errors.append(f"Service '{service}': {exc}")

    # LocalBusiness schemas for primary markets
    for market in PRIMARY_MARKETS:
        try:
            lb = generate_local_business(company_slug, market)
            batch.schemas.append(lb)
        except Exception as exc:
            batch.errors.append(f"LocalBusiness '{market}': {exc}")

    # HowTo schema (generic project process)
    try:
        how_to = generate_how_to(
            name=f"{company.name} Project Process",
            description=f"How {company.name} delivers {company.services[0]} projects from start to finish.",
            steps=[
                {
                    "name": "Pre-Construction Planning",
                    "text": "Review project plans, conduct site assessment, and develop a detailed scope of work and schedule.",
                },
                {
                    "name": "Mobilization",
                    "text": "Coordinate material deliveries, mobilize crews, and establish on-site safety protocols.",
                },
                {
                    "name": "Execution",
                    "text": f"Perform {company.services[0]} according to project specifications with daily quality control inspections.",
                },
                {
                    "name": "Quality Assurance",
                    "text": "Conduct final inspections, address punch-list items, and obtain sign-off from the general contractor.",
                },
                {
                    "name": "Project Closeout",
                    "text": "Deliver as-built documentation, complete warranty paperwork, and demobilize from the site.",
                },
            ],
            company_slug=company_slug,
        )
        batch.schemas.append(how_to)
    except Exception as exc:
        batch.errors.append(f"HowTo: {exc}")

    return batch


def validate_json_ld(schema: SchemaMarkup) -> list[str]:
    """Validate a SchemaMarkup object and return a list of issues (empty = valid).

    Checks:
      - @context is present and correct
      - @type is present and matches schema_type
      - JSON is serializable
      - Required fields per type are present
    """
    issues: list[str] = []
    ld = schema.json_ld

    if ld.get("@context") != "https://schema.org":
        issues.append("@context must be 'https://schema.org'")

    expected_type = schema.schema_type.value
    actual_type = ld.get("@type", "")
    if actual_type != expected_type:
        issues.append(f"@type mismatch: expected '{expected_type}', got '{actual_type}'")

    # Type-specific required fields
    required_fields: dict[str, list[str]] = {
        "HomeAndConstructionBusiness": ["name", "description", "telephone"],
        "FAQPage": ["mainEntity"],
        "HowTo": ["name", "step"],
        "Service": ["name", "provider"],
        "LocalBusiness": ["name", "address"],
    }

    for field in required_fields.get(expected_type, []):
        if field not in ld:
            issues.append(f"Missing required field '{field}' for {expected_type}")

    # Verify serializable
    try:
        json.dumps(ld)
    except (TypeError, ValueError) as exc:
        issues.append(f"JSON-LD is not serializable: {exc}")

    return issues


def render_json_ld_script_tag(schema: SchemaMarkup) -> str:
    """Render a SchemaMarkup as an HTML <script> tag ready for page insertion."""
    json_str = json.dumps(schema.json_ld, indent=2)
    return f'<script type="application/ld+json">\n{json_str}\n</script>'
