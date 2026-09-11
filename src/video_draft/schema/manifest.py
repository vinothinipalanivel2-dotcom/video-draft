"""Schema for asset and model manifest."""

from typing import Dict, List
from pydantic import BaseModel, Field


class ModelProvenance(BaseModel):
    model_id: str
    model_name: str
    checkpoint: str
    revision: str
    license: str
    commercial_use: bool
    execution_environment: str


class AssetManifest(BaseModel):
    execution_id: str
    brief_id: str
    timestamp: str
    output_mp4: str
    output_mp4_sha256: str
    timeline_json: str
    route_decision_json: str
    captions_srt: str
    models_used: List[ModelProvenance] = Field(default_factory=list)
    asset_hashes: Dict[str, str] = Field(default_factory=dict)
    reproducibility_seed: int
