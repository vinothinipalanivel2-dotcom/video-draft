"""Factory for video clip generation adapters."""

import os
from typing import Optional

from video_draft.adapters.base import (
    BaseClipGenerator,
    ClipGenerationError,
    ProviderUnavailableError,
)
from video_draft.adapters.mock_generator import MockClipGenerator
from video_draft.adapters.procedural_generator import ProceduralClipGenerator


def get_clip_generator(
    model_id: str,
    mock: bool = False,
    allow_cpu_fallback: bool = True,
    ffmpeg_bin: Optional[str] = None,
) -> BaseClipGenerator:
    """Retrieve an appropriate clip generation adapter for the given model ID.

    Args:
        model_id: The identifier of the video model or engine.
        mock: If True, returns a deterministic mock generator.
        allow_cpu_fallback: If True, falls back to CPU procedural generator for GPU models
                           when accelerator compute is not available.
        ffmpeg_bin: Optional path to FFmpeg binary.

    Returns:
        BaseClipGenerator instance.

    Raises:
        ProviderUnavailableError: If a remote/GPU model is requested without compute and
                                 fallback is disallowed.
    """
    if mock or model_id == "mock":
        return MockClipGenerator()

    # CPU Procedural Engine
    normalized_id = model_id.lower().replace("-", "_")
    if normalized_id in ("cpu_procedural_engine", "procedural", "default"):
        return ProceduralClipGenerator(ffmpeg_bin=ffmpeg_bin)

    # Open-weight GPU models (e.g., zeroscope_v2_576w, animatediff_v15_motion, etc.)
    # Check for configured remote free accelerator endpoint
    remote_endpoint = os.environ.get("VIDEO_DRAFT_REMOTE_INFERENCE_URL")
    if remote_endpoint:
        # Placeholder / hook for remote accelerator worker
        pass

    if allow_cpu_fallback:
        # Transparently use ProceduralClipGenerator as CPU fallback engine
        return ProceduralClipGenerator(ffmpeg_bin=ffmpeg_bin)

    raise ProviderUnavailableError(
        f"Model '{model_id}' requires GPU accelerator compute which is not configured in this environment. "
        "Enable CPU fallback or provide an accelerator compute endpoint.",
        model_id=model_id,
    )
