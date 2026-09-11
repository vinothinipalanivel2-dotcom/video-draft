"""Configuration loader and validation engine."""

import os
import json
from pathlib import Path
from typing import Any, Dict, Optional
import yaml
from pydantic import ValidationError

from video_draft.schema.config import AppConfig


class ConfigurationError(Exception):
    """Raised when application configuration is missing, malformed, or invalid."""
    pass


def _find_default_config_path() -> Optional[Path]:
    """Search for system.yaml in standard locations without hardcoding absolute paths."""
    candidates = [
        Path("configs/system.yaml"),
        Path.cwd() / "configs" / "system.yaml",
        Path(__file__).resolve().parent.parent.parent / "configs" / "system.yaml",
    ]
    for c in candidates:
        if c.is_file():
            return c
    return None


def _load_raw_config(file_path: Path) -> Dict[str, Any]:
    """Reads YAML or JSON file into dictionary."""
    if not file_path.exists():
        raise ConfigurationError(f"Configuration file not found: {file_path}")

    try:
        content = file_path.read_text(encoding="utf-8")
        if file_path.suffix in (".yaml", ".yml"):
            data = yaml.safe_load(content)
        elif file_path.suffix == ".json":
            data = json.loads(content)
        else:
            # Attempt yaml by default
            data = yaml.safe_load(content)

        if not isinstance(data, dict):
            raise ConfigurationError(f"Configuration root must be a dictionary/mapping, got {type(data).__name__}")
        return data
    except (yaml.YAMLError, json.JSONDecodeError) as err:
        raise ConfigurationError(f"Failed to parse configuration file {file_path}: {err}") from err


def _apply_env_overrides(raw_data: Dict[str, Any]) -> Dict[str, Any]:
    """Applies environment variable overrides to raw configuration dictionary."""
    data = dict(raw_data)
    system = data.setdefault("system", {})
    paths = data.setdefault("paths", {})
    execution = data.setdefault("execution", {})

    # System overrides
    if "VIDEO_DRAFT_LOG_LEVEL" in os.environ:
        system["log_level"] = os.environ["VIDEO_DRAFT_LOG_LEVEL"]
    if "VIDEO_DRAFT_LOG_FORMAT" in os.environ:
        system["log_format"] = os.environ["VIDEO_DRAFT_LOG_FORMAT"]

    # Path overrides
    if "VIDEO_DRAFT_ASSETS_DIR" in os.environ:
        paths["assets_dir"] = os.environ["VIDEO_DRAFT_ASSETS_DIR"]
    if "VIDEO_DRAFT_OUTPUTS_DIR" in os.environ:
        paths["outputs_dir"] = os.environ["VIDEO_DRAFT_OUTPUTS_DIR"]
    if "VIDEO_DRAFT_CACHE_DIR" in os.environ:
        paths["cache_dir"] = os.environ["VIDEO_DRAFT_CACHE_DIR"]

    # Execution overrides
    if "VIDEO_DRAFT_FORCE_CPU" in os.environ:
        val = os.environ["VIDEO_DRAFT_FORCE_CPU"].lower()
        execution["force_cpu"] = val in ("1", "true", "yes")
    if "VIDEO_DRAFT_SEED" in os.environ:
        try:
            execution["deterministic_seed"] = int(os.environ["VIDEO_DRAFT_SEED"])
        except ValueError:
            raise ConfigurationError(f"VIDEO_DRAFT_SEED must be an integer, got '{os.environ['VIDEO_DRAFT_SEED']}'")

    return data


def load_config(config_path: Optional[str | Path] = None) -> AppConfig:
    """Loads and validates configuration from file path or default search paths."""
    resolved_path: Optional[Path] = None

    if config_path is not None:
        resolved_path = Path(config_path)
        if not resolved_path.is_file():
            raise ConfigurationError(f"Configuration file not found: {resolved_path}")
    else:
        resolved_path = _find_default_config_path()

    raw_data: Dict[str, Any] = {}
    if resolved_path and resolved_path.is_file():
        raw_data = _load_raw_config(resolved_path)

    raw_data = _apply_env_overrides(raw_data)

    try:
        return AppConfig(**raw_data)
    except ValidationError as err:
        raise ConfigurationError(f"Configuration validation failed: {err}") from err
