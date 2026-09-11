"""Schema for route_decision.json recording model selection, candidates, and rationale."""

from typing import Any, Dict, List, Optional
from pydantic import BaseModel, Field, model_validator


class ModelScore(BaseModel):
    """Detailed score breakdown for a single evaluated model."""
    model_id: str
    model_name: str
    total_score: float
    aspect_ratio_match: float = 1.0
    vram_score: float = 1.0
    motion_score: float = 1.0
    license_score: float = 1.0
    latency_penalty: float = 0.0
    eligible: bool = True
    disqualification_reason: Optional[str] = None


class CandidateEvaluation(BaseModel):
    """Comprehensive evaluation record for each candidate model in the registry."""
    model_id: str
    model_name: str
    eligible: bool
    score: Optional[float] = None
    score_breakdown: Dict[str, float] = Field(default_factory=dict)
    rejection_reasons: List[str] = Field(default_factory=list)


class FallbackRoute(BaseModel):
    """Specification of the designated fallback route."""
    fallback_model: str
    fallback_model_name: str
    fallback_reason: str


class RouteDecision(BaseModel):
    """Complete, transparent route decision artifact for live inspection and logging."""
    route_id: str = Field(default="route-default", description="Unique deterministic route execution ID")
    brief_id: str = Field(default="brief-default", description="Target creative brief identifier")
    input_brief_hash: str = Field(default="hash-default", description="SHA-256 digest of input creative brief")
    timestamp: str = Field(default="", description="ISO 8601 UTC timestamp of decision")
    registry_version: str = Field(default="1.1.0", description="Version of capability registry used")
    routing_policy_version: str = Field(default="1.0.0", description="Version of routing policy used")

    selected_model: str = Field(..., description="ID of the chosen video generation model")
    selected_model_id: str = Field(default="", description="Alias for selected_model (compatibility)")
    selected_model_name: str = Field(..., description="Human-readable name of chosen model")
    selected_score: float = Field(..., description="Calculated selection score [0.0, 1.0]")
    is_cpu_fallback: bool = Field(default=False, description="Whether routed to CPU fallback engine")
    rationale: str = Field(..., description="Human-readable explanation of routing decision")
    target_hardware: str = Field(default="cpu", description="Hardware execution target: cpu or gpu")

    candidates: List[CandidateEvaluation] = Field(
        default_factory=list, description="Detailed evaluations of all candidates"
    )
    candidate_scores: Dict[str, float] = Field(
        default_factory=dict, description="Mapping of eligible model_id to normalized score"
    )
    hard_constraint_results: Dict[str, bool] = Field(
        default_factory=dict, description="Eligibility per candidate model"
    )
    rejection_reasons: Dict[str, List[str]] = Field(
        default_factory=dict, description="Specific hard rejection reasons per candidate"
    )

    fallback_model: str = Field(..., description="Designated fallback model ID")
    fallback_reason: str = Field(..., description="Rationale for designated fallback")
    fallback: Optional[FallbackRoute] = None
    fallback_chain: List[str] = Field(
        default_factory=list, description="Ordered candidate models for sequential fallback execution"
    )
    retry_policy: Dict[str, Any] = Field(
        default_factory=dict, description="Configured generation retry parameters"
    )
    scene_durations_evaluated: Optional[List[float]] = Field(
        default=None, description="Actual planned scene durations evaluated during routing"
    )

    routing_weights: Dict[str, float] = Field(
        default_factory=dict, description="Configured scoring weights applied"
    )
    system_capabilities: Dict[str, Any] = Field(
        default_factory=dict, description="Host environment hardware probe snapshot"
    )

    # Backwards compatibility fields
    scores: Dict[str, ModelScore] = Field(default_factory=dict)
    considered_models: List[str] = Field(default_factory=list)

    @model_validator(mode="after")
    def populate_compatibility_fields(self) -> "RouteDecision":
        if not self.selected_model_id:
            self.selected_model_id = self.selected_model
        if not self.considered_models:
            self.considered_models = [c.model_id for c in self.candidates]
        if not self.fallback:
            self.fallback = FallbackRoute(
                fallback_model=self.fallback_model,
                fallback_model_name=self.fallback_model,
                fallback_reason=self.fallback_reason,
            )
        return self
