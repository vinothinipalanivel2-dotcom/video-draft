"""Unit tests for clip validation engine."""

from pathlib import Path
import pytest

from video_draft.adapters.base import ClipArtifact
from video_draft.adapters.validator import ClipValidationError, ClipValidator
from video_draft.schema.scene_plan import SceneBeat, ScenePlan


@pytest.fixture
def sample_beat() -> SceneBeat:
    return SceneBeat(
        scene_id="scene_01",
        scene_index=1,
        title="Intro",
        beat_type="intro",
        narration_chunk="Intro narration.",
        visual_prompt="Intro visual prompt",
        duration_sec=3.0,
        start_sec=0.0,
        end_sec=3.0,
        transition_in="fade",
        transition_out="fade",
    )


@pytest.fixture
def valid_clip(tmp_path: Path, sample_beat: SceneBeat) -> ClipArtifact:
    clip_file = tmp_path / "valid_clip.mp4"
    clip_file.write_bytes(b"A" * 500)
    return ClipArtifact(
        scene_id=sample_beat.scene_id,
        scene_index=sample_beat.scene_index,
        asset_path=str(clip_file),
        asset_hash="a" * 64,
        duration_sec=sample_beat.duration_sec,
        width=1280,
        height=720,
        fps=30,
        generator_model="cpu_procedural_engine",
        transition_in="fade",
        transition_out="fade",
        metadata={"mock": True},
    )


def test_validate_clip_success(valid_clip: ClipArtifact, sample_beat: SceneBeat):
    """Verify valid clip passes validation."""
    validator = ClipValidator(probe_media_streams=False)
    result = validator.validate_clip(valid_clip, sample_beat, "16:9")
    assert result["status"] == "valid"
    assert result["scene_id"] == "scene_01"


def test_validate_clip_missing_file(valid_clip: ClipArtifact, sample_beat: SceneBeat):
    """Verify non-existent asset file triggers ClipValidationError."""
    valid_clip.asset_path = "non_existent_file.mp4"
    validator = ClipValidator(probe_media_streams=False)
    with pytest.raises(ClipValidationError) as exc_info:
        validator.validate_clip(valid_clip, sample_beat, "16:9")
    assert "does not exist" in str(exc_info.value)
    assert exc_info.value.field == "file_existence"


def test_validate_clip_empty_file(tmp_path: Path, valid_clip: ClipArtifact, sample_beat: SceneBeat):
    """Verify empty/corrupted file (<128 bytes) triggers ClipValidationError."""
    empty_file = tmp_path / "empty.mp4"
    empty_file.write_bytes(b"tiny")
    valid_clip.asset_path = str(empty_file)
    validator = ClipValidator(probe_media_streams=False)
    with pytest.raises(ClipValidationError) as exc_info:
        validator.validate_clip(valid_clip, sample_beat, "16:9")
    assert "empty or too small" in str(exc_info.value)
    assert exc_info.value.field == "file_size"


def test_validate_clip_scene_id_mismatch(valid_clip: ClipArtifact, sample_beat: SceneBeat):
    """Verify mismatched scene_id triggers ClipValidationError."""
    valid_clip.scene_id = "scene_99"
    validator = ClipValidator(probe_media_streams=False)
    with pytest.raises(ClipValidationError) as exc_info:
        validator.validate_clip(valid_clip, sample_beat, "16:9")
    assert "does not match expected scene_id" in str(exc_info.value)
    assert exc_info.value.field == "scene_id"


def test_validate_clip_duration_drift(valid_clip: ClipArtifact, sample_beat: SceneBeat):
    """Verify duration exceeding tolerance triggers ClipValidationError."""
    valid_clip.duration_sec = 6.0  # expected is 3.0
    validator = ClipValidator(probe_media_streams=False)
    with pytest.raises(ClipValidationError) as exc_info:
        validator.validate_clip(valid_clip, sample_beat, "16:9", tolerance_sec=0.25)
    assert "differs from planned duration" in str(exc_info.value)
    assert exc_info.value.field == "duration"


