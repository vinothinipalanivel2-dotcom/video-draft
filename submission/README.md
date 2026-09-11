# IncuBrix Track 03: Open-Source Draft Video Generation and Model Routing
## Candidate Assessment Submission Package

**Candidate**: Track 03 Lead Architect  
**Evaluation Target**: IncuBrix Track 03 (SASTRA 2027 Graduate Hiring)  
**System Status**: **Production-Hardened & Release Ready (143/143 Automated Tests Passing)**  
**Target Hardware**: 100% Local CPU Execution (Zero GPU dependency, zero commercial/paid APIs)

---

## Executive Summary

`video-draft` is an automated, modular, local-first engine for synthesizing multi-scene draft videos from creative briefs. It integrates:
- **Capability-Based Model Routing**: Explainable multi-attribute scoring across 5 open-weight models with deterministic tie-breaking and automatic CPU procedural fallback.
- **Archetype-Specific Scene Planning**: Deterministic decomposition for **Education**, **News**, and **Product** genres with pacing tempos and visual prompts.
- **Reliable Clip Synthesis**: Bounded retries distinguishing transient glitches from permanent failures with graceful fallback chaining.
- **FFmpeg Assembly & Muxing**: Frame-accurate multi-track video assembly, smooth transitions, and synchronized narration audio.
- **Multi-Format Subtitles**: Timed SubRip (`.srt`) and WebVTT (`.vtt`) caption generation.
- **Objective Quality Gate**: Rigorous 10-dimension evaluation verifying bitstream decodability, duration precision, and cross-artifact consistency.
- **Cryptographic Provenance**: Byte-level SHA-256 asset manifests and reproducible seed management.

---

## Evaluator Quickstart (Single Commands)

All commands are designed to run safely on a standard CPU host:

### 1. Run Complete Pipeline (Generates MP4, Timeline, Captions, Manifest)
```bash
video-draft run --brief configs/briefs/baseline_16x9.json --output-dir outputs/demo --mock
```

### 2. Run Objective Quality Gate Evaluation
```bash
video-draft evaluate --manifest outputs/demo/manifest.json
```

### 3. Run Automated Benchmark Harness
```bash
video-draft benchmark --brief configs/briefs/baseline_16x9.json --runs 3 --output-dir outputs/benchmark
```

### 4. Run Synthetic Load & Reliability Test (Exercises All Archetypes & Fallbacks)
```bash
video-draft benchmark --synthetic --runs 3
```

### 5. Run Complete Test Suite
```bash
pytest -v
```

---

## Submission Package Contents

- **`submission/architecture.md`**: Architectural breakdown, module descriptions, and ASCII data-flow diagram.
- **`submission/requirements_traceability.md`**: Complete R01–R16 assessment requirements compliance matrix.
- **`submission/benchmark_summary.md`**: Measured CPU execution latency breakdown and throughput metrics.
- **`submission/reproducibility.md`**: Deterministic reproduction guide, environment setup, and seed control.
- **`submission/model_governance.md`**: Open-source license attribution, Hugging Face checkpoints, and hardware profiles.
- **`submission/DISCLOSURE.md`**: Factual assessment disclosure covering AI assistance, tools, compute, assets, and models.
- **`submission/final_submission_checklist.md`**: Section-by-section verification checklist and final recommendation.
- **`submission/evidence_index.md`**: Direct traceability index mapping requirements to concrete files.
- **`submission/artifacts/`**:
  - `final_draft.mp4`: Assembled 16:9 draft video.
  - `timeline.json`: Multi-track timeline specification.
  - `scene_plan.json`: Structured beat decomposition.
  - `route_decision.json`: Explainable model routing artifact.
  - `captions.srt` & `captions.vtt`: Timed subtitle cues.
  - `manifest.json`: Cryptographic SHA-256 asset manifest.
  - `evaluation_report.json`: Quality Gate evaluation scorecard (10/10 checks passed).
  - `benchmark_report.json`: Multi-run latency benchmark metrics.
