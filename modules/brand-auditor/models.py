"""
Brand Consistency Auditor - Data Models
========================================
Pydantic models and enums for audit reports, inconsistencies,
platform listings, and remediation tasks.
"""

from __future__ import annotations

from enum import Enum
from typing import Dict, List, Optional

from pydantic import BaseModel, Field


# ---------------------------------------------------------------------------
# Enums
# ---------------------------------------------------------------------------

class Severity(str, Enum):
    """How urgent an inconsistency is."""
    critical = "critical"
    warning = "warning"
    info = "info"


class AuditCategory(str, Enum):
    """Top-level audit section."""
    nap = "nap"
    visual = "visual"
    voice = "voice"
    directory = "directory"


# ---------------------------------------------------------------------------
# Core Data Structures
# ---------------------------------------------------------------------------

class Inconsistency(BaseModel):
    """A single brand-standard deviation found during audit."""
    field: str = Field(..., description="Which data point diverges (e.g. 'phone', 'address', 'color')")
    expected: str = Field(..., description="The canonical / brand-standard value")
    found: str = Field(..., description="What was actually found")
    severity: Severity = Field(..., description="How serious the mismatch is")
    platform: str = Field("", description="Where the inconsistency was found (e.g. 'Google Business')")


class BrandCheck(BaseModel):
    """Result of a single audit check within a category."""
    category: AuditCategory
    score: float = Field(..., ge=0, le=100, description="Score 0-100 for this check")
    details: str = Field("", description="Human-readable explanation")
    inconsistencies: List[Inconsistency] = Field(default_factory=list)


class Platform(BaseModel):
    """A directory / platform listing status."""
    name: str
    url: str = ""
    has_listing: bool = False
    accuracy_score: Optional[float] = Field(None, ge=0, le=100)
    issues: List[Inconsistency] = Field(default_factory=list)


class RemediationTask(BaseModel):
    """An actionable fix task generated from audit findings."""
    priority: str = Field(..., pattern=r"^P[1-3]$", description="P1 (critical), P2 (important), P3 (minor)")
    effort_minutes: int = Field(..., ge=0, description="Estimated effort in minutes")
    description: str = Field(..., description="What needs to be fixed")
    steps: List[str] = Field(default_factory=list, description="Step-by-step instructions")
    company: str = Field("", description="Company slug this task applies to")
    category: AuditCategory = Field(AuditCategory.nap, description="Which audit category this relates to")
    platform: str = Field("", description="Platform/directory if applicable")


class AuditReport(BaseModel):
    """Complete brand consistency audit for one company."""
    company: str = Field(..., description="Company slug")
    company_name: str = Field("", description="Official company name")
    overall_score: float = Field(..., ge=0, le=100, description="Weighted overall score")
    sections: Dict[str, BrandCheck] = Field(default_factory=dict, description="Per-category results")
    issues: List[Inconsistency] = Field(default_factory=list, description="All inconsistencies found")
    recommendations: List[str] = Field(default_factory=list, description="Prioritised recommendations")
    platforms: List[Platform] = Field(default_factory=list, description="Directory listing statuses")
    remediation_tasks: List[RemediationTask] = Field(default_factory=list, description="Generated fix tasks")
    audit_timestamp: str = Field("", description="ISO-8601 timestamp of audit run")
