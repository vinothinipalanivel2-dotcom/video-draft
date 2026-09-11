"""FFmpeg assembly engine for combining clips, applying transitions, and muxing audio."""

import os
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from video_draft.adapters.base import ClipArtifact
from video_draft.assembly.ffmpeg_tools import (
    AssemblyError,
    FFmpegNotFoundError,
    get_ffmpeg_binary,
    probe_media,
    run_ffmpeg,
)
from video_draft.assembly.timeline_builder import TimelineBuilder
from video_draft.schema.scene_plan import ScenePlan
from video_draft.schema.timeline import Timeline


SUPPORTED_TRANSITIONS = {"fade", "dissolve", "cut", "none", "wipe"}


class FFmpegAssembler:
    """Combines intermediate scene clips, applies scene transitions, and muxes audio into final MP4."""

    def __init__(self, ffmpeg_bin: Optional[str] = None, transition_duration_sec: float = 0.35) -> None:
        self.ffmpeg_bin = ffmpeg_bin
        self.transition_duration_sec = transition_duration_sec

    def _build_clip_video_filter(
        self,
        input_index: int,
        width: int,
        height: int,
        duration: float,
        transition_in: Optional[str],
        transition_out: Optional[str],
    ) -> str:
        """Construct FFmpeg video filter chain for a single clip: scaling, padding, and transitions."""
        # 1. Geometry normalization: scale preserving aspect ratio, pad to exact target resolution
        filter_chain = [
            f"scale={width}:{height}:force_original_aspect_ratio=decrease",
            f"pad={width}:{height}:(ow-iw)/2:(oh-ih)/2",
            "setsar=1",
            "format=yuv420p",
        ]

        t_dur = min(self.transition_duration_sec, max(0.1, duration / 3.0))

        # 2. Transition In
        t_in = (transition_in or "none").lower()
        if t_in not in SUPPORTED_TRANSITIONS:
            raise AssemblyError(f"Unsupported incoming transition effect: '{transition_in}'")

        if t_in in ("fade", "dissolve"):
            filter_chain.append(f"fade=t=in:st=0:d={t_dur:.2f}")

        # 3. Transition Out
        t_out = (transition_out or "none").lower()
        if t_out not in SUPPORTED_TRANSITIONS:
            raise AssemblyError(f"Unsupported outgoing transition effect: '{transition_out}'")

        if t_out in ("fade", "dissolve"):
            fade_start = max(0.0, duration - t_dur)
            filter_chain.append(f"fade=t=out:st={fade_start:.2f}:d={t_dur:.2f}")

        filters_str = ",".join(filter_chain)
        return f"[{input_index}:v]{filters_str}[v{input_index}]"

    def assemble_from_timeline(self, timeline: Timeline, output_path: Union[Path, str]) -> Path:
        """Assemble final video from an editable timeline.json object.

        Args:
            timeline: The validated Timeline specification.
            output_path: Destination path for the assembled MP4.

        Returns:
            Path to the verified output video file.

        Raises:
            AssemblyError: If FFmpeg fails or inputs are invalid.
            FFmpegNotFoundError: If FFmpeg executable is missing.
        """
        if not timeline.video_tracks:
            raise AssemblyError("Timeline contains no video tracks to assemble")

        out_path = Path(output_path)
        out_path.parent.mkdir(parents=True, exist_ok=True)

        target_w = timeline.resolution.width
        target_h = timeline.resolution.height
        num_clips = len(timeline.video_tracks)

        # Validate all clip files exist on disk
        for clip in timeline.video_tracks:
            clip_file = Path(clip.asset_path)
            if not clip_file.is_file():
                raise AssemblyError(
                    f"Missing clip asset file: '{clip.asset_path}' for scene '{clip.scene_id}'"
                )

        # Construct FFmpeg command arguments
        cmd_args: List[str] = ["-y"]
        filter_parts: List[str] = []
        concat_inputs: List[str] = []

        # Add each video input
        for idx, clip in enumerate(timeline.video_tracks):
            cmd_args.extend(["-i", str(clip.asset_path)])
            clip_filter = self._build_clip_video_filter(
                input_index=idx,
                width=target_w,
                height=target_h,
                duration=clip.duration_sec,
                transition_in=clip.transition_in,
                transition_out=clip.transition_out,
            )
            filter_parts.append(clip_filter)
            concat_inputs.append(f"[v{idx}]")

        # Concat filter
        concat_str = f"{''.join(concat_inputs)}concat=n={num_clips}:v=1:a=0[v_out]"
        filter_parts.append(concat_str)

        filter_complex = "; ".join(filter_parts)
        cmd_args.extend(["-filter_complex", filter_complex])

        # Audio track handling
        has_audio = False
        audio_input_idx = num_clips
        if timeline.audio_tracks:
            audio_track = timeline.audio_tracks[0]
            audio_path = Path(audio_track.asset_path)
            if audio_path.is_file():
                cmd_args.extend(["-i", str(audio_path)])
                has_audio = True

        # Mapping and encoding options
        cmd_args.extend(["-map", "[v_out]"])
        if has_audio:
            cmd_args.extend(["-map", f"{audio_input_idx}:a", "-c:a", "aac", "-b:a", "192k"])

        cmd_args.extend([
            "-c:v", "libx264",
            "-preset", "fast",
            "-pix_fmt", "yuv420p",
            "-r", str(timeline.fps),
            "-movflags", "+faststart",
            str(out_path),
        ])

        # Run FFmpeg command
        run_ffmpeg(cmd_args, ffmpeg_bin=self.ffmpeg_bin, timeout=180.0)

        if not out_path.is_file() or out_path.stat().st_size == 0:
            raise AssemblyError(f"FFmpeg assembly completed but output file is missing or empty: {out_path}")

        return out_path

    def assemble_scene_plan(
        self,
        plan: ScenePlan,
        clips: List[ClipArtifact],
        output_path: Union[Path, str],
        audio_artifact: Optional[Union[Path, str, Any]] = None,
    ) -> Path:
        """Assemble video directly from a ScenePlan and list of generated clips."""
        timeline = TimelineBuilder.build_timeline(
            plan=plan,
            clips=clips,
            audio_artifact=audio_artifact,
        )
        return self.assemble_from_timeline(timeline, output_path)
