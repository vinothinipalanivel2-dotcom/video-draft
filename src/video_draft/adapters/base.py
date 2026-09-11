"""Base classes, data structures, and exceptions for video clip generation."""

from abc import ABC, abstractmethod
import hashlib
from pathlib import Path
from typing import Any, Dict, Optional
from pydantic import BaseModel, Field

from video_draft.schema.scene_plan import SceneBeat


class ClipGenerationError(Exception):
    """Raised when an error occurs during clip generation."""
    def __init__(
        self,
        message: str,
        scene_id: Optional[str] = None,
        model_id: Optional[str] = None,
        is_retryable: bool = True,
    ) -> None:
        super().__init__(message)
        self.scene_id = scene_id
        self.model_id = model_id
        self.is_retryable = is_retryable


class TransientGenerationError(ClipGenerationError):
    """Raised for transient, retryable generation failures (e.g. process timeouts, temporary IO)."""
    def __init__(self, message: str, scene_id: Optional[str] = None, model_id: Optional[str] = None) -> None:
        super().__init__(message, scene_id=scene_id, model_id=model_id, is_retryable=True)


class PermanentGenerationError(ClipGenerationError):
    """Raised for permanent, non-retryable generation errors (e.g. format violations)."""
    def __init__(self, message: str, scene_id: Optional[str] = None, model_id: Optional[str] = None) -> None:
        super().__init__(message, scene_id=scene_id, model_id=model_id, is_retryable=False)


class ProviderUnavailableError(ClipGenerationError):
    """Raised when the selected model or provider is not available in the current environment."""
    def __init__(self, message: str, scene_id: Optional[str] = None, model_id: Optional[str] = None) -> None:
        super().__init__(message, scene_id=scene_id, model_id=model_id, is_retryable=False)


class ClipArtifact(BaseModel):
    """Encapsulates a generated intermediate video clip and its validation metadata."""
    scene_id: str = Field(..., description="Unique scene identifier matching SceneBeat")
    scene_index: int = Field(..., ge=1, description="1-based scene index")
    asset_path: str = Field(..., description="Relative or absolute filesystem path to generated video clip")
    asset_hash: str = Field(..., min_length=8, description="SHA-256 hash of the media asset")
    duration_sec: float = Field(..., ge=0.1, description="Authoritative duration of the clip in seconds")
    width: int = Field(..., ge=64, description="Frame width in pixels")
    height: int = Field(..., ge=64, description="Frame height in pixels")
    fps: int = Field(default=30, ge=1, description="Frames per second")
    generator_model: str = Field(..., description="Model or engine ID that generated this clip")
    transition_in: str = Field(default="fade", description="Incoming transition effect")
    transition_out: str = Field(default="fade", description="Outgoing transition effect")
    metadata: Dict[str, Any] = Field(default_factory=dict, description="Generator-specific telemetry and parameters")

    @classmethod
    def compute_sha256(cls, file_path: Path) -> str:
        """Compute SHA-256 hash of a file."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(65536), b""):
                hasher.update(chunk)
        return hasher.hexdigest()


class BaseClipGenerator(ABC):
    """Abstract base class for video generation adapters."""

    @abstractmethod
    def generate_clip(
        self,
        beat: SceneBeat,
        model_id: str,
        aspect_ratio: str,
        output_dir: Path,
    ) -> ClipArtifact:
        """Generate a single video clip corresponding to a planned scene beat.

        Args:
            beat: Authoritative scene beat from ScenePlan.
            model_id: Model or engine identifier.
            aspect_ratio: "16:9" or "9:16".
            output_dir: Destination directory for generated clip artifacts.

        Returns:
            ClipArtifact metadata describing the generated media file.

        Raises:
            ClipGenerationError: If generation fails.
            ProviderUnavailableError: If the provider is not accessible.
        """
        pass
