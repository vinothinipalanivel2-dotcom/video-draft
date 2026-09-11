# Reproducibility & Determinism Guide
## IncuBrix Track 03: Open-Source Draft Video Generation and Model Routing

## 1. Determinism Guarantees

The `video-draft` system achieves strict deterministic behavior across runs through:

1. **Explicit Random Seeds**: Creative briefs declare an integer `seed` (e.g. `seed: 42`). This seed initializes all procedural noise generators, kinetic transitions, and scene timing offsets.
2. **Pinned Model Checkpoints & Revisions**: Registered models in `configs/models/registry.yaml` declare explicit Git revisions and commit hashes.
3. **Deterministic Scene Planning**: Archetype strategies allocate exact mathematical durations based on target duration and pacing tempo rules.
4. **Idempotent Output Directory Management**: Successive executions of `video-draft run --output-dir <dir>` automatically purge stale intermediate and final video artifacts, ensuring clean state without deleting unrelated user files.
5. **Byte-Level Cryptographic Manifest**: Every artifact (`final_draft.mp4`, `scene_plan.json`, `timeline.json`, `captions.srt`, intermediate clips) is hashed using SHA-256 and recorded in `manifest.json`.

---

## 2. Environment Prerequisites

- **Operating System**: Windows 10/11, macOS, or Linux (Ubuntu 20.04+).
- **Python**: Python 3.10+ (tested on Python 3.14.6).
- **FFmpeg**: Version 4.4+ installed and accessible on system `PATH` (or provided via `imageio-ffmpeg`).
- **GPU**: **None required**. Orchestration, planning, routing, assembly, and evaluation run 100% on standard CPU.

---

## 3. Exact Reproduction Commands

```bash
# 1. Clone repository and install in editable mode
git clone <repo-url>
cd draft-video-routing
pip install -e .

# 2. Verify all 143 automated tests pass
pytest -v

# 3. Reproduce 16:9 Education Draft Run
video-draft run --brief configs/briefs/baseline_16x9.json --output-dir outputs/run_16x9 --mock

# 4. Reproduce 9:16 Product Draft Run
video-draft run --brief configs/briefs/baseline_9x16.json --output-dir outputs/run_9x16 --mock

# 5. Verify Quality Gate Scorecard
video-draft evaluate --manifest outputs/run_16x9/manifest.json

# 6. Run Benchmark Harness
video-draft benchmark --brief configs/briefs/baseline_16x9.json --runs 3
```
