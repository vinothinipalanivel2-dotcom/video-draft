"""Programmatic capability registry for open-source video generation models."""

import os
from pathlib import Path
from typing import Any, Dict, List, Literal, Optional
import yaml
from pydantic import BaseModel, Field, field_validator, model_validator


EvidenceStatusType = Literal["measured", "reported", "estimated", "unknown"]

VALID_ASPECT_RATIOS = {"16:9", "9:16", "1:1", "4:3", "21:9"}
VALID_LICENSES = {
    "Apache-2.0",
    "OpenRAIL",
    "OpenRAIL-M",
    "Creative Commons",
    "MIT",
    "BSD-3-Clause",
    "GPL-3.0",
}


class RegistryValidationError(Exception):
    """Raised when the capability registry YAML or dictionary fails validation."""
    pass


class DurationRange(BaseModel):
    """Supported clip duration bounds in seconds."""
    min_sec: float = Field(..., ge=0.1, description="Minimum clip duration in seconds")
    max_sec: float = Field(..., ge=0.1, description="Maximum clip duration in seconds")

    @model_validator(mode="after")
    def validate_duration_bounds(self) -> "DurationRange":
        if self.min_sec > self.max_sec:
            raise ValueError(f"min_sec ({self.min_sec}) cannot exceed max_sec ({self.max_sec})")
        return self


class HardwareRequirements(BaseModel):
    """Execution hardware requirements for a model."""
    requires_gpu: bool = Field(default=True, description="Whether GPU accelerator is required")
    min_vram_gb: float = Field(..., ge=0.0, description="Minimum VRAM in gigabytes")
    recommended_vram_gb: float = Field(..., ge=0.0, description="Recommended VRAM in gigabytes")
    min_ram_gb: float = Field(..., ge=1.0, description="Minimum system RAM in gigabytes")

    @model_validator(mode="after")
    def validate_vram_bounds(self) -> "HardwareRequirements":
        if self.min_vram_gb > self.recommended_vram_gb:
            raise ValueError(
                f"min_vram_gb ({self.min_vram_gb}) cannot exceed recommended_vram_gb ({self.recommended_vram_gb})"
            )
        return self


class ModelCapability(BaseModel):
    """Detailed capability profile for an open-weight or fallback video model."""
    model_id: str = Field(..., min_length=1, description="Unique model identifier")
    model_name: str = Field(..., min_length=1, description="Human-readable model name")
    checkpoint: str = Field(..., min_length=1, description="Hugging Face repo, local path, or checkpoint tag")
    revision: str = Field(..., min_length=1, description="Git commit SHA, tag, or version")
    repository: str = Field(..., min_length=1, description="Source code repository URL or identifier")
    license: str = Field(..., min_length=1, description="Software and weights license identifier")
    commercial_use: bool = Field(default=True, description="Whether commercial deployment is permitted")
    generation_type: str = Field(default="text-to-video", description="Inference modality")
    supported_aspect_ratios: List[str] = Field(..., min_length=1, description="List of supported aspect ratios")
    supported_durations: DurationRange = Field(..., description="Duration bounds for single-shot generation")
    supported_resolutions: List[str] = Field(default_factory=list, description="Output resolutions")
    hardware_requirements: HardwareRequirements = Field(..., description="Hardware prerequisites")
    estimated_vram_gb: Optional[float] = Field(default=None, ge=0.0)
    parameter_count: Optional[str] = Field(default=None, description="Model weights parameter count (e.g. '1.3B')")
    controllability: float = Field(..., ge=0.0, le=1.0, description="Prompt adherence and motion controllability")
    style_strengths: List[str] = Field(default_factory=list, description="Visual styles with high fidelity")
    use_case_fit: Dict[str, float] = Field(
        default_factory=dict, description="Affinity scores per archetype [0.0, 1.0]"
    )
    expected_latency: float = Field(..., ge=0.0, description="Expected generation latency per clip in seconds")
    reliability: float = Field(..., ge=0.0, le=1.0, description="Execution success and temporal defect score")
    availability: bool = Field(default=True, description="Whether model is available on target environment")
    limitations: List[str] = Field(default_factory=list, description="Known failure modes and boundaries")
    source_urls: List[str] = Field(default_factory=list, description="Primary sources and documentation links")
    evidence_status: EvidenceStatusType = Field(
        ..., description="Provenance quality: measured, reported, estimated, unknown"
    )

    @field_validator("supported_aspect_ratios")
    @classmethod
    def validate_aspect_ratios(cls, ratios: List[str]) -> List[str]:
        if not ratios:
            raise ValueError("Model must support at least one aspect ratio.")
        for r in ratios:
            if r not in VALID_ASPECT_RATIOS:
                raise ValueError(f"Invalid aspect ratio '{r}'. Must be one of {sorted(VALID_ASPECT_RATIOS)}")
        return ratios

    @field_validator("license")
    @classmethod
    def validate_license(cls, lic: str) -> str:
        clean = lic.strip()
        if not clean:
            raise ValueError("License string cannot be empty.")
        return clean

    @field_validator("use_case_fit")
    @classmethod
    def validate_use_case_fit(cls, fit: Dict[str, float]) -> Dict[str, float]:
        for k, v in fit.items():
            if not (0.0 <= v <= 1.0):
                raise ValueError(f"use_case_fit score for '{k}' must be between 0.0 and 1.0, got {v}")
        return fit


