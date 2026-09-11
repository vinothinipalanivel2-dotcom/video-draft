"""Unit tests for FinalMediaValidator inspecting assembled MP4 video artifacts."""

from pathlib import Path
import pytest

from video_draft.assembly.ffmpeg_tools import get_ffmpeg_binary, run_ffmpeg
from video_draft.evaluation.media_validator import FinalMediaValidator


@pytest.fixture
def sample_valid_mp4(tmp_path: Path) -> Path:
    """Generate a minimal valid 16:9 30fps MP4 with audio track."""
    video_path = tmp_path / "valid_sample.mp4"
    # Create 2-second test video with silent audio track using FFmpeg
    args = [
        "-y",
        "-f", "lavfi", "-i", "color=c=blue:s=1280x720:d=2.0:r=30",
        "-f", "lavfi", "-i", "anullsrc=r=44100:cl=mono",
        "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
        "-c:a", "aac", "-b:a", "64k",
        "-t", "2.0",
        str(video_path),
    ]
    run_ffmpeg(args)
    return video_path


def test_validate_valid_video(sample_valid_mp4: Path):
    """Verify FinalMediaValidator passes a correctly formed MP4 video with audio."""
    validator = FinalMediaValidator(default_tolerance_sec=0.5)
    res = validator.validate(
        video_path=sample_valid_mp4,
        expected_aspect_ratio="16:9",
        expected_duration=2.0,
        require_audio=True,
    )

    assert res.file_exists is True
    assert res.file_size_bytes >= 1024
    assert res.duration_valid is True
    assert abs(res.duration_sec - 2.0) <= 0.5
    assert res.resolution_valid is True
    assert res.width == 1280
    assert res.height == 720
    assert res.aspect_ratio_valid is True
    assert res.fps_valid is True
    assert res.codec_valid is True
    assert res.has_audio is True
    assert res.audio_valid is True
    assert res.is_decodable is True
    assert res.is_valid is True
    assert len(res.issues) == 0


def test_validate_missing_video(tmp_path: Path):
    """Verify validator flags non-existent files."""
    validator = FinalMediaValidator()
    res = validator.validate(
        video_path=tmp_path / "non_existent.mp4",
        expected_aspect_ratio="16:9",
        expected_duration=5.0,
    )
    assert res.file_exists is False
    assert res.is_valid is False
    assert any("does not exist" in issue for issue in res.issues)


def test_validate_truncated_file(tmp_path: Path):
    """Verify validator flags files under the minimum file size."""
    small_file = tmp_path / "small.mp4"
    small_file.write_bytes(b"too small")

    validator = FinalMediaValidator(min_file_size_bytes=1024)
    res = validator.validate(
        video_path=small_file,
        expected_aspect_ratio="16:9",
        expected_duration=5.0,
        check_decodability=False,
    )
    assert res.file_exists is True
    assert res.file_size_bytes < 1024
    assert res.is_valid is False
    assert any("below minimum threshold" in issue for issue in res.issues)


def test_validate_duration_mismatch(sample_valid_mp4: Path):
    """Verify validator flags duration drift exceeding allowable tolerance."""
    validator = FinalMediaValidator(default_tolerance_sec=0.3)
    # Target is 10.0s, but video is 2.0s
    res = validator.validate(
        video_path=sample_valid_mp4,
        expected_aspect_ratio="16:9",
        expected_duration=10.0,
    )
    assert res.duration_valid is False
    assert res.is_valid is False
    assert any("Duration mismatch" in issue for issue in res.issues)


def test_validate_aspect_ratio_mismatch(sample_valid_mp4: Path):
    """Verify validator flags resolution and aspect ratio mismatches."""
    validator = FinalMediaValidator()
    # Video is 1280x720 (16:9), but brief requested 9:16
    res = validator.validate(
        video_path=sample_valid_mp4,
        expected_aspect_ratio="9:16",
        expected_duration=2.0,
    )
    assert res.resolution_valid is False
    assert res.aspect_ratio_valid is False
    assert res.is_valid is False
    assert any("Resolution mismatch" in issue for issue in res.issues)


def test_validate_missing_audio_when_required(tmp_path: Path):
    """Verify validator flags missing audio stream when require_audio is True."""
    silent_vid = tmp_path / "silent.mp4"
    # Create video with NO audio stream
    args = [
        "-y",
        "-f", "lavfi", "-i", "color=c=red:s=1280x720:d=1.0:r=30",
        "-c:v", "libx264", "-tune", "stillimage", "-pix_fmt", "yuv420p",
        "-an",
        str(silent_vid),
    ]
    run_ffmpeg(args)

    validator = FinalMediaValidator()
    res = validator.validate(
        video_path=silent_vid,
        expected_aspect_ratio="16:9",
        expected_duration=1.0,
        require_audio=True,
    )
    assert res.has_audio is False
    assert res.audio_valid is False
    assert res.is_valid is False
    assert any("Audio stream missing" in issue for issue in res.issues)
