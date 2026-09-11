"""Unit tests for the video-draft CLI interface."""

from pathlib import Path
from click.testing import CliRunner
import pytest

from video_draft.cli import main


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


def test_cli_help(runner: CliRunner):
    """Verify CLI starts and displays help."""
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
    assert "video-draft: Open-Source Draft Video Generation and Model Routing CLI." in result.output
    for cmd in ["validate", "plan", "route", "generate", "assemble", "evaluate", "benchmark", "run"]:
        assert cmd in result.output


def test_cli_version(runner: CliRunner):
    """Verify CLI prints version."""
    result = runner.invoke(main, ["--version"])
    assert result.exit_code == 0
    assert "0.1.0" in result.output


def test_cli_validate_success(runner: CliRunner, temp_brief_file: Path):
    """Verify validate command succeeds with a valid brief."""
    result = runner.invoke(main, ["validate", "--brief", str(temp_brief_file)])
    assert result.exit_code == 0
    assert "SUCCESS: Creative brief 'test-brief-001' conforms to all schema requirements." in result.output


def test_cli_validate_failure(runner: CliRunner, temp_invalid_brief_file: Path):
    """Verify validate command fails with an invalid brief."""
    result = runner.invoke(main, ["validate", "--brief", str(temp_invalid_brief_file)])
    assert result.exit_code != 0
    assert "ERROR: Creative brief validation failed:" in result.output


def test_cli_plan_command(runner: CliRunner, temp_brief_file: Path):
    """Verify plan command starts."""
    result = runner.invoke(main, ["plan", "--brief", str(temp_brief_file)])
    assert result.exit_code == 0
    assert "[STUB] Planned scene structure" in result.output
    assert "Plan ID:" in result.output
    assert "Archetype Strategy:" in result.output


def test_cli_plan_command_with_output(runner: CliRunner, temp_brief_file: Path, tmp_path: Path):
    """Verify plan command outputs scene_plan.json when --output is passed."""
    out_file = tmp_path / "scene_plan.json"
    result = runner.invoke(main, ["plan", "--brief", str(temp_brief_file), "--output", str(out_file)])
    assert result.exit_code == 0
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "plan_id" in content
    assert "scenes" in content
    assert "EducationStrategy" in content


def test_cli_route_command(runner: CliRunner, temp_brief_file: Path):
    """Verify route command starts and respects --force-cpu flag."""
    result = runner.invoke(main, ["route", "--brief", str(temp_brief_file), "--force-cpu"])
    assert result.exit_code == 0
    assert "cpu-procedural-engine" in result.output
    assert "MODEL ROUTING DECISION" in result.output
    assert "Selected model:" in result.output


def test_cli_route_command_with_output(runner: CliRunner, temp_brief_file: Path, tmp_path: Path):
    """Verify route command writes route_decision.json when --output is provided."""
    out_file = tmp_path / "route_decision.json"
    result = runner.invoke(main, ["route", "--brief", str(temp_brief_file), "--output", str(out_file), "--force-cpu"])
    assert result.exit_code == 0
    assert out_file.exists()
    content = out_file.read_text(encoding="utf-8")
    assert "selected_model" in content
    assert "cpu_procedural_engine" in content


def test_cli_generate_command(runner: CliRunner, tmp_path: Path):
    """Verify generate command starts."""
    dummy_plan = tmp_path / "plan.json"
    dummy_plan.write_text("{}", encoding="utf-8")
    result = runner.invoke(main, ["generate", "--scene-plan", str(dummy_plan)])
    assert result.exit_code == 0
    assert "[STUB] Clip generation completed" in result.output


def test_cli_assemble_command(runner: CliRunner, tmp_path: Path):
    """Verify assemble command starts."""
    dummy_timeline = tmp_path / "timeline.json"
    dummy_timeline.write_text("{}", encoding="utf-8")
    result = runner.invoke(main, ["assemble", "--timeline", str(dummy_timeline)])
    assert result.exit_code == 0
    assert "[STUB] Video assembly completed" in result.output


def test_cli_evaluate_command(runner: CliRunner, tmp_path: Path):
    """Verify evaluate command starts."""
    dummy_manifest = tmp_path / "manifest.json"
    dummy_manifest.write_text("{}", encoding="utf-8")
    result = runner.invoke(main, ["evaluate", "--manifest", str(dummy_manifest)])
    assert result.exit_code == 0
    assert "[STUB] Evaluation completed" in result.output


def test_cli_benchmark_command(runner: CliRunner):
    """Verify benchmark command starts."""
    result = runner.invoke(main, ["benchmark", "--iterations", "2"])
    assert result.exit_code == 0
    assert "[STUB] Benchmark completed across 2 iterations" in result.output


def test_cli_run_command(runner: CliRunner, temp_brief_file: Path):
    """Verify full pipeline run command starts."""
    result = runner.invoke(main, ["run", "--brief", str(temp_brief_file), "--force-cpu"])
    assert result.exit_code == 0
    assert "[STUB] Full pipeline executed" in result.output


def test_cli_generate_command_real_plan(runner: CliRunner, temp_brief_file: Path, tmp_path: Path):
    """Verify generate command processes real scene plan with --mock."""
    plan_out = tmp_path / "scene_plan.json"
    plan_res = runner.invoke(main, ["plan", "--brief", str(temp_brief_file), "--output", str(plan_out)])
    assert plan_res.exit_code == 0

    clips_dir = tmp_path / "clips"
    gen_res = runner.invoke(main, ["generate", "--scene-plan", str(plan_out), "--output-dir", str(clips_dir), "--mock"])
    assert gen_res.exit_code == 0
    assert "SCENE CLIP GENERATION" in gen_res.output
    assert "All 4 scene clips generated and validated successfully." in gen_res.output


def test_cli_run_command_end_to_end(runner: CliRunner, temp_brief_file: Path, tmp_path: Path):
    """Verify end-to-end full pipeline run via CLI with --mock."""
    out_dir = tmp_path / "pipeline_run"
    result = runner.invoke(main, ["run", "--brief", str(temp_brief_file), "--output-dir", str(out_dir), "--force-cpu", "--mock"])
    assert result.exit_code == 0
    assert "VIDEO-DRAFT END-TO-END PIPELINE RUN" in result.output
    assert "[1/6] ROUTE:" in result.output
    assert "[2/6] PLAN:" in result.output
    assert "[3/6] AUDIO:" in result.output
    assert "[4/6] GENERATE:" in result.output
    assert "[5/6] VALIDATE:" in result.output
    assert "[6/6] ASSEMBLE:" in result.output
    assert (out_dir / "final_draft.mp4").is_file()

