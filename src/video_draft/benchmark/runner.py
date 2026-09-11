"""Benchmark execution engine and synthetic workload harness for draft video pipeline."""

import datetime
import json
from pathlib import Path
import tempfile
import time
from typing import Any, Callable, Dict, List, Optional

from video_draft.adapters.base import BaseClipGenerator, TransientGenerationError, PermanentGenerationError
from video_draft.adapters.mock_generator import MockClipGenerator
from video_draft.adapters.procedural_generator import ProceduralClipGenerator
from video_draft.adapters.reliable_generator import ReliableClipGenerator, RetryPolicy
from video_draft.adapters.validator import ClipValidator
from video_draft.assembly.ffmpeg_assembler import FFmpegAssembler
from video_draft.assembly.timeline_builder import TimelineBuilder
from video_draft.audio.generator import DeterministicAudioGenerator
from video_draft.benchmark.models import (
    AggregateTimings,
    BenchmarkReport,
    BenchmarkRunMetrics,
    StageTimings,
)
from video_draft.evaluation.quality_gate import QualityGate
from video_draft.planner.scene_planner import ScenePlanner
from video_draft.router.router import route
from video_draft.schema.brief import CreativeBrief, SystemConstraints
from video_draft.utils.system_info import get_system_hardware_info


class BenchmarkRunner:
    """Automated benchmark harness measuring stage-by-stage latencies and reliability."""

    def __init__(
        self,
        route_fn: Optional[Callable] = None,
        planner: Optional[ScenePlanner] = None,
        audio_gen: Optional[DeterministicAudioGenerator] = None,
        validator: Optional[ClipValidator] = None,
        quality_gate: Optional[QualityGate] = None,
    ) -> None:
        self.route_fn = route_fn or route
        self.planner = planner or ScenePlanner()
        self.audio_gen = audio_gen or DeterministicAudioGenerator()
        self.validator = validator or ClipValidator()
        self.quality_gate = quality_gate or QualityGate()

    def run_benchmark(
        self,
        brief: Optional[CreativeBrief] = None,
        runs: int = 3,
        mock: bool = True,
        output_dir: Optional[Path] = None,
        synthetic: bool = False,
        progress_callback: Optional[Callable[[int, int, str], None]] = None,
    ) -> BenchmarkReport:
        """Execute benchmark iterations and return structured BenchmarkReport."""
        execution_id = f"bench-{int(time.time())}"
        run_metrics: List[BenchmarkRunMetrics] = []
        archetypes_tested: set = set()
        aspect_ratios_tested: set = set()

        if output_dir:
            output_dir.mkdir(parents=True, exist_ok=True)

        for i in range(runs):
            run_idx = i + 1
            if progress_callback:
                progress_callback(run_idx, runs, "starting")

            # Determine target brief for this iteration
            if synthetic:
                current_brief, failure_injection = self._generate_synthetic_brief(run_idx, runs)
            else:
                current_brief = brief or self._get_default_brief()
                failure_injection = None

            archetypes_tested.add(current_brief.genre)
            aspect_ratios_tested.add(current_brief.aspect_ratio)

            # Execute single iteration inside dedicated directory
            with tempfile.TemporaryDirectory(prefix=f"bench_run_{run_idx}_") as tmp_str:
                run_workdir = Path(tmp_str)
                metrics = self._execute_single_run(
                    run_index=run_idx,
                    brief=current_brief,
                    workdir=run_workdir,
                    mock=mock,
                    failure_injection=failure_injection,
                )
                run_metrics.append(metrics)

            if progress_callback:
                progress_callback(run_idx, runs, "completed" if metrics.success else "failed")

        # Compute aggregate timings and statistics
        successful_runs = [m for m in run_metrics if m.success]
        num_success = len(successful_runs)
        num_failed = len(run_metrics) - num_success

        if num_success > 0:
            avg_timings = AggregateTimings(
                avg_planning_sec=round(sum(m.stage_timings.planning_sec for m in successful_runs) / num_success, 4),
                avg_routing_sec=round(sum(m.stage_timings.routing_sec for m in successful_runs) / num_success, 4),
                avg_audio_sec=round(sum(m.stage_timings.audio_sec for m in successful_runs) / num_success, 4),
                avg_clip_generation_sec=round(sum(m.stage_timings.clip_generation_sec for m in successful_runs) / num_success, 4),
                avg_clip_validation_sec=round(sum(m.stage_timings.clip_validation_sec for m in successful_runs) / num_success, 4),
                avg_assembly_sec=round(sum(m.stage_timings.assembly_sec for m in successful_runs) / num_success, 4),
                avg_evaluation_sec=round(sum(m.stage_timings.evaluation_sec for m in successful_runs) / num_success, 4),
                avg_total_wall_clock_sec=round(sum(m.stage_timings.total_wall_clock_sec for m in successful_runs) / num_success, 4),
            )
            primary_used = sum(1 for m in successful_runs if not m.fallback_used)
            fallback_used = sum(1 for m in successful_runs if m.fallback_used)
            primary_pct = round((primary_used / num_success) * 100.0, 1)
            fallback_pct = round((fallback_used / num_success) * 100.0, 1)
            avg_quality = round(sum(m.quality_score for m in successful_runs) / num_success, 4)
        else:
            avg_timings = AggregateTimings()
            primary_pct = 0.0
            fallback_pct = 0.0
            avg_quality = 0.0

        report = BenchmarkReport(
            execution_id=execution_id,
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            brief_id=brief.id if brief else ("synthetic" if synthetic else "default"),
            synthetic_mode=synthetic,
            runs_requested=runs,
            runs_completed=len(run_metrics),
            runs_successful=num_success,
            runs_failed=num_failed,
            archetypes_tested=sorted(list(archetypes_tested)),
            aspect_ratios_tested=sorted(list(aspect_ratios_tested)),
            primary_model_usage_pct=primary_pct,
            fallback_usage_pct=fallback_pct,
            average_quality_score=avg_quality,
            aggregate_timings=avg_timings,
            system_info=get_system_hardware_info(),
            runs=run_metrics,
        )

        if output_dir:
            out_file = output_dir / "benchmark_report.json"
            out_file.write_text(report.model_dump_json(indent=2), encoding="utf-8")

        return report

    def _execute_single_run(
        self,
        run_index: int,
        brief: CreativeBrief,
        workdir: Path,
        mock: bool,
        failure_injection: Optional[str] = None,
    ) -> BenchmarkRunMetrics:
        """Measure end-to-end execution of a single run with stage isolation."""
        t_total_start = time.perf_counter()
        timings = StageTimings()

        try:
            # 1. Planning
            t0 = time.perf_counter()
            plan = self.planner.plan(brief)
            timings.planning_sec = round(time.perf_counter() - t0, 4)

            # 2. Routing (scene-aware)
            t0 = time.perf_counter()
            decision = self.route_fn(creative_brief=brief, scene_plan=plan, force_cpu=True)
            timings.routing_sec = round(time.perf_counter() - t0, 4)

            # 3. Audio synthesis
            t0 = time.perf_counter()
            audio_path = workdir / "master_narration.wav"
            self.audio_gen.build_narration_track(plan.scenes, audio_path)
            timings.audio_sec = round(time.perf_counter() - t0, 4)

            # 4. Clip generation (with synthetic failure injection if requested)
            t0 = time.perf_counter()
            clips_dir = workdir / "clips"
            clips_dir.mkdir(parents=True, exist_ok=True)

            override_gen = None
            if failure_injection == "transient":
                class TransientMockGen(MockClipGenerator):
                    def __init__(self) -> None:
                        super().__init__()
                        self.attempts = 0

                    def generate_clip(self, beat, model_id, aspect_ratio, output_dir):
                        if beat.scene_index == 1 and self.attempts == 0:
                            self.attempts += 1
                            raise TransientGenerationError("Simulated transient socket timeout")
                        return super().generate_clip(beat, model_id, aspect_ratio, output_dir)

                override_gen = TransientMockGen()

            elif failure_injection == "permanent":
                class PermanentFailMockGen(BaseClipGenerator):
                    def generate_clip(self, beat, model_id, aspect_ratio, output_dir):
                        if model_id != "cpu_procedural_engine":
                            raise PermanentGenerationError(f"Simulated CUDA OOM on model '{model_id}'")
                        return ProceduralClipGenerator().generate_clip(beat, model_id, aspect_ratio, output_dir)

                override_gen = PermanentFailMockGen()

            reliable_gen = ReliableClipGenerator(
                decision=decision,
                mock=mock,
                validator=self.validator,
                allow_cpu_fallback=True,
                retry_policy=RetryPolicy(max_retries=2, backoff_sec=0.01),
                override_generator=override_gen,
            )

            clips = []
            fallback_used_in_run = False
            fallback_model_name = None

            for beat in plan.scenes:
                clip, report = reliable_gen.generate_clip_with_fallback(
                    beat=beat,
                    aspect_ratio=plan.aspect_ratio,
                    output_dir=clips_dir,
                )
                clips.append(clip)
                if report.fallback_occurred:
                    fallback_used_in_run = True
                    fallback_model_name = report.final_model

            timings.clip_generation_sec = round(time.perf_counter() - t0, 4)

            # 5. Clip validation
            t0 = time.perf_counter()
            self.validator.validate_sequence(clips, plan)
            timings.clip_validation_sec = round(time.perf_counter() - t0, 4)

            # 6. Assembly
            t0 = time.perf_counter()
            timeline = TimelineBuilder.build_timeline(plan=plan, clips=clips, audio_artifact=audio_path)
            out_mp4 = workdir / "final_draft.mp4"
            assembler = FFmpegAssembler()
            assembler.assemble_from_timeline(timeline=timeline, output_path=out_mp4)
            timings.assembly_sec = round(time.perf_counter() - t0, 4)

            # 7. Quality Gate Evaluation
            t0 = time.perf_counter()
            qgate_report = self.quality_gate.evaluate_pipeline(
                brief=brief,
                plan=plan,
                decision=decision,
                clips=clips,
                timeline=timeline,
                final_video_path=out_mp4,
                audio_path=audio_path,
                check_decodability=True,
            )
            timings.evaluation_sec = round(time.perf_counter() - t0, 4)
            timings.total_wall_clock_sec = round(time.perf_counter() - t_total_start, 4)

            resolution_str = f"{timeline.resolution.width}x{timeline.resolution.height}"

            return BenchmarkRunMetrics(
                run_index=run_index,
                brief_id=brief.id,
                archetype=brief.genre,
                aspect_ratio=brief.aspect_ratio,
                target_duration_sec=brief.target_duration_sec,
                reproducibility_seed=brief.seed,
                success=True,
                error=None,
                stage_timings=timings,
                num_scenes=len(plan.scenes),
                num_clips_generated=len(clips),
                selected_model=decision.selected_model_name,
                fallback_used=fallback_used_in_run,
                fallback_model=fallback_model_name,
                output_duration_sec=plan.planned_duration_sec,
                output_resolution=resolution_str,
                quality_score=qgate_report.overall_score,
                quality_passed=qgate_report.overall_passed,
            )

        except Exception as err:
            timings.total_wall_clock_sec = round(time.perf_counter() - t_total_start, 4)
            return BenchmarkRunMetrics(
                run_index=run_index,
                brief_id=brief.id,
                archetype=brief.genre,
                aspect_ratio=brief.aspect_ratio,
                target_duration_sec=brief.target_duration_sec,
                reproducibility_seed=brief.seed,
                success=False,
                error=str(err),
                stage_timings=timings,
                num_scenes=0,
                num_clips_generated=0,
                selected_model="unknown",
                fallback_used=False,
                output_duration_sec=0.0,
                output_resolution="unknown",
                quality_score=0.0,
                quality_passed=False,
            )

    def _generate_synthetic_brief(self, run_index: int, total_runs: int) -> tuple[CreativeBrief, Optional[str]]:
        """Generate diverse synthetic creative briefs covering archetypes, ratios, and failure modes."""
        archetypes = ["education", "news", "product"]
        aspect_ratios = ["16:9", "9:16"]

        genre = archetypes[(run_index - 1) % len(archetypes)]
        ar = aspect_ratios[(run_index - 1) % len(aspect_ratios)]
        target_dur = 16.0 if genre == "education" else (18.0 if genre == "news" else 15.0)

        # Synthetic failure scenarios to test reliability
        failure_mode = None
        if total_runs >= 3 and run_index == 2:
            failure_mode = "transient"  # Tests retry
        elif total_runs >= 3 and run_index == 3:
            failure_mode = "permanent"  # Tests fallback chain

        brief = CreativeBrief(
            id=f"synthetic-brief-{run_index:02d}-{genre}",
            title=f"Synthetic Load Test {run_index} ({genre.title()} {ar})",
            genre=genre,
            aspect_ratio=ar,
            target_duration_sec=target_dur,
            script=f"Automated benchmark execution evaluating pipeline resilience and latency for {genre}.",
            seed=42 + run_index,
            constraints=SystemConstraints(
                max_vram_gb=16.0,
                allow_cpu_fallback=True,
                quality_tier="draft",
            ),
        )
        return brief, failure_mode

    def _get_default_brief(self) -> CreativeBrief:
        """Baseline creative brief for non-synthetic benchmarking."""
        return CreativeBrief(
            id="bench-baseline-edu",
            title="Benchmark Baseline Explainer",
            genre="education",
            aspect_ratio="16:9",
            target_duration_sec=16.0,
            script="Mitosis is cell division where chromosomes replicate and divide into two cells.",
            seed=42,
            constraints=SystemConstraints(
                max_vram_gb=16.0,
                allow_cpu_fallback=True,
                quality_tier="draft",
            ),
        )
