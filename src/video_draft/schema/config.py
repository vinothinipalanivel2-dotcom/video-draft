"""Configuration schemas for video_draft system."""

from pathlib import Path
from typing import Literal, Optional
from pydantic import BaseModel, Field, field_validator


class SystemSettings(BaseModel):
    """General system settings."""
    project_name: str = "video-draft"
    version: str = "0.1.0"
    environment: Literal["development", "testing", "production"] = "development"
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"] = "INFO"
    log_format: Literal["json", "text"] = "json"


class PathsConfig(BaseModel):
    """Relative filesystem paths for assets, outputs, configs and cache."""
    assets_dir: Path = Field(default_factory=lambda: Path("assets"))
    outputs_dir: Path = Field(default_factory=lambda: Path("outputs"))
    configs_dir: Path = Field(default_factory=lambda: Path("configs"))
    cache_dir: Path = Field(default_factory=lambda: Path(".cache"))

    @field_validator("assets_dir", "outputs_dir", "configs_dir", "cache_dir", mode="before")
    @classmethod
    def parse_path(cls, v: str | Path) -> Path:
        return Path(v)


class ExecutionConfig(BaseModel):
    """Runtime execution constraints."""
    force_cpu: bool = True
    allow_gpu: bool = False
    deterministic_seed: int = 42
    timeout_seconds: int = Field(default=300, ge=1, le=3600)
    resumable: bool = True


class RoutingConfig(BaseModel):
    """Routing rules and registry locations."""
    rules_config: Path = Field(default_factory=lambda: Path("configs/routing_rules.yaml"))
    models_registry: Path = Field(default_factory=lambda: Path("configs/models/registry.yaml"))
    default_fallback: str = "cpu-procedural-engine"

    @field_validator("rules_config", "models_registry", mode="before")
    @classmethod
    def parse_path(cls, v: str | Path) -> Path:
        return Path(v)


class AppConfig(BaseModel):
    """Root application configuration schema."""
    system: SystemSettings = Field(default_factory=SystemSettings)
    paths: PathsConfig = Field(default_factory=PathsConfig)
    execution: ExecutionConfig = Field(default_factory=ExecutionConfig)
    routing: RoutingConfig = Field(default_factory=RoutingConfig)
