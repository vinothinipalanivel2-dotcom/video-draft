"""Unit tests for configuration loading, overrides, and error validation."""

import os
from pathlib import Path
import pytest
import yaml

from video_draft.config import ConfigurationError, load_config
from video_draft.schema.config import AppConfig


def test_default_config_loading():
    """Verify loading default configuration resolves correctly."""
    cfg = load_config()
    assert isinstance(cfg, AppConfig)
    assert cfg.system.project_name == "video-draft"
    assert cfg.system.log_level in ("DEBUG", "INFO", "WARNING", "ERROR")
    assert cfg.paths.outputs_dir == Path("outputs")


def test_custom_yaml_config_loading(tmp_path: Path):
    """Verify loading a custom YAML configuration file."""
    custom_yaml = tmp_path / "custom.yaml"
    custom_yaml.write_text(
        yaml.dump(
            {
                "system": {
                    "project_name": "custom-draft",
                    "log_level": "DEBUG",
                },
                "execution": {
                    "force_cpu": False,
                    "deterministic_seed": 999,
                },
            }
        ),
        encoding="utf-8",
    )

    cfg = load_config(custom_yaml)
    assert cfg.system.project_name == "custom-draft"
    assert cfg.system.log_level == "DEBUG"
    assert cfg.execution.force_cpu is False
    assert cfg.execution.deterministic_seed == 999


def test_env_var_overrides(monkeypatch):
    """Verify environment variables override configuration file settings."""
    monkeypatch.setenv("VIDEO_DRAFT_LOG_LEVEL", "WARNING")
    monkeypatch.setenv("VIDEO_DRAFT_FORCE_CPU", "false")
    monkeypatch.setenv("VIDEO_DRAFT_OUTPUTS_DIR", "custom_outputs")
    monkeypatch.setenv("VIDEO_DRAFT_SEED", "777")

    cfg = load_config()
    assert cfg.system.log_level == "WARNING"
    assert cfg.execution.force_cpu is False
    assert cfg.paths.outputs_dir == Path("custom_outputs")
    assert cfg.execution.deterministic_seed == 777


def test_invalid_config_nonexistent_file():
    """Verify non-existent config path raises ConfigurationError."""
    with pytest.raises(ConfigurationError, match="not found"):
        load_config(Path("non_existent_config_file_12345.yaml"))


def test_invalid_config_malformed_yaml(tmp_path: Path):
    """Verify malformed YAML syntax raises ConfigurationError."""
    bad_yaml = tmp_path / "malformed.yaml"
    bad_yaml.write_text("system:\n  log_level: [unclosed list", encoding="utf-8")

    with pytest.raises(ConfigurationError, match="Failed to parse"):
        load_config(bad_yaml)


def test_invalid_config_schema_violation(tmp_path: Path):
    """Verify invalid configuration values (e.g. invalid enum or bad timeout) are rejected."""
    bad_cfg = tmp_path / "bad_schema.yaml"
    bad_cfg.write_text(
        yaml.dump(
            {
                "system": {
                    "log_level": "NOT_A_REAL_LOG_LEVEL",
                },
                "execution": {
                    "timeout_seconds": -50,  # Negative timeout violates constraint
                },
            }
        ),
        encoding="utf-8",
    )

    with pytest.raises(ConfigurationError, match="Configuration validation failed"):
        load_config(bad_cfg)


def test_invalid_env_seed_rejected(monkeypatch):
    """Verify non-integer seed in environment variable is rejected with ConfigurationError."""
    monkeypatch.setenv("VIDEO_DRAFT_SEED", "not_a_number")

    with pytest.raises(ConfigurationError, match="VIDEO_DRAFT_SEED must be an integer"):
        load_config()
