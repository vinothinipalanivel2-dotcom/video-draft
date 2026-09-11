"""Unit tests for structured logging."""

import json
from pathlib import Path
from video_draft.utils.logger import setup_logger


def test_structured_json_logging(tmp_path: Path):
    """Verify structured logger writes valid JSON lines to log file."""
    log_file = tmp_path / "test_run.log.jsonl"
    logger = setup_logger(name="test_logger", log_level="INFO", log_format="json", log_file=log_file)

    logger.info("Pipeline started", event="pipeline_init", run_id="run-1234", duration=25.0)

    assert log_file.exists()
    lines = log_file.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 1

    entry = json.loads(lines[0])
    assert entry["level"] == "INFO"
    assert entry["logger"] == "test_logger"
    assert entry["message"] == "Pipeline started"
    assert entry["event"] == "pipeline_init"
    assert entry["run_id"] == "run-1234"
    assert entry["duration"] == 25.0
    assert "timestamp" in entry
