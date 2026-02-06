"""
AEO/GEO Content Engine -- Pydantic Models

Data models for answer capsules, FAQ sets, schema markup, citation reports,
optimization scores, and target queries used throughout the engine.
"""

from __future__ import annotations

import json
from enum import Enum
from typing import Any, Dict, List, Optional

from pydantic import BaseModel, Field, field_validator, model_validator


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------
class QueryIntent(str, Enum):
    """Search intent categories."""

    INFORMATIONAL = "informational"
    TRANSACTIONAL = "transactional"
    NAVIGATIONAL = "navigational"


class CitationTrend(str, Enum):
    """Direction of citation visibility over time."""

    UP = "up"
    DOWN = "down"
    STABLE = "stable"


class SchemaType(str, Enum):
    """Supported schema.org JSON-LD types."""

    HOME_AND_CONSTRUCTION_BUSINESS = "HomeAndConstructionBusiness"
    FAQ_PAGE = "FAQPage"
    HOW_TO = "HowTo"
    SERVICE = "Service"
    LOCAL_BUSINESS = "LocalBusiness"


# ---------------------------------------------------------------------------
# Target Query
# ---------------------------------------------------------------------------
class TargetQuery(BaseModel):
    """A single target query with metadata."""

    query: str = Field(..., min_length=5, description="The search query text")
    company_slug: str = Field(..., description="Company this query targets")
    service: str = Field(default="", description="Specific service category")
    intent: QueryIntent = Field(
        default=QueryIntent.TRANSACTIONAL, description="Search intent category"
    )
    priority: int = Field(
        default=5, ge=1, le=10, description="Priority ranking 1 (low) - 10 (high)"
    )
    geographic_modifier: str = Field(
        default="", description="Geographic modifier applied to the query"
    )


# ---------------------------------------------------------------------------
# Answer Capsule
# ---------------------------------------------------------------------------
class AnswerCapsule(BaseModel):
    """A self-contained 40-60 word answer capsule optimized for AI citation."""

    content: str = Field(
        ..., min_length=20, description="The answer capsule text (40-60 words)"
    )
    word_count: int = Field(..., ge=40, le=60, description="Word count (must be 40-60)")
    query: str = Field(..., description="The target query this capsule answers")
    company_slug: str = Field(..., description="Company this capsule is for")
    source_attribution: str = Field(
        default="", description="Source or basis for the answer"
    )

    @field_validator("word_count")
    @classmethod
    def validate_word_count_range(cls, v: int) -> int:
        """Enforce strict 40-60 word count."""
        if v < 40:
            raise ValueError(
                f"Capsule word count is {v}, minimum is 40. "
                "Capsule must be expanded to at least 40 words."
            )
        if v > 60:
            raise ValueError(
                f"Capsule word count is {v}, maximum is 60. "
                "Capsule must be trimmed to 60 words or fewer."
            )
        return v

    @model_validator(mode="after")
    def verify_content_matches_word_count(self) -> AnswerCapsule:
        """Ensure the stated word_count matches the actual content word count."""
        actual = len(self.content.split())
        if actual != self.word_count:
            raise ValueError(
                f"Stated word_count ({self.word_count}) does not match actual "
                f"content word count ({actual}). They must agree."
            )
        return self


# ---------------------------------------------------------------------------
# FAQ Set
# ---------------------------------------------------------------------------
class FAQPair(BaseModel):
    """A single question-and-answer pair for FAQ markup."""

    question: str = Field(..., min_length=10, description="The FAQ question")
    answer: str = Field(..., min_length=20, description="The FAQ answer")


class FAQSet(BaseModel):
    """A complete FAQ set for a service/company page."""

    company_slug: str = Field(..., description="Company this FAQ set belongs to")
    service: str = Field(..., description="Service area the FAQs cover")
    pairs: List[FAQPair] = Field(
        ..., min_length=1, description="List of question-answer pairs"
    )
    page_url: str = Field(default="", description="Target page URL for this FAQ set")

    @field_validator("pairs")
    @classmethod
    def validate_pair_count(cls, v: List[FAQPair]) -> List[FAQPair]:
        """Warn if outside the recommended 8-12 range (but do not reject)."""
        # Validation is soft -- the generator aims for 8-12 but fewer is accepted
        return v


