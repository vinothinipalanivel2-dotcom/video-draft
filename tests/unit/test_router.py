"""Comprehensive unit tests for the explainable capability routing engine."""

import copy
import pytest
from pathlib import Path

from video_draft.router.registry import ModelRegistry
from video_draft.router.router import load_routing_config, route
from video_draft.schema.brief import CreativeBrief, SystemConstraints
from video_draft.schema.routing import RouteDecision


@pytest.fixture
def base_education_brief() -> CreativeBrief:
    return CreativeBrief(
        id="brief-edu-001",
        title="Explaining Black Holes",
        genre="education",
        aspect_ratio="16:9",
        target_duration_sec=20.0,
        script="A black hole is a region of spacetime where gravity is so strong that nothing can escape.",
        seed=42,
        constraints=SystemConstraints(
            max_vram_gb=16.0,
            allow_cpu_fallback=True,
            quality_tier="draft",
        ),
    )


@pytest.fixture
def base_news_brief() -> CreativeBrief:
    return CreativeBrief(
        id="brief-news-002",
        title="Breaking Tech News",
        genre="news",
        aspect_ratio="9:16",
        target_duration_sec=18.0,
        script="Major breakthrough announced today in open-source artificial intelligence models.",
        seed=101,
        constraints=SystemConstraints(
            max_vram_gb=16.0,
            allow_cpu_fallback=True,
            quality_tier="draft",
        ),
    )


@pytest.fixture
def base_product_brief() -> CreativeBrief:
    return CreativeBrief(
        id="brief-prod-003",
        title="Smart Watch Launch",
        genre="product",
        aspect_ratio="9:16",
        target_duration_sec=25.0,
        script="Introducing the all new titanium smartwatch with seamless biometric tracking.",
        seed=202,
        constraints=SystemConstraints(
            max_vram_gb=16.0,
            allow_cpu_fallback=True,
            quality_tier="draft",
        ),
    )


@pytest.fixture
def gpu_capabilities() -> dict:
    return {
        "os": "Windows",
        "cpu_count": 8,
        "total_ram_gb": 32.0,
        "has_cuda": True,
        "free_accelerator_enabled": True,
        "vram_gb": 16.0,
    }


@pytest.fixture
def cpu_only_capabilities() -> dict:
    return {
        "os": "Windows",
        "cpu_count": 4,
        "total_ram_gb": 16.0,
        "has_cuda": False,
        "free_accelerator_enabled": False,
        "vram_gb": 0.0,
    }


# -----------------------------------------------------------------------------
# 1. Normal Routing Tests (Education, News, Product)
# -----------------------------------------------------------------------------

def test_normal_education_routing(base_education_brief: CreativeBrief, gpu_capabilities: dict):
    """Verify education brief routing selects top candidate with explainable rationale."""
    decision = route(base_education_brief, system_capabilities=gpu_capabilities, force_cpu=False)
    assert isinstance(decision, RouteDecision)
    assert decision.selected_model in ("cogvideox_2b", "wan2_1_t2v_1_3b")
    assert decision.selected_score > 0.70
    assert not decision.is_cpu_fallback
    assert "education" in decision.rationale.lower()
    assert decision.target_hardware == "accelerator"


def test_normal_news_routing(base_news_brief: CreativeBrief, gpu_capabilities: dict):
    """Verify news brief routing prioritizes fast latency and reliability."""
    decision = route(base_news_brief, system_capabilities=gpu_capabilities, force_cpu=False)
    assert isinstance(decision, RouteDecision)
    assert decision.selected_score > 0.70
    assert not decision.is_cpu_fallback
    assert "news" in decision.rationale.lower()


def test_normal_product_routing(base_product_brief: CreativeBrief, gpu_capabilities: dict):
    """Verify product social brief routing prioritizes visual quality and aspect ratio."""
    decision = route(base_product_brief, system_capabilities=gpu_capabilities, force_cpu=False)
    assert isinstance(decision, RouteDecision)
    assert decision.selected_score > 0.70
    assert not decision.is_cpu_fallback
    assert "product" in decision.rationale.lower()


# -----------------------------------------------------------------------------
# 2. Aspect Ratio Tests (16:9, 9:16, unsupported)
# -----------------------------------------------------------------------------

def test_aspect_ratio_16x9(base_education_brief: CreativeBrief, gpu_capabilities: dict):
    """Verify 16:9 aspect ratio is respected."""
    base_education_brief.aspect_ratio = "16:9"
    decision = route(base_education_brief, system_capabilities=gpu_capabilities, force_cpu=False)
    selected_cap = ModelRegistry.load_from_yaml().get_model(decision.selected_model)
    assert "16:9" in selected_cap.supported_aspect_ratios


def test_aspect_ratio_9x16(base_news_brief: CreativeBrief, gpu_capabilities: dict):
    """Verify 9:16 aspect ratio is respected."""
    base_news_brief.aspect_ratio = "9:16"
    decision = route(base_news_brief, system_capabilities=gpu_capabilities, force_cpu=False)
    selected_cap = ModelRegistry.load_from_yaml().get_model(decision.selected_model)
    assert "9:16" in selected_cap.supported_aspect_ratios


