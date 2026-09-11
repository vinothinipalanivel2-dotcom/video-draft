"""Comprehensive tests for Phase 5 — Model Routing, Fallback & Generation Reliability."""

import datetime
from pathlib import Path
import pytest
from click.testing import CliRunner

from video_draft.adapters.base import (
    ClipGenerationError,
    PermanentGenerationError,
    ProviderUnavailableError,
    TransientGenerationError,
)
from video_draft.adapters.mock_generator import MockClipGenerator
from video_draft.adapters.reliable_generator import (
    GenerationReliabilityError,
    ReliableClipGenerator,
    RetryPolicy,
)
from video_draft.adapters.validator import ClipValidationError, ClipValidator
from video_draft.cli import main
from video_draft.router.registry import ModelRegistry
from video_draft.router.router import route
from video_draft.schema.brief import CreativeBrief, SystemConstraints
from video_draft.schema.routing import CandidateEvaluation, RouteDecision
from video_draft.schema.scene_plan import SceneBeat, ScenePlan


@pytest.fixture
def sample_brief() -> CreativeBrief:
    return CreativeBrief(
        id="brief-test-rel",
        title="Reliability Test Brief",
        genre="education",
        target_duration_sec=16.0,
        aspect_ratio="16:9",
        script="A comprehensive explainer on model fallback mechanisms and generation reliability.",
        constraints=SystemConstraints(
            max_vram_gb=16.0,
            allow_cpu_fallback=True,
            quality_tier="draft",
        ),
    )


@pytest.fixture
def sample_beat() -> SceneBeat:
    return SceneBeat(
        scene_id="scene_01",
        scene_index=1,
        title="Intro",
        beat_type="intro",
        narration_chunk="Testing fallback mechanisms in video draft.",
        visual_prompt="A test diagram showing model routing",
        duration_sec=4.0,
        start_sec=0.0,
        end_sec=4.0,
    )


@pytest.fixture
def dummy_decision() -> RouteDecision:
    return RouteDecision(
        route_id="route-rel-test",
        brief_id="brief-test-rel",
        input_brief_hash="hash123",
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        selected_model="model_primary",
        selected_model_name="Primary Model",
        selected_score=0.95,
        target_hardware="cpu",
        rationale="Top ranked candidate",
        fallback_model="cpu_procedural_engine",
        fallback_reason="Procedural CPU fallback",
        fallback_chain=["model_secondary", "cpu_procedural_engine"],
        candidates=[
            CandidateEvaluation(
                model_id="model_primary",
                model_name="Primary Model",
                eligible=True,
                score=0.95,
            ),
            CandidateEvaluation(
                model_id="model_secondary",
                model_name="Secondary Model",
                eligible=True,
                score=0.85,
            ),
        ],
    )


def test_route_decision_fallback_chain_construction(sample_brief: CreativeBrief):
    """Verify route() constructs an ordered fallback_chain in RouteDecision."""
    decision = route(creative_brief=sample_brief, force_cpu=True)
    assert decision.selected_model == "cpu_procedural_engine"
    assert isinstance(decision.fallback_chain, list)
    assert "cpu_procedural_engine" in decision.fallback_chain


def test_route_with_scene_aware_duration(sample_brief: CreativeBrief):
    """Verify route() evaluates scene plan duration bounds when scene_plan is provided."""
    from video_draft.planner.scene_planner import ScenePlanner

    planner = ScenePlanner()
    plan = planner.plan(sample_brief)

    # Mutate one scene beat duration to 6.0s (zeroscope max duration is 4.0s)
    plan.scenes[0].duration_sec = 6.0

    decision = route(creative_brief=sample_brief, scene_plan=plan, force_cpu=False)
    assert decision.scene_durations_evaluated is not None
    assert 6.0 in decision.scene_durations_evaluated

    # Models supporting only <= 4.0s (e.g. zeroscope_v2_576w max is 4.0s) must be disqualified
    zeroscope_cand = next((c for c in decision.candidates if "zeroscope" in c.model_id), None)
    if zeroscope_cand:
        assert not zeroscope_cand.eligible
        assert any("duration" in r.lower() for r in zeroscope_cand.rejection_reasons)


