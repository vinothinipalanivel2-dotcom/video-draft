"""Comprehensive end-to-end integration tests for the full video-draft pipeline."""

import json
from pathlib import Path
import pytest
from click.testing import CliRunner

from video_draft.assembly.ffmpeg_tools import probe_media, verify_media_decodable
from video_draft.cli import main
from video_draft.evaluation.media_validator import FinalMediaValidator
from video_draft.evaluation.quality_gate import QualityGate
from video_draft.schema.brief import CreativeBrief, SystemConstraints


@pytest.fixture
def runner() -> CliRunner:
    return CliRunner()


@pytest.fixture
def edu_16x9_brief_file(tmp_path: Path) -> Path:
    brief = CreativeBrief(
        id="brief-edu-e2e",
        title="Cellular Mitosis Explainer",
        genre="education",
        aspect_ratio="16:9",
        target_duration_sec=16.0,
        script=(
            "Mitosis is the process of cell division. "
            "Chromosomes duplicate and align in the center. "
            "Finally, the cell divides into two identical cells."
        ),
        seed=42,
        constraints=SystemConstraints(
            max_vram_gb=16.0,
            allow_cpu_fallback=True,
            quality_tier="draft",
        ),
    )
    b_file = tmp_path / "brief_16x9.json"
    b_file.write_text(brief.model_dump_json(indent=2), encoding="utf-8")
    return b_file


@pytest.fixture
def product_9x16_brief_file(tmp_path: Path) -> Path:
    brief = CreativeBrief(
        id="brief-prod-e2e",
        title="Smart Tracker Pro Launch",
        genre="product",
        aspect_ratio="9:16",
        target_duration_sec=15.0,
        script=(
            "Introducing the all-new Smart Tracker Pro. "
            "Ultra-thin titanium design with all-day battery life. "
            "Order yours today and never lose what matters."
        ),
        seed=101,
        constraints=SystemConstraints(
            max_vram_gb=16.0,
            allow_cpu_fallback=True,
            quality_tier="draft",
        ),
    )
    b_file = tmp_path / "brief_9x16.json"
    b_file.write_text(brief.model_dump_json(indent=2), encoding="utf-8")
    return b_file


def test_end_to_end_16x9_education_workflow(runner: CliRunner, edu_16x9_brief_file: Path, tmp_path: Path):
    """Verify complete 16:9 Education draft pipeline generates all artifacts and passes Quality Gate."""
    out_dir = tmp_path / "run_edu_16x9"
    result = runner.invoke(
        main,
        ["run", "--brief", str(edu_16x9_brief_file), "--output-dir", str(out_dir), "--force-cpu", "--mock"],
    )
    assert result.exit_code == 0
    assert "SUCCESS: Pipeline completed in CPU mode." in result.output
    assert "[1/6] ROUTE:" in result.output
    assert "[2/6] PLAN:" in result.output
    assert "[3/6] AUDIO:" in result.output
    assert "[4/6] GENERATE:" in result.output
    assert "[5/6] VALIDATE:" in result.output
    assert "[6/6] ASSEMBLE:" in result.output
    assert "[7/7] QUALITY:" in result.output

    # Verify all expected artifacts exist on disk
    mp4_file = out_dir / "final_draft.mp4"
    plan_file = out_dir / "scene_plan.json"
    tl_file = out_dir / "timeline.json"
    srt_file = out_dir / "captions.srt"
    manifest_file = out_dir / "manifest.json"
    eval_file = out_dir / "evaluation_report.json"

    assert mp4_file.is_file()
    assert plan_file.is_file()
    assert tl_file.is_file()
    assert srt_file.is_file()
    assert manifest_file.is_file()
    assert eval_file.is_file()

    # Validate final MP4 video artifact
    validator = FinalMediaValidator(default_tolerance_sec=0.5)
    media_res = validator.validate(
        video_path=mp4_file,
        expected_aspect_ratio="16:9",
        expected_duration=16.0,
        require_audio=True,
    )
    assert media_res.is_valid is True
    assert media_res.width == 1280
    assert media_res.height == 720
    assert media_res.has_audio is True
    assert media_res.is_decodable is True

    # Validate manifest contents
    manifest_data = json.loads(manifest_file.read_text(encoding="utf-8"))
    assert manifest_data["brief_id"] == "brief-edu-e2e"
    assert manifest_data["reproducibility_seed"] == 42
    assert len(manifest_data["output_mp4_sha256"]) == 64
    assert len(manifest_data["models_used"]) >= 1

    # Validate evaluation report contents
    eval_data = json.loads(eval_file.read_text(encoding="utf-8"))
    assert eval_data["overall_passed"] is True
    assert eval_data["overall_score"] >= 0.95


