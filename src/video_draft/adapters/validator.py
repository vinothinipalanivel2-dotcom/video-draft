"""Validation layer for generated video clip artifacts."""

from pathlib import Path
from typing import Any, Dict, List, Optional

from video_draft.adapters.base import ClipArtifact
from video_draft.assembly.ffmpeg_tools import probe_media
from video_draft.schema.scene_plan import SceneBeat, ScenePlan


class ClipValidationError(Exception):
    """Raised when a generated video clip fails quality, duration, or schema validation."""

    def __init__(
        self,
        message: str,
        scene_id: Optional[str] = None,
        scene_index: Optional[int] = None,
        field: Optional[str] = None,
    ) -> None:
        super().__init__(message)
        self.scene_id = scene_id
        self.scene_index = scene_index
        self.field = field


class ClipValidator:
    """Validates intermediate video clips prior to FFmpeg timeline assembly."""

    def __init__(self, probe_media_streams: bool = True) -> None:
        self.probe_media_streams = probe_media_streams

    def validate_clip(
        self,
        clip: ClipArtifact,
        expected_beat: SceneBeat,
        expected_aspect_ratio: str,
        tolerance_sec: float = 0.35,
    ) -> Dict[str, Any]:
        """Validate a single clip artifact against its corresponding SceneBeat.

        Args:
            clip: Generated clip artifact.
            expected_beat: Planned scene beat specification.
            expected_aspect_ratio: "16:9" or "9:16".
            tolerance_sec: Allowable duration drift due to video container/encoder frame boundaries.

        Returns:
            Dictionary with validation status and probed media attributes.

        Raises:
            ClipValidationError: If any validation rule is violated.
        """
        asset_path = Path(clip.asset_path)

        # 1. File existence
        if not asset_path.exists():
            raise ClipValidationError(
                f"Clip file does not exist at '{clip.asset_path}' for scene '{clip.scene_id}'",
                scene_id=clip.scene_id,
                scene_index=clip.scene_index,
                field="file_existence",
            )

        # 2. Non-empty file / corrupt artifact
        file_size = asset_path.stat().st_size
        if file_size < 128:
            raise ClipValidationError(
                f"Clip file at '{clip.asset_path}' is empty or too small ({file_size} bytes) for scene '{clip.scene_id}'",
                scene_id=clip.scene_id,
                scene_index=clip.scene_index,
                field="file_size",
            )

        # 3. Scene identity & indexing
        if clip.scene_id != expected_beat.scene_id:
            raise ClipValidationError(
                f"Clip scene_id '{clip.scene_id}' does not match expected scene_id '{expected_beat.scene_id}'",
                scene_id=clip.scene_id,
                scene_index=clip.scene_index,
                field="scene_id",
            )

        if clip.scene_index != expected_beat.scene_index:
            raise ClipValidationError(
                f"Clip scene_index {clip.scene_index} does not match expected {expected_beat.scene_index}",
                scene_id=clip.scene_id,
                scene_index=clip.scene_index,
                field="scene_index",
            )

        # 4. Duration check against planned authoritative beat duration
        duration_diff = abs(clip.duration_sec - expected_beat.duration_sec)
        if duration_diff > tolerance_sec:
            raise ClipValidationError(
                f"Clip duration {clip.duration_sec:.2f}s differs from planned duration {expected_beat.duration_sec:.2f}s "
                f"by {duration_diff:.2f}s (tolerance: {tolerance_sec:.2f}s) for scene '{clip.scene_id}'",
                scene_id=clip.scene_id,
                scene_index=clip.scene_index,
                field="duration",
            )

        # 5. Aspect ratio check
        if expected_aspect_ratio == "16:9":
            if clip.width < clip.height:
                raise ClipValidationError(
                    f"Aspect ratio mismatch for scene '{clip.scene_id}': expected 16:9 landscape, "
                    f"got {clip.width}x{clip.height}",
                    scene_id=clip.scene_id,
                    scene_index=clip.scene_index,
                    field="aspect_ratio",
                )
        elif expected_aspect_ratio == "9:16":
            if clip.height < clip.width:
                raise ClipValidationError(
                    f"Aspect ratio mismatch for scene '{clip.scene_id}': expected 9:16 portrait, "
                    f"got {clip.width}x{clip.height}",
                    scene_id=clip.scene_id,
                    scene_index=clip.scene_index,
                    field="aspect_ratio",
                )

        # 6. Frame rate
        if clip.fps < 10:
            raise ClipValidationError(
                f"Invalid frame rate {clip.fps} fps for scene '{clip.scene_id}'",
                scene_id=clip.scene_id,
                scene_index=clip.scene_index,
                field="fps",
            )

        # 7. Readable media stream inspection (if enabled and file is real media)
        probed_info: Dict[str, Any] = {}
        if self.probe_media_streams and not clip.metadata.get("mock"):
            try:
                probed = probe_media(asset_path)
                probed_info = probed
                if probed.get("duration", 0.0) > 0.0:
                    stream_dur_diff = abs(probed["duration"] - expected_beat.duration_sec)
                    if stream_dur_diff > tolerance_sec:
                        raise ClipValidationError(
                            f"Probed media stream duration ({probed['duration']:.2f}s) differs from planned "
                            f"duration ({expected_beat.duration_sec:.2f}s) for scene '{clip.scene_id}'",
                            scene_id=clip.scene_id,
                            scene_index=clip.scene_index,
                            field="media_stream_duration",
                        )
            except Exception as err:
                if isinstance(err, ClipValidationError):
                    raise
                # Probe failure on real media indicates corrupt video file
                raise ClipValidationError(
                    f"Failed to decode media stream for scene '{clip.scene_id}': {err}",
                    scene_id=clip.scene_id,
                    scene_index=clip.scene_index,
                    field="media_stream_decode",
                ) from err

        return {
            "scene_id": clip.scene_id,
            "scene_index": clip.scene_index,
            "status": "valid",
            "file_size": file_size,
            "probed": probed_info,
        }

    def validate_sequence(
        self,
        clips: List[ClipArtifact],
        plan: ScenePlan,
        tolerance_sec: float = 0.50,
    ) -> bool:
        """Validate entire ordered sequence of clips against the ScenePlan.

        Args:
            clips: Ordered list of clip artifacts.
            plan: The authoritative ScenePlan.
            tolerance_sec: Allowable cumulative duration drift.

        Returns:
            True if entire sequence passes all validation constraints.

        Raises:
            ClipValidationError: If sequence continuity or completeness fails.
        """
        if len(clips) != len(plan.scenes):
            raise ClipValidationError(
                f"Clip count mismatch: ScenePlan defines {len(plan.scenes)} scenes, but received {len(clips)} clips",
                field="clip_count",
            )

        cumulative_duration = 0.0
        for expected_index, (clip, beat) in enumerate(zip(clips, plan.scenes), start=1):
            if clip.scene_index != expected_index:
                raise ClipValidationError(
                    f"Disordered clips: expected index {expected_index}, got {clip.scene_index} (scene '{clip.scene_id}')",
                    scene_id=clip.scene_id,
                    scene_index=clip.scene_index,
                    field="sequence_order",
                )
            if clip.scene_id != beat.scene_id:
                raise ClipValidationError(
                    f"Scene alignment mismatch: expected '{beat.scene_id}', got '{clip.scene_id}' at index {expected_index}",
                    scene_id=clip.scene_id,
                    scene_index=clip.scene_index,
                    field="scene_alignment",
                )
            # Individual clip validation
            self.validate_clip(clip, beat, plan.aspect_ratio)
            cumulative_duration += clip.duration_sec

        # Cumulative duration check
        total_diff = abs(cumulative_duration - plan.planned_duration_sec)
        if total_diff > tolerance_sec:
            raise ClipValidationError(
                f"Total cumulative clips duration ({cumulative_duration:.2f}s) differs from planned duration "
                f"({plan.planned_duration_sec:.2f}s) by {total_diff:.2f}s (tolerance: {tolerance_sec:.2f}s)",
                field="cumulative_duration",
            )

        return True
