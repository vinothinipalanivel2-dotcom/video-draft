"""Final MP4 media validation layer verifying streams, decodability, duration, and geometry."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from video_draft.assembly.ffmpeg_tools import probe_media, verify_media_decodable
from video_draft.evaluation.models import FinalMediaValidationResult


class FinalMediaValidator:
    """Validates assembled final MP4 video against contract requirements."""

    def __init__(
        self,
        min_file_size_bytes: int = 1024,
        min_fps: float = 20.0,
        default_tolerance_sec: float = 0.5,
    ) -> None:
        self.min_file_size_bytes = min_file_size_bytes
        self.min_fps = min_fps
        self.default_tolerance_sec = default_tolerance_sec

    def validate(
        self,
        video_path: Union[Path, str],
        expected_aspect_ratio: str,
        expected_duration: float,
        require_audio: bool = True,
        tolerance_sec: Optional[float] = None,
        check_decodability: bool = True,
    ) -> FinalMediaValidationResult:
        """Validate an assembled video file against expected parameters.

        Args:
            video_path: Path to the MP4 file.
            expected_aspect_ratio: "16:9" or "9:16".
            expected_duration: Target duration in seconds.
            require_audio: Whether audio stream presence is mandatory.
            tolerance_sec: Allowable duration drift in seconds.
            check_decodability: Whether to run frame-decodability check via FFmpeg.

        Returns:
            FinalMediaValidationResult detailing all validation checks.
        """
        path = Path(video_path)
        issues: List[str] = []
        tol = tolerance_sec if tolerance_sec is not None else self.default_tolerance_sec

        # 1. Existence check
        if not path.is_file():
            return FinalMediaValidationResult(
                file_path=str(path),
                file_exists=False,
                file_size_bytes=0,
                is_valid=False,
                duration_expected=expected_duration,
                aspect_ratio=expected_aspect_ratio,
                issues=[f"Video file does not exist: '{path}'"],
            )

        file_size = path.stat().st_size
        size_valid = file_size >= self.min_file_size_bytes
        if not size_valid:
            issues.append(f"File size ({file_size} bytes) is below minimum threshold ({self.min_file_size_bytes} bytes)")

        # 2. Probe media metadata
        try:
            probe = probe_media(path)
        except Exception as err:
            return FinalMediaValidationResult(
                file_path=str(path),
                file_exists=True,
                file_size_bytes=file_size,
                is_valid=False,
                duration_expected=expected_duration,
                aspect_ratio=expected_aspect_ratio,
                issues=[f"Failed to probe media streams with FFmpeg: {err}"],
            )

        actual_duration = probe.get("duration", 0.0)
        width = probe.get("width")
        height = probe.get("height")
        fps = probe.get("fps")
        video_codec = probe.get("video_codec")
        has_audio = probe.get("has_audio", False)

        # 3. Duration verification
        duration_drift = abs(actual_duration - expected_duration)
        duration_valid = duration_drift <= tol
        if not duration_valid:
            issues.append(
                f"Duration mismatch: actual={actual_duration:.2f}s, expected={expected_duration:.2f}s "
                f"(drift={duration_drift:.2f}s exceeds tolerance={tol:.2f}s)"
            )

        # 4. Resolution & Aspect Ratio verification
        expected_w, expected_h = (720, 1280) if expected_aspect_ratio == "9:16" else (1280, 720)
        resolution_valid = False
        aspect_ratio_valid = False

        if width is not None and height is not None:
            resolution_valid = (width == expected_w and height == expected_h)
            if not resolution_valid:
                issues.append(
                    f"Resolution mismatch: actual={width}x{height}, expected={expected_w}x{expected_h}"
                )

            actual_ratio = width / max(height, 1)
            target_ratio = 9.0 / 16.0 if expected_aspect_ratio == "9:16" else 16.0 / 9.0
            aspect_ratio_valid = abs(actual_ratio - target_ratio) < 0.05
            if not aspect_ratio_valid:
                issues.append(
                    f"Aspect ratio mismatch: actual ratio={actual_ratio:.3f}, expected={target_ratio:.3f} ({expected_aspect_ratio})"
                )
        else:
            issues.append("Could not determine video dimensions from media probe")

        # 5. Frame rate check
        fps_valid = False
        if fps is not None:
            fps_valid = fps >= self.min_fps
            if not fps_valid:
                issues.append(f"Frame rate too low: actual={fps:.1f} fps, minimum required={self.min_fps:.1f} fps")
        else:
            issues.append("Could not determine frame rate from media probe")

        # 6. Video codec check
        codec_valid = False
        if video_codec:
            valid_codecs = {"h264", "avc1", "hevc", "h265", "mp4v"}
            codec_valid = video_codec.lower() in valid_codecs
            if not codec_valid:
                issues.append(f"Unexpected video codec: '{video_codec}'. Expected H.264/HEVC")
        else:
            issues.append("Video stream missing or unidentifiable")

        # 7. Audio stream check
        audio_valid = True
        if require_audio:
            audio_valid = has_audio
            if not audio_valid:
                issues.append("Audio stream missing from final video draft")

        # 8. Decodability check
        is_decodable = False
        if check_decodability:
            is_decodable = verify_media_decodable(path)
            if not is_decodable:
                issues.append("Media file failed decodability stream check (corrupted or unplayable bitstream)")
        else:
            is_decodable = True

        overall_valid = (
            size_valid
            and duration_valid
            and resolution_valid
            and aspect_ratio_valid
            and fps_valid
            and codec_valid
            and audio_valid
            and is_decodable
        )

        return FinalMediaValidationResult(
            file_path=str(path),
            file_exists=True,
            file_size_bytes=file_size,
            is_valid=overall_valid,
            duration_sec=actual_duration,
            duration_expected=expected_duration,
            duration_valid=duration_valid,
            width=width,
            height=height,
            resolution_valid=resolution_valid,
            aspect_ratio=expected_aspect_ratio,
            aspect_ratio_valid=aspect_ratio_valid,
            fps=fps,
            fps_valid=fps_valid,
            video_codec=video_codec,
            codec_valid=codec_valid,
            has_audio=has_audio,
            audio_valid=audio_valid,
            is_decodable=is_decodable,
            issues=issues,
        )