def test_retry_policy_classification():
    """Verify RetryPolicy accurately categorizes transient vs permanent errors."""
    policy = RetryPolicy()

    # Transient / retryable errors
    assert policy.is_retryable(TransientGenerationError("Network timeout"))
    assert policy.is_retryable(ClipValidationError("File missing", field="file_existence"))
    assert policy.is_retryable(ClipValidationError("File empty", field="file_size"))
    assert policy.is_retryable(RuntimeError("Unknown glitch"))

    # Permanent / non-retryable errors
    assert not policy.is_retryable(PermanentGenerationError("Invalid format"))
    assert not policy.is_retryable(ProviderUnavailableError("Provider offline"))
    assert not policy.is_retryable(ClipValidationError("Duration mismatch", field="duration"))
    assert not policy.is_retryable(ClipValidationError("Aspect ratio mismatch", field="aspect_ratio"))


def test_reliable_generator_direct_success(dummy_decision: RouteDecision, sample_beat: SceneBeat, tmp_path: Path):
    """Verify successful generation without fallback or retries when primary model succeeds."""
    mock_gen = MockClipGenerator(use_real_ffmpeg=False)
    validator = ClipValidator(probe_media_streams=False)
    orchestrator = ReliableClipGenerator(
        decision=dummy_decision,
        validator=validator,
        override_generator=mock_gen,
    )

    clip, report = orchestrator.generate_clip_with_fallback(
        beat=sample_beat,
        aspect_ratio="16:9",
        output_dir=tmp_path,
    )

    assert clip is not None
    assert Path(clip.asset_path).is_file()
    assert not report.fallback_occurred
    assert report.total_retries == 0
    assert len(report.attempts) == 1
    assert report.final_model == "model_primary"
    assert clip.metadata["fallback_occurred"] is False


def test_reliable_generator_transient_retry_success(
    dummy_decision: RouteDecision, sample_beat: SceneBeat, tmp_path: Path
):
    """Verify recovery on second attempt when a transient failure occurs on first attempt."""
    mock_gen = MockClipGenerator(use_real_ffmpeg=False, transient_failures_count=1)
    validator = ClipValidator(probe_media_streams=False)
    policy = RetryPolicy(max_retries=2, backoff_sec=0.01)

    orchestrator = ReliableClipGenerator(
        decision=dummy_decision,
        retry_policy=policy,
        validator=validator,
        override_generator=mock_gen,
    )

    clip, report = orchestrator.generate_clip_with_fallback(
        beat=sample_beat,
        aspect_ratio="16:9",
        output_dir=tmp_path,
    )

    assert clip is not None
    assert not report.fallback_occurred
    assert report.total_retries == 1
    assert len(report.attempts) == 2
    assert report.attempts[0].success is False
    assert report.attempts[1].success is True
    assert report.final_model == "model_primary"


def test_reliable_generator_fallback_to_secondary(
    dummy_decision: RouteDecision, sample_beat: SceneBeat, tmp_path: Path
):
    """Verify fallback to secondary candidate when primary candidate fails."""
    # Primary model fails, secondary succeeds
    mock_gen = MockClipGenerator(
        use_real_ffmpeg=False,
        fail_for_models={"model_primary"},
    )
    validator = ClipValidator(probe_media_streams=False)
    policy = RetryPolicy(max_retries=1, backoff_sec=0.01)

    orchestrator = ReliableClipGenerator(
        decision=dummy_decision,
        retry_policy=policy,
        validator=validator,
        override_generator=mock_gen,
    )

    clip, report = orchestrator.generate_clip_with_fallback(
        beat=sample_beat,
        aspect_ratio="16:9",
        output_dir=tmp_path,
    )

    assert clip is not None
    assert report.fallback_occurred is True
    assert report.requested_model == "model_primary"
    assert report.final_model == "model_secondary"
    assert clip.metadata["fallback_occurred"] is True
    assert clip.metadata["final_model"] == "model_secondary"

    # Primary made 2 attempts (1 initial + 1 retry), secondary made 1 attempt
    assert mock_gen.attempt_counts["model_primary"] == 2
    assert mock_gen.attempt_counts["model_secondary"] == 1


