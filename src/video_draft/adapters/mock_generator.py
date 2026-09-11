"""Deterministic mock clip generator for fast, offline unit testing."""

import os
from pathlib import Path
from typing import Optional

from video_draft.adapters.base import (
    BaseClipGenerator,
    ClipArtifact,
    ClipGenerationError,
    PermanentGenerationError,
    ProviderUnavailableError,
    TransientGenerationError,
)
from video_draft.assembly.ffmpeg_tools import get_ffmpeg_binary, run_ffmpeg
from video_draft.schema.scene_plan import SceneBeat


class MockClipGenerator(BaseClipGenerator):
    """Deterministic, offline clip generator for unit tests and local verification.

    Generates synthetic video clips without requiring GPU acceleration or network access.
    """

    def __init__(
        self,
        fail_on_scene_id: Optional[str] = None,
        use_real_ffmpeg: bool = True,
        simulate_corrupt_file: bool = False,
        fail_for_models: Optional[set[str]] = None,
        non_retryable_models: Optional[set[str]] = None,
        transient_failures_count: int = 0,
    ) -> None:
        self.fail_on_scene_id = fail_on_scene_id
        self.use_real_ffmpeg = use_real_ffmpeg
        self.simulate_corrupt_file = simulate_corrupt_file
        self.fail_for_models = fail_for_models or set()
        self.non_retryable_models = non_retryable_models or set()
        self.transient_failures_remaining = transient_failures_count
        self.attempt_counts: dict[str, int] = {}

    def generate_clip(
        self,
        beat: SceneBeat,
        model_id: str,
        aspect_ratio: str,
        output_dir: Path,
    ) -> ClipArtifact:
        self.attempt_counts[model_id] = self.attempt_counts.get(model_id, 0) + 1

        # Check transient failure count
        if self.transient_failures_remaining > 0:
            self.transient_failures_remaining -= 1
            raise TransientGenerationError(
                f"Transient simulated glitch during clip rendering for model '{model_id}'",
                scene_id=beat.scene_id,
                model_id=model_id,
            )

        if model_id in self.non_retryable_models:
            raise PermanentGenerationError(
                f"Permanent simulated failure for model '{model_id}'",
                scene_id=beat.scene_id,
                model_id=model_id,
            )

        if model_id in self.fail_for_models:
            raise ClipGenerationError(
                f"Simulated generation failure for model '{model_id}'",
                scene_id=beat.scene_id,
                model_id=model_id,
            )

        if self.fail_on_scene_id and beat.scene_id == self.fail_on_scene_id:
            raise ClipGenerationError(
                f"Simulated generation failure for scene '{beat.scene_id}' with model '{model_id}'",
                scene_id=beat.scene_id,
                model_id=model_id,
            )

        output_dir.mkdir(parents=True, exist_ok=True)
        clip_filename = f"{beat.scene_id}_{model_id.replace('/', '_')}.mp4"
        clip_path = output_dir / clip_filename

        # Resolution based on aspect ratio
        if aspect_ratio == "9:16":
            width, height = 720, 1280
        else:
            width, height = 1280, 720

        fps = 30
        duration = beat.duration_sec

        if self.simulate_corrupt_file:
            # Write a corrupt 0-byte or garbage file
            clip_path.write_bytes(b"CORRUPT_NOT_A_VIDEO")
            asset_hash = ClipArtifact.compute_sha256(clip_path)
            return ClipArtifact(
                scene_id=beat.scene_id,
                scene_index=beat.scene_index,
                asset_path=str(clip_path),
                asset_hash=asset_hash,
                duration_sec=duration,
                width=width,
                height=height,
                fps=fps,
                generator_model=model_id,
                transition_in=beat.transition_in,
                transition_out=beat.transition_out,
                metadata={"mock": True, "corrupt": True},
            )

        # Attempt to create a minimal real MP4 using FFmpeg if requested and available
        created_via_ffmpeg = False
        if self.use_real_ffmpeg:
            try:
                # Use solid color with testsrc or color filter
                # Determine color based on scene index
                colors = ["0x203040", "0x304050", "0x405060", "0x506070", "0x607080"]
                c = colors[(beat.scene_index - 1) % len(colors)]
                lavfi_filter = f"color=c={c}:s={width}x{height}:d={duration}:r={fps}"
                args = [
                    "-y",
                    "-f", "lavfi",
                    "-i", lavfi_filter,
                    "-c:v", "libx264",
                    "-preset", "ultrafast",
                    "-tune", "stillimage",
                    "-pix_fmt", "yuv420p",
                    str(clip_path),
                ]
                run_ffmpeg(args, timeout=30.0)
                created_via_ffmpeg = True
            except Exception:
                created_via_ffmpeg = False

        if not created_via_ffmpeg:
            # Fallback: write deterministic synthetic binary payload if FFmpeg is unavailable
            payload = (
                f"MOCK_MP4_HEADER_SCENE_{beat.scene_id}_DURATION_{duration}_{width}x{height}".encode("utf-8")
                * 20
            )
            clip_path.write_bytes(payload)

        asset_hash = ClipArtifact.compute_sha256(clip_path)

        return ClipArtifact(
            scene_id=beat.scene_id,
            scene_index=beat.scene_index,
            asset_path=str(clip_path),
            asset_hash=asset_hash,
            duration_sec=duration,
            width=width,
            height=height,
            fps=fps,
            generator_model=model_id,
            transition_in=beat.transition_in,
            transition_out=beat.transition_out,
            metadata={
                "mock": True,
                "created_via_ffmpeg": created_via_ffmpeg,
                "visual_prompt": beat.visual_prompt,
            },
        )
