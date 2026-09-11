"""Reliable generation orchestrator with deterministic fallback chains and retry policies."""

import time
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
from pydantic import BaseModel, Field

from video_draft.adapters.base import (
    BaseClipGenerator,
    ClipArtifact,
    ClipGenerationError,
    ProviderUnavailableError,
)
from video_draft.adapters.factory import get_clip_generator
from video_draft.adapters.validator import ClipValidationError, ClipValidator
from video_draft.schema.routing import RouteDecision
from video_draft.schema.scene_plan import SceneBeat


class GenerationReliabilityError(Exception):
    """Raised when all candidates in the routing fallback chain fail generation or validation."""
    def __init__(self, message: str, scene_id: Optional[str] = None, attempts: Optional[List[Any]] = None) -> None:
        super().__init__(message)
        self.scene_id = scene_id
        self.attempts = attempts or []


class RetryPolicy(BaseModel):
    """Configuration for controlled generation retries."""
    max_retries: int = Field(default=2, ge=0, le=5, description="Maximum retry attempts per candidate model")
    backoff_sec: float = Field(default=0.05, ge=0.0, description="Delay between retries in seconds")
    enable_fallback_chain: bool = Field(default=True, description="Whether to proceed to next fallback model")

    def is_retryable(self, error: Exception) -> bool:
        """Determine whether an error is transient/retryable or permanent."""
        if isinstance(error, ClipGenerationError):
            return getattr(error, "is_retryable", True)
        if isinstance(error, ClipValidationError):
            # Missing or empty files might be transient renderer race conditions
            if getattr(error, "field", None) in ("file_existence", "file_size"):
                return True
            # Structural/algorithmic mismatches (scene_id, duration, aspect_ratio) are non-retryable
            return False
        # Generic exceptions default to retryable once
        return True


class GenerationAttempt(BaseModel):
    """Record of a single clip synthesis attempt."""
    scene_id: str
    model_id: str
    attempt_number: int
    success: bool
    error_message: Optional[str] = None
    is_fallback: bool = False


class GenerationReport(BaseModel):
    """Comprehensive observability report for a generated scene clip."""
    scene_id: str
    requested_model: str
    final_model: str
    fallback_occurred: bool
    fallback_reason: Optional[str] = None
    attempts: List[GenerationAttempt] = Field(default_factory=list)
    total_retries: int = 0
    clip_artifact: Optional[ClipArtifact] = None


