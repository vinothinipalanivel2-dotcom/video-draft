"""Shared pytest fixtures for video_draft test suite."""

import json
from pathlib import Path
import pytest


@pytest.fixture
def sample_valid_brief_dict() -> dict:
    """Returns a valid creative brief dictionary matching IncuBrix requirements."""
    return {
        "id": "test-brief-001",
        "title": "Quantum Computing Fundamentals",
        "genre": "education",
        "aspect_ratio": "16:9",
        "target_duration_sec": 22.5,
        "script": "Classical computers use bits of zeros and ones. Quantum computers use qubits that exist in superposition.",
        "seed": 1337,
        "constraints": {
            "max_latency_sec": 60.0,
            "max_vram_gb": 0.0,
            "allow_cpu_fallback": True,
            "quality_tier": "draft",
        },
    }


@pytest.fixture
def sample_invalid_brief_dict() -> dict:
    """Returns an invalid creative brief dictionary (duration too short, bad aspect ratio)."""
    return {
        "id": "bad-brief-001",
        "title": "Invalid Brief",
        "genre": "invalid_genre",
        "aspect_ratio": "4:3",
        "target_duration_sec": 4.0,  # Below 15.0 minimum
        "script": "Too short",
    }


@pytest.fixture
def temp_brief_file(tmp_path: Path, sample_valid_brief_dict: dict) -> Path:
    """Writes a valid brief to a temporary file."""
    brief_file = tmp_path / "valid_brief.json"
    brief_file.write_text(json.dumps(sample_valid_brief_dict), encoding="utf-8")
    return brief_file


@pytest.fixture
def temp_invalid_brief_file(tmp_path: Path, sample_invalid_brief_dict: dict) -> Path:
    """Writes an invalid brief to a temporary file."""
    brief_file = tmp_path / "invalid_brief.json"
    brief_file.write_text(json.dumps(sample_invalid_brief_dict), encoding="utf-8")
    return brief_file
