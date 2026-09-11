# IncuBrix Track 03: Demonstration Evidence Map
## PS03 — Open-Source Draft Video Generation and Model Routing

This document maps each segment of the technical demonstration to the exact files, artifacts, and test fixtures in the repository.

---

| Timestamp | Section | Visual Subject | File / Path in Repository | Primary Technical Metric |
| :--- | :--- | :--- | :--- | :--- |
| **0:00 - 0:30** | Introduction | Project Overview | `README.md`, `pyproject.toml` | Track 03 (PS03), Python 3.14.6 |
| **0:30 - 1:15** | Architecture | Pipeline Contracts | `submission/architecture.md`, `src/video_draft/` | 8 decoupled packages |
| **1:15 - 2:10** | Model Registry | Open Capabilities | `configs/models/registry.yaml` | 5 open models + CPU procedural engine |
| **2:10 - 3:15** | Live Run | CLI Pipeline Execution | `outputs/demo_recording/` | Stages [1/6] to [7/7], 0 errors |
| **3:15 - 4:10** | Video & Archetypes | Final Video Playback | `submission/artifacts/final_draft.mp4` | 20.0s, 1280x720 (16:9), 30 fps, H.264/AAC |
| | | Education Archetype | `outputs/verify_16x9/final_draft.mp4` | 16:9 Landscape, 20.0s, 4 beats |
| | | Product Archetype | `outputs/verify_9x16/final_draft.mp4` | 9:16 Portrait, 15.0s, 4 beats, CTA |
| | | News Archetype | `outputs/verify_news/final_draft.mp4` | 16:9 Landscape, 18.0s, 5 beats, lower-third |
| **4:10 - 5:10** | Artifacts | Multi-track Timeline | `submission/artifacts/timeline.json` | 4 video tracks, 0 gaps, 20.00s |
| | | Subtitles | `submission/artifacts/captions.srt`, `.vtt` | 4 sequential cues, ms precision |
| | | Provenance Manifest | `submission/artifacts/manifest.json` | 10 SHA-256 hashes matching on-disk files |
| | | Quality Gate | `submission/artifacts/evaluation_report.json` | 10/10 checks passed, score 1.0000 |
| **5:10 - 6:00** | Automated Tests | Pytest Regression Suite | `tests/` | 143 passed, 0 failed, 0 skipped |
| | | Submission Audit | `scripts/verify_submission.py` | 7/7 checks passed (100% clean) |
| | | Latency Benchmark | `submission/benchmark_summary.md` | 9.89s avg wall-clock, 188.5 MB RAM |
| **6:00 - 6:45** | Reliability | Fallback Generator | `src/video_draft/adapters/reliable_generator.py` | Transient retry (2x), OOM cascade |
| | | Failure Tests | `tests/unit/test_reliability.py` | 11/11 passed (simulated scenarios) |
| **6:45 - 7:30** | Submission | Completed Workbook | `submission/IncuBrix_PS03_..._COMPLETED.xlsx` | 105 candidate fields populated |
| | | Final Handoff Report | `submission/FINAL_HANDOFF_REPORT.md` | 10-section comprehensive audit |
| | | Disclosure Statement | `submission/DISCLOSURE.md`, `SOURCES.md`, `AI_USE.md` | Zero paid APIs, zero proprietary keys |
| **7:30 - 7:45** | Closing | Remote Synchronization | `https://github.com/vinothinipalanivel2-dotcom/video-draft` | Branch main, commit verified |
