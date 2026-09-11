# Evidence Index: IncuBrix Track 03 Assessment
## Open-Source Draft Video Generation and Model Routing

This index provides direct traceability between assessment requirements, concrete implementation source files, automated test suites, and empirical runtime artifacts.

---

## 1. Requirements to Implementation & Artifact Map

| Requirement ID | Primary Source File(s) | Verification Test File(s) | Generated Artifact(s) |
| :--- | :--- | :--- | :--- |
| **R01: Open-Weight Models** | `configs/models/registry.yaml`<br>`src/video_draft/router/registry.py` | `tests/unit/test_registry.py` | `submission/model_governance.md` |
| **R02: Local CPU Orchestration** | `src/video_draft/planner/`<br>`src/video_draft/assembly/ffmpeg_tools.py` | `tests/integration/test_end_to_end_pipeline.py`<br>`tests/unit/test_assembly.py` | `submission/artifacts/final_draft.mp4`<br>`submission/benchmark_summary.md` |
| **R03: Free-Tier Acceleration** | `src/video_draft/adapters/base.py`<br>`notebooks/video_draft_colab.ipynb` | `tests/unit/test_adapters.py` | `notebooks/video_draft_colab.ipynb` |
| **R04: Zero Paid APIs** | Codebase audit<br>`configs/system.yaml` | `tests/unit/test_config.py`<br>`tests/unit/test_imports.py` | `submission/DISCLOSURE.md` |
| **R05: Reproducibility & Provenance** | `src/video_draft/evaluation/manifest_builder.py`<br>`src/video_draft/schema/brief.py` | `tests/unit/test_quality_gate.py` | `submission/artifacts/manifest.json`<br>`submission/reproducibility.md` |
| **R06: Three Archetypes** | `src/video_draft/planner/strategies/education.py`<br>`src/video_draft/planner/strategies/news.py`<br>`src/video_draft/planner/strategies/product.py` | `tests/unit/test_planner.py` | `outputs/verify_16x9/final_draft.mp4`<br>`outputs/verify_9x16/final_draft.mp4`<br>`outputs/verify_news/final_draft.mp4` |
| **R07: 16:9 & 9:16 Aspect Ratios** | `src/video_draft/assembly/ffmpeg_assembler.py`<br>`src/video_draft/adapters/procedural_generator.py` | `tests/unit/test_assembly.py`<br>`tests/unit/test_media_validator.py` | `outputs/verify_16x9/final_draft.mp4` (1280x720)<br>`outputs/verify_9x16/final_draft.mp4` (720x1280) |
| **R08: Comparison of >= 5 Models** | `configs/models/registry.yaml`<br>`docs/routing.md` | `tests/unit/test_registry.py`<br>`tests/unit/test_router.py` | `submission/model_governance.md`<br>`docs/routing.md` |
| **R09: Capability-Based Routing** | `src/video_draft/router/router.py`<br>`configs/routing_rules.yaml` | `tests/unit/test_router.py`<br>`tests/unit/test_cli.py` | `submission/artifacts/route_decision.json` |
| **R10: Ranked Fallback Chain** | `src/video_draft/adapters/reliable_generator.py`<br>`src/video_draft/adapters/procedural_generator.py` | `tests/unit/test_reliability.py` | `submission/artifacts/route_decision.json`<br>`tests/unit/test_reliability.py` |
| **R11: Idempotency & Safe Reruns** | `src/video_draft/cli.py` (`run_cmd`) | `tests/integration/test_end_to_end_pipeline.py` | `outputs/idempotency_test/` |
| **R12a: Final Draft MP4** | `src/video_draft/assembly/ffmpeg_assembler.py` | `tests/unit/test_media_validator.py` | `submission/artifacts/final_draft.mp4` |
| **R12b: Editable Timeline** | `src/video_draft/assembly/timeline_builder.py`<br>`src/video_draft/schema/timeline.py` | `tests/unit/test_assembly.py` | `submission/artifacts/timeline.json` |
| **R12c: Route Decision** | `src/video_draft/schema/routing.py`<br>`src/video_draft/router/router.py` | `tests/unit/test_router.py` | `submission/artifacts/route_decision.json` |
| **R12d: Asset Manifest** | `src/video_draft/evaluation/manifest_builder.py`<br>`src/video_draft/schema/manifest.py` | `tests/unit/test_quality_gate.py` | `submission/artifacts/manifest.json` |
| **R12e: Captions (.srt/.vtt)** | `src/video_draft/audio/subtitles.py` | `tests/unit/test_quality_gate.py` | `submission/artifacts/captions.srt`<br>`submission/artifacts/captions.vtt` |
| **R12f: Structured Logging** | `src/video_draft/utils/logger.py` | `tests/unit/test_logger.py` | Execution console logs & telemetry |
| **R13: Public CLI Suite** | `src/video_draft/cli.py` | `tests/unit/test_cli.py` | CLI verbs: `validate`, `plan`, `route`, `generate`, `assemble`, `evaluate`, `benchmark`, `run` |
| **R14: Test & Benchmark Suite** | `tests/`<br>`src/video_draft/benchmark/runner.py` | `tests/unit/test_benchmark.py` | 143 passing tests<br>`submission/artifacts/benchmark_report.json` |
| **R15: Model Governance** | `configs/models/registry.yaml`<br>`submission/model_governance.md` | `tests/unit/test_registry.py` | `submission/model_governance.md` |
| **R16: Quality Gate & Consistency** | `src/video_draft/evaluation/quality_gate.py`<br>`src/video_draft/evaluation/consistency.py` | `tests/unit/test_consistency.py`<br>`tests/unit/test_quality_gate.py` | `submission/artifacts/evaluation_report.json` (Score: 1.0000) |

---

## 2. Directory Structure of Submission Package

```text
submission/
├── README.md                              # Evaluator quickstart and overview
├── architecture.md                        # Complete module architecture and data-flow
├── requirements_traceability.md           # R01–R16 assessment compliance matrix
├── benchmark_summary.md                   # Latency, throughput, and synthetic benchmark results
├── reproducibility.md                     # Exact commands for reproducing verified outputs
├── model_governance.md                    # Open-weight license attribution and profiles
├── DISCLOSURE.md                          # IncuBrix assessment tools, compute, and AI disclosure
├── final_submission_checklist.md          # Multi-section verification checklist and recommendation
├── evidence_index.md                      # This file
├── FINAL_HANDOFF_REPORT.md                # Definitive final handoff documentation
├── submission_validation_report.json      # Output of automated SubmissionValidator (7/7 passed)
└── artifacts/
    ├── final_draft.mp4                    # Decodable 16:9 draft video with synced audio
    ├── timeline.json                      # Continuous multi-track timeline specification
    ├── scene_plan.json                    # 4-beat structured scene plan
    ├── route_decision.json                # Explainable multi-attribute routing decision
    ├── captions.srt                       # Synchronized SubRip subtitles
    ├── captions.vtt                       # Synchronized WebVTT subtitles
    ├── manifest.json                      # Cryptographic SHA-256 asset provenance manifest
    ├── evaluation_report.json             # 10/10 Quality Gate evaluation scorecard
    ├── benchmark_report.json              # Multi-run benchmark execution telemetry
    ├── clips/                             # Intermediate synthesized scene clips
    └── audio/                             # Synthesized master narration audio track
```
