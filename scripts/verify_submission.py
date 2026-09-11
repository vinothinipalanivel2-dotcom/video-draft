from pathlib import Path
import sys
from video_draft.evaluation.submission_validator import SubmissionValidator

def main():
    repo_root = Path(__file__).parent.parent
    sub_dir = repo_root / "submission"
    validator = SubmissionValidator()
    report = validator.validate_submission(submission_dir=sub_dir, repo_root=repo_root)

    print("==================================================")
    print("        VIDEO-DRAFT SUBMISSION AUDIT              ")
    print("==================================================")
    for name, chk in report.checks.items():
        status = "PASS" if chk.passed else "FAIL"
        print(f"[{status}] {name:25s} Score: {chk.score:.2f} - {chk.message}")
    print("==================================================")
    print(f"RESULT: {report.passed_checks}/{report.total_checks} checks passed.")
    print(f"OVERALL STATUS: {'READY FOR SUBMISSION' if report.overall_passed else 'REJECTED'}")
    print("==================================================")
    if not report.overall_passed:
        sys.exit(1)

if __name__ == "__main__":
    main()
