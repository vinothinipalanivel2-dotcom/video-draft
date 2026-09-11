"""Unit tests for submission pack validation, security scanning, and Colab notebook."""

import json
from pathlib import Path
import pytest

from video_draft.evaluation.submission_validator import SubmissionValidator


@pytest.fixture
def repo_root() -> Path:
    return Path(__file__).parent.parent.parent


def test_submission_validator_on_real_submission(repo_root: Path):
    """Verify that the generated submission/ directory passes all validation checks."""
    sub_dir = repo_root / "submission"
    assert sub_dir.is_dir(), "submission directory must exist"

    validator = SubmissionValidator()
    report = validator.validate_submission(submission_dir=sub_dir, repo_root=repo_root)

    assert report.overall_passed is True, f"Submission validation failed with issues: {report.issues}"
    assert report.passed_checks == report.total_checks
    assert report.security_clean is True
    assert (sub_dir / "submission_validation_report.json").is_file()


def test_submission_validator_detects_missing_doc(tmp_path: Path, repo_root: Path):
    """Verify validator flags missing markdown documentation in submission/."""
    dummy_sub = tmp_path / "dummy_sub"
    dummy_sub.mkdir()
    (dummy_sub / "artifacts").mkdir()

    # Only create 1 doc instead of 6
    (dummy_sub / "README.md").write_text("stub", encoding="utf-8")

    validator = SubmissionValidator()
    report = validator.validate_submission(submission_dir=dummy_sub, repo_root=repo_root)

    assert report.overall_passed is False
    assert report.checks["documentation_presence"].passed is False
    assert "Missing required documentation" in str(report.issues)


def test_submission_validator_detects_missing_artifact(tmp_path: Path, repo_root: Path):
    """Verify validator flags missing pipeline artifacts."""
    dummy_sub = tmp_path / "dummy_sub"
    dummy_sub.mkdir()
    artifacts_dir = dummy_sub / "artifacts"
    artifacts_dir.mkdir()

    # Create all docs
    for d in SubmissionValidator.REQUIRED_DOCS:
        (dummy_sub / d).write_text("stub", encoding="utf-8")

    # Leave artifacts empty
    validator = SubmissionValidator()
    report = validator.validate_submission(submission_dir=dummy_sub, repo_root=repo_root)

    assert report.overall_passed is False
    assert report.checks["artifacts_presence"].passed is False


def test_submission_validator_detects_leaked_secret(tmp_path: Path):
    """Verify secret scanner detects simulated API keys."""
    scan_root = tmp_path / "code_root"
    scan_root.mkdir()
    leak_file = scan_root / "leaked_config.py"
    leak_file.write_text("OPENAI_KEY = 'sk-1234567890abcdef1234567890abcdef'", encoding="utf-8")

    validator = SubmissionValidator()
    findings = validator._scan_for_secrets(scan_root)
    assert len(findings) > 0
    assert "leaked_config.py" in findings[0][0]


def test_colab_notebook_structure(repo_root: Path):
    """Verify notebooks/video_draft_colab.ipynb is a valid Jupyter notebook with required sections."""
    nb_path = repo_root / "notebooks" / "video_draft_colab.ipynb"
    assert nb_path.is_file(), "Colab notebook must exist"

    data = json.loads(nb_path.read_text(encoding="utf-8"))
    assert "cells" in data
    assert len(data["cells"]) >= 10

    # Ensure code cells contain required stages
    code_sources = [
        "".join(c.get("source", []))
        for c in data["cells"]
        if c.get("cell_type") == "code"
    ]
    full_code = "\n".join(code_sources)

    assert "import video_draft" in full_code
    assert "CreativeBrief" in full_code
    assert "route(" in full_code
    assert "ScenePlanner" in full_code
    assert "video-draft run" in full_code
    assert "video-draft evaluate" in full_code
    assert "video-draft benchmark" in full_code