def test_unsupported_aspect_ratio(base_education_brief: CreativeBrief, gpu_capabilities: dict):
    """Verify candidate models that do not support a requested aspect ratio are eliminated."""
    registry = ModelRegistry.load_from_yaml()
    models_dict = {m.model_id: m for m in registry.list_models()}
    cog = models_dict["cogvideox_2b"]
    cog_limited = cog.model_copy(update={"supported_aspect_ratios": ["9:16"]})
    models_dict["cogvideox_2b"] = cog_limited
    custom_registry = ModelRegistry(models=models_dict)

    base_education_brief.aspect_ratio = "16:9"
    decision = route(base_education_brief, system_capabilities=gpu_capabilities, registry=custom_registry, force_cpu=False)
    assert decision.hard_constraint_results["cogvideox_2b"] is False
    assert any("Aspect ratio '16:9' not supported" in r for r in decision.rejection_reasons["cogvideox_2b"])


# -----------------------------------------------------------------------------
# 3. Hardware Tests (CPU-only, GPU available, Insufficient RAM)
# -----------------------------------------------------------------------------

def test_cpu_only_routing(base_education_brief: CreativeBrief, cpu_only_capabilities: dict):
    """Verify that under CPU-only capabilities, GPU models are eliminated and CPU fallback is selected."""
    decision = route(base_education_brief, system_capabilities=cpu_only_capabilities, force_cpu=True)
    assert decision.selected_model == "cpu_procedural_engine"
    assert decision.is_cpu_fallback is True
    assert decision.target_hardware == "cpu"
    # Verify all GPU models were rejected with hardware reason
    for c in decision.candidates:
        if c.model_id != "cpu_procedural_engine":
            assert not c.eligible
            assert any("GPU inference disabled" in r for r in c.rejection_reasons)


def test_insufficient_ram_rejection(base_education_brief: CreativeBrief, gpu_capabilities: dict):
    """Verify models requiring high RAM are disqualified when host RAM is insufficient."""
    low_ram_caps = copy.deepcopy(gpu_capabilities)
    low_ram_caps["total_ram_gb"] = 8.0  # Hunyuan and Wan requiring 16GB+ will fail

    decision = route(base_education_brief, system_capabilities=low_ram_caps, force_cpu=False)
    wan_rejections = decision.rejection_reasons.get("wan2_1_t2v_1_3b", [])
    assert any("Insufficient system RAM" in r for r in wan_rejections)


# -----------------------------------------------------------------------------
# 4. Latency Budget Tests
# -----------------------------------------------------------------------------

def test_latency_budget_constraint(base_education_brief: CreativeBrief, gpu_capabilities: dict):
    """Verify models exceeding brief's max_latency_sec are disqualified."""
    base_education_brief.constraints.max_latency_sec = 30.0  # Only models <= 30s latency eligible
    decision = route(base_education_brief, system_capabilities=gpu_capabilities, force_cpu=False)

    wan_rej = decision.rejection_reasons.get("wan2_1_t2v_1_3b", [])
    assert any("exceeds brief budget" in r for r in wan_rej)


# -----------------------------------------------------------------------------
# 5. Availability Tests
# -----------------------------------------------------------------------------

def test_model_unavailable_constraint(base_education_brief: CreativeBrief, gpu_capabilities: dict):
    """Verify models marked unavailable are eliminated by hard constraints."""
    registry = ModelRegistry.load_from_yaml()
    decision = route(base_education_brief, system_capabilities=gpu_capabilities, registry=registry, force_cpu=False)
    assert decision.hard_constraint_results["hunyuan_video"] is False
    assert any("marked unavailable" in r for r in decision.rejection_reasons["hunyuan_video"])


def test_multiple_models_unavailable(base_education_brief: CreativeBrief, gpu_capabilities: dict):
    """Verify routing handles multiple unavailable models and routes to remaining available model."""
    registry = ModelRegistry.load_from_yaml()
    models_dict = {}
    # Mark wan2_1 and cogvideox unavailable
    for m in registry.list_models():
        if m.model_id in ("wan2_1_t2v_1_3b", "cogvideox_2b"):
            models_dict[m.model_id] = m.model_copy(update={"availability": False})
        else:
            models_dict[m.model_id] = m
    custom_registry = ModelRegistry(models=models_dict)

    decision = route(base_education_brief, system_capabilities=gpu_capabilities, registry=custom_registry, force_cpu=False)
    # LTX or AnimateDiff should be selected instead
    assert decision.selected_model in ("ltx_video", "animatediff_v3")
    assert not decision.is_cpu_fallback


