# Automated Latency & Reliability Benchmark Summary
## IncuBrix Track 03: Open-Source Draft Video Generation and Model Routing

## 1. Benchmark Harness Overview

The standalone benchmark engine (`src/video_draft/benchmark/runner.py`) provides millisecond-accurate timing telemetry across isolated pipeline stages using `time.perf_counter()`.

It executes in two modes:
1. **Targeted Brief Benchmarking**: Measures repeated runs of an individual creative brief.
2. **Synthetic Load & Reliability Harness (`--synthetic`)**: Automatically generates multi-genre workloads (Education, News, Product) across both 16:9 landscape and 9:16 portrait aspect ratios, testing transient failure retries and permanent error fallback.

---

## 2. Measured Benchmark Results (Local CPU Environment)

*Environment*: Windows 11 / AMD64 / Python 3.14.6  
*Command*: `video-draft benchmark --brief configs/briefs/baseline_16x9.json --runs 3`

| Metric | Measured Value | Description |
| :--- | :---: | :--- |
| **Total Iterations** | 3 | Complete end-to-end pipeline cycles |
| **Success Rate** | 100% (3 / 3) | 0 pipeline failures |
| **Average Total Wall-Clock Time** | **9.89s** | Full cycle from brief to evaluated MP4 |
| **Planning Stage Latency** | < 0.01s | Scene decomposition & beat timing |
| **Routing Stage Latency** | 0.04s | Capability evaluation & candidate ranking |
| **Audio Synthesis Latency** | 0.84s | Master narration track generation |
| **Clip Generation Latency** | 1.74s | Multi-scene intermediate clip synthesis |
| **Clip Validation Latency** | < 0.01s | Stream and geometry contract checks |
| **FFmpeg Assembly Latency** | 6.54s | Filtergraph scaling, fades, and audio muxing |
| **Quality Gate Evaluation Latency**| 0.73s | Media probing, decodability, and consistency |
| **Primary Model Usage** | 100.0% | Default execution mode |
| **Fallback Usage** | 0.0% | Triggered only upon failure injection |
| **Average Quality Score** | **1.0000** | 10/10 Quality Gate checks passing |

---

## 3. Synthetic Load & Resilience Results

*Command*: `video-draft benchmark --synthetic --runs 3`

- **Archetypes Covered**: Education (4 beats), News (5 beats), Product (4 beats)
- **Aspect Ratios Covered**: 16:9 Landscape ($1280 	imes 720$), 9:16 Portrait ($720 	imes 1280$)
- **Transient Failure Recovery**: Verified automatic retry of simulated network glitches on scene 1.
- **Permanent Failure Fallback**: Verified graceful fallback to CPU procedural engine when primary model encounters simulated memory exhaustion.
- **Synthetic Pass Rate**: 100% across all 3 diverse stress scenarios.
