"""Schema for editable timeline.json representing assembled draft video."""

from typing import List, Optional
from pydantic import BaseModel, Field


class Resolution(BaseModel):
    width: int
    height: int


class SceneClip(BaseModel):
    scene_id: str
    scene_index: int
    prompt: str
    start_sec: float
    end_sec: float
    duration_sec: float
    asset_path: str
    asset_hash: str
    generator_model: str
    transition_in: Optional[str] = "fade"
    transition_out: Optional[str] = "fade"

    @property
    def timeline_start_sec(self) -> float:
        return self.start_sec

    @property
    def timeline_end_sec(self) -> float:
        return self.end_sec


class AudioTrack(BaseModel):
    track_id: str
    asset_path: str
    start_sec: float
    duration_sec: float
    volume: float = 1.0


class SubtitleTrack(BaseModel):
    track_id: str
    asset_path: str
    format: str = "srt"


class Timeline(BaseModel):
    version: str = "1.0.0"
    brief_id: str
    total_duration_sec: float
    fps: int = 30
    resolution: Resolution
    video_tracks: List[SceneClip] = Field(default_factory=list)
    audio_tracks: List[AudioTrack] = Field(default_factory=list)
    subtitle_tracks: List[SubtitleTrack] = Field(default_factory=list)

    @property
    def total_duration(self) -> float:
        return self.total_duration_sec