def test_all_video_models_unavailable_falls_back(base_education_brief: CreativeBrief, gpu_capabilities: dict):
    """Verify emergency CPU fallback is selected if all accelerator models are unavailable."""
    registry = ModelRegistry.load_from_yaml()
    models_dict = {}
    for m in registry.list_models():
        if m.model_id != "cpu_procedural_engine":
            models_dict[m.model_id] = m.model_copy(update={"availability": False})
        else:
            models_dict[m.model_id] = m
    custom_registry = ModelRegistry(models=models_dict)

    decision = route(base_education_brief, system_capabilities=gpu_capabilities, registry=custom_registry, force_cpu=False)
    assert decision.selected_model == "cpu_procedural_engine"
    assert decision.is_cpu_fallback is True


# -----------------------------------------------------------------------------
# 6. Fallback Hierarchy Tests
# -----------------------------------------------------------------------------

def test_preferred_rejected_secondary_selected(base_education_brief: CreativeBrief, gpu_capabilities: dict):
    """Verify when the preferred model is rejected by a constraint, the secondary candidate is selected."""
    # Run default baseline to see normal winner
    normal_decision = route(base_education_brief, system_capabilities=gpu_capabilities, force_cpu=False)
    preferred_model = normal_decision.selected_model

    # Now make the preferred model unavailable
    registry = ModelRegistry.load_from_yaml()
    models_dict = {m.model_id: m for m in registry.list_models()}
    models_dict[preferred_model] = models_dict[preferred_model].model_copy(update={"availability": False})
    custom_registry = ModelRegistry(models=models_dict)

    secondary_decision = route(
        base_education_brief,
        system_capabilities=gpu_capabilities,
        registry=custom_registry,
        force_cpu=False,
    )
    assert secondary_decision.selected_model != preferred_model
    assert not secondary_decision.is_cpu_fallback
    assert secondary_decision.hard_constraint_results[preferred_model] is False


def test_fallback_hierarchy_record(base_education_brief: CreativeBrief, gpu_capabilities: dict):
    """Verify fallback model and reason are explicitly recorded in RouteDecision."""
    decision = route(base_education_brief, system_capabilities=gpu_capabilities, force_cpu=False)
    assert decision.fallback_model == "cpu_procedural_engine"
    assert "fails or times out" in decision.fallback_reason
    assert decision.fallback is not None
    assert decision.fallback.fallback_model == "cpu_procedural_engine"


# -----------------------------------------------------------------------------
# 7. Explainability Tests
# -----------------------------------------------------------------------------

def test_explainability_complete(base_education_brief: CreativeBrief, gpu_capabilities: dict):
    """Verify every rejected candidate has explicit reasons and every eligible candidate has score breakdown."""
    decision = route(base_education_brief, system_capabilities=gpu_capabilities, force_cpu=False)

    for candidate in decision.candidates:
        if not candidate.eligible:
            assert len(candidate.rejection_reasons) > 0, f"Rejected model {candidate.model_id} has no rejection reason"
            assert candidate.score is None
        else:
            assert candidate.score is not None
            assert len(candidate.score_breakdown) >= 6
            assert "quality" in candidate.score_breakdown
            assert "use_case_fit" in candidate.score_breakdown
            assert "controllability" in candidate.score_breakdown


# -----------------------------------------------------------------------------
# 8. Determinism Tests
# -----------------------------------------------------------------------------

def test_routing_determinism(base_education_brief: CreativeBrief, gpu_capabilities: dict):
    """Verify running route twice with identical inputs yields identical scores and selection."""
    decision1 = route(base_education_brief, system_capabilities=gpu_capabilities, force_cpu=False)
    decision2 = route(base_education_brief, system_capabilities=gpu_capabilities, force_cpu=False)

    assert decision1.selected_model == decision2.selected_model
    assert decision1.selected_score == decision2.selected_score
    assert decision1.candidate_scores == decision2.candidate_scores
    assert decision1.input_brief_hash == decision2.input_brief_hash


# -----------------------------------------------------------------------------
# 9. Configuration Tuning Tests
# -----------------------------------------------------------------------------

def test_configuration_weight_change_affects_scoring(base_news_brief: CreativeBrief, gpu_capabilities: dict):
    """Verify modifying routing weights in configuration modifies scoring outcomes."""
    config_default = load_routing_config()
    decision_default = route(
        base_news_brief,
        system_capabilities=gpu_capabilities,
        routing_config=config_default,
        force_cpu=False,
    )

    # Modify weights to heavily penalize latency (favoring ultra-fast model AnimateDiff)
    config_skewed = copy.deepcopy(config_default)
    config_skewed["weights"]["use_cases"]["news"] = {
        "latency": 0.80,
        "reliability": 0.10,
        "quality": 0.05,
        "controllability": 0.05,
    }

    decision_skewed = route(
        base_news_brief,
        system_capabilities=gpu_capabilities,
        routing_config=config_skewed,
        force_cpu=False,
    )

    # Scores should differ under different weight configurations
    assert decision_default.candidate_scores != decision_skewed.candidate_scores
