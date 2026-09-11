# Explainable Model Routing & Capability Registry

**Project**: `video-draft` (IncuBrix Track 03: Open-Source Draft Video Generation and Model Routing)  
**Module**: `video_draft.router` (`registry.py`, `router.py`)  
**Configuration**: `configs/models/registry.yaml`, `configs/routing_rules.yaml`

---

## 1. Routing Architecture

The `video-draft` model routing engine evaluates input creative briefs against a capability registry of open-weight video models and system hardware profiles. It executes a two-stage evaluation pipeline:

```
+-------------------------------------------------------------------------+
|                           CREATIVE BRIEF INPUT                          |
|   (genre, aspect_ratio, target_duration_sec, constraints, script)       |
+------------------------------------+------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|                  STAGE 1: HARD CONSTRAINT FILTERING                     |
|  - Eliminates incompatible models before scoring                        |
|  - Checks: availability, aspect ratio, hardware/VRAM/RAM, force_cpu,    |
|    commercial license requirement, max latency budget                   |
|  - Records explicit disqualification reason for every eliminated model  |
+------------------------------------+------------------------------------+
                                     |
                         [Eligible Candidates]
                                     |
                                     v
+-------------------------------------------------------------------------+
|                  STAGE 2: MULTI-ATTRIBUTE SCORING                       |
|  - Normalizes scores across 8 attributes [0.0, 1.0]:                    |
|    * Quality           * Use-case fit       * Controllability           |
|    * Hardware fit      * Latency score      * Reliability               |
|    * Aspect ratio fit  * Duration fit                                   |
|  - Applies configurable use-case weights (education, news, product)     |
+------------------------------------+------------------------------------+
                                     |
                                     v
+-------------------------------------------------------------------------+
|               STAGE 3: SELECTION & FALLBACK HIERARCHY                   |
|  - Primary Route: Top-scoring eligible generative video model           |
|  - Secondary Alternatives: Ranked runners-up                            |
|  - Fail-Safe Fallback: CPU-Procedural-Fallback-Engine                   |
|  - Output: Fully explainable RouteDecision artifact                     |
+-------------------------------------------------------------------------+
```

---

## 2. Capability Registry

The capability registry is defined declaratively in `configs/models/registry.yaml` and loaded programmatically by `ModelRegistry` in `src/video_draft/router/registry.py`. Model capabilities are never hardcoded in Python.

### Registered Models (5 Open-Weight + 1 Fallback)

| Model ID | Model Name | Architecture | Parameters | License | Min VRAM | Supported AR | Evidence Status |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `wan2_1_t2v_1_3b` | Wan2.1-T2V-1.3B | Flow-Matching DiT | 1.3B | Apache-2.0 | 8.0 GB | 16:9, 9:16, 1:1 | Reported |
| `cogvideox_2b` | CogVideoX-2B | 3D Causal VAE + DiT | 2.0B | Apache-2.0 | 10.0 GB | 16:9, 9:16 | Reported |
| `ltx_video` | LTX-Video-0.9.1 | Spatial-Temporal Transformer | 2.0B | OpenRAIL | 12.0 GB | 16:9, 9:16 | Reported |
| `hunyuan_video` | HunyuanVideo | Dual-Stream DiT | 13.0B | Apache-2.0 | 24.0 GB | 16:9, 9:16 | Reported |
| `animatediff_v3` | AnimateDiff-v3 | UNet Motion Module + SD1.5 | 1.0B | Apache-2.0 | 6.0 GB | 16:9, 9:16, 1:1 | Reported |
| `cpu_procedural_engine` | CPU-Procedural-Fallback-Engine | Procedural Motion Graphics | None (Code) | Apache-2.0 | 0.0 GB | 16:9, 9:16, 1:1 | Measured |

### Evidence Status Distinction
The registry strictly enforces the `evidence_status` enum:
- `measured`: Benchmark numbers verified directly on local test machines.
- `reported`: Official numbers taken directly from published model cards and research papers.
- `estimated`: Calculated projections based on architecture specifications.
- `unknown`: Values for which no credible primary source exists. Unknown values are never replaced with fabricated numbers.

---

## 3. Hard Constraints

Before any candidate model is scored, it must satisfy all hard constraints. If a model fails any check, it is immediately disqualified and its exact rejection reason is recorded in `RouteDecision.rejection_reasons`.

1. **Model Availability**: If `model.availability == False` (e.g. HunyuanVideo on free-tier accelerators), it is disqualified.
2. **Aspect Ratio Compatibility**: The brief's requested aspect ratio (e.g. `16:9` or `9:16`) must exist in `model.supported_aspect_ratios`.
3. **GPU Requirement & Force-CPU**: If `force_cpu=True` or host hardware lacks an accelerator, all models with `hardware_requirements.requires_gpu == True` are eliminated.
4. **Host RAM Capacity**: System RAM must satisfy `model.hardware_requirements.min_ram_gb`.
5. **GPU VRAM Capacity**: Available GPU VRAM must meet or exceed `model.hardware_requirements.min_vram_gb`.
6. **Commercial License Constraint**: If the brief specifies `quality_tier="production"` or the configuration enforces commercial use, models with non-commercial licenses are eliminated.
7. **Latency Budget**: If the brief defines `max_latency_sec`, models whose `expected_latency` exceeds the budget are disqualified.

