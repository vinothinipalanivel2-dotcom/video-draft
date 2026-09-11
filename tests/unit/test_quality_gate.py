"""Unit tests for QualityGate, ManifestBuilder, and Subtitle generation."""

import datetime
from pathlib import Path
import pytest

from video_draft.adapters.base import ClipArtifact
from video_draft.audio.subtitles import generate_subtitles_from_plan
from video_draft.evaluation.manifest_builder import ManifestBuilder, compute_file_sha256
from video_draft.evaluation.media_validator import FinalMediaValidator
from video_draft.evaluation.models import FinalMediaValidationResult, QualityEvaluationReport
from video_draft.evaluation.quality_gate import QualityGate
from video_draft.schema.brief import CreativeBrief, SystemConstraints
from video_draft.schema.routing import CandidateEvaluation, RouteDecision
from video_draft.schema.scene_plan import SceneBeat, ScenePlan
from video_draft.schema.timeline import Resolution, SceneClip, Timeline


@pytest.fixture
def mock_brief() -> CreativeBrief:
    return CreativeBrief(
        id="brief-qgate-01",
        title="Quality Gate Validation Brief",
        genre="education",
        aspect_ratio="16:9",
        target_duration_sec=16.0,
        script="Quality gates guarantee that all artifacts satisfy system contracts before release.",
        seed=42,
        constraints=SystemConstraints(
            max_vram_gb=16.0,
            allow_cpu_fallback=True,
            quality_tier="draft",
        ),
    )


@pytest.fixture
def mock_plan(mock_brief: CreativeBrief) -> ScenePlan:
    from video_draft.planner.scene_planner import ScenePlanner
    planner = ScenePlanner()
    return planner.plan(mock_brief)


@pytest.fixture
def mock_decision(mock_brief: CreativeBrief) -> RouteDecision:
    return RouteDecision(
        route_id="route-qgate-01",
        brief_id=mock_brief.id,
        input_brief_hash="hash123",
        timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
        selected_model="cpu_procedural_engine",
        selected_model_name="CPU Procedural Engine",
        selected_score=0.95,
        target_hardware="cpu",
        rationale="CPU fallback execution",
        fallback_model="cpu_procedural_engine",
        fallback_reason="Procedural fallback",
        fallback_chain=["cpu_procedural_engine"],
        candidates=[
            CandidateEvaluation(
                model_id="cpu_procedural_engine",
                model_name="CPU Procedural Engine",
                eligible=True,
                score=0.95,
            )
        ],
    )


@pytest.fixture
def mock_pipeline_artifacts(tmp_path: Path, mock_brief: CreativeBrief, mock_plan: ScenePlan):
    """Create minimal dummy pipeline artifacts on disk."""
    out_dir = tmp_path / "artifacts"
    out_dir.mkdir()
    clips_dir = out_dir / "clips"
    clips_dir.mkdir()

    # Create dummy video clips
    clips = []
    for beat in mock_plan.scenes:
        c_path = clips_dir / f"{beat.scene_id}.mp4"
        c_path.write_bytes(b"MOCK_CLIP_PAYLOAD" * 100)
        c = ClipArtifact(
            scene_id=beat.scene_id,
            scene_index=beat.scene_index,
            asset_path=str(c_path),
            asset_hash=compute_file_sha256(c_path),
            duration_sec=beat.duration_sec,
            width=1280,
            height=720,
            fps=30,
            generator_model="cpu_procedural_engine",
        )
        clips.append(c)

    # Create dummy final video
    final_video = out_dir / "final_draft.mp4"
    final_video.write_bytes(b"MOCK_FINAL_VIDEO_PAYLOAD" * 200)

    # Create timeline
    tracks = [
        SceneClip(
            scene_id=c.scene_id,
            scene_index=c.scene_index,
            prompt="visual",
            start_sec=mock_plan.scenes[i].start_sec,
            end_sec=mock_plan.scenes[i].end_sec,
            duration_sec=c.duration_sec,
            asset_path=c.asset_path,
            asset_hash=c.asset_hash,
            generator_model=c.generator_model,
        )
        for i, c in enumerate(clips)
    ]
    timeline = Timeline(
        brief_id=mock_brief.id,
        total_duration_sec=mock_plan.planned_duration_sec,
        resolution=Resolution(width=1280, height=720),
        video_tracks=tracks,
    )

    return out_dir, clips, timeline, final_video


