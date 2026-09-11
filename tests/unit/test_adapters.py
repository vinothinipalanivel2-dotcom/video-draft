"""Unit tests for video clip generation adapters and factory."""

from pathlib import Path
import pytest

from video_draft.adapters.base import (
    BaseClipGenerator,
    ClipArtifact,
    ClipGenerationError,
    ProviderUnavailableError,
)
from video_draft.adapters.factory import get_clip_generator
from video_draft.adapters.mock_generator import MockClipGenerator
from video_draft.adapters.procedural_generator import ProceduralClipGenerator
from video_draft.schema.scene_plan import SceneBeat


@pytest.fixture
def sample_beat() -> SceneBeat:
    return SceneBeat(
        scene_id="scene_01",
        scene_index=1,
        title="Intro Hook",
        beat_type="intro",
        narration_chunk="Welcome to our open source video generation system.",
        visual_prompt="Minimalist modern title card with sleek motion graphics",
        duration_sec=3.0,
        start_sec=0.0,
        end_sec=3.0,
        transition_in="fade",
        transition_out="fade",
        overlay_text="Open-Source Video Drafting",
        metadata={"genre": "education"},
    )


def test_mock_clip_generator_success(tmp_path: Path, sample_beat: SceneBeat):
    """Verify mock generator produces valid ClipArtifact and file on disk."""
    generator = MockClipGenerator(use_real_ffmpeg=False)
    clip = generator.generate_clip(
        beat=sample_beat,
        model_id="mock_model",
        aspect_ratio="16:9",
        output_dir=tmp_path,
    )
    assert isinstance(clip, ClipArtifact)
    assert clip.scene_id == "scene_01"
    assert clip.scene_index == 1
    assert clip.width == 1280
    assert clip.height == 720
    assert clip.duration_sec == 3.0
    assert Path(clip.asset_path).is_file()
    assert len(clip.asset_hash) == 64


def test_mock_clip_generator_9x16(tmp_path: Path, sample_beat: SceneBeat):
    """Verify mock generator respects 9:16 portrait dimensions."""
    generator = MockClipGenerator(use_real_ffmpeg=False)
    clip = generator.generate_clip(
        beat=sample_beat,
        model_id="mock_model",
        aspect_ratio="9:16",
        output_dir=tmp_path,
    )
    assert clip.width == 720
    assert clip.height == 1280


def test_mock_clip_generator_simulated_failure(tmp_path: Path, sample_beat: SceneBeat):
    """Verify mock generator raises ClipGenerationError when requested."""
    generator = MockClipGenerator(fail_on_scene_id="scene_01")
    with pytest.raises(ClipGenerationError) as exc_info:
        generator.generate_clip(
            beat=sample_beat,
            model_id="mock_model",
            aspect_ratio="16:9",
            output_dir=tmp_path,
        )
    assert "Simulated generation failure" in str(exc_info.value)
    assert exc_info.value.scene_id == "scene_01"


def test_procedural_generator_creation(tmp_path: Path, sample_beat: SceneBeat):
    """Verify procedural generator creates a real MP4 clip via FFmpeg."""
    generator = ProceduralClipGenerator()
    clip = generator.generate_clip(
        beat=sample_beat,
        model_id="cpu_procedural_engine",
        aspect_ratio="16:9",
        output_dir=tmp_path,
    )
    assert isinstance(clip, ClipArtifact)
    assert clip.scene_id == "scene_01"
    assert Path(clip.asset_path).exists()
    assert Path(clip.asset_path).stat().st_size > 500


def test_adapter_factory_returns_expected_instances():
    """Verify get_clip_generator returns appropriate subclass instances."""
    mock_gen = get_clip_generator(model_id="mock", mock=True)
    assert isinstance(mock_gen, MockClipGenerator)

    cpu_gen = get_clip_generator(model_id="cpu_procedural_engine")
    assert isinstance(cpu_gen, ProceduralClipGenerator)

    # Open model with fallback enabled returns procedural generator
    gpu_fallback_gen = get_clip_generator(model_id="zeroscope_v2_576w", allow_cpu_fallback=True)
    assert isinstance(gpu_fallback_gen, ProceduralClipGenerator)

    # Open model with fallback disabled raises ProviderUnavailableError
    with pytest.raises(ProviderUnavailableError):
        get_clip_generator(model_id="zeroscope_v2_576w", allow_cpu_fallback=False)