---

## 4. Scoring Algorithm

For all models that pass hard constraints, the router calculates normalized sub-scores in $[0.0, 1.0]$:

1. **Quality Score ($S_{\text{quality}}$)**:
   $$S_{\text{quality}} = 0.5 \cdot \text{controllability} + 0.5 \cdot \text{reliability}$$
2. **Use-Case Fit ($S_{\text{use\_case}}$)**:
   Model affinity for the brief's genre (e.g. `model.use_case_fit.get(genre)`).
3. **Controllability Score ($S_{\text{ctrl}}$)**:
   Direct measure of prompt following and motion controllability.
4. **Hardware Fit Score ($S_{\text{hw}}$)**:
   Evaluates efficiency and resource overhead. Models with smaller VRAM footprints on given hardware score higher.
5. **Latency Score ($S_{\text{lat}}$)**:
   $$S_{\text{lat}} = \max\left(0.0, 1.0 - \frac{\text{expected\_latency}}{160.0}\right)$$
6. **Reliability Score ($S_{\text{rel}}$)**:
   Historical completion and defect-free generation rate.
7. **Aspect Ratio Fit ($S_{\text{ar}}$)**:
   $1.0$ if the aspect ratio is natively rendered; $0.5$ if cropping/padding is required.
8. **Duration Fit ($S_{\text{dur}}$)**:
   $1.0$ if target scene duration ($\approx \text{total\_duration} / 4$) falls cleanly within $[min\_sec, max\_sec]$; $0.7$ otherwise.

### Composite Score Formula
$$\text{Final Score} = \sum_{i} w_i \cdot S_i$$
Where weights $\sum_i w_i = 1.0$.

---

## 5. Configurable Weights

Scoring weights are declared in `configs/routing_rules.yaml`. The router applies archetype-specific weight profiles:

| Scoring Attribute | Default Weight | Education Archetype | News Archetype | Product Archetype |
| :--- | :--- | :--- | :--- | :--- |
| **Quality** | 0.25 | 0.15 | 0.10 | **0.30** |
| **Use-Case Fit** | 0.20 | 0.20 | 0.20 | 0.20 |
| **Controllability** | 0.15 | **0.25** | 0.10 | 0.15 |
| **Latency** | 0.10 | 0.05 | **0.25** | 0.02 |
| **Reliability** | 0.10 | 0.15 | **0.20** | 0.10 |
| **Hardware Fit** | 0.10 | 0.05 | 0.05 | 0.03 |
| **Aspect Ratio Fit** | 0.05 | 0.10 | 0.05 | **0.15** |
| **Duration Fit** | 0.05 | 0.05 | 0.05 | 0.05 |

---

## 6. Fallback Strategy & Hierarchy

The routing engine implements a deterministic 4-stage fallback hierarchy:

1. **Preferred Compatible Model**: Highest-scoring generative video model passing all hard constraints.
2. **Secondary Compatible Model**: Runner-up generative model, ready to take over if the preferred model encounters a runtime exception or timeout.
3. **Alternative Compatible Model**: Third-ranked generative candidate.
4. **CPU Procedural Fallback Engine (`cpu_procedural_engine`)**: Always-available, 100% offline procedural generator synthesizing Ken-Burns motion graphics and typography on CPU.

The designated fallback model and trigger conditions are recorded explicitly in `RouteDecision.fallback`.

---

## 7. CPU-Only Behavior

When running on a local non-GPU laptop:
- In `--force-cpu` mode (or when no CUDA accelerator is detected):
  - All GPU diffusion models are rejected with: `"GPU inference disabled (force_cpu=True or CPU-only target)"`.
  - The router selects `cpu_procedural_engine`.
  - Execution completes in seconds without attempting video diffusion on CPU.

---

## 8. Deterministic Behavior

The routing algorithm is strictly deterministic:
- Given identical creative brief contents and configuration, the scoring engine produces identical composite scores, ranking, and candidate evaluations.
- Brief hashing uses SHA-256 (`RouteDecision.input_brief_hash`), ensuring that routing decisions can be validated and audited across sessions.

---

## 9. CLI Usage Examples

### Standard Evaluation
```bash
video-draft route --brief configs/briefs/baseline_16x9.json
```

### Force CPU Fallback
```bash
video-draft route --brief configs/briefs/baseline_16x9.json --force-cpu
```

### Export Route Decision to JSON
```bash
video-draft route --brief configs/briefs/baseline_16x9.json --output outputs/route_decision.json
```

---

## 10. Limitations

1. **Static Latency Profiles**: Current latency evaluations use reported benchmark estimates. Dynamic latency tracking will be integrated in Phase 6/7.
2. **Discrete Aspect Ratios**: Models are evaluated against discrete standard aspect ratios (`16:9`, `9:16`, `1:1`). Arbitrary free-form aspect ratios require letterboxing.
3. **Free-Tier Memory Constraints**: Large foundation models ($>10\text{B}$ parameters, like HunyuanVideo) cannot execute on free-tier 15GB GPUs and require CPU fallback or smaller open-weight models (Wan2.1-1.3B, CogVideoX-2B, LTX-Video).
