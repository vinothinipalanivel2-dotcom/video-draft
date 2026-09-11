"""Unit tests for FFmpeg assembly pipeline, transitions, and timeline builder."""

from pathlib import Path
import pytest

from video_draft.adapters.procedural_generator import ProceduralClipGenerator
from video_draft.assembly.ffmpeg_assembler import FFmpegAssembler
from video_draft.assembly.ffmpeg_tools import (
    AssemblyError,
    get_ffmpeg_binary,
    probe_media,
)
from video_draft.assembly.timeline_builder import TimelineBuilder
from video_draft.audio.generator import DeterministicAudioGenerator
from video_draft.schema.scene_plan import SceneBeat, ScenePlan
from video_draft.schema.timeline import Timeline


@pytest.fixture
def mini_plan() -> ScenePlan:
    beat1 = SceneBeat(
        scene_id="scene_01",
        scene_index=1,
        title="Scene 1",
        beat_type="intro",
        narration_chunk="First intro scene.",
        visual_prompt="First visual prompt",
        duration_sec=5.0,
        start_sec=0.0,
        end_sec=5.0,
        transition_in="fade",
        transition_out="fade",
    )
    beat2 = SceneBeat(
        scene_id="scene_02",
        scene_index=2,
        title="Scene 2",
        beat_type="core",
        narration_chunk="Second core scene.",
        visual_prompt="Second visual prompt",
        duration_sec=5.0,
        start_sec=5.0,
        end_sec=10.0,
        transition_in="fade",
        transition_out="fade",
    )
    beat3 = SceneBeat(
        scene_id="scene_03",
        scene_index=3,
        title="Scene 3",
        beat_type="cta",
        narration_chunk="Third conclusion scene.",
        visual_prompt="Third visual prompt",
        duration_sec=5.0,
        start_sec=10.0,
        end_sec=15.0,
        transition_in="fade",
        transition_out="fade",
    )
    return ScenePlan(
        plan_id="mini_plan_001",
        brief_id="brief_mini",
        genre="education",
        aspect_ratio="16:9",
        target_duration_sec=15.0,
        planned_duration_sec=15.0,
        strategy_name="EducationStrategy",
        pacing_tempo="moderate",
        caption_treatment="standard",
        visual_strategy="explanatory",
        scenes=[beat1, beat2, beat3],
        input_brief_hash="1122334455667788",
        created_at="2026-09-06T00:00:00Z",
    )


def test_ffmpeg_binary_discovery():
    """Verify FFmpeg binary can be discovered on host."""
    binary = get_ffmpeg_binary()
    assert binary is not None
    assert Path(binary).is_file()


def test_transition_filter_syntax():
    """Verify video filter strings for supported transitions."""
    assembler = FFmpegAssembler(transition_duration_sec=0.3)

    # Fade filter
    fade_filter = assembler._build_clip_video_filter(0, 1280, 720, 2.0, "fade", "fade")
    assert "fade=t=in" in fade_filter
    assert "fade=t=out" in fade_filter
    assert "scale=1280:720" in fade_filter

    # Cut filter (no fade)
    cut_filter = assembler._build_clip_video_filter(1, 1280, 720, 2.0, "cut", "cut")
    assert "fade=" not in cut_filter

    # Unsupported transition raises AssemblyError
    with pytest.raises(AssemblyError):
        assembler._build_clip_video_filter(0, 1280, 720, 2.0, "spin_zoom_unsupported", "fade")


def test_timeline_builder_roundtrip(tmp_path: Path, mini_plan: ScenePlan):
    """Verify TimelineBuilder produces valid Timeline and can save/load JSON."""
    generator = ProceduralClipGenerator()
    clips = [
        generator.generate_clip(b, "cpu_procedural_engine", mini_plan.aspect_ratio, tmp_path / "clips")
        for b in mini_plan.scenes
    ]

    audio_gen = DeterministicAudioGenerator()
    audio_path = audio_gen.build_narration_track(mini_plan.scenes, tmp_path / "audio" / "narration.wav")

    timeline = TimelineBuilder.build_timeline(
        plan=mini_plan,
        clips=clips,
        audio_artifact=audio_path,
    )

    assert isinstance(timeline, Timeline)
    assert len(timeline.video_tracks) == 3
    assert len(timeline.audio_tracks) == 1
    assert timeline.total_duration_sec == 15.0

    timeline_json = tmp_path / "timeline.json"
    TimelineBuilder.save_timeline(timeline, timeline_json)
    assert timeline_json.is_file()

    loaded = TimelineBuilder.load_timeline(timeline_json)
    assert loaded.brief_id == mini_plan.brief_id
    assert len(loaded.video_tracks) == 3


def test_ffmpeg_assembly_end_to_end(tmp_path: Path, mini_plan: ScenePlan):
    """Verify complete video assembly produces valid playable MP4 with audio."""
    generator = ProceduralClipGenerator()
    clips = [
        generator.generate_clip(b, "cpu_procedural_engine", mini_plan.aspect_ratio, tmp_path / "clips")
        for b in mini_plan.scenes
    ]

    audio_gen = DeterministicAudioGenerator()
    audio_path = audio_gen.build_narration_track(mini_plan.scenes, tmp_path / "audio" / "narration.wav")

    timeline = TimelineBuilder.build_timeline(
        plan=mini_plan,
        clips=clips,
        audio_artifact=audio_path,
    )

    final_mp4 = tmp_path / "output.mp4"
    assembler = FFmpegAssembler()
    result_path = assembler.assemble_from_timeline(timeline, final_mp4)

    assert result_path.is_file()
    assert result_path.stat().st_size > 1000

    # Probe assembled video
    info = probe_media(result_path)
    assert info["has_audio"] is True
    assert info["width"] == 1280
    assert info["height"] == 720
    assert abs(info["duration"] - 15.0) < 0.25