# ---------------------------------------------------------------------------
# Schema Markup
# ---------------------------------------------------------------------------
class SchemaMarkup(BaseModel):
    """A schema.org JSON-LD markup block."""

    schema_type: SchemaType = Field(..., description="The schema.org type")
    json_ld: Dict[str, Any] = Field(..., description="The complete JSON-LD object")
    company_slug: str = Field(default="", description="Company this schema targets")
    page_url: str = Field(default="", description="Target page URL")

    @field_validator("json_ld")
    @classmethod
    def validate_json_ld_structure(cls, v: Dict[str, Any]) -> Dict[str, Any]:
        """Ensure the JSON-LD has required top-level keys."""
        if "@context" not in v:
            raise ValueError("JSON-LD must include '@context' key")
        if "@type" not in v:
            raise ValueError("JSON-LD must include '@type' key")
        # Verify it is serializable
        try:
            json.dumps(v)
        except (TypeError, ValueError) as exc:
            raise ValueError(f"JSON-LD is not serializable: {exc}") from exc
        return v


# ---------------------------------------------------------------------------
# Citation Report
# ---------------------------------------------------------------------------
class CitationReport(BaseModel):
    """A single citation tracking entry for an AI platform."""

    query: str = Field(..., description="The query that was monitored")
    company_slug: str = Field(..., description="Company being tracked")
    platform: str = Field(
        default="general", description="AI platform (e.g. ChatGPT, Perplexity, Gemini)"
    )
    position: Optional[int] = Field(
        default=None,
        ge=1,
        description="Position in the AI response (1 = first mention)",
    )
    score: int = Field(
        default=0, ge=0, le=100, description="Visibility score 0-100"
    )
    trend: CitationTrend = Field(
        default=CitationTrend.STABLE, description="Trend direction"
    )
    snippet: str = Field(
        default="", description="Excerpt of the AI response mentioning the company"
    )
    checked_at: str = Field(
        default="", description="ISO timestamp of the check"
    )


# ---------------------------------------------------------------------------
# Optimization Score
# ---------------------------------------------------------------------------
class OptimizationIssue(BaseModel):
    """A single issue found during page optimization analysis."""

    category: str = Field(..., description="Issue category (e.g. heading_structure)")
    severity: str = Field(
        default="medium",
        description="Severity: low, medium, high, critical",
    )
    message: str = Field(..., description="Human-readable description of the issue")
    recommendation: str = Field(
        default="", description="Specific recommendation to fix this issue"
    )


class OptimizationScore(BaseModel):
    """AEO readiness score and analysis for a single page."""

    page_url: str = Field(..., description="URL of the analyzed page")
    score: int = Field(
        ..., ge=0, le=100, description="Overall AEO readiness score (0-100)"
    )
    breakdown: Dict[str, int] = Field(
        default_factory=dict,
        description="Per-category scores (heading_structure, capsule_presence, etc.)",
    )
    issues: List[OptimizationIssue] = Field(
        default_factory=list, description="List of issues found"
    )
    recommendations: List[str] = Field(
        default_factory=list, description="Prioritized list of recommendations"
    )
    company_slug: str = Field(default="", description="Company this page belongs to")

    @field_validator("score")
    @classmethod
    def validate_score_range(cls, v: int) -> int:
        if v < 0 or v > 100:
            raise ValueError(f"Score must be 0-100, got {v}")
        return v


# ---------------------------------------------------------------------------
# Batch Result Containers
# ---------------------------------------------------------------------------
class CapsuleBatch(BaseModel):
    """A batch of generated answer capsules."""

    company_slug: str
    capsules: List[AnswerCapsule] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class FAQBatch(BaseModel):
    """A batch of generated FAQ sets."""

    company_slug: str
    faq_sets: List[FAQSet] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class SchemaBatch(BaseModel):
    """A batch of generated schema markup blocks."""

    company_slug: str
    schemas: List[SchemaMarkup] = Field(default_factory=list)
    errors: List[str] = Field(default_factory=list)


class OptimizationBatch(BaseModel):
    """A batch of page optimization results."""

    pages: List[OptimizationScore] = Field(default_factory=list)
    average_score: float = Field(default=0.0)


class CitationBatch(BaseModel):
    """A batch of citation monitoring results."""

    company_slug: str
    reports: List[CitationReport] = Field(default_factory=list)
    average_score: float = Field(default=0.0)
