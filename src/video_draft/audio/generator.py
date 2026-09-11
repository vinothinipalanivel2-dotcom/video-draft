"""Deterministic audio narration generation and timing alignment."""

from abc import ABC, abstractmethod
import math
from pathlib import Path
import struct
from typing import Any, Dict, List, Optional
import wave
from pydantic import BaseModel, Field

from video_draft.schema.scene_plan import SceneBeat


class AudioGenerationError(Exception):
    """Raised when audio narration generation or concatenation fails."""
    pass


class AudioArtifact(BaseModel):
    """Represents a generated audio clip aligned to a scene beat."""
    track_id: str = Field(..., description="Unique track identifier")
    scene_id: str = Field(..., description="Target scene beat identifier")
    asset_path: str = Field(..., description="Path to generated WAV/MP3 audio file")
    duration_sec: float = Field(..., ge=0.1, description="Audio duration in seconds")
    start_sec: float = Field(..., ge=0.0, description="Timeline start offset in seconds")
    sample_rate: int = Field(default=44100, description="Audio sample rate in Hz")
    metadata: Dict[str, Any] = Field(default_factory=dict)


class BaseAudioGenerator(ABC):
    """Abstract base class for audio narration generators."""

    @abstractmethod
    def generate_scene_audio(self, beat: SceneBeat, output_dir: Path) -> AudioArtifact:
        """Generate an audio chunk for a single scene beat."""
        pass

    @abstractmethod
    def build_narration_track(self, beats: List[SceneBeat], output_path: Path) -> Path:
        """Synthesize and align a complete continuous narration track for all scene beats."""
        pass


class DeterministicAudioGenerator(BaseAudioGenerator):
    """Deterministic, offline audio generator producing compliant WAV audio artifacts.

    Uses Python's standard wave and struct modules to generate exact-duration PCM audio
    without requiring external TTS APIs, payment methods, or GPU compute.
    """

    def __init__(self, sample_rate: int = 44100, base_frequency: float = 220.0) -> None:
        self.sample_rate = sample_rate
        self.base_frequency = base_frequency

    def generate_scene_audio(self, beat: SceneBeat, output_dir: Path) -> AudioArtifact:
        """Generate a deterministic WAV audio file for a single scene beat."""
        output_dir.mkdir(parents=True, exist_ok=True)
        file_path = output_dir / f"{beat.scene_id}_audio.wav"

        duration = beat.duration_sec
        num_samples = int(duration * self.sample_rate)
        freq = self.base_frequency + (beat.scene_index * 25.0)

        # Generate smooth, low-amplitude acoustic tone with subtle fade in/out
        fade_len = min(int(0.05 * self.sample_rate), num_samples // 4)
        raw_frames = bytearray()

        for i in range(num_samples):
            envelope = 1.0
            if i < fade_len:
                envelope = i / fade_len
            elif i > num_samples - fade_len:
                envelope = (num_samples - i) / fade_len

            # Low volume subtle tone (amplitude ~ 2500 out of 32767)
            t = float(i) / self.sample_rate
            sample_val = int(2500 * envelope * math.sin(2.0 * math.pi * freq * t))
            # Pack 16-bit signed integer mono
            raw_frames.extend(struct.pack("<h", sample_val))

        with wave.open(str(file_path), "wb") as wav_file:
            wav_file.setnchannels(1)  # Mono
            wav_file.setsampwidth(2)  # 16-bit
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(raw_frames)

        return AudioArtifact(
            track_id=f"audio_{beat.scene_id}",
            scene_id=beat.scene_id,
            asset_path=str(file_path),
            duration_sec=duration,
            start_sec=beat.start_sec,
            sample_rate=self.sample_rate,
            metadata={
                "narration_chunk": beat.narration_chunk,
                "frequency_hz": freq,
                "samples_count": num_samples,
            },
        )

    def build_narration_track(self, beats: List[SceneBeat], output_path: Path) -> Path:
        """Stitch scene audio into a master narration track aligned to scene start times."""
        if not beats:
            raise AudioGenerationError("Cannot build narration track from empty scene beats list")

        output_path.parent.mkdir(parents=True, exist_ok=True)
        total_duration = max(b.end_sec for b in beats)
        total_samples = int(total_duration * self.sample_rate)

        # Pre-allocate buffer of 16-bit integers
        buffer = [0] * total_samples

        for beat in beats:
            start_idx = int(beat.start_sec * self.sample_rate)
            beat_samples = int(beat.duration_sec * self.sample_rate)
            freq = self.base_frequency + (beat.scene_index * 25.0)
            fade_len = min(int(0.05 * self.sample_rate), beat_samples // 4)

            for i in range(beat_samples):
                buf_idx = start_idx + i
                if buf_idx >= total_samples:
                    break
                envelope = 1.0
                if i < fade_len:
                    envelope = i / fade_len
                elif i > beat_samples - fade_len:
                    envelope = (beat_samples - i) / fade_len

                t = float(i) / self.sample_rate
                sample_val = int(2500 * envelope * math.sin(2.0 * math.pi * freq * t))
                # Add to buffer with clipping protection
                buffer[buf_idx] = max(-32767, min(32767, buffer[buf_idx] + sample_val))

        # Write final WAV
        raw_frames = bytearray()
        for s in buffer:
            raw_frames.extend(struct.pack("<h", s))

        with wave.open(str(output_path), "wb") as wav_file:
            wav_file.setnchannels(1)
            wav_file.setsampwidth(2)
            wav_file.setframerate(self.sample_rate)
            wav_file.writeframes(raw_frames)

        return output_path
