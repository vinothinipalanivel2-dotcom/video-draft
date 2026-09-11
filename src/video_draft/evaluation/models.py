"""Data schemas for quality evaluation, media validation, and cross-artifact consistency."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class CheckResult(BaseModel):
    """Result of a single evaluation check dimension."""
    dimension: str = Field(..., description="Name of the evaluated dimension")
    passed: bool = Field(..., description="Whether the check passed")
    score: float = Field(default=1.0, ge=0.0, le=1.0, description="Objective score [0.0, 1.0]")
    message: str = Field(default="", description="Summary of check evaluation")
    details: Dict[str, Any] = Field(default_factory=dict, description="Detailed metrics and telemetry")


class FinalMediaValidationResult(BaseModel):
    """Validation results for final assembled MP4 video file."""
    file_path: str
    file_exists: bool
    file_size_bytes: int = 0
    is_valid: bool = False
    duration_sec: float = 0.0
    duration_expected: float = 0.0
    duration_valid: bool = False
    width: Optional[int] = None
    height: Optional[int] = None
    resolution_valid: bool = False
    aspect_ratio: str = ""
    aspect_ratio_valid: bool = False
    fps: Optional[float] = None
    fps_valid: bool = False
    video_codec: Optional[str] = None
    codec_valid: bool = False
    has_audio: bool = False
    audio_valid: bool = False
    is_decodable: bool = False
    issues: List[str] = Field(default_factory=list)


class ConsistencyReport(BaseModel):
    """Cross-artifact pipeline consistency report."""
    is_consistent: bool = False
    scene_count_match: bool = False
    scene_ids_match: bool = False
    scene_ordering_valid: bool = False
    duration_alignment_valid: bool = False
    audio_alignment_valid: bool = False
    timeline_continuity_valid: bool = False
    aspect_ratio_consistent: bool = False
    provenance_consistent: bool = False
    issues: List[str] = Field(default_factory=list)
    details: Dict[str, Any] = Field(default_factory=dict)


class QualityEvaluationReport(BaseModel):
    """Complete objective quality and compliance evaluation report."""
    evaluation_id: str
    timestamp: str
    brief_id: str
    overall_passed: bool
    overall_score: float = Field(default=1.0, ge=0.0, le=1.0)
    checks: Dict[str, CheckResult] = Field(default_factory=dict)
    media_validation: Optional[FinalMediaValidationResult] = None
    consistency: Optional[ConsistencyReport] = None
    summary: str = ""
    reproducibility_verified: bool = False
    fallback_used: bool = False
    final_video_path: Optional[str] = None
    manifest_path: Optional[str] = None
