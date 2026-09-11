"""Unit tests for pipeline benchmark runner, metrics, and CLI invocation."""

import json
from pathlib import Path
import pytest
from click.testing import CliRunner

from video_draft.benchmark.models import BenchmarkReport, BenchmarkRunMetrics
from video_draft.benchmark.runner import BenchmarkRunner
from video_draft.cli import main
from video_draft.schema.brief import CreativeBrief, SystemConstraints


@pytest.fixture
def sample_brief() -> CreativeBrief:
    return CreativeBrief(
        id="bench-test-brief",
        title="Benchmark Test Explainer",
        genre="education",
        aspect_ratio="16:9",
        target_duration_sec=16.0,
        script="Cell division through mitosis duplicates chromosomes into two daughter cells.",
        seed=42,
        constraints=SystemConstraints(
            max_vram_gb=16.0,
            allow_cpu_fallback=True,
            quality_tier="draft",
        ),
    )


def test_benchmark_runner_single_run(sample_brief: CreativeBrief, tmp_path: Path):
    """Verify BenchmarkRunner executes a single iteration and records all stages."""
    runner = BenchmarkRunner()
    out_dir = tmp_path / "bench_out"
    report = runner.run_benchmark(brief=sample_brief, runs=1, mock=True, output_dir=out_dir)

    assert isinstance(report, BenchmarkReport)
    assert report.runs_requested == 1
    assert report.runs_completed == 1
    assert report.runs_successful == 1
    assert report.runs_failed == 0
    assert report.average_quality_score >= 0.95
    assert (out_dir / "benchmark_report.json").is_file()

    # Timing metrics sanity
    timings = report.aggregate_timings
    assert timings.avg_total_wall_clock_sec > 0.0
    assert timings.avg_assembly_sec > 0.0
    assert timings.avg_clip_generation_sec > 0.0

    # Single run metrics
    m = report.runs[0]
    assert m.success is True
    assert m.num_scenes == 4
    assert m.num_clips_generated == 4
    assert m.output_resolution == "1280x720"


def test_benchmark_runner_synthetic_workload():
    """Verify synthetic load mode exercises diverse archetypes and resilience features."""
    runner = BenchmarkRunner()
    report = runner.run_benchmark(runs=3, mock=True, synthetic=True)

    assert report.synthetic_mode is True
    assert report.runs_completed == 3
    assert report.runs_successful == 3
    assert set(report.archetypes_tested) == {"education", "news", "product"}
    assert "16:9" in report.aspect_ratios_tested
    assert "9:16" in report.aspect_ratios_tested


def test_cli_benchmark_invocation(tmp_path: Path):
    """Verify CLI benchmark command runs and saves report."""
    runner = CliRunner()
    out_dir = tmp_path / "cli_bench"
    result = runner.invoke(main, [
        "benchmark",
        "--runs", "1",
        "--output-dir", str(out_dir),
    ])

    assert result.exit_code == 0
    assert "VIDEO-DRAFT BENCHMARK" in result.output
    assert "Runs Requested:       1" in result.output
    assert "Successful:           1" in result.output
    assert (out_dir / "benchmark_report.json").is_file()
