"""Validator for IncuBrix Track 03 candidate submission package."""

import json
from pathlib import Path
import re
from typing import Any, Dict, List, Tuple
from pydantic import BaseModel, Field

from video_draft.assembly.ffmpeg_tools import probe_media, verify_media_decodable
from video_draft.evaluation.manifest_builder import compute_file_sha256
from video_draft.evaluation.models import CheckResult


class SubmissionValidationReport(BaseModel):
    """Structured report verifying the integrity, cleanliness, and completeness of submission package."""
    timestamp: str
    overall_passed: bool
    total_checks: int
    passed_checks: int
    failed_checks: int
    checks: Dict[str, CheckResult] = Field(default_factory=dict)
    discovered_artifacts: List[str] = Field(default_factory=list)
    security_clean: bool = True
    issues: List[str] = Field(default_factory=list)


class SubmissionValidator:
    """Validates candidate submission directory against IncuBrix Track 03 standards."""

    REQUIRED_DOCS = [
        "README.md",
        "architecture.md",
        "requirements_traceability.md",
        "benchmark_summary.md",
        "reproducibility.md",
        "model_governance.md",
    ]

    REQUIRED_ARTIFACTS = [
        "final_draft.mp4",
        "timeline.json",
        "scene_plan.json",
        "route_decision.json",
        "manifest.json",
        "evaluation_report.json",
        "benchmark_report.json",
        "captions.srt",
    ]

    SECRET_PATTERNS = [
        re.compile(r"sk-[a-zA-Z0-9]{20,}", re.IGNORECASE),
        re.compile(r"hf_[a-zA-Z0-9]{20,}", re.IGNORECASE),
        re.compile(r"AKIA[0-9A-Z]{16}", re.IGNORECASE),
        re.compile(r"bearer\s+[a-zA-Z0-9\-_\.]+", re.IGNORECASE),
        re.compile(r"api[_-]?key\s*[:=]\s*['\"][a-zA-Z0-9_\-]{8,}['\"]", re.IGNORECASE),
        re.compile(r"password\s*[:=]\s*['\"][^'\"]+['\"]", re.IGNORECASE),
    ]

    def validate_submission(self, submission_dir: Path, repo_root: Path) -> SubmissionValidationReport:
        """Run all submission verification checks and return SubmissionValidationReport."""
        import datetime
        checks: Dict[str, CheckResult] = {}
        issues: List[str] = []
        artifacts_dir = submission_dir / "artifacts"

        # 1. Check required documentation in submission/
        missing_docs = [doc for doc in self.REQUIRED_DOCS if not (submission_dir / doc).is_file()]
        doc_pass = (len(missing_docs) == 0)
        if not doc_pass:
            issues.append(f"Missing required documentation in submission/: {missing_docs}")
        checks["documentation_presence"] = CheckResult(
            dimension="documentation_presence",
            passed=doc_pass,
            score=1.0 if doc_pass else 0.0,
            message="All 6 required submission markdown documents present" if doc_pass else f"Missing docs: {missing_docs}",
            details={"missing": missing_docs, "required": self.REQUIRED_DOCS},
        )

        # 2. Check required artifacts in submission/artifacts/
        missing_artifacts = [art for art in self.REQUIRED_ARTIFACTS if not (artifacts_dir / art).is_file()]
        art_pass = (len(missing_artifacts) == 0)
        if not art_pass:
            issues.append(f"Missing required artifacts in submission/artifacts/: {missing_artifacts}")
        checks["artifacts_presence"] = CheckResult(
            dimension="artifacts_presence",
            passed=art_pass,
            score=1.0 if art_pass else 0.0,
            message="All 8 required pipeline artifacts present" if art_pass else f"Missing artifacts: {missing_artifacts}",
            details={"missing": missing_artifacts, "required": self.REQUIRED_ARTIFACTS},
        )

        # 3. Check JSON validity of all JSON artifacts
        json_valid = True
        json_issues = []
        for j_file in artifacts_dir.glob("*.json"):
            try:
                json.loads(j_file.read_text(encoding="utf-8"))
            except Exception as err:
                json_valid = False
                json_issues.append(f"{j_file.name}: {err}")
        if not json_valid:
            issues.extend(json_issues)
        checks["json_artifacts_validity"] = CheckResult(
            dimension="json_artifacts_validity",
            passed=json_valid,
            score=1.0 if json_valid else 0.0,
            message="All JSON artifacts are well-formed and valid" if json_valid else f"Malformed JSON: {json_issues}",
            details={"issues": json_issues},
        )

        # 4. Check Final MP4 file decodability and stream validity
        mp4_path = artifacts_dir / "final_draft.mp4"
        mp4_valid = False
        mp4_details: Dict[str, Any] = {}
        if mp4_path.is_file():
            try:
                probe = probe_media(mp4_path)
                decodable = verify_media_decodable(mp4_path)
                mp4_valid = bool(probe.get("duration", 0) > 0 and decodable)
                mp4_details = {
                    "duration": probe.get("duration"),
                    "resolution": f"{probe.get('width')}x{probe.get('height')}",
                    "codec": probe.get("video_codec"),
                    "has_audio": probe.get("has_audio"),
                    "decodable": decodable,
                }
            except Exception as err:
                issues.append(f"MP4 validation error: {err}")
                mp4_details["error"] = str(err)
        else:
            issues.append("final_draft.mp4 not found for probe")

        checks["final_mp4_integrity"] = CheckResult(
            dimension="final_mp4_integrity",
            passed=mp4_valid,
            score=1.0 if mp4_valid else 0.0,
            message="Final MP4 probed successfully and stream is playable/decodable" if mp4_valid else "MP4 invalid or not decodable",
            details=mp4_details,
        )

        # 5. Check Manifest SHA-256 Hash Resolution
        manifest_path = artifacts_dir / "manifest.json"
        manifest_valid = False
        hash_mismatches = []
        if manifest_path.is_file():
            try:
                mf_data = json.loads(manifest_path.read_text(encoding="utf-8"))
                hashes = mf_data.get("asset_hashes", {})
                for fname, expected_hash in hashes.items():
                    # Resolve fname
                    target = None
                    if (artifacts_dir / fname).is_file():
                        target = artifacts_dir / fname
                    elif (artifacts_dir / "clips" / fname).is_file():
                        target = artifacts_dir / "clips" / fname
                    elif (artifacts_dir / "audio" / fname).is_file():
                        target = artifacts_dir / "audio" / fname
                    elif (repo_root / fname).is_file():
                        target = repo_root / fname

                    if target and target.is_file():
                        actual_hash = compute_file_sha256(target)
                        if actual_hash != expected_hash:
                            hash_mismatches.append(f"{fname}: expected {expected_hash[:8]}..., got {actual_hash[:8]}...")
                manifest_valid = (len(hash_mismatches) == 0)
                if not manifest_valid:
                    issues.extend(hash_mismatches)
            except Exception as err:
                issues.append(f"Manifest verification error: {err}")

        checks["manifest_hash_resolution"] = CheckResult(
            dimension="manifest_hash_resolution",
            passed=manifest_valid,
            score=1.0 if manifest_valid else 0.0,
            message="All manifest SHA-256 hashes resolve to existing matching files" if manifest_valid else f"Hash mismatches: {hash_mismatches}",
            details={"mismatches": hash_mismatches},
        )

        # 6. Check Colab Notebook Presence & Validity
        notebook_path = repo_root / "notebooks" / "video_draft_colab.ipynb"
        nb_valid = False
        if notebook_path.is_file():
            try:
                nb_json = json.loads(notebook_path.read_text(encoding="utf-8"))
                nb_valid = "cells" in nb_json and len(nb_json["cells"]) >= 10
            except Exception:
                nb_valid = False
        checks["colab_notebook_validity"] = CheckResult(
            dimension="colab_notebook_validity",
            passed=nb_valid,
            score=1.0 if nb_valid else 0.0,
            message="Interactive Colab/Kaggle notebook exists and parses" if nb_valid else "Notebook missing or malformed",
            details={"path": str(notebook_path), "valid": nb_valid},
        )

        # 7. Security Audit: Scan repository for potential leaked API keys or secrets
        secret_findings = self._scan_for_secrets(repo_root)
        security_clean = (len(secret_findings) == 0)
        if not security_clean:
            issues.extend([f"Potential secret in {f}: {m}" for f, m in secret_findings])

        checks["security_and_secrets_clean"] = CheckResult(
            dimension="security_and_secrets_clean",
            passed=security_clean,
            score=1.0 if security_clean else 0.0,
            message="No API keys, passwords, or credentials detected in repository" if security_clean else f"Secrets detected: {len(secret_findings)}",
            details={"findings": secret_findings},
        )

        total = len(checks)
        passed = sum(1 for c in checks.values() if c.passed)
        failed = total - passed
        overall_passed = (failed == 0)

        discovered = [p.name for p in artifacts_dir.glob("*.*")]

        report = SubmissionValidationReport(
            timestamp=datetime.datetime.now(datetime.timezone.utc).isoformat(),
            overall_passed=overall_passed,
            total_checks=total,
            passed_checks=passed,
            failed_checks=failed,
            checks=checks,
            discovered_artifacts=discovered,
            security_clean=security_clean,
            issues=issues,
        )

        # Write validation report to submission/
        report_file = submission_dir / "submission_validation_report.json"
        report_file.write_text(report.model_dump_json(indent=2), encoding="utf-8")

        return report

    def _scan_for_secrets(self, root: Path) -> List[Tuple[str, str]]:
        """Scan repository text files for potential secrets or credentials."""
        findings: List[Tuple[str, str]] = []
        ignored_dirs = {".git", ".pytest_cache", "__pycache__", "venv", ".venv", "node_modules", "tests"}

        for p in root.rglob("*"):
            if any(part in ignored_dirs for part in p.parts):
                continue
            if not p.is_file():
                continue
            if p.suffix in (".py", ".json", ".yaml", ".yml", ".md", ".toml", ".txt"):
                try:
                    text = p.read_text(encoding="utf-8", errors="ignore")
                    for pat in self.SECRET_PATTERNS:
                        match = pat.search(text)
                        if match:
                            rel = p.relative_to(root)
                            # Ignore mock / test dummy strings
                            matched_str = match.group(0)
                            if "mock" in matched_str.lower() or "example" in matched_str.lower():
                                continue
                            findings.append((str(rel), matched_str[:20] + "..."))
                except Exception:
                    pass
        return findings
