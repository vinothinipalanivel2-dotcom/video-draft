# Requirements Traceability Matrix (RTM)
## IncuBrix Track 03: Open-Source Draft Video Generation and Model Routing

| Req ID | Requirement Description | Target Code Location | Verification Test(s) | Status |
| :--- | :--- | :--- | :--- | :---: |
| **R01** | Open-source & open-weight model focus | `configs/models/registry.yaml`, `src/video_draft/router/registry.py` | `tests/unit/test_registry.py` | **VERIFIED** |
| **R02** | Local CPU execution (no mandatory GPU) | `src/video_draft/planner/`, `src/video_draft/assembly/ffmpeg_tools.py` | `tests/integration/test_end_to_end_pipeline.py` | **VERIFIED** |
| **R03** | Generative inference on approved free tiers | `src/video_draft/adapters/base.py`, `notebooks/video_draft_colab.ipynb` | `tests/unit/test_adapters.py` | **VERIFIED** |
| **R04** | Zero paid APIs, proprietary keys, credit cards | Global audit, `configs/system.yaml` | `tests/unit/test_config.py`, `tests/unit/test_imports.py` | **VERIFIED** |
| **R05** | Reproducibility (seeds, pinned revisions, hashing) | `src/video_draft/evaluation/manifest_builder.py`, `quality_gate.py` | `tests/unit/test_quality_gate.py` | **VERIFIED** |
| **R06** | 3 Distinct Archetypes: Education, News, Product | `src/video_draft/planner/strategies/{education,news,product}.py` | `tests/unit/test_planner.py` | **VERIFIED** |
| **R07** | Aspect Ratios: 16:9 Landscape & 9:16 Portrait | `src/video_draft/assembly/ffmpeg_assembler.py`, `procedural_generator.py` | `tests/unit/test_assembly.py` | **VERIFIED** |
| **R08** | Comparison of >= 5 Credible Open Video Models | `configs/models/registry.yaml`, `docs/routing.md` | `tests/unit/test_registry.py`, `tests/unit/test_router.py` | **VERIFIED** |
| **R09** | Capability-Based Routing Engine | `src/video_draft/router/capability_router.py` (and `router.py`) | `tests/unit/test_router.py`, `tests/unit/test_cli.py` | **VERIFIED** |
| **R10** | Ranked Fallback Chain & CPU Procedural Fallback | `src/video_draft/adapters/reliable_generator.py`, `procedural_generator.py`| `tests/unit/test_reliability.py` | **VERIFIED** |
| **R11** | Idempotence & Safe Pipeline Reruns | `src/video_draft/cli.py` (`run_cmd`) | `tests/integration/test_end_to_end_pipeline.py` | **VERIFIED** |
| **R12a**| Final MP4 Draft Video (15-30s) | `src/video_draft/assembly/ffmpeg_assembler.py` | `tests/unit/test_media_validator.py` | **VERIFIED** |
| **R12b**| Editable `timeline.json` | `src/video_draft/assembly/timeline_builder.py` | `tests/unit/test_assembly.py` | **VERIFIED** |
| **R12c**| Structured `route_decision.json` | `src/video_draft/schema/routing.py` | `tests/unit/test_router.py` | **VERIFIED** |
| **R12d**| Asset & Model Manifest (`manifest.json`) | `src/video_draft/evaluation/manifest_builder.py` | `tests/unit/test_quality_gate.py` | **VERIFIED** |
| **R12e**| Subtitles / Captions (.srt, .vtt) | `src/video_draft/audio/subtitles.py` | `tests/unit/test_quality_gate.py` | **VERIFIED** |
| **R12f**| Execution & Structured Logging | `src/video_draft/utils/logger.py` | `tests/unit/test_logger.py` | **VERIFIED** |
| **R13** | CLI Interface (`run`, `evaluate`, `benchmark`) | `src/video_draft/cli.py` | `tests/unit/test_cli.py` | **VERIFIED** |
| **R14** | Automated Test Suite & Benchmark Harness | `tests/`, `src/video_draft/benchmark/runner.py` | 143 automated tests passing | **VERIFIED** |
| **R15** | Governance: Open-Source Model Attribution | `submission/model_governance.md`, `configs/models/registry.yaml` | `tests/unit/test_registry.py` | **VERIFIED** |
| **R16** | Live Validation Ownership & Bounded Live Change | `src/video_draft/evaluation/quality_gate.py`, `router/router.py` | `tests/unit/test_consistency.py` | **VERIFIED** |
