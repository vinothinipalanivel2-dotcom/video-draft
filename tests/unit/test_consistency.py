"""Unit tests for CrossArtifactConsistencyChecker verifying alignment across pipeline stages."""

from pathlib import Path
import pytest

from video_draft.adapters.base import ClipArtifact
from video_draft.evaluation.consistency import CrossArtifactConsistencyChecker
from video_draft.schema.brief import CreativeBrief, SystemConstraints
from video_draft.schema.routing import RouteDecision
from video_draft.schema.scene_plan import SceneBeat, ScenePlan
from video_draft.schema.timeline import AudioTrack, Resolution, SceneClip, Timeline


@pytest.fixture
def base_brief() -> CreativeBrief:
    return CreativeBrief(
        id="brief-consist-01",
        title="Consistency Test Brief",
        genre="education",
        aspect_ratio="16:9",
        target_duration_sec=16.0,
        script="A consistent pipeline guarantees contract alignment from brief to final video.",
        constraints=SystemConstraints(
            max_vram_gb=16.0,
            allow_cpu_fallback=True,
            quality_tier="draft",
        ),
    )


@pytest.fixture
def base_plan(base_brief: CreativeBrief) -> ScenePlan:
    from video_draft.planner.scene_planner import ScenePlanner
    planner = ScenePlanner()
    return planner.plan(base_brief)


@pytest.fixture
def base_clips(tmp_path: Path, base_plan: ScenePlan) -> list[ClipArtifact]:
    clips = []
    for beat in base_plan.scenes:
        c_path = tmp_path / f"{beat.scene_id}.mp4"
        c_path.write_bytes(b"dummy" * 100)
        c = ClipArtifact(
            scene_id=beat.scene_id,
            scene_index=beat.scene_index,
            asset_path=str(c_path),
            asset_hash=f"hash_{beat.scene_id}",
            duration_sec=beat.duration_sec,
            width=1280,
            height=720,
            fps=30,
            generator_model="cpu_procedural_engine",
        )
        clips.append(c)
    return clips


@pytest.fixture
def base_timeline(base_brief: CreativeBrief, base_plan: ScenePlan, base_clips: list[ClipArtifact]) -> Timeline:
    tracks = [
        SceneClip(
            scene_id=c.scene_id,
            scene_index=c.scene_index,
            prompt="visual",
            start_sec=base_plan.scenes[i].start_sec,
            end_sec=base_plan.scenes[i].end_sec,
            duration_sec=c.duration_sec,
            asset_path=c.asset_path,
            asset_hash=c.asset_hash,
            generator_model=c.generator_model,
        )
        for i, c in enumerate(base_clips)
    ]
    return Timeline(
        brief_id=base_brief.id,
        total_duration_sec=base_plan.planned_duration_sec,
        resolution=Resolution(width=1280, height=720),
        video_tracks=tracks,
        audio_tracks=[],
    )


def test_consistency_check_perfect_alignment(
    base_brief: CreativeBrief,
    base_plan: ScenePlan,
    base_clips: list[ClipArtifact],
    base_timeline: Timeline,
):
    """Verify consistency checker passes when all stages are strictly aligned."""
    checker = CrossArtifactConsistencyChecker(duration_tolerance_sec=0.5)
    report = checker.check_consistency(
        brief=base_brief,
        plan=base_plan,
        clips=base_clips,
        timeline=base_timeline,
    )

    assert report.is_consistent is True
    assert report.scene_count_match is True
    assert report.scene_ids_match is True
    assert report.scene_ordering_valid is True
    assert report.duration_alignment_valid is True
    assert report.timeline_continuity_valid is True
    assert report.aspect_ratio_consistent is True
    assert len(report.issues) == 0


def test_consistency_check_scene_count_mismatch(
    base_brief: CreativeBrief,
    base_plan: ScenePlan,
    base_clips: list[ClipArtifact],
    base_timeline: Timeline,
):
    """Verify consistency checker catches mismatch when a clip is missing."""
    checker = CrossArtifactConsistencyChecker()
    # Pass only 1 clip instead of 2
    report = checker.check_consistency(
        brief=base_brief,
        plan=base_plan,
        clips=[base_clips[0]],
        timeline=base_timeline,
    )

    assert report.is_consistent is False
    assert report.scene_count_match is False
    assert any("Scene count mismatch" in issue for issue in report.issues)


def test_consistency_check_scene_id_drift(
    base_brief: CreativeBrief,
    base_plan: ScenePlan,
    base_clips: list[ClipArtifact],
    base_timeline: Timeline,
):
    """Verify consistency checker catches mismatched scene IDs."""
    base_clips[1].scene_id = "unexpected_scene_id"

    checker = CrossArtifactConsistencyChecker()
    report = checker.check_consistency(
        brief=base_brief,
        plan=base_plan,
        clips=base_clips,
        timeline=base_timeline,
    )

    assert report.is_consistent is False
    assert report.scene_ids_match is False
    assert any("Scene ID mismatch" in issue for issue in report.issues)


def test_consistency_check_duration_drift(
    base_brief: CreativeBrief,
    base_plan: ScenePlan,
    base_clips: list[ClipArtifact],
    base_timeline: Timeline,
):
    """Verify consistency checker catches clips total duration drift."""
    # Drastically reduce clip 2 duration
    base_clips[1].duration_sec = 2.0  # total is now 10s instead of 16s

    checker = CrossArtifactConsistencyChecker(duration_tolerance_sec=0.5)
    report = checker.check_consistency(
        brief=base_brief,
        plan=base_plan,
        clips=base_clips,
        timeline=base_timeline,
    )

    assert report.is_consistent is False
    assert report.duration_alignment_valid is False
    assert any("duration drift" in issue.lower() for issue in report.issues)


def test_consistency_check_timeline_discontinuity(
    base_brief: CreativeBrief,
    base_plan: ScenePlan,
    base_clips: list[ClipArtifact],
    base_timeline: Timeline,
):
    """Verify consistency checker detects gaps between timeline tracks."""
    # Create a 2-second gap between track 1 and track 2
    base_timeline.video_tracks[1].start_sec = 10.0
    base_timeline.video_tracks[1].end_sec = 18.0

    checker = CrossArtifactConsistencyChecker()
    report = checker.check_consistency(
        brief=base_brief,
        plan=base_plan,
        clips=base_clips,
        timeline=base_timeline,
    )

    assert report.is_consistent is False
    assert report.timeline_continuity_valid is False
    assert any("discontinuity" in issue.lower() for issue in report.issues)


def test_consistency_check_aspect_ratio_conflict(
    base_brief: CreativeBrief,
    base_plan: ScenePlan,
    base_clips: list[ClipArtifact],
    base_timeline: Timeline,
):
    """Verify consistency checker detects aspect ratio conflict between brief and timeline."""
    base_brief.aspect_ratio = "9:16"  # Brief is 9:16, but timeline is 1280x720 (16:9)

    checker = CrossArtifactConsistencyChecker()
    report = checker.check_consistency(
        brief=base_brief,
        plan=base_plan,
        clips=base_clips,
        timeline=base_timeline,
    )

    assert report.is_consistent is False
    assert report.aspect_ratio_consistent is False
    assert any("Aspect ratio conflict" in issue for issue in report.issues)
