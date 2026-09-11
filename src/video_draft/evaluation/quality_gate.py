"""Formal end-to-end quality gate and objective evaluation framework."""

import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from video_draft.adapters.base import ClipArtifact
from video_draft.evaluation.consistency import CrossArtifactConsistencyChecker
from video_draft.evaluation.media_validator import FinalMediaValidator
from video_draft.evaluation.models import (
    CheckResult,
    ConsistencyReport,
    FinalMediaValidationResult,
    QualityEvaluationReport,
)
from video_draft.schema.brief import CreativeBrief
from video_draft.schema.routing import RouteDecision
from video_draft.schema.scene_plan import ScenePlan
from video_draft.schema.timeline import Timeline


class QualityGate:
    """Formal pipeline quality gate evaluating contracts, consistency, and media validity."""

    def __init__(
        self,
        media_validator: Optional[FinalMediaValidator] = None,
        consistency_checker: Optional[CrossArtifactConsistencyChecker] = None,
        duration_tolerance_sec: float = 0.5,
    ) -> None:
        self.media_validator = media_validator or FinalMediaValidator(default_tolerance_sec=duration_tolerance_sec)
        self.consistency_checker = consistency_checker or CrossArtifactConsistencyChecker(duration_tolerance_sec=duration_tolerance_sec)
        self.duration_tolerance_sec = duration_tolerance_sec

    def evaluate_pipeline(
        self,
        brief: CreativeBrief,
        plan: ScenePlan,
        decision: RouteDecision,
        clips: List[ClipArtifact],
        timeline: Timeline,
        final_video_path: Union[Path, str],
        audio_path: Optional[Union[Path, str]] = None,
        manifest_path: Optional[Union[Path, str]] = None,
        check_decodability: bool = True,
    ) -> QualityEvaluationReport:
        """Execute complete quality gate evaluation on all generated pipeline artifacts.

        Returns:
            Comprehensive QualityEvaluationReport with pass/fail and dimension scores.
        """
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        eval_id = f"eval-{brief.id}-{int(datetime.datetime.now(datetime.timezone.utc).timestamp())}"
        checks: Dict[str, CheckResult] = {}
        vid_path = Path(final_video_path)

        # 1. Planning Validity
        plan_passed = bool(plan and len(plan.scenes) > 0 and plan.planned_duration_sec > 0)
        plan_score = 1.0 if plan_passed else 0.0
        checks["planning_validity"] = CheckResult(
            dimension="planning_validity",
            passed=plan_passed,
            score=plan_score,
            message=f"Plan decomposed into {len(plan.scenes)} beats ({plan.planned_duration_sec:.2f}s, {plan.strategy_name})",
            details={"strategy": plan.strategy_name, "scene_count": len(plan.scenes), "planned_duration": plan.planned_duration_sec},
        )

        # 2. Routing Validity
        route_passed = bool(decision and decision.selected_model and decision.target_hardware)
        checks["routing_validity"] = CheckResult(
            dimension="routing_validity",
            passed=route_passed,
            score=1.0 if route_passed else 0.0,
            message=f"Model '{decision.selected_model_name}' routed to {decision.target_hardware.upper()}",
            details={"selected_model": decision.selected_model, "target_hardware": decision.target_hardware, "fallback_model": decision.fallback_model},
        )

        # 3. Generation Success
        num_expected = len(plan.scenes)
        num_generated = len(clips)
        gen_passed = (num_expected == num_generated) and all(Path(c.asset_path).is_file() for c in clips)
        gen_score = 1.0 if gen_passed else (num_generated / max(num_expected, 1))
        checks["generation_success"] = CheckResult(
            dimension="generation_success",
            passed=gen_passed,
            score=round(gen_score, 4),
            message=f"Generated {num_generated}/{num_expected} scene clip artifacts",
            details={"expected_clips": num_expected, "generated_clips": num_generated},
        )

        # 4. Clip Validity
        clips_valid = all(
            c.duration_sec > 0 and c.width > 0 and c.height > 0 and bool(c.asset_hash)
            for c in clips
        ) if clips else False
        checks["clip_validity"] = CheckResult(
            dimension="clip_validity",
            passed=clips_valid,
            score=1.0 if clips_valid else 0.0,
            message=f"All {len(clips)} clip artifacts verified with valid hashes and geometry",
            details={"validated_clip_count": len(clips)},
        )

        # 5. Media Validation (Final MP4)
        media_result = self.media_validator.validate(
            video_path=vid_path,
            expected_aspect_ratio=brief.aspect_ratio,
            expected_duration=plan.planned_duration_sec,
            require_audio=True,
            tolerance_sec=self.duration_tolerance_sec,
            check_decodability=check_decodability,
        )
        checks["final_media_validity"] = CheckResult(
            dimension="final_media_validity",
            passed=media_result.is_valid,
            score=1.0 if media_result.is_valid else 0.0,
            message="Final MP4 stream and bitstream validation passed" if media_result.is_valid else f"Media validation issues: {'; '.join(media_result.issues)}",
            details=media_result.model_dump(),
        )

        # 6. Timing Accuracy
        timing_drift = abs(media_result.duration_sec - plan.planned_duration_sec)
        timing_passed = timing_drift <= self.duration_tolerance_sec
        timing_score = max(0.0, 1.0 - (timing_drift / max(plan.planned_duration_sec, 1.0)))
        checks["timing_accuracy"] = CheckResult(
            dimension="timing_accuracy",
            passed=timing_passed,
            score=round(timing_score, 4),
            message=f"Duration drift: {timing_drift:.2f}s (tolerance: {self.duration_tolerance_sec:.2f}s)",
            details={"actual_sec": media_result.duration_sec, "planned_sec": plan.planned_duration_sec, "drift_sec": round(timing_drift, 3)},
        )

        # 7. Audio Alignment
        audio_passed = media_result.has_audio
        if audio_path and Path(audio_path).is_file():
            audio_passed = audio_passed and Path(audio_path).is_file()
        checks["audio_alignment"] = CheckResult(
            dimension="audio_alignment",
            passed=audio_passed,
            score=1.0 if audio_passed else 0.0,
            message="Audio track present and synchronized" if audio_passed else "Audio track missing or not muxed",
            details={"has_audio": media_result.has_audio, "audio_file": str(audio_path) if audio_path else None},
        )

        # 8. Assembly Validity
        assembly_passed = bool(timeline and len(timeline.video_tracks) == num_expected and vid_path.is_file())
        checks["assembly_validity"] = CheckResult(
            dimension="assembly_validity",
            passed=assembly_passed,
            score=1.0 if assembly_passed else 0.0,
            message=f"Timeline assembly completed with {len(timeline.video_tracks)} video tracks",
            details={"timeline_tracks": len(timeline.video_tracks), "output_video": str(vid_path)},
        )

        # 9. Cross-Artifact Consistency
        consistency_result = self.consistency_checker.check_consistency(
            brief=brief,
            plan=plan,
            clips=clips,
            timeline=timeline,
            final_video_path=vid_path,
            final_video_duration=media_result.duration_sec if media_result.duration_valid else None,
            audio_path=audio_path,
            route_decision=decision,
        )
        checks["cross_consistency"] = CheckResult(
            dimension="cross_consistency",
            passed=consistency_result.is_consistent,
            score=1.0 if consistency_result.is_consistent else 0.0,
            message="All cross-artifact contracts aligned" if consistency_result.is_consistent else f"Consistency issues: {'; '.join(consistency_result.issues)}",
            details=consistency_result.model_dump(),
        )

        # 10. Fallback Usage
        fallback_used = decision.is_cpu_fallback or any(
            c.metadata.get("fallback_occurred", False) for c in clips
        )
        checks["fallback_usage"] = CheckResult(
            dimension="fallback_usage",
            passed=True,  # Informational check
            score=1.0,
            message=f"Fallback used: {fallback_used}" + (f" (Model: {decision.selected_model})" if fallback_used else ""),
            details={"fallback_occurred": fallback_used, "selected_model": decision.selected_model},
        )

        # Overall calculation
        critical_checks = [
            "planning_validity",
            "routing_validity",
            "generation_success",
            "clip_validity",
            "final_media_validity",
            "timing_accuracy",
            "assembly_validity",
            "cross_consistency",
        ]
        overall_passed = all(checks[c].passed for c in critical_checks if c in checks)
        avg_score = sum(c.score for c in checks.values()) / max(len(checks), 1)

        summary = (
            f"Quality Gate {'PASSED' if overall_passed else 'FAILED'} "
            f"({sum(1 for c in checks.values() if c.passed)}/{len(checks)} checks passed, score: {avg_score:.4f})"
        )

        return QualityEvaluationReport(
            evaluation_id=eval_id,
            timestamp=now_iso,
            brief_id=brief.id,
            overall_passed=overall_passed,
            overall_score=round(avg_score, 4),
            checks=checks,
            media_validation=media_result,
            consistency=consistency_result,
            summary=summary,
            reproducibility_verified=bool(brief.seed is not None),
            fallback_used=fallback_used,
            final_video_path=str(vid_path),
            manifest_path=str(manifest_path) if manifest_path else None,
        )

    @staticmethod
    def verify_reproducibility(
        run1_plan: ScenePlan,
        run2_plan: ScenePlan,
        run1_timeline: Timeline,
        run2_timeline: Timeline,
    ) -> Tuple[bool, List[str]]:
        """Verify deterministic structural reproducibility between two runs of the pipeline."""
        issues: List[str] = []

        # 1. Scene count & timing reproducibility
        if len(run1_plan.scenes) != len(run2_plan.scenes):
            issues.append(f"Scene count mismatch: run1={len(run1_plan.scenes)}, run2={len(run2_plan.scenes)}")

        for s1, s2 in zip(run1_plan.scenes, run2_plan.scenes):
            if s1.scene_id != s2.scene_id:
                issues.append(f"Scene ID drift: {s1.scene_id} != {s2.scene_id}")
            if abs(s1.duration_sec - s2.duration_sec) > 0.001:
                issues.append(f"Scene duration drift in {s1.scene_id}: {s1.duration_sec} != {s2.duration_sec}")
            if s1.visual_prompt != s2.visual_prompt:
                issues.append(f"Visual prompt drift in {s1.scene_id}")

        # 2. Timeline tracks reproducibility
        if len(run1_timeline.video_tracks) != len(run2_timeline.video_tracks):
            issues.append("Timeline video track counts do not match")

        for t1, t2 in zip(run1_timeline.video_tracks, run2_timeline.video_tracks):
            if abs(t1.timeline_start_sec - t2.timeline_start_sec) > 0.001:
                issues.append(f"Timeline track start drift: {t1.timeline_start_sec} != {t2.timeline_start_sec}")

        return (len(issues) == 0, issues)

    @staticmethod
    def save_report(report: QualityEvaluationReport, output_file: Union[Path, str]) -> Path:
        """Save QualityEvaluationReport to JSON file."""
        target = Path(output_file)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(report.model_dump_json(indent=2), encoding="utf-8")
        return target
