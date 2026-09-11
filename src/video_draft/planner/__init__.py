"""Scene planner and archetype decomposition strategies."""

from video_draft.planner.errors import (
    PlannerError,
    PlannerValidationError,
    UnsupportedArchetypeError,
)
from video_draft.planner.scene_planner import ScenePlanner, plan_scenes
from video_draft.planner.strategies import (
    BaseArchetypeStrategy,
    EducationStrategy,
    NewsStrategy,
    ProductStrategy,
    get_strategy,
    list_supported_archetypes,
    register_strategy,
)
from video_draft.schema.scene_plan import SceneBeat, ScenePlan

__all__ = [
    "ScenePlanner",
    "plan_scenes",
    "ScenePlan",
    "SceneBeat",
    "PlannerError",
    "PlannerValidationError",
    "UnsupportedArchetypeError",
    "BaseArchetypeStrategy",
    "EducationStrategy",
    "NewsStrategy",
    "ProductStrategy",
    "get_strategy",
    "register_strategy",
    "list_supported_archetypes",
]
