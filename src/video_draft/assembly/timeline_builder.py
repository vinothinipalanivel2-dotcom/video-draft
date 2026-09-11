"""Builder and serializer for timeline.json representations."""

import json
from pathlib import Path
from typing import List, Optional, Union

from video_draft.adapters.base import ClipArtifact
from video_draft.audio.generator import AudioArtifact
from video_draft.schema.scene_plan import ScenePlan
from video_draft.schema.timeline import AudioTrack, Resolution, SceneClip, SubtitleTrack, Timeline


class TimelineBuilder:
    """Constructs editable timeline.json artifacts from ScenePlan and generated media clips."""

    @staticmethod
    def build_timeline(
        plan: ScenePlan,
        clips: List[ClipArtifact],
        audio_artifact: Optional[Union[Path, str, AudioArtifact]] = None,
        fps: int = 30,
    ) -> Timeline:
        """Construct a validated Timeline instance from a ScenePlan and its generated clips.

        Args:
            plan: The authoritative ScenePlan.
            clips: Ordered list of validated ClipArtifact objects.
            audio_artifact: Optional master audio track path or AudioArtifact.
            fps: Frame rate for the final timeline (default: 30).

        Returns:
            Timeline model instance ready for serialization or assembly.
        """
        if len(clips) != len(plan.scenes):
            raise ValueError(
                f"Mismatch: plan defines {len(plan.scenes)} scenes, but {len(clips)} clips were provided"
            )

        if plan.aspect_ratio == "9:16":
            res = Resolution(width=720, height=1280)
        else:
            res = Resolution(width=1280, height=720)

        video_tracks: List[SceneClip] = []
        for beat, clip in zip(plan.scenes, clips):
            video_tracks.append(
                SceneClip(
                    scene_id=clip.scene_id,
                    scene_index=clip.scene_index,
                    prompt=beat.visual_prompt,
                    start_sec=beat.start_sec,
                    end_sec=beat.end_sec,
                    duration_sec=clip.duration_sec,
                    asset_path=clip.asset_path,
                    asset_hash=clip.asset_hash,
                    generator_model=clip.generator_model,
                    transition_in=clip.transition_in,
                    transition_out=clip.transition_out,
                )
            )

        audio_tracks: List[AudioTrack] = []
        if audio_artifact:
            if isinstance(audio_artifact, AudioArtifact):
                audio_tracks.append(
                    AudioTrack(
                        track_id=audio_artifact.track_id,
                        asset_path=str(audio_artifact.asset_path),
                        start_sec=audio_artifact.start_sec,
                        duration_sec=audio_artifact.duration_sec,
                        volume=1.0,
                    )
                )
            else:
                audio_path = Path(audio_artifact)
                audio_tracks.append(
                    AudioTrack(
                        track_id="master_narration",
                        asset_path=str(audio_path),
                        start_sec=0.0,
                        duration_sec=plan.planned_duration_sec,
                        volume=1.0,
                    )
                )

        return Timeline(
            version="1.0.0",
            brief_id=plan.brief_id,
            total_duration_sec=round(plan.planned_duration_sec, 3),
            fps=fps,
            resolution=res,
            video_tracks=video_tracks,
            audio_tracks=audio_tracks,
            subtitle_tracks=[],
        )

    @staticmethod
    def save_timeline(timeline: Timeline, output_path: Union[Path, str]) -> Path:
        """Serialize a Timeline instance to timeline.json."""
        out = Path(output_path)
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(timeline.model_dump_json(indent=2), encoding="utf-8")
        return out

    @staticmethod
    def load_timeline(input_path: Union[Path, str]) -> Timeline:
        """Deserialize and validate a Timeline instance from timeline.json."""
        path = Path(input_path)
        if not path.is_file():
            raise FileNotFoundError(f"Timeline file not found: {path}")
        raw = path.read_text(encoding="utf-8")
        data = json.loads(raw)
        return Timeline(**data)
