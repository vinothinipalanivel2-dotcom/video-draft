"""Deterministic Scene Planner orchestrating archetype strategies."""

import hashlib
from typing import Any, Dict, Optional

from video_draft.planner.errors import PlannerValidationError, UnsupportedArchetypeError
from video_draft.planner.strategies import get_strategy
from video_draft.schema.brief import CreativeBrief
from video_draft.schema.scene_plan import ScenePlan


def _hash_brief_content(brief: CreativeBrief) -> str:
    """Computes deterministic SHA-256 digest of relevant brief contents."""
    payload = brief.model_dump_json(exclude={"metadata"})
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


class ScenePlanner:
    """
    Transforms structured creative briefs into deterministic scene plans.
    Delegates archetype-specific pacing, prompt composition, and visual framing
    to modular archetype strategies without embedding model-specific logic.
    """

    def plan(self, brief: CreativeBrief) -> ScenePlan:
        """
        Plans scene breakdown from a validated CreativeBrief.
        Raises PlannerValidationError if brief is missing critical fields or constraints.
        Raises UnsupportedArchetypeError if brief genre is not registered.
        """
        # Input validation
        if not isinstance(brief, CreativeBrief):
            raise PlannerValidationError(f"Expected CreativeBrief instance, got {type(brief).__name__}")

        if not brief.script or not brief.script.strip():
            raise PlannerValidationError("Creative brief script cannot be empty.")

        if len(brief.script.strip()) < 10:
            raise PlannerValidationError("Script must contain at least 10 characters.")

        if brief.target_duration_sec < 15.0 or brief.target_duration_sec > 30.0:
            raise PlannerValidationError(
                f"target_duration_sec ({brief.target_duration_sec}) must be between 15.0 and 30.0 seconds."
            )

        if brief.aspect_ratio not in ("16:9", "9:16"):
            raise PlannerValidationError(
                f"aspect_ratio '{brief.aspect_ratio}' is invalid. Supported: '16:9', '9:16'."
            )

        # Select archetype strategy
        try:
            strategy = get_strategy(brief.genre)
        except UnsupportedArchetypeError:
            raise

        # Generate deterministic brief hash
        brief_hash = _hash_brief_content(brief)

        # Execute strategy
        try:
            plan = strategy.plan(brief, brief_hash)
        except Exception as err:
            raise PlannerValidationError(f"Strategy '{strategy.strategy_name}' failed to generate plan: {err}") from err

        return plan


def plan_scenes(brief: CreativeBrief) -> ScenePlan:
    """Convenience functional interface for scene planning."""
    planner = ScenePlanner()
    return planner.plan(brief)
