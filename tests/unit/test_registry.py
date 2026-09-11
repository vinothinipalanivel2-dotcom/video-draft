"""Unit tests for the model capability registry and strict validation."""

from pathlib import Path
import pytest
import yaml

from video_draft.router.registry import (
    DurationRange,
    HardwareRequirements,
    ModelCapability,
    ModelRegistry,
    RegistryValidationError,
)


def test_load_official_registry():
    """Verify official configs/models/registry.yaml loads and validates all 6 models."""
    registry = ModelRegistry.load_from_yaml(Path("configs/models/registry.yaml"))
    assert len(registry) == 6

    expected_models = [
        "wan2_1_t2v_1_3b",
        "cogvideox_2b",
        "ltx_video",
        "hunyuan_video",
        "animatediff_v3",
        "cpu_procedural_engine",
    ]
    for m in expected_models:
        assert registry.has_model(m)
        cap = registry.get_model(m)
        assert cap.model_name
        assert cap.license
        assert cap.checkpoint
        assert cap.revision
        assert cap.supported_aspect_ratios
        assert cap.supported_durations.min_sec <= cap.supported_durations.max_sec
        assert cap.hardware_requirements.min_vram_gb >= 0.0
        assert cap.evidence_status in ("measured", "reported", "estimated", "unknown")


def test_registry_missing_file_raises():
    """Verify missing registry file raises RegistryValidationError."""
    with pytest.raises(RegistryValidationError, match="not found"):
        ModelRegistry.load_from_yaml(Path("non_existent_registry.yaml"))


def test_registry_empty_dictionary_raises():
    """Verify empty models dictionary raises RegistryValidationError."""
    with pytest.raises(RegistryValidationError, match="cannot be empty"):
        ModelRegistry.from_dict({"version": "1.0.0", "models": {}})


def test_registry_invalid_aspect_ratio_raises():
    """Verify invalid aspect ratio is rejected by ModelCapability."""
    with pytest.raises(RegistryValidationError, match="Invalid aspect ratio 'invalid_ratio'"):
        ModelRegistry.from_dict(
            {
                "version": "1.0.0",
                "models": {
                    "bad_model": {
                        "model_name": "Bad Model",
                        "checkpoint": "org/bad",
                        "revision": "main",
                        "repository": "https://example.com",
                        "license": "Apache-2.0",
                        "supported_aspect_ratios": ["invalid_ratio"],
                        "supported_durations": {"min_sec": 1.0, "max_sec": 5.0},
                        "hardware_requirements": {
                            "requires_gpu": True,
                            "min_vram_gb": 8.0,
                            "recommended_vram_gb": 12.0,
                            "min_ram_gb": 16.0,
                        },
                        "controllability": 0.8,
                        "expected_latency": 30.0,
                        "reliability": 0.9,
                        "evidence_status": "reported",
                    }
                },
            }
        )


def test_registry_invalid_duration_range_raises():
    """Verify min_sec > max_sec is rejected."""
    with pytest.raises(RegistryValidationError, match="min_sec .* cannot exceed max_sec"):
        ModelRegistry.from_dict(
            {
                "version": "1.0.0",
                "models": {
                    "bad_duration": {
                        "model_name": "Bad Duration Model",
                        "checkpoint": "org/bad",
                        "revision": "main",
                        "repository": "https://example.com",
                        "license": "Apache-2.0",
                        "supported_aspect_ratios": ["16:9"],
                        "supported_durations": {"min_sec": 10.0, "max_sec": 5.0},
                        "hardware_requirements": {
                            "requires_gpu": True,
                            "min_vram_gb": 8.0,
                            "recommended_vram_gb": 12.0,
                            "min_ram_gb": 16.0,
                        },
                        "controllability": 0.8,
                        "expected_latency": 30.0,
                        "reliability": 0.9,
                        "evidence_status": "reported",
                    }
                },
            }
        )


def test_registry_invalid_hardware_vram_raises():
    """Verify min_vram_gb > recommended_vram_gb is rejected."""
    with pytest.raises(RegistryValidationError, match="min_vram_gb .* cannot exceed recommended_vram_gb"):
        ModelRegistry.from_dict(
            {
                "version": "1.0.0",
                "models": {
                    "bad_vram": {
                        "model_name": "Bad VRAM Model",
                        "checkpoint": "org/bad",
                        "revision": "main",
                        "repository": "https://example.com",
                        "license": "Apache-2.0",
                        "supported_aspect_ratios": ["16:9"],
                        "supported_durations": {"min_sec": 1.0, "max_sec": 5.0},
                        "hardware_requirements": {
                            "requires_gpu": True,
                            "min_vram_gb": 16.0,
                            "recommended_vram_gb": 8.0,
                            "min_ram_gb": 16.0,
                        },
                        "controllability": 0.8,
                        "expected_latency": 30.0,
                        "reliability": 0.9,
                        "evidence_status": "reported",
                    }
                },
            }
        )


def test_registry_invalid_evidence_status_raises():
    """Verify unknown/fabricated evidence status is rejected."""
    with pytest.raises(RegistryValidationError, match="Input should be 'measured', 'reported', 'estimated' or 'unknown'"):
        ModelRegistry.from_dict(
            {
                "version": "1.0.0",
                "models": {
                    "bad_evidence": {
                        "model_name": "Bad Evidence Model",
                        "checkpoint": "org/bad",
                        "revision": "main",
                        "repository": "https://example.com",
                        "license": "Apache-2.0",
                        "supported_aspect_ratios": ["16:9"],
                        "supported_durations": {"min_sec": 1.0, "max_sec": 5.0},
                        "hardware_requirements": {
                            "requires_gpu": True,
                            "min_vram_gb": 8.0,
                            "recommended_vram_gb": 12.0,
                            "min_ram_gb": 16.0,
                        },
                        "controllability": 0.8,
                        "expected_latency": 30.0,
                        "reliability": 0.9,
                        "evidence_status": "fabricated_status",
                    }
                },
            }
        )


def test_registry_get_unknown_model_raises():
    """Verify KeyError when requesting an unregistered model ID."""
    registry = ModelRegistry.load_from_yaml()
    with pytest.raises(KeyError, match="not found in registry"):
        registry.get_model("non_existent_model_id")