def test_validate_clip_aspect_ratio_mismatch(valid_clip: ClipArtifact, sample_beat: SceneBeat):
    """Verify orientation mismatch triggers ClipValidationError."""
    valid_clip.width = 720
    valid_clip.height = 1280  # portrait
    validator = ClipValidator(probe_media_streams=False)
    with pytest.raises(ClipValidationError) as exc_info:
        validator.validate_clip(valid_clip, sample_beat, "16:9")
    assert "Aspect ratio mismatch" in str(exc_info.value)
    assert exc_info.value.field == "aspect_ratio"


def test_validate_clip_low_fps(valid_clip: ClipArtifact, sample_beat: SceneBeat):
    """Verify fps < 10 triggers ClipValidationError."""
    valid_clip.fps = 5
    validator = ClipValidator(probe_media_streams=False)
    with pytest.raises(ClipValidationError) as exc_info:
        validator.validate_clip(valid_clip, sample_beat, "16:9")
    assert "Invalid frame rate" in str(exc_info.value)
    assert exc_info.value.field == "fps"


def test_validate_sequence_success(tmp_path: Path):
    """Verify sequence validation succeeds on coherent ScenePlan and clips."""
    beat1 = SceneBeat(
        scene_id="scene_01",
        scene_index=1,
        title="Intro",
        beat_type="intro",
        narration_chunk="Part 1",
        visual_prompt="Visual 1",
        duration_sec=7.0,
        start_sec=0.0,
        end_sec=7.0,
    )
    beat2 = SceneBeat(
        scene_id="scene_02",
        scene_index=2,
        title="Body",
        beat_type="core",
        narration_chunk="Part 2",
        visual_prompt="Visual 2",
        duration_sec=8.0,
        start_sec=7.0,
        end_sec=15.0,
    )
    plan = ScenePlan(
        plan_id="test_plan",
        brief_id="brief_01",
        genre="education",
        aspect_ratio="16:9",
        target_duration_sec=15.0,
        planned_duration_sec=15.0,
        strategy_name="EducationStrategy",
        pacing_tempo="measured",
        caption_treatment="standard",
        visual_strategy="explanatory",
        scenes=[beat1, beat2],
        input_brief_hash="12345678",
        created_at="2026-09-06T00:00:00Z",
    )

    f1 = tmp_path / "c1.mp4"
    f2 = tmp_path / "c2.mp4"
    f1.write_bytes(b"B" * 500)
    f2.write_bytes(b"C" * 500)

    clips = [
        ClipArtifact(
            scene_id="scene_01",
            scene_index=1,
            asset_path=str(f1),
            asset_hash="b" * 64,
            duration_sec=7.0,
            width=1280,
            height=720,
            generator_model="mock",
            metadata={"mock": True},
        ),
        ClipArtifact(
            scene_id="scene_02",
            scene_index=2,
            asset_path=str(f2),
            asset_hash="c" * 64,
            duration_sec=8.0,
            width=1280,
            height=720,
            generator_model="mock",
            metadata={"mock": True},
        ),
    ]

    validator = ClipValidator(probe_media_streams=False)
    assert validator.validate_sequence(clips, plan) is True


def test_validate_sequence_count_mismatch(tmp_path: Path):
    """Verify mismatched clip count triggers ClipValidationError."""
    beat1 = SceneBeat(
        scene_id="scene_01",
        scene_index=1,
        title="Intro",
        beat_type="intro",
        narration_chunk="Part 1",
        visual_prompt="Visual 1",
        duration_sec=15.0,
        start_sec=0.0,
        end_sec=15.0,
    )
    plan = ScenePlan(
        plan_id="test_plan",
        brief_id="brief_01",
        genre="education",
        aspect_ratio="16:9",
        target_duration_sec=15.0,
        planned_duration_sec=15.0,
        strategy_name="EducationStrategy",
        pacing_tempo="measured",
        caption_treatment="standard",
        visual_strategy="explanatory",
        scenes=[beat1],
        input_brief_hash="12345678",
        created_at="2026-09-06T00:00:00Z",
    )

    validator = ClipValidator(probe_media_streams=False)
    with pytest.raises(ClipValidationError) as exc_info:
        validator.validate_sequence([], plan)
    assert "Clip count mismatch" in str(exc_info.value)
    assert exc_info.value.field == "clip_count"
