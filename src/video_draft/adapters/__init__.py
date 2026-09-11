"""Video generation adapters (CPU procedural fallback, remote free compute, mock)."""

from video_draft.adapters.base import (
    BaseClipGenerator,
    ClipArtifact,
    ClipGenerationError,
    PermanentGenerationError,
    ProviderUnavailableError,
    TransientGenerationError,
)
from video_draft.adapters.factory import get_clip_generator
from video_draft.adapters.mock_generator import MockClipGenerator
from video_draft.adapters.procedural_generator import ProceduralClipGenerator
from video_draft.adapters.reliable_generator import (
    GenerationAttempt,
    GenerationReliabilityError,
    GenerationReport,
    ReliableClipGenerator,
    RetryPolicy,
)
from video_draft.adapters.validator import ClipValidationError, ClipValidator

__all__ = [
    "BaseClipGenerator",
    "ClipArtifact",
    "ClipGenerationError",
    "PermanentGenerationError",
    "ProviderUnavailableError",
    "TransientGenerationError",
    "ClipValidationError",
    "ClipValidator",
    "MockClipGenerator",
    "ProceduralClipGenerator",
    "GenerationAttempt",
    "GenerationReliabilityError",
    "GenerationReport",
    "ReliableClipGenerator",
    "RetryPolicy",
    "get_clip_generator",
]
