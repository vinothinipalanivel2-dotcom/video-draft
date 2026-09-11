"""Unit tests for audio narration synthesis and timing alignment."""

from pathlib import Path
import wave
import pytest

from video_draft.audio.generator import (
    AudioArtifact,
    AudioGenerationError,
    DeterministicAudioGenerator,
)
from video_draft.schema.scene_plan import SceneBeat


@pytest.fixture
def sample_beats() -> list[SceneBeat]:
    return [
        SceneBeat(
            scene_id="scene_01",
            scene_index=1,
            title="Hook",
            beat_type="intro",
            narration_chunk="Welcome to the open video assessment.",
            visual_prompt="Title visual",
            duration_sec=2.5,
            start_sec=0.0,
            end_sec=2.5,
        ),
        SceneBeat(
            scene_id="scene_02",
            scene_index=2,
            title="Core Point",
            beat_type="core",
            narration_chunk="This architecture runs deterministically on non-GPU laptops.",
            visual_prompt="System diagram",
            duration_sec=3.5,
            start_sec=2.5,
            end_sec=6.0,
        ),
    ]


def test_generate_scene_audio_creates_valid_wav(tmp_path: Path, sample_beats: list[SceneBeat]):
    """Verify single scene audio generates valid 44.1kHz mono WAV."""
    generator = DeterministicAudioGenerator(sample_rate=44100)
    artifact = generator.generate_scene_audio(sample_beats[0], tmp_path)

    assert isinstance(artifact, AudioArtifact)
    assert artifact.scene_id == "scene_01"
    assert artifact.duration_sec == 2.5
    assert Path(artifact.asset_path).is_file()

    with wave.open(artifact.asset_path, "rb") as wf:
        assert wf.getnchannels() == 1
        assert wf.getsampwidth() == 2
        assert wf.getframerate() == 44100
        n_frames = wf.getnframes()
        actual_duration = n_frames / 44100
        assert abs(actual_duration - 2.5) < 0.01


def test_build_narration_track_stitching(tmp_path: Path, sample_beats: list[SceneBeat]):
    """Verify master narration track aligns all scenes and spans total duration."""
    generator = DeterministicAudioGenerator(sample_rate=44100)
    master_path = tmp_path / "master.wav"
    out = generator.build_narration_track(sample_beats, master_path)

    assert out.is_file()
    with wave.open(str(out), "rb") as wf:
        assert wf.getnchannels() == 1
        assert wf.getframerate() == 44100
        n_frames = wf.getnframes()
        total_duration = n_frames / 44100
        # Expected max end_sec is 6.0
        assert abs(total_duration - 6.0) < 0.01


def test_build_narration_track_empty_raises(tmp_path: Path):
    """Verify empty scene list raises AudioGenerationError."""
    generator = DeterministicAudioGenerator()
    with pytest.raises(AudioGenerationError):
        generator.build_narration_track([], tmp_path / "empty.wav")
