# video-draft: Open-Source Draft Video Generation and Model Routing

[![License: Apache-2.0](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)
[![Python: 3.10+](https://img.shields.io/badge/Python-3.10%2B-green.svg)](pyproject.toml)
[![Compute: Local CPU](https://img.shields.io/badge/Compute-Local%20CPU-orange.svg)](#)
[![Tests: 143 Passing](https://img.shields.io/badge/Tests-143%20Passing-brightgreen.svg)](#)
[![Quality Gate: 10/10 Passed](https://img.shields.io/badge/Quality%20Gate-10%2F10%20Passed-success.svg)](#)

> **IncuBrix Candidate Assessment — Track 03 (PS03)**  
> **Candidate Assessment Submission Package & System Documentation**  
> **Target Architecture**: Local CPU Orchestration, Zero Paid APIs, Open-Weight Models Only

---

## 1. What is this?

`video-draft` is an automated, modular, local-first engine that solves **IncuBrix Track 03 (PS03: Open-Source Draft Video Generation and Model Routing)**. It ingests structured creative briefs and orchestrates:
1. **Explainable Capability-Based Routing**: Multi-dimensional scoring across open-weight models with deterministic tie-breaking and automatic CPU fallback.
2. **Archetype Scene Planning**: Structured narrative decomposition for **Education**, **News**, and **Product** video genres.
3. **Synchronized Audio & Subtitles**: Deterministic master narration synthesis and SubRip (`.srt`) / WebVTT (`.vtt`) timed captions.
4. **Reliable Synthesis**: Bounded retries distinguishing transient glitches from permanent failures.
5. **Broadcast-Standard Video Assembly**: Frame-accurate FFmpeg assembly in **16:9 landscape** ($1280 	imes 720$) and **9:16 portrait** ($720 	imes 1280$) with crossfades and audio muxing.
6. **Objective Quality Gate**: Rigorous 10-dimension release gating verifying bitstream integrity, stream decodability, duration precision, and cross-artifact consistency.
7. **Cryptographic Provenance**: Byte-level SHA-256 asset manifests conforming to assessment specifications.

---

## 2. How Does It Work?

```text
CreativeBrief (.json)
    │
    ▼
Capability Router (Multi-attribute scoring, hard constraints, ranked fallback chain)
    │
    ▼
Scene Planner (Education / News / Product Archetype Strategies)
    │
    ├──▶ Audio Generator (Synthesizes master_narration.wav)
    ├──▶ Subtitle Generator (Generates captions.srt & captions.vtt)
    │
    ▼
Reliable Clip Generator (Bounded retries, transient recovery, CPU procedural fallback)
    │
    ▼
Clip Validator (Verifies geometry, duration, fps, frame continuity)
    │
    ▼
Timeline Builder (Constructs editable multi-track timeline.json)
    │
    ▼
FFmpeg Assembler (Filtergraph scaling, padding, transition crossfades, audio muxing)
    │
    ▼
Quality Gate (Bitstream decodability, probe validation, 7 cross-artifact contracts)
    │
    ▼
Release Artifacts: final_draft.mp4, timeline.json, manifest.json, evaluation_report.json
```

---

## 3. How Do I Run It? (Exact CPU-Safe Commands)

All core commands run 100% locally on a standard CPU laptop without CUDA or paid keys:

### Complete End-to-End Pipeline
```bash
# Generates final video, timeline, plan, captions, manifest, and evaluation report
video-draft run --brief configs/briefs/baseline_16x9.json --output-dir outputs/run1 --mock
```

### Objective Quality Gate Evaluation
```bash
# Probes MP4, validates bitstream decodability, verifies 7 cross-artifact contracts
video-draft evaluate --manifest outputs/run1/manifest.json
```

### Latency & Performance Benchmark
```bash
# Executes 3-run timing benchmark with stage latency breakdown
video-draft benchmark --brief configs/briefs/baseline_16x9.json --runs 3 --output-dir outputs/benchmark
```

### Synthetic Load & Resilience Harness
```bash
# Exercises Education, News, and Product archetypes, 16:9 and 9:16, retries and fallbacks
video-draft benchmark --synthetic --runs 3
```

### Run Full Test Suite (143 Passing Tests)
```bash
pytest -v
```

---

## 4. What Artifacts Are Produced?

Every pipeline run in `--output-dir <dir>` outputs:

| Artifact | File | Description |
| :--- | :--- | :--- |
| **Final Draft Video** | `final_draft.mp4` | Assembled MP4 video with H.264 video and AAC audio. |
| **Editable Timeline** | `timeline.json` | Multi-track specification with clip timings, transitions, and audio tracks. |
| **Scene Plan** | `scene_plan.json` | Decomposed narrative beats with pacing tempos and visual prompts. |
| **Route Decision** | `route_decision.json` | Selected model, candidate scores, hardware target, and fallback chain. |
| **Captions / Subtitles** | `captions.srt` & `.vtt` | Timed SubRip and WebVTT subtitles synchronized with the scene plan. |
| **Asset Manifest** | `manifest.json` | Cryptographic SHA-256 hashes for all inputs, clips, and outputs. |
| **Evaluation Report** | `evaluation_report.json` | Structured Quality Gate scorecard across 10 evaluation dimensions. |

---

## 5. How Does Fallback Work?

Generation reliability uses an ordered fallback hierarchy:

$$	ext{Preferred Model} \longrightarrow 	ext{Ranked Open Alternatives} \longrightarrow 	ext{CPU Procedural Fallback Engine}$$

1. **Hard Constraint Filter**: Disqualifies models exceeding available VRAM or incompatible with the brief duration / aspect ratio.
2. **Controlled Retries**: Transient errors (e.g. socket timeout, file lock) are retried up to 2 times with exponential backoff.
3. **Permanent Failure Fallback**: Non-retryable errors (e.g. CUDA OOM, unsupported codec) immediately skip remaining retries and activate the next candidate model in the chain.
4. **Guaranteed Local Fallback**: The zero-GPU **CPU Procedural Engine** (`procedural_generator.py`) guarantees that an assembled, valid draft video is always produced.

---

## 6. How Is Reproducibility Achieved?

- **Deterministic Seeds**: Briefs declare integer seeds (e.g. `seed: 42`) controlling all procedural visual generation and pacing.
- **Pinned Model Revisions**: Models in `configs/models/registry.yaml` declare explicit Git commit hashes.
- **Deterministic Planning**: Archetype strategies allocate exact mathematical durations without random drift.
- **Cryptographic Manifest**: Byte-level SHA-256 hashes record immutable provenance in `manifest.json`.
- **Idempotent Reruns**: Re-running `video-draft run` purges stale outputs without touching unrelated user files.

---

## 7. Open-Source Model Governance

All registered models use public open weights with transparent licenses:
- **Wan2.1-T2V-1.3B** (Apache-2.0, Wan-AI/Wan2.1-T2V-1.3B)
- **CogVideoX-2B** (Apache-2.0, THUDM/CogVideoX-2b)
- **LTX-Video-0.9.1** (OpenRAIL, Lightricks/LTX-Video)
- **HunyuanVideo** (Apache-2.0, tencent/HunyuanVideo)
- **AnimateDiff-v3** (Apache-2.0, guoyww/animatediff-motion-adapter-v1-5-3)
- **CPU-Procedural-Fallback-Engine** (Apache-2.0, Built-in)

See `submission/model_governance.md` for complete licensing attribution.

---

## 8. How Is Quality Measured?

The **Quality Gate** (`src/video_draft/evaluation/quality_gate.py`) evaluates 10 objective dimensions:
- `planning_validity` (10%): Beat counts and narrative strategy.
- `routing_validity` (10%): Hardware and capability matching.
- `generation_success` (15%): Multi-scene clip synthesis completion.
- `clip_validity` (10%): Resolution, aspect ratio, fps thresholds.
- `final_media_validity` (15%): Stream probe, codec, and bitstream decodability via FFmpeg null muxer.
- `timing_accuracy` (10%): Duration drift $\le 0.5$s against plan.
- `audio_alignment` (10%): Presence and synchronization of audio narration.
- `assembly_validity` (10%): Timeline track alignment with output MP4.
- `cross_consistency` (10%): 7 cross-stage relational contracts.
- `fallback_usage` (Info): Provenance of primary vs fallback generator.

---

## 9. Submission & Documentation Directory

- **`submission/`**: Complete evaluator package with quickstart, architecture, RTM, benchmark metrics, and generated artifacts.
- **`notebooks/video_draft_colab.ipynb`**: Interactive Google Colab / Kaggle demonstration notebook.
- **`docs/`**: Comprehensive developer guides (`quality_and_evaluation.md`, `reliability.md`, `routing.md`, `planner.md`, `assembly.md`, `assessment_checklist.md`).