class ModelRegistry:
    """In-memory model registry loaded from YAML configuration."""

    def __init__(self, version: str = "1.0.0", models: Optional[Dict[str, ModelCapability]] = None):
        self.version = version
        self._models: Dict[str, ModelCapability] = models or {}

    @classmethod
    def load_from_yaml(cls, yaml_path: Optional[str | Path] = None) -> "ModelRegistry":
        """Loads and strictly validates model capabilities from registry YAML file."""
        if yaml_path is None:
            yaml_path = Path("configs/models/registry.yaml")
        else:
            yaml_path = Path(yaml_path)

        if not yaml_path.is_file():
            raise RegistryValidationError(f"Model registry file not found: {yaml_path}")

        try:
            content = yaml_path.read_text(encoding="utf-8")
            data = yaml.safe_load(content)
        except Exception as err:
            raise RegistryValidationError(f"Failed to read/parse registry YAML {yaml_path}: {err}") from err

        return cls.from_dict(data)

    @classmethod
    def from_dict(cls, data: Any) -> "ModelRegistry":
        """Validates and instantiates ModelRegistry from parsed dictionary."""
        if not isinstance(data, dict):
            raise RegistryValidationError(f"Registry data must be a dictionary, got {type(data).__name__}")

        version = data.get("version", "1.0.0")
        raw_models = data.get("models")

        if not isinstance(raw_models, dict):
            raise RegistryValidationError("Registry must contain a top-level 'models' dictionary mapping IDs to models.")

        if not raw_models:
            raise RegistryValidationError("Registry 'models' dictionary cannot be empty.")

        models: Dict[str, ModelCapability] = {}
        seen_ids = set()

        for key, model_data in raw_models.items():
            if not isinstance(model_data, dict):
                raise RegistryValidationError(f"Model entry '{key}' must be a dictionary.")

            # Ensure model_id is set
            model_data.setdefault("model_id", key)
            model_id = model_data.get("model_id")

            if model_id in seen_ids:
                raise RegistryValidationError(f"Duplicate model_id detected in registry: '{model_id}'")
            seen_ids.add(model_id)

            try:
                capability = ModelCapability(**model_data)
                models[model_id] = capability
            except Exception as err:
                raise RegistryValidationError(f"Validation failed for model '{model_id}': {err}") from err

        return cls(version=version, models=models)

    def get_model(self, model_id: str) -> ModelCapability:
        """Retrieves a model capability by its ID. Raises KeyError if not found."""
        if model_id not in self._models:
            raise KeyError(f"Model '{model_id}' not found in registry. Available: {list(self._models.keys())}")
        return self._models[model_id]

    def list_models(self) -> List[ModelCapability]:
        """Returns all registered models."""
        return list(self._models.values())

    def list_model_ids(self) -> List[str]:
        """Returns list of registered model IDs."""
        return list(self._models.keys())

    def has_model(self, model_id: str) -> bool:
        """Checks if a model ID is registered."""
        return model_id in self._models

    def __contains__(self, model_id: str) -> bool:
        """Checks if model_id is present in registry via 'in' operator."""
        return model_id in self._models

    def __getitem__(self, model_id: str) -> ModelCapability:
        """Retrieves model by indexing registry[model_id]."""
        return self.get_model(model_id)

    def __len__(self) -> int:
        return len(self._models)
