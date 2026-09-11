"""Builder for standard AssetManifest recording execution provenance and asset hashes."""

import datetime
import hashlib
from pathlib import Path
from typing import Dict, List, Optional, Union

from video_draft.router.registry import ModelRegistry
from video_draft.schema.brief import CreativeBrief
from video_draft.schema.manifest import AssetManifest, ModelProvenance
from video_draft.schema.routing import RouteDecision


def compute_file_sha256(filepath: Union[Path, str]) -> str:
    """Calculate the SHA-256 hexadecimal hash of a file on disk."""
    p = Path(filepath)
    if not p.is_file():
        return ""
    hasher = hashlib.sha256()
    with open(p, "rb") as f:
        while chunk := f.read(65536):
            hasher.update(chunk)
    return hasher.hexdigest()


class ManifestBuilder:
    """Constructs verifiable AssetManifest conforming to schema/manifest.py."""

    @staticmethod
    def build_manifest(
        brief: CreativeBrief,
        output_dir: Union[Path, str],
        output_mp4: Union[Path, str],
        timeline_json: Union[Path, str],
        route_decision_json: Union[Path, str],
        captions_srt: Union[Path, str],
        route_decision: Optional[RouteDecision] = None,
        registry: Optional[ModelRegistry] = None,
        execution_id: Optional[str] = None,
    ) -> AssetManifest:
        """Build an AssetManifest recording all file hashes and model provenance.

        Args:
            brief: Input CreativeBrief.
            output_dir: Output base directory.
            output_mp4: Path to assembled final MP4.
            timeline_json: Path to timeline.json.
            route_decision_json: Path to route_decision.json.
            captions_srt: Path to captions.srt.
            route_decision: Optional RouteDecision object.
            registry: Optional ModelRegistry.
            execution_id: Unique run ID (defaults to brief_id + timestamp).

        Returns:
            Validated AssetManifest instance.
        """
        out_base = Path(output_dir)
        now_iso = datetime.datetime.now(datetime.timezone.utc).isoformat()
        exec_id = execution_id or f"exec-{brief.id}-{int(datetime.datetime.now(datetime.timezone.utc).timestamp())}"

        # 1. Compute hashes of key artifacts
        mp4_path = Path(output_mp4)
        mp4_hash = compute_file_sha256(mp4_path)

        asset_hashes: Dict[str, str] = {
            "output_mp4": mp4_hash,
            "timeline_json": compute_file_sha256(timeline_json),
            "route_decision_json": compute_file_sha256(route_decision_json),
            "captions_srt": compute_file_sha256(captions_srt),
        }

        # Include scene plan if present
        plan_file = out_base / "scene_plan.json"
        if plan_file.is_file():
            asset_hashes["scene_plan_json"] = compute_file_sha256(plan_file)

        # Include audio track if present
        audio_file = out_base / "audio" / "master_narration.wav"
        if audio_file.is_file():
            asset_hashes["master_narration_wav"] = compute_file_sha256(audio_file)

        # Include all intermediate clips
        clips_dir = out_base / "clips"
        if clips_dir.is_dir():
            for clip_path in sorted(clips_dir.glob("*.mp4")):
                asset_hashes[clip_path.name] = compute_file_sha256(clip_path)

        # 2. Build Model Provenance records
        models_used: List[ModelProvenance] = []
        model_id = route_decision.selected_model if route_decision else "cpu_procedural_engine"
        target_hw = route_decision.target_hardware if route_decision else "cpu"

        if registry is None:
            try:
                registry = ModelRegistry.load_from_yaml()
            except Exception:
                registry = None

        if registry and model_id in registry:
            cap = registry[model_id]
            provenance = ModelProvenance(
                model_id=cap.model_id,
                model_name=cap.model_name,
                checkpoint=f"hf.co/{cap.model_id}",
                revision="main",
                license=cap.license,
                commercial_use=cap.commercial_use,
                execution_environment=target_hw,
            )
        else:
            provenance = ModelProvenance(
                model_id=model_id,
                model_name=route_decision.selected_model_name if route_decision else "CPU Procedural Fallback",
                checkpoint="builtin/procedural",
                revision="v1.0.0",
                license="Apache-2.0",
                commercial_use=True,
                execution_environment=target_hw,
            )
        models_used.append(provenance)

        return AssetManifest(
            execution_id=exec_id,
            brief_id=brief.id,
            timestamp=now_iso,
            output_mp4=str(output_mp4),
            output_mp4_sha256=mp4_hash,
            timeline_json=str(timeline_json),
            route_decision_json=str(route_decision_json),
            captions_srt=str(captions_srt),
            models_used=models_used,
            asset_hashes=asset_hashes,
            reproducibility_seed=brief.seed or 42,
        )

    @staticmethod
    def save_manifest(manifest: AssetManifest, output_file: Union[Path, str]) -> Path:
        """Serialize and save manifest to JSON file."""
        target = Path(output_file)
        target.parent.mkdir(parents=True, exist_ok=True)
        target.write_text(manifest.model_dump_json(indent=2), encoding="utf-8")
        return target
