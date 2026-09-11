"""Unit tests for ScenePlanner and archetype strategies."""

import pytest
from pathlib import Path

from video_draft.planner import (
    EducationStrategy,
    NewsStrategy,
    PlannerValidationError,
    ProductStrategy,
    ScenePlanner,
    UnsupportedArchetypeError,
    get_strategy,
    list_supported_archetypes,
    plan_scenes,
)
from video_draft.schema.brief import CreativeBrief, SystemConstraints
from video_draft.schema.scene_plan import ScenePlan


@pytest.fixture
def edu_brief() -> CreativeBrief:
    return CreativeBrief(
        id="brief-edu-plan-01",
        title="Cellular Mitosis Explainer",
        genre="education",
        aspect_ratio="16:9",
        target_duration_sec=24.0,
        script=(
            "Mitosis is the process of cell division where a single cell divides into two identical daughter cells. "
            "First, DNA replicates during interphase. Next, chromosomes condense and align along the cell equator. "
            "Finally, sister chromatids separate into opposite poles and the cell divides."
        ),
        seed=42,
    )


@pytest.fixture
def news_brief() -> CreativeBrief:
    return CreativeBrief(
        id="brief-news-plan-02",
        title="Global Semiconductor Supply Update",
        genre="news",
        aspect_ratio="9:16",
        target_duration_sec=20.0,
        script=(
            "Major supply chain disruptions reported across global chip manufacturers today. "
            "New regulations take effect across European and Asian markets immediately. "
            "Automotive and consumer tech sectors expect production delays. "
            "Industry analysts urge diversification of fabrication hubs. "
            "Markets remain volatile as leaders convene emergency talks."
        ),
        seed=101,
    )


@pytest.fixture
def product_brief() -> CreativeBrief:
    return CreativeBrief(
        id="brief-prod-plan-03",
        title="Next-Gen Wireless Earbuds",
        genre="product",
        aspect_ratio="9:16",
        target_duration_sec=16.0,
        script=(
            "Meet SoundPulse, engineered with pure acoustic precision and active noise cancellation. "
            "Experience ultra-low latency spatial audio with 40-hour battery life. "
            "Designed for relentless all-weather endurance. "
            "Upgrade your sound today with exclusive pre-order pricing."
        ),
        seed=202,
    )


# -----------------------------------------------------------------------------
# 1. Scene Planner Basics & Schema Integrity
# -----------------------------------------------------------------------------

def test_basic_valid_planning(edu_brief: CreativeBrief):
    """Verify ScenePlanner transforms a valid brief into a fully compliant ScenePlan."""
    planner = ScenePlanner()
    plan = planner.plan(edu_brief)

    assert isinstance(plan, ScenePlan)
    assert plan.brief_id == edu_brief.id
    assert plan.genre == "education"
    assert plan.aspect_ratio == "16:9"
    assert plan.strategy_name == "EducationStrategy"
    assert len(plan.scenes) >= 3
    assert plan.planned_duration_sec == pytest.approx(edu_brief.target_duration_sec, abs=0.1)


def test_convenience_function_plan_scenes(edu_brief: CreativeBrief):
    """Verify plan_scenes helper produces identical output to ScenePlanner().plan()."""
    plan = plan_scenes(edu_brief)
    assert isinstance(plan, ScenePlan)
    assert plan.brief_id == edu_brief.id


def test_scene_ordering_and_continuity(news_brief: CreativeBrief):
    """Verify scenes have strictly sequential indices and continuous timestamps (no gaps or overlaps)."""
    plan = plan_scenes(news_brief)

    previous_end = 0.0
    for idx, scene in enumerate(plan.scenes, start=1):
        assert scene.scene_index == idx
        assert scene.scene_id == f"scene_{idx:02d}"
        assert scene.start_sec == pytest.approx(previous_end, abs=0.01)
        assert scene.end_sec > scene.start_sec
        assert scene.duration_sec == pytest.approx(scene.end_sec - scene.start_sec, abs=0.01)
        previous_end = scene.end_sec

    assert previous_end == pytest.approx(plan.planned_duration_sec, abs=0.01)


def test_deterministic_output(product_brief: CreativeBrief):
    """Verify running the planner multiple times with the same brief yields identical plans."""
    planner = ScenePlanner()
    plan1 = planner.plan(product_brief)
    plan2 = planner.plan(product_brief)

    assert plan1.plan_id == plan2.plan_id
    assert plan1.input_brief_hash == plan2.input_brief_hash
    assert plan1.planned_duration_sec == plan2.planned_duration_sec
    assert len(plan1.scenes) == len(plan2.scenes)
    for s1, s2 in zip(plan1.scenes, plan2.scenes):
        assert s1.scene_id == s2.scene_id
        assert s1.duration_sec == s2.duration_sec
        assert s1.visual_prompt == s2.visual_prompt
        assert s1.narration_chunk == s2.narration_chunk
        assert s1.overlay_text == s2.overlay_text


# -----------------------------------------------------------------------------
# 2. Archetype Strategy Specific Behavior
# -----------------------------------------------------------------------------

