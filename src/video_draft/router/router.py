"""Explainable model routing engine for draft video generation."""

import hashlib
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple
import yaml

from video_draft.router.registry import ModelCapability, ModelRegistry
from video_draft.schema.brief import CreativeBrief
from video_draft.schema.routing import CandidateEvaluation, FallbackRoute, ModelScore, RouteDecision
from video_draft.utils.system_info import get_system_hardware_info


def _hash_brief(brief: CreativeBrief) -> str:
    """Computes deterministic SHA-256 hash of the creative brief payload."""
    serialized = brief.model_dump_json(exclude={"metadata"})
    return hashlib.sha256(serialized.encode("utf-8")).hexdigest()


def load_routing_config(config_path: Optional[str | Path] = None) -> Dict[str, Any]:
    """Loads routing policy and weights configuration from YAML file."""
    if config_path is None:
        candidates = [
            Path("configs/routing_rules.yaml"),
            Path.cwd() / "configs" / "routing_rules.yaml",
            Path(__file__).resolve().parent.parent.parent / "configs" / "routing_rules.yaml",
        ]
        for c in candidates:
            if c.is_file():
                config_path = c
                break

    if config_path and Path(config_path).is_file():
        try:
            content = Path(config_path).read_text(encoding="utf-8")
            return yaml.safe_load(content) or {}
        except Exception:
            pass

    # Safe built-in fallback configuration if file is missing
    return {
        "version": "1.0.0",
        "weights": {
            "default": {
                "quality": 0.25,
                "use_case_fit": 0.20,
                "controllability": 0.15,
                "hardware_fit": 0.10,
                "latency": 0.10,
                "reliability": 0.10,
                "aspect_ratio_fit": 0.05,
                "duration_fit": 0.05,
            },
            "use_cases": {
                "education": {
                    "controllability": 0.25,
                    "use_case_fit": 0.20,
                    "reliability": 0.15,
                    "quality": 0.15,
                    "aspect_ratio_fit": 0.10,
                    "duration_fit": 0.05,
                    "hardware_fit": 0.05,
                    "latency": 0.05,
                },
                "news": {
                    "latency": 0.25,
                    "reliability": 0.20,
                    "use_case_fit": 0.20,
                    "quality": 0.10,
                    "controllability": 0.10,
                    "duration_fit": 0.05,
                    "hardware_fit": 0.05,
                    "aspect_ratio_fit": 0.05,
                },
                "product": {
                    "quality": 0.30,
                    "use_case_fit": 0.20,
                    "aspect_ratio_fit": 0.15,
                    "controllability": 0.15,
                    "reliability": 0.10,
                    "duration_fit": 0.05,
                    "hardware_fit": 0.03,
                    "latency": 0.02,
                },
            },
        },
        "fallback": {
            "default_fallback_model": "cpu_procedural_engine",
        },
    }


