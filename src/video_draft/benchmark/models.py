"""Pydantic models for pipeline benchmarking and synthetic load testing."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field


class StageTimings(BaseModel):
    """Wall-clock durations in seconds for distinct pipeline stages."""
    planning_sec: float = 0.0
    routing_sec: float = 0.0
    audio_sec: float = 0.0
    clip_generation_sec: float = 0.0
    clip_validation_sec: float = 0.0
    assembly_sec: float = 0.0
    evaluation_sec: float = 0.0
    total_wall_clock_sec: float = 0.0


class BenchmarkRunMetrics(BaseModel):
    """Metrics captured for a single pipeline benchmark run."""
    run_index: int
    brief_id: str
    archetype: str
    aspect_ratio: str
    target_duration_sec: float
    reproducibility_seed: int
    success: bool
    error: Optional[str] = None
    stage_timings: StageTimings
    num_scenes: int
    num_clips_generated: int
    selected_model: str
    fallback_used: bool
    fallback_model: Optional[str] = None
    output_duration_sec: float = 0.0
    output_resolution: str = "1280x720"
    quality_score: float = 0.0
    quality_passed: bool = False


class AggregateTimings(BaseModel):
    """Averaged timing metrics across benchmark iterations."""
    avg_planning_sec: float = 0.0
    avg_routing_sec: float = 0.0
    avg_audio_sec: float = 0.0
    avg_clip_generation_sec: float = 0.0
    avg_clip_validation_sec: float = 0.0
    avg_assembly_sec: float = 0.0
    avg_evaluation_sec: float = 0.0
    avg_total_wall_clock_sec: float = 0.0


class BenchmarkReport(BaseModel):
    """Complete benchmark execution report with deterministic vs timing data."""
    execution_id: str
    timestamp: str
    brief_id: Optional[str] = None
    synthetic_mode: bool = False
    runs_requested: int
    runs_completed: int
    runs_successful: int
    runs_failed: int
    archetypes_tested: List[str] = Field(default_factory=list)
    aspect_ratios_tested: List[str] = Field(default_factory=list)
    primary_model_usage_pct: float = 100.0
    fallback_usage_pct: float = 0.0
    average_quality_score: float = 0.0
    aggregate_timings: AggregateTimings
    system_info: Dict[str, Any] = Field(default_factory=dict)
    runs: List[BenchmarkRunMetrics] = Field(default_factory=list)