class ReliableClipGenerator:
    """Orchestrates video clip generation with explainable fallback chains and bounded retries."""

    def __init__(
        self,
        decision: RouteDecision,
        retry_policy: Optional[RetryPolicy] = None,
        validator: Optional[ClipValidator] = None,
        mock: bool = False,
        allow_cpu_fallback: bool = True,
        override_generator: Optional[BaseClipGenerator] = None,
    ) -> None:
        self.decision = decision
        self.retry_policy = retry_policy or RetryPolicy()
        self.validator = validator or ClipValidator(probe_media_streams=False)
        self.mock = mock
        self.allow_cpu_fallback = allow_cpu_fallback
        self.override_generator = override_generator

    def _build_candidate_chain(self) -> List[str]:
        """Construct the ordered list of candidate models from RouteDecision."""
        chain: List[str] = [self.decision.selected_model]

        if not self.retry_policy.enable_fallback_chain:
            return chain

        if self.decision.fallback_chain:
            for alt_model in self.decision.fallback_chain:
                if alt_model not in chain:
                    chain.append(alt_model)

        # Guarantee CPU procedural fallback is included if allowed
        fallback_target = self.decision.fallback_model or "cpu_procedural_engine"
        if self.allow_cpu_fallback and fallback_target not in chain:
            chain.append(fallback_target)

        return chain

    def generate_clip_with_fallback(
        self,
        beat: SceneBeat,
        aspect_ratio: str,
        output_dir: Path,
    ) -> Tuple[ClipArtifact, GenerationReport]:
        """Execute clip generation along the fallback chain with bounded retries.

        Args:
            beat: The planned scene beat.
            aspect_ratio: Target aspect ratio ("16:9" or "9:16").
            output_dir: Destination folder for rendered clip.

        Returns:
            Tuple of (validated ClipArtifact, GenerationReport).

        Raises:
            GenerationReliabilityError: If all candidate models in the fallback chain fail.
        """
        chain = self._build_candidate_chain()
        attempts: List[GenerationAttempt] = []
        total_retries = 0
        preferred_model = self.decision.selected_model
        fallback_reason: Optional[str] = None

        for candidate_idx, candidate_model in enumerate(chain):
            is_fallback = (candidate_model != preferred_model)
            attempts_for_candidate = 0

            while attempts_for_candidate <= self.retry_policy.max_retries:
                attempt_num = attempts_for_candidate + 1
                try:
                    if self.override_generator is not None:
                        generator = self.override_generator
                    else:
                        generator = get_clip_generator(
                            model_id=candidate_model,
                            mock=self.mock,
                            allow_cpu_fallback=self.allow_cpu_fallback,
                        )

                    # 1. Synthesize clip
                    clip = generator.generate_clip(
                        beat=beat,
                        model_id=candidate_model,
                        aspect_ratio=aspect_ratio,
                        output_dir=output_dir,
                    )

                    # 2. Validate clip
                    self.validator.validate_clip(clip, beat, aspect_ratio)

                    # Successful generation!
                    record = GenerationAttempt(
                        scene_id=beat.scene_id,
                        model_id=candidate_model,
                        attempt_number=attempt_num,
                        success=True,
                        is_fallback=is_fallback,
                    )
                    attempts.append(record)

                    # Augment clip metadata with observability telemetry
                    clip.metadata["fallback_occurred"] = is_fallback
                    clip.metadata["final_model"] = candidate_model
                    clip.metadata["total_attempts"] = len(attempts)
                    clip.metadata["candidate_chain"] = chain
                    if is_fallback:
                        clip.metadata["fallback_reason"] = fallback_reason or f"Fell back from '{preferred_model}' to '{candidate_model}'"

                    report = GenerationReport(
                        scene_id=beat.scene_id,
                        requested_model=preferred_model,
                        final_model=candidate_model,
                        fallback_occurred=is_fallback,
                        fallback_reason=fallback_reason,
                        attempts=attempts,
                        total_retries=total_retries,
                        clip_artifact=clip,
                    )
                    return clip, report

                except Exception as err:
                    err_msg = str(err)
                    record = GenerationAttempt(
                        scene_id=beat.scene_id,
                        model_id=candidate_model,
                        attempt_number=attempt_num,
                        success=False,
                        error_message=err_msg,
                        is_fallback=is_fallback,
                    )
                    attempts.append(record)

                    # Check retry policy
                    if not self.retry_policy.is_retryable(err):
                        fallback_reason = f"Non-retryable failure on model '{candidate_model}': {err_msg}"
                        break  # Immediately proceed to next fallback candidate

                    if attempts_for_candidate >= self.retry_policy.max_retries:
                        fallback_reason = (
                            f"Model '{candidate_model}' exhausted {self.retry_policy.max_retries} retries: {err_msg}"
                        )
                        break  # Proceed to next fallback candidate

                    # Retryable error with remaining attempts
                    total_retries += 1
                    attempts_for_candidate += 1
                    if self.retry_policy.backoff_sec > 0:
                        time.sleep(self.retry_policy.backoff_sec)

        # If all candidates in chain failed
        failure_summary = "; ".join(
            f"[model: {a.model_id}, attempt: {a.attempt_number}] {a.error_message}"
            for a in attempts if not a.success
        )
        raise GenerationReliabilityError(
            f"All {len(chain)} candidate models in fallback chain ({' -> '.join(chain)}) failed for scene '{beat.scene_id}'.\n"
            f"Failure details:\n{failure_summary}",
            scene_id=beat.scene_id,
            attempts=attempts,
        )