def test_quality_gate_evaluation_flow(
    mock_brief: CreativeBrief,
    mock_plan: ScenePlan,
    mock_decision: RouteDecision,
    mock_pipeline_artifacts,
):
    """Verify QualityGate executes all evaluation dimensions and aggregates score."""
    out_dir, clips, timeline, final_video = mock_pipeline_artifacts

    # Use validator with check_decodability=False for dummy test payload
    class StubMediaValidator(FinalMediaValidator):
        def validate(self, *args, **kwargs) -> FinalMediaValidationResult:
            return FinalMediaValidationResult(
                file_path=str(final_video),
                file_exists=True,
                file_size_bytes=len(final_video.read_bytes()),
                is_valid=True,
                duration_sec=16.0,
                duration_expected=16.0,
                duration_valid=True,
                width=1280,
                height=720,
                resolution_valid=True,
                aspect_ratio="16:9",
                aspect_ratio_valid=True,
                fps=30.0,
                fps_valid=True,
                video_codec="h264",
                codec_valid=True,
                has_audio=True,
                audio_valid=True,
                is_decodable=True,
            )

    qgate = QualityGate(media_validator=StubMediaValidator())
    report = qgate.evaluate_pipeline(
        brief=mock_brief,
        plan=mock_plan,
        decision=mock_decision,
        clips=clips,
        timeline=timeline,
        final_video_path=final_video,
        check_decodability=False,
    )

    assert report.overall_passed is True
    assert report.overall_score >= 0.9
    assert "planning_validity" in report.checks
    assert "routing_validity" in report.checks
    assert "generation_success" in report.checks
    assert "clip_validity" in report.checks
    assert "final_media_validity" in report.checks
    assert "timing_accuracy" in report.checks
    assert "assembly_validity" in report.checks
    assert "cross_consistency" in report.checks
    assert "fallback_usage" in report.checks


def test_quality_gate_reproducibility_check(mock_plan: ScenePlan, mock_pipeline_artifacts):
    """Verify verify_reproducibility checks structural identity between two runs."""
    _, _, timeline, _ = mock_pipeline_artifacts

    # Identical runs pass
    passed, issues = QualityGate.verify_reproducibility(
        run1_plan=mock_plan,
        run2_plan=mock_plan.model_copy(deep=True),
        run1_timeline=timeline,
        run2_timeline=timeline.model_copy(deep=True),
    )
    assert passed is True
    assert len(issues) == 0

    # Divergent scene plan fails
    plan_divergent = mock_plan.model_copy(deep=True)
    plan_divergent.scenes[0].duration_sec = 99.0
    passed, issues = QualityGate.verify_reproducibility(
        run1_plan=mock_plan,
        run2_plan=plan_divergent,
        run1_timeline=timeline,
        run2_timeline=timeline,
    )
    assert passed is False
    assert any("duration drift" in i.lower() for i in issues)


def test_manifest_builder(mock_brief: CreativeBrief, mock_decision: RouteDecision, mock_pipeline_artifacts, tmp_path: Path):
    """Verify ManifestBuilder computes SHA-256 digests and assembles AssetManifest."""
    out_dir, _, timeline, final_video = mock_pipeline_artifacts
    tl_path = out_dir / "timeline.json"
    tl_path.write_text(timeline.model_dump_json(), encoding="utf-8")
    rt_path = out_dir / "route_decision.json"
    rt_path.write_text(mock_decision.model_dump_json(), encoding="utf-8")
    srt_path = out_dir / "captions.srt"
    srt_path.write_text("1\n00:00:00,000 --> 00:00:08,000\nHello\n", encoding="utf-8")

    manifest = ManifestBuilder.build_manifest(
        brief=mock_brief,
        output_dir=out_dir,
        output_mp4=final_video,
        timeline_json=tl_path,
        route_decision_json=rt_path,
        captions_srt=srt_path,
        route_decision=mock_decision,
    )

    assert manifest.brief_id == mock_brief.id
    assert manifest.reproducibility_seed == 42
    assert len(manifest.output_mp4_sha256) == 64
    assert len(manifest.models_used) >= 1
    assert manifest.models_used[0].model_id == "cpu_procedural_engine"
    assert "output_mp4" in manifest.asset_hashes
    assert "timeline_json" in manifest.asset_hashes
    assert "captions_srt" in manifest.asset_hashes

    # Test manifest save
    saved = ManifestBuilder.save_manifest(manifest, out_dir / "manifest.json")
    assert saved.is_file()


def test_subtitle_generation_srt_and_vtt(mock_plan: ScenePlan, tmp_path: Path):
    """Verify subtitle generator produces valid formatted SRT and WebVTT outputs."""
    srt_path = tmp_path / "test.srt"
    vtt_path = tmp_path / "test.vtt"

    generate_subtitles_from_plan(mock_plan, srt_path, subtitle_format="srt")
    assert srt_path.is_file()
    srt_content = srt_path.read_text(encoding="utf-8")
    assert "1" in srt_content
    assert "-->" in srt_content
    assert mock_plan.scenes[0].narration_chunk in srt_content

    generate_subtitles_from_plan(mock_plan, vtt_path, subtitle_format="vtt")
    assert vtt_path.is_file()
    vtt_content = vtt_path.read_text(encoding="utf-8")
    assert "WEBVTT" in vtt_content
    assert "-->" in vtt_content