def test_end_to_end_9x16_product_workflow(runner: CliRunner, product_9x16_brief_file: Path, tmp_path: Path):
    """Verify complete 9:16 Product draft pipeline produces vertical video and valid manifest."""
    out_dir = tmp_path / "run_prod_9x16"
    result = runner.invoke(
        main,
        ["run", "--brief", str(product_9x16_brief_file), "--output-dir", str(out_dir), "--force-cpu", "--mock"],
    )
    assert result.exit_code == 0
    assert "SUCCESS: Pipeline completed in CPU mode." in result.output

    mp4_file = out_dir / "final_draft.mp4"
    assert mp4_file.is_file()

    # Validate vertical 9:16 geometry (720x1280)
    validator = FinalMediaValidator(default_tolerance_sec=0.5)
    media_res = validator.validate(
        video_path=mp4_file,
        expected_aspect_ratio="9:16",
        expected_duration=15.0,
        require_audio=True,
    )
    assert media_res.is_valid is True
    assert media_res.width == 720
    assert media_res.height == 1280
    assert media_res.aspect_ratio == "9:16"


def test_end_to_end_reproducibility(runner: CliRunner, edu_16x9_brief_file: Path, tmp_path: Path):
    """Verify identical brief inputs yield deterministic structural plans, routes, and timelines."""
    out_dir_1 = tmp_path / "repro_run_1"
    out_dir_2 = tmp_path / "repro_run_2"

    res1 = runner.invoke(main, ["run", "--brief", str(edu_16x9_brief_file), "--output-dir", str(out_dir_1), "--force-cpu", "--mock"])
    res2 = runner.invoke(main, ["run", "--brief", str(edu_16x9_brief_file), "--output-dir", str(out_dir_2), "--force-cpu", "--mock"])

    assert res1.exit_code == 0
    assert res2.exit_code == 0

    # Load artifacts from both runs
    plan1 = json.loads((out_dir_1 / "scene_plan.json").read_text(encoding="utf-8"))
    plan2 = json.loads((out_dir_2 / "scene_plan.json").read_text(encoding="utf-8"))

    tl1 = json.loads((out_dir_1 / "timeline.json").read_text(encoding="utf-8"))
    tl2 = json.loads((out_dir_2 / "timeline.json").read_text(encoding="utf-8"))

    route1 = json.loads((out_dir_1 / "route_decision.json").read_text(encoding="utf-8"))
    route2 = json.loads((out_dir_2 / "route_decision.json").read_text(encoding="utf-8"))

    # Assert plan determinism
    assert len(plan1["scenes"]) == len(plan2["scenes"])
    for s1, s2 in zip(plan1["scenes"], plan2["scenes"]):
        assert s1["scene_id"] == s2["scene_id"]
        assert s1["duration_sec"] == s2["duration_sec"]
        assert s1["visual_prompt"] == s2["visual_prompt"]

    # Assert route decision determinism
    assert route1["selected_model"] == route2["selected_model"]
    assert route1["selected_score"] == route2["selected_score"]
    assert route1["fallback_chain"] == route2["fallback_chain"]

    # Assert timeline determinism
    assert len(tl1["video_tracks"]) == len(tl2["video_tracks"])
    for t1, t2 in zip(tl1["video_tracks"], tl2["video_tracks"]):
        assert t1["scene_id"] == t2["scene_id"]
        assert t1["duration_sec"] == t2["duration_sec"]


def test_idempotency_and_safe_rerun(runner: CliRunner, edu_16x9_brief_file: Path, tmp_path: Path):
    """Verify rerunning pipeline in existing directory safely updates artifacts without corruption."""
    out_dir = tmp_path / "idempotent_run"

    # Run 1
    res1 = runner.invoke(main, ["run", "--brief", str(edu_16x9_brief_file), "--output-dir", str(out_dir), "--force-cpu", "--mock"])
    assert res1.exit_code == 0
    mp4_1 = out_dir / "final_draft.mp4"
    assert mp4_1.is_file()
    hash1 = (out_dir / "manifest.json").read_text(encoding="utf-8")

    # Run 2 into same directory
    res2 = runner.invoke(main, ["run", "--brief", str(edu_16x9_brief_file), "--output-dir", str(out_dir), "--force-cpu", "--mock"])
    assert res2.exit_code == 0
    assert mp4_1.is_file()

    # Final video must be valid and decodable after rerun
    assert verify_media_decodable(mp4_1) is True


def test_cli_evaluate_command_with_manifest(runner: CliRunner, edu_16x9_brief_file: Path, tmp_path: Path):
    """Verify CLI evaluate command processes real manifest and outputs evaluation scorecard."""
    run_dir = tmp_path / "eval_cli_test"
    run_res = runner.invoke(main, ["run", "--brief", str(edu_16x9_brief_file), "--output-dir", str(run_dir), "--force-cpu", "--mock"])
    assert run_res.exit_code == 0

    manifest_path = run_dir / "manifest.json"
    eval_out = run_dir / "cli_eval_report.json"

    eval_res = runner.invoke(main, ["evaluate", "--manifest", str(manifest_path), "--output", str(eval_out)])
    assert eval_res.exit_code == 0
    assert "DRAFT EVALUATION REPORT" in eval_res.output
    assert "Overall Status:" in eval_res.output
    assert "[STUB] Evaluation completed for manifest:" in eval_res.output
    assert eval_out.is_file()
