"""Cross-artifact consistency checker verifying integrity across all pipeline stages."""

from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from video_draft.adapters.base import ClipArtifact
from video_draft.assembly.ffmpeg_tools import probe_media
from video_draft.evaluation.models import ConsistencyReport
from video_draft.schema.brief import CreativeBrief
from video_draft.schema.routing import RouteDecision
from video_draft.schema.scene_plan import ScenePlan
from video_draft.schema.timeline import Timeline


class CrossArtifactConsistencyChecker:
    """Verifies end-to-end consistency across CreativeBrief, ScenePlan, Clips, Timeline, Audio, and Video."""

    def __init__(self, duration_tolerance_sec: float = 0.5) -> None:
        self.duration_tolerance_sec = duration_tolerance_sec

    def check_consistency(
        self,
        brief: CreativeBrief,
        plan: ScenePlan,
        clips: List[ClipArtifact],
        timeline: Timeline,
        final_video_path: Optional[Union[Path, str]] = None,
        final_video_duration: Optional[float] = None,
        audio_path: Optional[Union[Path, str]] = None,
        route_decision: Optional[RouteDecision] = None,
    ) -> ConsistencyReport:
        """Run all cross-artifact consistency checks and produce ConsistencyReport.

        Args:
            brief: Original creative brief.
            plan: Decomposed scene plan.
            clips: Intermediate synthesized clip artifacts.
            timeline: Assembled timeline specification.
            final_video_path: Optional path to assembled MP4.
            final_video_duration: Optional explicit duration in seconds of the final video.
            audio_path: Optional path to narration audio track.
            route_decision: Optional model route decision artifact.

        Returns:
            ConsistencyReport detailing all consistency evaluations.
        """
        issues: List[str] = []
        details: Dict[str, Any] = {}

        # 1. Scene count consistency
        num_plan_scenes = len(plan.scenes)
        num_clips = len(clips)
        num_tracks = len(timeline.video_tracks)
        scene_count_match = (num_plan_scenes == num_clips == num_tracks)
        if not scene_count_match:
            issues.append(
                f"Scene count mismatch: plan={num_plan_scenes}, generated_clips={num_clips}, timeline_tracks={num_tracks}"
            )
        details["scene_counts"] = {"plan": num_plan_scenes, "clips": num_clips, "timeline": num_tracks}

        # 2. Scene IDs and ordering consistency
        plan_scene_ids = [s.scene_id for s in plan.scenes]
        clip_scene_ids = [c.scene_id for c in clips]
        timeline_scene_ids = [t.scene_id for t in timeline.video_tracks]

        scene_ids_match = (plan_scene_ids == clip_scene_ids == timeline_scene_ids)
        if not scene_ids_match:
            issues.append(
                f"Scene ID mismatch across stages: plan={plan_scene_ids}, clips={clip_scene_ids}, timeline={timeline_scene_ids}"
            )

        # Ordering check: indices strictly 1..N
        plan_indices = [s.scene_index for s in plan.scenes]
        clip_indices = [c.scene_index for c in clips]
        timeline_indices = [t.scene_index for t in timeline.video_tracks]
        expected_indices = list(range(1, num_plan_scenes + 1))

        scene_ordering_valid = (
            plan_indices == expected_indices
            and clip_indices == expected_indices
            and timeline_indices == expected_indices
        )
        if not scene_ordering_valid:
            issues.append(
                f"Scene ordering anomaly: expected 1..{num_plan_scenes}, got plan={plan_indices}, clips={clip_indices}"
            )

        # 3. Duration alignment
        plan_duration = plan.planned_duration_sec
        clips_total_dur = sum(c.duration_sec for c in clips)
        timeline_total_dur = getattr(timeline, "total_duration_sec", getattr(timeline, "total_duration", 0.0))

        dur_drift_clips = abs(plan_duration - clips_total_dur)
        dur_drift_timeline = abs(plan_duration - timeline_total_dur)

        duration_alignment_valid = (
            dur_drift_clips <= self.duration_tolerance_sec
            and dur_drift_timeline <= self.duration_tolerance_sec
        )

        video_dur = final_video_duration
        if video_dur is None and final_video_path and Path(final_video_path).is_file():
            try:
                probe = probe_media(final_video_path)
                dur = probe.get("duration", 0.0)
                if dur and dur > 0.0:
                    video_dur = dur
            except Exception:
                pass

        if video_dur is not None and video_dur > 0:
            drift_vid = abs(plan_duration - video_dur)
            if drift_vid > self.duration_tolerance_sec:
                duration_alignment_valid = False
                issues.append(
                    f"Final video duration drift: actual={video_dur:.2f}s, planned={plan_duration:.2f}s "
                    f"(drift={drift_vid:.2f}s exceeds tolerance={self.duration_tolerance_sec:.2f}s)"
                )

        if dur_drift_clips > self.duration_tolerance_sec:
            issues.append(
                f"Clips total duration drift: clips={clips_total_dur:.2f}s, plan={plan_duration:.2f}s "
                f"(drift={dur_drift_clips:.2f}s)"
            )
        if dur_drift_timeline > self.duration_tolerance_sec:
            issues.append(
                f"Timeline total duration drift: timeline={timeline_total_dur:.2f}s, plan={plan_duration:.2f}s "
                f"(drift={dur_drift_timeline:.2f}s)"
            )

        details["durations"] = {
            "plan_sec": plan_duration,
            "clips_total_sec": round(clips_total_dur, 2),
            "timeline_sec": round(timeline_total_dur, 2),
            "video_sec": video_dur,
        }

        # 4. Audio alignment
        audio_alignment_valid = True
        if audio_path and Path(audio_path).is_file():
            try:
                probe_aud = probe_media(audio_path)
                audio_dur = probe_aud.get("duration", 0.0)
                details["audio_sec"] = audio_dur
                # Audio duration should be at least within 0.5s of planned duration
                if audio_dur < (plan_duration - self.duration_tolerance_sec):
                    audio_alignment_valid = False
                    issues.append(
                        f"Audio narration too short: audio={audio_dur:.2f}s, plan={plan_duration:.2f}s"
                    )
            except Exception as err:
                audio_alignment_valid = False
                issues.append(f"Failed to probe audio artifact: {err}")
        else:
            # If no audio provided but timeline expects audio tracks
            if len(timeline.audio_tracks) > 0:
                audio_alignment_valid = False
                issues.append("Timeline references audio tracks but master audio file is missing")

        # 5. Timeline boundary continuity
        timeline_continuity_valid = True
        if timeline.video_tracks:
            t0_start = getattr(timeline.video_tracks[0], "start_sec", getattr(timeline.video_tracks[0], "timeline_start_sec", 0.0))
            if abs(t0_start) > 0.05:
                timeline_continuity_valid = False
                issues.append(
                    f"Timeline does not start at 0.0s (first track starts at {t0_start}s)"
                )

            for i in range(len(timeline.video_tracks) - 1):
                curr_end = getattr(timeline.video_tracks[i], "end_sec", getattr(timeline.video_tracks[i], "timeline_end_sec", 0.0))
                next_start = getattr(timeline.video_tracks[i + 1], "start_sec", getattr(timeline.video_tracks[i + 1], "timeline_start_sec", 0.0))
                gap = abs(next_start - curr_end)
                if gap > 0.05:
                    timeline_continuity_valid = False
                    issues.append(
                        f"Timeline discontinuity between track {i+1} and {i+2}: gap/overlap of {gap:.3f}s"
                    )

        # 6. Aspect Ratio & Dimensions consistency
        brief_ar = brief.aspect_ratio
        plan_ar = plan.aspect_ratio
        tl_ar = "9:16" if (timeline.resolution.height > timeline.resolution.width) else "16:9"
        aspect_ratio_consistent = (brief_ar == plan_ar == tl_ar)
        if not aspect_ratio_consistent:
            issues.append(
                f"Aspect ratio conflict: brief={brief_ar}, plan={plan_ar}, timeline_resolution={tl_ar}"
            )

        # 7. Model Provenance consistency
        provenance_consistent = True
        if route_decision:
            allowed_models = {
                route_decision.selected_model,
                route_decision.fallback_model,
                "cpu_procedural_engine",
                "mock",
                "mock_model",
            }
            if route_decision.fallback_chain:
                allowed_models.update(route_decision.fallback_chain)

            for c in clips:
                gen_m = c.generator_model
                if gen_m not in allowed_models:
                    provenance_consistent = False
                    issues.append(
                        f"Clip '{c.scene_id}' generated by unexpected model '{gen_m}' (not in routing decision)"
                    )
        details["clip_provenance"] = [c.generator_model for c in clips]

        is_consistent = (
            scene_count_match
            and scene_ids_match
            and scene_ordering_valid
            and duration_alignment_valid
            and audio_alignment_valid
            and timeline_continuity_valid
            and aspect_ratio_consistent
            and provenance_consistent
        )

        return ConsistencyReport(
            is_consistent=is_consistent,
            scene_count_match=scene_count_match,
            scene_ids_match=scene_ids_match,
            scene_ordering_valid=scene_ordering_valid,
            duration_alignment_valid=duration_alignment_valid,
            audio_alignment_valid=audio_alignment_valid,
            timeline_continuity_valid=timeline_continuity_valid,
            aspect_ratio_consistent=aspect_ratio_consistent,
            provenance_consistent=provenance_consistent,
            issues=issues,
            details=details,
        )