def test_reliable_generator_non_retryable_skips_retries(
    dummy_decision: RouteDecision, sample_beat: SceneBeat, tmp_path: Path
):
    """Verify permanent failure does not waste retries and falls back immediately."""
    mock_gen = MockClipGenerator(
        use_real_ffmpeg=False,
        non_retryable_models={"model_primary"},
    )
    validator = ClipValidator(probe_media_streams=False)
    policy = RetryPolicy(max_retries=3, backoff_sec=0.01)

    orchestrator = ReliableClipGenerator(
        decision=dummy_decision,
        retry_policy=policy,
        validator=validator,
        override_generator=mock_gen,
    )

    clip, report = orchestrator.generate_clip_with_fallback(
        beat=sample_beat,
        aspect_ratio="16:9",
        output_dir=tmp_path,
    )

    assert clip is not None
    assert report.fallback_occurred is True
    assert report.final_model == "model_secondary"
    # Primary failed permanently: exactly 1 attempt made, 0 retries on primary
    assert mock_gen.attempt_counts["model_primary"] == 1


def test_reliable_generator_complete_exhaustion_raises(
    dummy_decision: RouteDecision, sample_beat: SceneBeat, tmp_path: Path
):
    """Verify GenerationReliabilityError is raised when all candidate models fail."""
    mock_gen = MockClipGenerator(
        use_real_ffmpeg=False,
        fail_for_models={"model_primary", "model_secondary", "cpu_procedural_engine"},
    )
    validator = ClipValidator(probe_media_streams=False)
    policy = RetryPolicy(max_retries=1, backoff_sec=0.01)

    orchestrator = ReliableClipGenerator(
        decision=dummy_decision,
        retry_policy=policy,
        validator=validator,
        override_generator=mock_gen,
    )

    with pytest.raises(GenerationReliabilityError) as exc_info:
        orchestrator.generate_clip_with_fallback(
            beat=sample_beat,
            aspect_ratio="16:9",
            output_dir=tmp_path,
        )

    err = exc_info.value
    assert err.scene_id == sample_beat.scene_id
    assert len(err.attempts) > 0
    assert "failed" in str(err).lower()


def test_reliable_generator_fallback_disabled(
    dummy_decision: RouteDecision, sample_beat: SceneBeat, tmp_path: Path
):
    """Verify generator halts if fallback chain is disabled in policy."""
    mock_gen = MockClipGenerator(
        use_real_ffmpeg=False,
        fail_for_models={"model_primary"},
    )
    validator = ClipValidator(probe_media_streams=False)
    policy = RetryPolicy(max_retries=0, enable_fallback_chain=False)

    orchestrator = ReliableClipGenerator(
        decision=dummy_decision,
        retry_policy=policy,
        validator=validator,
        override_generator=mock_gen,
    )

    with pytest.raises(GenerationReliabilityError):
        orchestrator.generate_clip_with_fallback(
            beat=sample_beat,
            aspect_ratio="16:9",
            output_dir=tmp_path,
        )

    # Secondary was never attempted
    assert "model_secondary" not in mock_gen.attempt_counts


def test_route_decision_serialization_with_phase5_fields(dummy_decision: RouteDecision):
    """Verify RouteDecision dumps and reloads JSON with fallback_chain and retry_policy."""
    json_str = dummy_decision.model_dump_json()
    loaded = RouteDecision.model_validate_json(json_str)

    assert loaded.fallback_chain == dummy_decision.fallback_chain
    assert loaded.retry_policy == dummy_decision.retry_policy
    assert loaded.selected_model == dummy_decision.selected_model


def test_cli_route_displays_fallback_chain(tmp_path: Path, sample_brief: CreativeBrief):
    """Verify CLI route command displays fallback chain in terminal output."""
    runner = CliRunner()
    brief_file = tmp_path / "brief.json"
    brief_file.write_text(sample_brief.model_dump_json(), encoding="utf-8")

    result = runner.invoke(main, ["route", "--brief", str(brief_file), "--force-cpu"])
    assert result.exit_code == 0
    assert "Fallback model:" in result.output
    assert "Fallback chain:" in result.output
    assert "cpu_procedural_engine" in result.output