def test_education_strategy_behavior(edu_brief: CreativeBrief):
    """Verify education strategy creates didactic pacing and explanatory lower thirds."""
    plan = plan_scenes(edu_brief)
    assert plan.strategy_name == "EducationStrategy"
    assert plan.pacing_tempo == "slow_didactic"
    assert plan.caption_treatment == "explanatory_lower_third"
    assert plan.visual_strategy == "diagrammatic_didactic"
    # Pedagogical 4-beat structure
    assert len(plan.scenes) == 4
    for scene in plan.scenes:
        assert scene.overlay_text is not None
        assert any(tag in scene.overlay_text for tag in ["OVERVIEW", "KEY CONCEPT", "ANALYSIS", "SUMMARY"])
        assert scene.transition_in in ("fade", "dissolve")
        assert scene.transition_out in ("fade", "dissolve")


def test_news_strategy_behavior(news_brief: CreativeBrief):
    """Verify news strategy creates fast urgent pacing, hard cuts, and ticker metadata."""
    plan = plan_scenes(news_brief)
    assert plan.strategy_name == "NewsStrategy"
    assert plan.pacing_tempo == "fast_urgent"
    assert plan.caption_treatment == "urgent_bottom_ticker"
    assert plan.visual_strategy == "b_roll_and_broadcast"
    # High-tempo 5-beat rapid structure
    assert len(plan.scenes) == 5
    for scene in plan.scenes:
        assert scene.overlay_text is not None
        assert "***" in scene.overlay_text  # Ticker formatting
        assert scene.transition_in in ("cut", "fade")
        assert scene.transition_out in ("cut", "fade")


def test_product_strategy_behavior(product_brief: CreativeBrief):
    """Verify product strategy creates punchy commercial beats, hero framing, and kinetic callouts."""
    plan = plan_scenes(product_brief)
    assert plan.strategy_name == "ProductStrategy"
    assert plan.pacing_tempo == "dynamic_punchy"
    assert plan.caption_treatment == "kinetic_headline"
    assert plan.visual_strategy == "commercial_hero_framing"
    # Commercial 4-beat structure: Hook -> Feature -> Lifestyle -> CTA
    assert len(plan.scenes) == 4
    for scene in plan.scenes:
        assert scene.overlay_text is not None
        assert "//" in scene.overlay_text  # Kinetic callout formatting
        assert scene.camera_motion in ("dynamic_macro_zoom", "smooth_360_orbit", "sweeping_low_angle", "punchy_snap_zoom")


def test_strategy_factory():
    """Verify get_strategy factory returns correct strategy instances."""
    assert isinstance(get_strategy("education"), EducationStrategy)
    assert isinstance(get_strategy("news"), NewsStrategy)
    assert isinstance(get_strategy("product"), ProductStrategy)
    assert "education" in list_supported_archetypes()
    assert "news" in list_supported_archetypes()
    assert "product" in list_supported_archetypes()


def test_unsupported_archetype_raises():
    """Verify requesting an unsupported archetype raises UnsupportedArchetypeError."""
    with pytest.raises(UnsupportedArchetypeError, match="Unsupported archetype 'vlog'"):
        get_strategy("vlog")


# -----------------------------------------------------------------------------
# 3. Validation and Error Handling
# -----------------------------------------------------------------------------

def test_invalid_input_type_raises():
    """Verify non-CreativeBrief input raises PlannerValidationError."""
    planner = ScenePlanner()
    with pytest.raises(PlannerValidationError, match="Expected CreativeBrief instance"):
        planner.plan({"title": "not a brief"})  # type: ignore


def test_empty_script_raises(edu_brief: CreativeBrief):
    """Verify brief with empty script raises PlannerValidationError."""
    planner = ScenePlanner()
    edu_brief.script = "   "
    with pytest.raises(PlannerValidationError, match="script cannot be empty"):
        planner.plan(edu_brief)


def test_short_script_raises(edu_brief: CreativeBrief):
    """Verify brief with less than 10 characters raises PlannerValidationError."""
    planner = ScenePlanner()
    edu_brief.script = "Short"
    with pytest.raises(PlannerValidationError, match="at least 10 characters"):
        planner.plan(edu_brief)


def test_invalid_duration_boundary_raises(edu_brief: CreativeBrief):
    """Verify brief with out-of-bounds duration raises PlannerValidationError."""
    planner = ScenePlanner()
    edu_brief.target_duration_sec = 10.0  # < 15.0s
    with pytest.raises(PlannerValidationError, match="must be between 15.0 and 30.0"):
        planner.plan(edu_brief)


def test_invalid_aspect_ratio_raises(edu_brief: CreativeBrief):
    """Verify brief with unsupported aspect ratio raises PlannerValidationError."""
    planner = ScenePlanner()
    edu_brief.aspect_ratio = "4:3"  # type: ignore
    with pytest.raises(PlannerValidationError, match="aspect_ratio '4:3' is invalid"):
        planner.plan(edu_brief)


# -----------------------------------------------------------------------------
# 4. Integration with Phase 2 Routing
# -----------------------------------------------------------------------------

def test_integration_planner_with_router(edu_brief: CreativeBrief):
    """Verify ScenePlan feeds into Phase 2 route() seamlessly."""
    from video_draft.router.router import route
    from video_draft.schema.routing import RouteDecision

    plan = plan_scenes(edu_brief)
    decision = route(creative_brief=edu_brief, scene_plan=plan, force_cpu=True)

    assert isinstance(decision, RouteDecision)
    assert decision.selected_model == "cpu_procedural_engine"
    assert decision.is_cpu_fallback is True
    assert decision.brief_id == edu_brief.id