def evaluate_hard_constraints(
    model: ModelCapability,
    brief: CreativeBrief,
    system_caps: Dict[str, Any],
    routing_config: Dict[str, Any],
    force_cpu: bool,
    scene_plan: Optional[Any] = None,
) -> List[str]:
    """
    Evaluates hard elimination rules for a candidate model.
    Returns a list of rejection reasons. If empty, the model is eligible.
    """
    reasons: List[str] = []

    # 1. Model Availability Check
    if not model.availability:
        reasons.append(f"Model '{model.model_id}' is marked unavailable in target environment.")

    # 2. Aspect Ratio Compatibility
    target_ar = getattr(scene_plan, "aspect_ratio", None) or brief.aspect_ratio
    if target_ar not in model.supported_aspect_ratios:
        reasons.append(
            f"Aspect ratio '{target_ar}' not supported. "
            f"Supported: {model.supported_aspect_ratios}"
        )

    # 3. CPU-Only / Force-CPU Constraint
    if force_cpu and model.hardware_requirements.requires_gpu:
        reasons.append("GPU inference disabled (force_cpu=True or CPU-only target).")

    # 4. Hardware RAM Capacity Check
    host_ram = system_caps.get("total_ram_gb")
    if isinstance(host_ram, (int, float)) and host_ram < model.hardware_requirements.min_ram_gb:
        reasons.append(
            f"Insufficient system RAM: model requires {model.hardware_requirements.min_ram_gb} GB, "
            f"host has {host_ram} GB."
        )

    # 5. Hardware VRAM Capacity Check (if GPU execution is active)
    if not force_cpu and model.hardware_requirements.requires_gpu:
        has_cuda = system_caps.get("has_cuda", False)
        # If host has no CUDA and no external accelerator specified
        if not has_cuda and not system_caps.get("free_accelerator_enabled", False):
            reasons.append("No CUDA-capable accelerator detected on host system.")

        host_vram = system_caps.get("vram_gb")
        if isinstance(host_vram, (int, float)) and host_vram < model.hardware_requirements.min_vram_gb:
            reasons.append(
                f"Insufficient GPU VRAM: requires {model.hardware_requirements.min_vram_gb} GB, "
                f"host has {host_vram} GB."
            )

    # 6. Commercial Use License Check (if required by brief or config)
    require_commercial = (
        routing_config.get("hard_constraints", {}).get("require_commercial_use", False)
        or brief.constraints.quality_tier == "production"
    )
    if require_commercial and not model.commercial_use:
        reasons.append(f"Commercial use prohibited by license '{model.license}'.")

    # 7. Latency Budget Constraint
    if brief.constraints.max_latency_sec is not None:
        if model.expected_latency > brief.constraints.max_latency_sec:
            reasons.append(
                f"Expected latency ({model.expected_latency}s) exceeds brief budget "
                f"({brief.constraints.max_latency_sec}s)."
            )

    # 8. Scene-Aware Duration Constraint (when ScenePlan is provided)
    if scene_plan and hasattr(scene_plan, "scenes") and scene_plan.scenes:
        max_scene_dur = max(s.duration_sec for s in scene_plan.scenes)
        min_scene_dur = min(s.duration_sec for s in scene_plan.scenes)
        if max_scene_dur > model.supported_durations.max_sec:
            reasons.append(
                f"Longest planned scene ({max_scene_dur:.1f}s) exceeds model max duration "
                f"({model.supported_durations.max_sec:.1f}s)."
            )
        if min_scene_dur < model.supported_durations.min_sec:
            reasons.append(
                f"Shortest planned scene ({min_scene_dur:.1f}s) is below model min duration "
                f"({model.supported_durations.min_sec:.1f}s)."
            )

    return reasons


def compute_candidate_score(
    model: ModelCapability,
    brief: CreativeBrief,
    system_caps: Dict[str, Any],
    weights: Dict[str, float],
    scene_plan: Optional[Any] = None,
) -> Tuple[float, Dict[str, float]]:
    """
    Computes explainable multi-attribute normalized score [0.0, 1.0] for an eligible model.
    Returns (total_score, score_breakdown).
    """
    # 1. Quality score [0.0, 1.0]
    quality_score = (model.controllability * 0.5) + (model.reliability * 0.5)

    # 2. Use-case fit [0.0, 1.0]
    use_case_fit = model.use_case_fit.get(brief.genre, 0.5)

    # 3. Controllability [0.0, 1.0]
    controllability_score = model.controllability

    # 4. Hardware fit score [0.0, 1.0]
    if model.hardware_requirements.requires_gpu:
        vram_ratio = min(1.0, 16.0 / max(model.hardware_requirements.min_vram_gb, 1.0))
        hardware_fit_score = 0.5 + 0.5 * vram_ratio
    else:
        hardware_fit_score = 0.95

    # 5. Latency score [0.0, 1.0]
    latency_score = max(0.0, 1.0 - (model.expected_latency / 160.0))

    # 6. Reliability score [0.0, 1.0]
    reliability_score = model.reliability

    # 7. Aspect ratio fit [0.0, 1.0]
    target_ar = getattr(scene_plan, "aspect_ratio", None) or brief.aspect_ratio
    aspect_ratio_fit_score = 1.0 if target_ar in model.supported_aspect_ratios else 0.5

    # 8. Duration fit [0.0, 1.0]
    if scene_plan and hasattr(scene_plan, "scenes") and scene_plan.scenes:
        fits = all(
            model.supported_durations.min_sec <= s.duration_sec <= model.supported_durations.max_sec
            for s in scene_plan.scenes
        )
        duration_fit_score = 1.0 if fits else 0.4
    else:
        target_scene_dur = min(5.0, brief.target_duration_sec / 4.0)
        if model.supported_durations.min_sec <= target_scene_dur <= model.supported_durations.max_sec:
            duration_fit_score = 1.0
        else:
            duration_fit_score = 0.7

    breakdown = {
        "quality": round(quality_score, 4),
        "use_case_fit": round(use_case_fit, 4),
        "controllability": round(controllability_score, 4),
        "hardware_fit": round(hardware_fit_score, 4),
        "latency": round(latency_score, 4),
        "reliability": round(reliability_score, 4),
        "aspect_ratio_fit": round(aspect_ratio_fit_score, 4),
        "duration_fit": round(duration_fit_score, 4),
    }

    # Normalize weights
    total_weight = sum(weights.values()) or 1.0
    normalized_weights = {k: v / total_weight for k, v in weights.items()}

    total_score = sum(breakdown.get(k, 0.0) * normalized_weights.get(k, 0.0) for k in normalized_weights)
    return round(total_score, 4), breakdown


