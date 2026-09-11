"""Procedural CPU fallback clip generator for local video generation."""

import re
from pathlib import Path
from typing import Optional

from video_draft.adapters.base import BaseClipGenerator, ClipArtifact, ClipGenerationError
from video_draft.assembly.ffmpeg_tools import get_ffmpeg_binary, run_ffmpeg
from video_draft.schema.scene_plan import SceneBeat


class ProceduralClipGenerator(BaseClipGenerator):
    """CPU-only procedural video clip generator.

    Uses FFmpeg procedural video filters (lavfi color, testsrc2, drawtext) to generate
    high-quality, standardized draft MP4 clips locally on a non-GPU laptop.
    """

    # Archetype color palettes (hex colors suitable for video backgrounds)
    PALETTES = {
        "education": ["0x1e293b", "0x0f172a", "0x1e3a5f", "0x172554", "0x0d3b66"],
        "news": ["0x3b0764", "0x450a0a", "0x172554", "0x2e1065", "0x4a044e"],
        "product": ["0x18181b", "0x27272a", "0x09090b", "0x1c1917", "0x292524"],
        "default": ["0x1f2937", "0x111827", "0x374151", "0x1e293b", "0x0f172a"],
    }

    def __init__(self, ffmpeg_bin: Optional[str] = None) -> None:
        self.ffmpeg_bin = ffmpeg_bin

    def _sanitize_text_for_ffmpeg(self, text: str) -> str:
        """Sanitize text string for FFmpeg drawtext filter escaping."""
        # Replace colons, single quotes, backslashes, percent signs
        clean = text.replace("\\", "\\\\").replace("'", "").replace(":", "\\:").replace("%", "\\%")
        # Keep length reasonable for video display
        return clean[:45]

    def generate_clip(
        self,
        beat: SceneBeat,
        model_id: str,
        aspect_ratio: str,
        output_dir: Path,
    ) -> ClipArtifact:
        """Procedurally render a video clip for the given scene beat."""
        output_dir.mkdir(parents=True, exist_ok=True)
        clip_filename = f"{beat.scene_id}_{model_id.replace('/', '_')}.mp4"
        clip_path = output_dir / clip_filename

        # Resolution based on target aspect ratio
        if aspect_ratio == "9:16":
            width, height = 720, 1280
            font_size = 36
            overlay_size = 28
        else:
            width, height = 1280, 720
            font_size = 42
            overlay_size = 30

        fps = 30
        duration = round(beat.duration_sec, 3)

        # Select color palette based on beat category or archetype metadata
        palette = self.PALETTES.get(beat.metadata.get("genre", "default"), self.PALETTES["default"])
        bg_color = palette[(beat.scene_index - 1) % len(palette)]

        # Prepare drawtext filters
        sanitized_title = self._sanitize_text_for_ffmpeg(beat.title)
        scene_header = f"Scene {beat.scene_index} - {sanitized_title}"

        filter_parts = [
            f"color=c={bg_color}:s={width}x{height}:d={duration}:r={fps}",
            f"drawtext=text='{scene_header}':fontcolor=white:fontsize={font_size}:x=(w-text_w)/2:y=(h-text_h)/2-40",
        ]

        # Add overlay text if present
        if beat.overlay_text:
            sanitized_overlay = self._sanitize_text_for_ffmpeg(beat.overlay_text)
            filter_parts.append(
                f"drawtext=text='{sanitized_overlay}':fontcolor=yellow:fontsize={overlay_size}:"
                f"x=(w-text_w)/2:y=(h-text_h)/2+40:box=1:boxcolor=black@0.5:boxborderw=8"
            )

        lavfi_filter = ",".join(filter_parts)

        cmd_args = [
            "-y",
            "-f", "lavfi",
            "-i", lavfi_filter,
            "-c:v", "libx264",
            "-preset", "ultrafast",
            "-pix_fmt", "yuv420p",
            "-r", str(fps),
            "-t", str(duration),
            str(clip_path),
        ]

        try:
            run_ffmpeg(cmd_args, ffmpeg_bin=self.ffmpeg_bin, timeout=45.0)
        except Exception as err:
            # If drawtext failed due to missing font engine, fallback to pure solid color
            fallback_args = [
                "-y",
                "-f", "lavfi",
                "-i", f"color=c={bg_color}:s={width}x{height}:d={duration}:r={fps}",
                "-c:v", "libx264",
                "-preset", "ultrafast",
                "-pix_fmt", "yuv420p",
                "-r", str(fps),
                "-t", str(duration),
                str(clip_path),
            ]
            try:
                run_ffmpeg(fallback_args, ffmpeg_bin=self.ffmpeg_bin, timeout=45.0)
            except Exception as nested_err:
                raise ClipGenerationError(
                    f"Procedural clip generation failed for scene '{beat.scene_id}': {nested_err}",
                    scene_id=beat.scene_id,
                    model_id=model_id,
                ) from nested_err

        if not clip_path.is_file() or clip_path.stat().st_size == 0:
            raise ClipGenerationError(
                f"Procedural clip generator did not produce a valid file at {clip_path}",
                scene_id=beat.scene_id,
                model_id=model_id,
            )

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
                "procedural": True,
                "engine": "cpu_procedural_engine",
                "bg_color": bg_color,
                "aspect_ratio": aspect_ratio,
            },
        )
