"""
Visual Asset Generator - Data Models
Pydantic models and enums for asset management.
"""

from datetime import datetime
from enum import Enum
from typing import Optional
from uuid import uuid4

from pydantic import BaseModel, Field


# ──────────────────────────────────────────────────────────────
# Enums
# ──────────────────────────────────────────────────────────────


class AssetType(str, Enum):
    """Types of visual assets that can be generated."""

    SOCIAL_POST = "social_post"
    COVER_PHOTO = "cover_photo"
    OG_IMAGE = "og_image"
    FLYER = "flyer"
    STAT_CARD = "stat_card"
    QUOTE_CARD = "quote_card"


class AssetStatus(str, Enum):
    """Lifecycle status of a generated asset."""

    GENERATED = "generated"
    APPROVED = "approved"
    REJECTED = "rejected"


# ──────────────────────────────────────────────────────────────
# Models
# ──────────────────────────────────────────────────────────────


class BrandPalette(BaseModel):
    """Brand color palette and typography for a company."""

    primary: str = Field(description="Primary brand color hex code")
    accent: str = Field(description="Accent brand color hex code")
    text_light: str = Field(default="#FFFFFF", description="Light text color")
    text_dark: str = Field(default="#1B2A4A", description="Dark text color")
    font_heading: str = Field(default="Playfair Display", description="Heading font family")
    font_body: str = Field(default="Inter", description="Body font family")


class PlatformSize(BaseModel):
    """Dimensions for a social media platform format."""

    name: str = Field(description="Human-readable platform name")
    width: int = Field(gt=0, description="Width in pixels")
    height: int = Field(gt=0, description="Height in pixels")

    @property
    def aspect_ratio(self) -> float:
        return self.width / self.height

    @property
    def dimensions_tuple(self) -> tuple[int, int]:
        return (self.width, self.height)


class Template(BaseModel):
    """Template definition for asset generation."""

    name: str = Field(description="Template display name")
    html_path: str = Field(description="Path to HTML template file relative to templates dir")
    variables: list[str] = Field(default_factory=list, description="Template variable names")
    description: Optional[str] = Field(default=None, description="Template description")


class Asset(BaseModel):
    """A generated visual asset with metadata."""

    id: str = Field(default_factory=lambda: uuid4().hex[:12], description="Unique asset ID")
    company: str = Field(description="Company key (e.g., 'us_framing')")
    type: AssetType = Field(description="Asset type classification")
    title: str = Field(description="Human-readable asset title")
    template: Optional[str] = Field(default=None, description="Template key used for generation")
    platform: Optional[str] = Field(default=None, description="Target platform key")
    width: int = Field(gt=0, description="Image width in pixels")
    height: int = Field(gt=0, description="Image height in pixels")
    status: AssetStatus = Field(default=AssetStatus.GENERATED, description="Asset lifecycle status")
    file_path: Optional[str] = Field(default=None, description="Path to generated image file")
    file_size_bytes: Optional[int] = Field(default=None, description="File size in bytes")
    created_at: datetime = Field(default_factory=datetime.now, description="Creation timestamp")
    tags: list[str] = Field(default_factory=list, description="Searchable tags")
    variables: Optional[dict[str, str]] = Field(
        default=None, description="Template variables used during generation"
    )

    @property
    def dimensions(self) -> str:
        return f"{self.width}x{self.height}"

    def to_summary(self) -> str:
        return (
            f"[{self.id}] {self.title} ({self.company}) "
            f"{self.dimensions} [{self.status.value}]"
        )