def route(
    creative_brief: CreativeBrief,
    scene_plan: Optional[Any] = None,
    system_capabilities: Optional[Dict[str, Any]] = None,
    routing_config: Optional[Dict[str, Any]] = None,
    registry: Optional[ModelRegistry] = None,
    force_cpu: Optional[bool] = None,
) -> RouteDecision:
    """
    Evaluates model capabilities against brief constraints, scene plan timing, and hardware profile.
    Constructs a deterministic, explainable RouteDecision with ranked candidate fallback chain.
    """
    # 1. Initialize registry & configuration
    if registry is None:
        registry = ModelRegistry.load_from_yaml()

    if routing_config is None:
        routing_config = load_routing_config()

    if system_capabilities is None:
        system_capabilities = get_system_hardware_info()

    # Determine force_cpu policy
    if force_cpu is None:
        force_cpu = (
            creative_brief.constraints.max_vram_gb == 0.0
            or not system_capabilities.get("has_cuda", False)
            and not system_capabilities.get("free_accelerator_enabled", False)
        )

    # 2. Select use-case-specific scoring weights
    weights_section = routing_config.get("weights", {})
    genre_weights = weights_section.get("use_cases", {}).get(
        creative_brief.genre, weights_section.get("default", {})
    )

    candidates: List[CandidateEvaluation] = []
    eligible_candidates: List[Tuple[ModelCapability, float, Dict[str, float]]] = []
    rejection_reasons_map: Dict[str, List[str]] = {}
    hard_results_map: Dict[str, bool] = {}
    scores_map: Dict[str, float] = {}
    legacy_model_scores: Dict[str, ModelScore] = {}

    # 3. Evaluate each model in the registry
    for model in registry.list_models():
        rejections = evaluate_hard_constraints(
            model=model,
            brief=creative_brief,
            system_caps=system_capabilities,
            routing_config=routing_config,
            force_cpu=force_cpu,
            scene_plan=scene_plan,
        )

        if rejections:
            hard_results_map[model.model_id] = False
            rejection_reasons_map[model.model_id] = rejections
            candidates.append(
                CandidateEvaluation(
                    model_id=model.model_id,
                    model_name=model.model_name,
                    eligible=False,
                    score=None,
                    score_breakdown={},
                    rejection_reasons=rejections,
                )
            )
            legacy_model_scores[model.model_id] = ModelScore(
                model_id=model.model_id,
                model_name=model.model_name,
                total_score=0.0,
                eligible=False,
                disqualification_reason="; ".join(rejections),
            )
        else:
            hard_results_map[model.model_id] = True
            rejection_reasons_map[model.model_id] = []
            score, breakdown = compute_candidate_score(
                model=model,
                brief=creative_brief,
                system_caps=system_capabilities,
                weights=genre_weights,
                scene_plan=scene_plan,
            )
            scores_map[model.model_id] = score
            eligible_candidates.append((model, score, breakdown))

            candidates.append(
                CandidateEvaluation(
                    model_id=model.model_id,
                    model_name=model.model_name,
                    eligible=True,
                    score=score,
                    score_breakdown=breakdown,
                    rejection_reasons=[],
                )
            )
            legacy_model_scores[model.model_id] = ModelScore(
                model_id=model.model_id,
                model_name=model.model_name,
                total_score=score,
                aspect_ratio_match=breakdown.get("aspect_ratio_fit", 1.0),
                vram_score=breakdown.get("hardware_fit", 1.0),
                motion_score=breakdown.get("quality", 1.0),
                license_score=1.0,
                latency_penalty=round(1.0 - breakdown.get("latency", 1.0), 4),
                eligible=True,
            )

    # 4. Fallback determination
    fallback_model_id = routing_config.get("fallback", {}).get(
        "default_fallback_model", "cpu_procedural_engine"
    )
    fallback_capability = (
        registry.get_model(fallback_model_id) if registry.has_model(fallback_model_id) else None
    )
    fallback_name = fallback_capability.model_name if fallback_capability else fallback_model_id

    fallback_cfg = routing_config.get("fallback", {})
    retry_policy_dict = {
        "max_retries": fallback_cfg.get("max_retries", 2),
        "backoff_sec": fallback_cfg.get("retry_backoff_sec", 0.05),
        "enable_fallback_chain": fallback_cfg.get("enable_fallback_chain", True),
    }

    scene_durations_evaluated = (
        [round(s.duration_sec, 2) for s in scene_plan.scenes]
        if (scene_plan and hasattr(scene_plan, "scenes") and scene_plan.scenes)
        else None
    )

    # 5. Selection logic and deterministic fallback chain construction
    generative_candidates = [
        c for c in eligible_candidates if c[0].model_id != fallback_model_id
    ]

    if generative_candidates and not force_cpu:
        # Deterministic sorting: sort primarily by score descending, then tie-break on model_id ascending
        generative_candidates.sort(key=lambda x: (-x[1], x[0].model_id))
        winner_model, winner_score, winner_breakdown = generative_candidates[0]
        is_cpu_fallback = False

        # Build fallback chain: remaining generative models + CPU procedural fallback
        fallback_chain = [c[0].model_id for c in generative_candidates[1:]] + [fallback_model_id]

        alt_text = ""
        if len(generative_candidates) > 1:
            runner_up = generative_candidates[1][0]
            alt_text = f" Runner-up: '{runner_up.model_name}' (Score: {generative_candidates[1][1]})."
        rationale = (
            f"Selected '{winner_model.model_name}' with top composite score of {winner_score} "
            f"optimized for '{creative_brief.genre}' archetype.{alt_text}"
        )
        fallback_reason = (
            f"If '{winner_model.model_name}' fails or times out during inference, "
            f"execution falls back along chain: {' -> '.join(fallback_chain)}."
        )
    else:
        # Either force_cpu=True or no generative models eligible -> CPU procedural fallback
        if fallback_capability:
            winner_model = fallback_capability
            winner_score = scores_map.get(fallback_model_id, 0.85)
            is_cpu_fallback = True
            fallback_chain = [fallback_model_id]
            if force_cpu:
                rationale = (
                    f"Selected '{winner_model.model_name}' because GPU inference is disabled (force_cpu=True)."
                )
                fallback_reason = "Already running on CPU fallback engine."
            else:
                rationale = (
                    "All candidate generative video models were eliminated by hard constraints. "
                    f"Routing to CPU procedural fallback: '{fallback_name}'."
                )
                fallback_reason = "Emergency fallback triggered due to complete generative model elimination."
        else:
            raise RuntimeError("Routing failed: No candidate models eligible and fallback model not found.")

    brief_hash = _hash_brief(creative_brief)
    route_id = f"route-{creative_brief.id}-{brief_hash[:8]}"
    target_hw = "cpu" if is_cpu_fallback else "accelerator"

    return RouteDecision(
        route_id=route_id,
        brief_id=creative_brief.id,
        input_brief_hash=brief_hash,
        timestamp=datetime.now(timezone.utc).isoformat(),
        registry_version=registry.version,
        routing_policy_version=routing_config.get("version", "1.0.0"),
        selected_model=winner_model.model_id,
        selected_model_id=winner_model.model_id,
        selected_model_name=winner_model.model_name,
        selected_score=winner_score,
        is_cpu_fallback=is_cpu_fallback,
        rationale=rationale,
        target_hardware=target_hw,
        candidates=candidates,
        candidate_scores=scores_map,
        hard_constraint_results=hard_results_map,
        rejection_reasons=rejection_reasons_map,
        fallback_model=fallback_model_id,
        fallback_reason=fallback_reason,
        fallback=FallbackRoute(
            fallback_model=fallback_model_id,
            fallback_model_name=fallback_name,
            fallback_reason=fallback_reason,
        ),
        fallback_chain=fallback_chain,
        retry_policy=retry_policy_dict,
        scene_durations_evaluated=scene_durations_evaluated,
        routing_weights=genre_weights,
        system_capabilities=system_capabilities,
        scores=legacy_model_scores,
        considered_models=[c.model_id for c in candidates],
    )
