"""Creative brief and constraint schemas."""

from typing import Any, Dict, Literal, Optional
from pydantic import BaseModel, Field, field_validator


class SystemConstraints(BaseModel):
    """User-specified execution and budget constraints."""
    max_latency_sec: Optional[float] = Field(default=None, ge=1.0)
    max_vram_gb: Optional[float] = Field(default=0.0, ge=0.0)
    allow_cpu_fallback: bool = True
    quality_tier: Literal["draft", "preview", "production"] = "draft"


class CreativeBrief(BaseModel):
    """Schema for structured creative video brief."""
    id: str = Field(..., min_length=1, description="Unique identifier for the creative brief")
    title: str = Field(..., min_length=1, description="Human-readable title of the video draft")
    genre: Literal["education", "news", "product"] = Field(
        ..., description="Supported archetypes: education/explainer, news/commentary, product/social"
    )
    aspect_ratio: Literal["16:9", "9:16"] = Field(
        default="16:9", description="Target video orientation: 16:9 landscape or 9:16 vertical"
    )
    target_duration_sec: float = Field(
        ..., ge=15.0, le=30.0, description="Draft video duration between 15 and 30 seconds"
    )
    script: str = Field(
        ..., min_length=10, description="Full narration and dialogue script"
    )
    seed: int = Field(
        default=42, description="Deterministic pseudo-random generator seed"
    )
    constraints: SystemConstraints = Field(default_factory=SystemConstraints)
    metadata: Dict[str, Any] = Field(default_factory=dict)

    @field_validator("script")
    @classmethod
    def script_cannot_be_empty(cls, v: str) -> str:
        clean = v.strip()
        if len(clean) < 10:
            raise ValueError("Script must be at least 10 characters long.")
        return clean
