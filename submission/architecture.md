# System Architecture & Technical Design
## IncuBrix Track 03: Open-Source Draft Video Generation and Model Routing

## 1. High-Level Architecture Overview

`video-draft` is designed as a local-first, modular Python system that orchestrates draft video creation from creative briefs with zero proprietary APIs and zero mandatory GPU requirements:

```text
+---------------------------------------------------------------------------------------------------+
|                                            INPUT LAYER                                            |
|  - CreativeBrief (.json): genre, aspect_ratio (16:9 / 9:16), target_duration (15-30s), script     |
|  - Constraints: max_vram_gb, allow_cpu_fallback, quality_tier                                      |
+-------------------------------------------------+-------------------------------------------------+
                                                  |
                                                  v
+-------------------------------------------------+-------------------------------------------------+
|                                     INTERFACE & ORCHESTRATION                                     |
|  - Click CLI: validate | plan | route | generate | assemble | evaluate | benchmark | run           |
|  - Structured Logging: JSON-lines format with ISO timestamps, event taxonomy, and elapsed times   |
+-------------------------------------------------+-------------------------------------------------+
                                                  |
                                                  v
+-------------------------------------------------+-------------------------------------------------+
|                                      SCENE PLANNING SUBSYSTEM                                     |
|  - ScenePlanner: Orchestrates beat allocation and narrative progression                           |
|  - Archetype Strategies:                                                                          |
|      * EducationStrategy: 4-beat structure (Hook, Core Explainer, Deep Dive, Summary)             |
|      * NewsStrategy: 5-beat structure (Breaking Hook, Facts, Field Detail, Context, Wrap)         |
|      * ProductStrategy: 4-beat structure (Hero Reveal, Feature Showcase, Real-World Use, CTA)     |
|  - Outputs: ScenePlan (.json) with per-scene pacing tempos and visual prompt specifications       |
+-------------------------------------------------+-------------------------------------------------+
                                                  |
                                                  v
+-------------------------------------------------+-------------------------------------------------+
|                                    CAPABILITY ROUTING ENGINE                                      |
|  - ModelRegistry: 5 open-weight models (Wan2.1-1.3B, CogVideoX-2B, LTX-Video, Hunyuan, AnimateDiff)|
|  - Constraint Filter: Hard boolean filtering (availability, VRAM ceiling, aspect ratio, duration) |
|  - Multi-Dimensional Scoring: Weighted sum based on genre archetype                              |
|  - Fallback Chain: Deterministic candidate ordering ending in CPU-Procedural-Fallback-Engine       |
|  - Outputs: RouteDecision (.json)                                                                 |
+-------------------------------------------------+-------------------------------------------------+
                                                  |
                                                  v
+-------------------------------------------------+-------------------------------------------------+
|                                    AUDIO & SUBTITLE GENERATION                                    |
|  - DeterministicAudioGenerator: Pure-tone / synthesized narration track (master_narration.wav)    |
|  - SubtitleGenerator: Synchronized SubRip (.srt) and WebVTT (.vtt) caption cue generation         |
+-------------------------------------------------+-------------------------------------------------+
                                                  |
                                                  v
+-------------------------------------------------+-------------------------------------------------+
|                                   RELIABLE GENERATION ADAPTERS                                    |
|  - BaseClipGenerator: Abstract synthesis interface                                                |
|  - MockClipGenerator: Deterministic test generator with synthetic frame sequences                |
|  - ProceduralClipGenerator: Zero-GPU Ken-Burns panning, kinetic typography, and procedural color  |
|  - Free Accelerator Adapters: Ingestion abstractions for Colab T4, Kaggle P100, HF ZeroGPU        |
|  - ReliableClipGenerator: Bounded retry loop (transient vs permanent) and fallback execution      |
|  - ClipValidator: Verification of individual MP4 streams (geometry, duration, fps)              |
+-------------------------------------------------+-------------------------------------------------+
                                                  |
                                                  v
+-------------------------------------------------+-------------------------------------------------+
|                                    ASSEMBLY & TIMELINE ENGINE                                     |
|  - TimelineBuilder: Multi-track representation with scene clips, transitions, and audio track    |
|  - FFmpegAssembler: Filtergraph scaling, padding (setsar=1, format=yuv420p), transition fades    |
|  - Audio Muxing: Synchronous multiplexing with aac audio stream                                   |
|  - Outputs: final_draft.mp4 & timeline.json                                                       |
+-------------------------------------------------+-------------------------------------------------+
                                                  |
                                                  v
+-------------------------------------------------+-------------------------------------------------+
|                                 QUALITY GATE & PROVENANCE SUBSYSTEM                               |
|  - FinalMediaValidator: Bitstream integrity (ffmpeg null-muxer decode), probe validation          |
|  - CrossArtifactConsistencyChecker: 7 cross-stage relational contracts                            |
|  - ManifestBuilder: Byte-level SHA-256 asset hashing and provenance tracking                      |
|  - QualityGate: Objective 10-dimension evaluation scorecard (0.0 - 1.0)                           |
|  - Outputs: manifest.json & evaluation_report.json                                                |
+---------------------------------------------------------------------------------------------------+
```

## 2. Model-Agnostic Design Rationale

The engine does not hardcode any single generative model. Instead, models are treated as interchangeable capability providers defined in `configs/models/registry.yaml`.

This model-agnostic abstraction guarantees:
1. **Zero Vendor Lock-In**: Any open model can be registered with its VRAM ceiling, aspect ratios, and speed profile.
2. **Deterministic Fallbacks**: If high-VRAM models are unavailable or encounter runtime errors, execution cascades gracefully to lightweight alternatives or the local CPU procedural engine.
3. **Hardware Agnosticism**: Runs on non-GPU developer laptops, free Colab T4 instances, or dedicated multi-GPU clusters using the identical CLI interface.
