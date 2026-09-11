"""Pydantic schemas for deterministic scene plans and scene beats."""

from typing import Any, Dict, List, Literal, Optional
from pydantic import BaseModel, Field, model_validator


class SceneBeat(BaseModel):
    """Represents a single planned scene beat within a draft video."""
    scene_id: str = Field(..., min_length=1, description="Deterministic scene identifier (e.g. 'scene_01')")
    scene_index: int = Field(..., ge=1, description="1-based sequential position of scene")
    title: str = Field(..., min_length=1, description="Conceptual beat title (e.g. 'Hook & Problem')")
    beat_type: str = Field(..., min_length=1, description="Archetype beat category (e.g. 'intro', 'core', 'cta')")
    narration_chunk: str = Field(..., min_length=1, description="Narration dialogue spoken during this scene")
    visual_prompt: str = Field(..., min_length=1, description="Engineered generative visual prompt")
    duration_sec: float = Field(..., ge=0.5, le=30.0, description="Duration of this scene in seconds")
    start_sec: float = Field(..., ge=0.0, description="Timestamp offset where scene begins")
    end_sec: float = Field(..., ge=0.5, description="Timestamp offset where scene ends")
    transition_in: str = Field(default="fade", description="Incoming transition effect")
    transition_out: str = Field(default="fade", description="Outgoing transition effect")
    overlay_text: Optional[str] = Field(default=None, description="Lower-third, ticker, or badge overlay text")
    camera_motion: str = Field(default="static", description="Camera motion guidance")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Strategy-specific attributes")

    @model_validator(mode="after")
    def validate_timings(self) -> "SceneBeat":
        if self.end_sec <= self.start_sec:
            raise ValueError(f"end_sec ({self.end_sec}) must be greater than start_sec ({self.start_sec})")
        computed_duration = round(self.end_sec - self.start_sec, 3)
        if abs(computed_duration - round(self.duration_sec, 3)) > 0.05:
            raise ValueError(
                f"duration_sec ({self.duration_sec}) does not match end_sec - start_sec ({computed_duration})"
            )
        return self


class ScenePlan(BaseModel):
    """Complete structured scene plan generated from a creative brief."""
    plan_id: str = Field(..., min_length=1, description="Deterministic plan identifier")
    brief_id: str = Field(..., min_length=1, description="Source creative brief identifier")
    genre: Literal["education", "news", "product"] = Field(..., description="Target archetype")
    aspect_ratio: Literal["16:9", "9:16"] = Field(..., description="Aspect ratio")
    target_duration_sec: float = Field(..., ge=15.0, le=30.0, description="Requested total duration")
    planned_duration_sec: float = Field(..., ge=14.5, le=30.5, description="Sum of planned scene durations")
    strategy_name: str = Field(..., min_length=1, description="Name of strategy class used")
    pacing_tempo: str = Field(..., description="Archetype pacing tempo (e.g. 'slow_didactic', 'fast_urgent')")
    caption_treatment: str = Field(..., description="Archetype subtitle/caption placement")
    visual_strategy: str = Field(..., description="Overarching visual composition approach")
    scenes: List[SceneBeat] = Field(..., min_length=1, description="Ordered list of scene beats")
    input_brief_hash: str = Field(..., min_length=8, description="SHA-256 hash of source creative brief")
    created_at: str = Field(..., description="ISO 8601 UTC timestamp")

    @model_validator(mode="after")
    def validate_scene_continuity(self) -> "ScenePlan":
        if not self.scenes:
            raise ValueError("ScenePlan must contain at least one scene beat.")

        # Validate strictly monotonically increasing indices and continuous timestamps
        expected_index = 1
        previous_end = 0.0

        for scene in self.scenes:
            if scene.scene_index != expected_index:
                raise ValueError(
                    f"Scene indices must be strictly sequential starting at 1. Expected {expected_index}, got {scene.scene_index}"
                )
            if abs(scene.start_sec - previous_end) > 0.05:
                raise ValueError(
                    f"Discontinuous scene timing at scene {scene.scene_index}: start_sec ({scene.start_sec}) != previous end_sec ({previous_end})"
                )
            previous_end = scene.end_sec
            expected_index += 1

        total_computed = sum(s.duration_sec for s in self.scenes)
        if abs(round(total_computed, 2) - round(self.planned_duration_sec, 2)) > 0.1:
            raise ValueError(
                f"planned_duration_sec ({self.planned_duration_sec}) does not match sum of scene durations ({total_computed})"
            )
        return self
