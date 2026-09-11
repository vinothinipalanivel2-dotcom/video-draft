# Phase 5: Model Routing, Fallback & Generation Reliability

## 1. Overview & Architectural Goals

The **Generation Reliability Engine** guarantees deterministic, explainable, and resilient video draft production across heterogeneous execution environments. It bridges the gap between capability evaluation and synthesis execution by coupling:

1. **Scene-Aware Capability Routing**: Multi-dimensional scoring evaluating hardware, aspect ratios, latency budgets, and individual scene beat duration constraints.
2. **Deterministic Fallback Chains**: Explicit candidate ordering (`Preferred Model -> Ranked Alternatives -> CPU Procedural Fallback -> Controlled Failure`).
3. **Controlled Retry Policies**: Bounded retries distinguishing transient (retryable) errors from permanent (non-retryable) failures.
4. **End-to-End Observability**: Telemetry logging every attempt, retry count, fallback event, and artifact provenance metadata.

---

## 2. Hard Constraint Evaluation & Scene-Aware Filtering

Before scoring candidates, each registered model undergoes strict Boolean constraint evaluation:

| Constraint Dimension | Rule | Failure Behavior |
| :--- | :--- | :--- |
| **Availability** | `model.available == True` | Disqualified with `"Model is marked unavailable"` |
| **Hardware / VRAM** | Requires GPU only if CUDA accelerator present or free accelerator enabled | Disqualified with `"No CUDA-capable accelerator detected"` |
| **VRAM Ceiling** | `min_vram_gb <= brief.constraints.max_vram_gb` | Disqualified with `"Requires X GB VRAM, exceeds Y GB limit"` |
| **Aspect Ratio** | `brief.aspect_ratio in model.supported_aspect_ratios` | Disqualified with `"Unsupported aspect ratio"` |
| **Duration Bounds** | Scene-aware check: all scene durations $t_s \in [min, max]$ | Disqualified with `"Scene duration X exceeds model max Y"` |
| **Latency Budget** | `expected_latency <= max_latency_sec` (if budgeted) | Disqualified with `"Expected latency X exceeds budget Y"` |

If all generative models are eliminated by hard constraints, the router automatically activates the zero-GPU **CPU Procedural Fallback Engine**.

---

## 3. Multi-Dimensional Scoring & Candidate Ranking

For all eligible candidates, the routing engine calculates a normalized score $\in [0.0, 1.0]$:

$$\text{Score} = \sum_{k} w_k \cdot S_k$$

Where the dimension scores $S_k$ are:
- **Quality Score ($S_{\text{quality}}$)**: Base visual fidelity metric from capability registry.
- **Use-Case Fit ($S_{\text{use\_case}}$)**: Match for brief genre (`education`, `news`, `product`).
- **Controllability ($S_{\text{controllability}}$)**: Prompt adherence, camera control, and layout stability.
- **Hardware Fit ($S_{\text{hardware}}$)**: Proximity to optimal VRAM and local efficiency.
- **Latency Score ($S_{\text{latency}}$)**: Inversely proportional to synthesis duration ($1.0 - t_{\text{lat}} / 160.0$).
- **Reliability ($S_{\text{reliability}}$)**: Historic generation consistency and failure rate.
- **Aspect Ratio Fit ($S_{\text{ar}}$)**: Native support bonus.
- **Duration Fit ($S_{\text{dur}}$)**: Scene beat duration compatibility score.

### Archetype Weight Matrices

Routing weights are dynamically mapped to creative brief genres:

| Dimension | Education Weight | News Weight | Product Weight |
| :--- | :---: | :---: | :---: |
| `quality` | 0.20 | 0.15 | 0.30 |
| `use_case_fit` | 0.20 | 0.20 | 0.20 |
| `controllability` | 0.25 | 0.15 | 0.25 |
| `hardware_fit` | 0.10 | 0.15 | 0.05 |
| `latency` | 0.05 | 0.20 | 0.05 |
| `reliability` | 0.20 | 0.15 | 0.15 |

### Deterministic Tie-Breaking
Candidate ranking sorts by `(-score, model_id)` to ensure identical inputs yield identical routes across platforms and executions.

---

## 4. Fallback Chain Architecture

The `RouteDecision` artifact publishes an explicit fallback sequence:

```
+-------------------------------------------------------------+
| Preferred Candidate (Rank #1 Eligible Generative Model)     |
+-------------------------------------------------------------+
                               | (Fails or Exhausts Retries)
                               v
+-------------------------------------------------------------+
| Alternative Candidates (Ranked #2..N Eligible Models)       |
+-------------------------------------------------------------+
                               | (Fails or Exhausts Retries)
                               v
+-------------------------------------------------------------+
| CPU Procedural Fallback Engine (Guaranteed Execution Target) |
+-------------------------------------------------------------+
                               | (Fails or Disabled)
                               v
+-------------------------------------------------------------+
| Controlled Failure (Raises GenerationReliabilityError)      |
+-------------------------------------------------------------+
```

---

## 5. Controlled Retry Policy

Synthesis attempts use bounded exponential or linear backoff configured via `RetryPolicy`:

### Transient vs. Permanent Error Classification

```python
class RetryPolicy(BaseModel):
    max_retries: int = 2
    backoff_sec: float = 0.05
    enable_fallback_chain: bool = True
```

- **Transient (Retryable)**:
  - Network timeouts or API connection drops (`TransientGenerationError`)
  - Render race conditions / missing temporary files (`file_existence`, `file_size`)
  - Retried up to `max_retries` with delay before fallback.
- **Permanent (Non-Retryable)**:
  - Provider unavailable or missing local driver (`ProviderUnavailableError`)
  - Model unsupported or format failure (`PermanentGenerationError`)
  - Structural mismatch (`duration`, `aspect_ratio`, `scene_id` validation errors)
  - **Zero retries wasted**: Immediately triggers fallback to next candidate.

---

## 6. Telemetry and Observability

Each generated scene clip produces a `GenerationReport` and enriches `ClipArtifact.metadata`:

```json
{
  "scene_id": "scene_01",
  "requested_model": "wan2_1_t2v_1_3b",
  "final_model": "cpu_procedural_engine",
  "fallback_occurred": true,
  "fallback_reason": "No CUDA-capable accelerator detected on host system.",
  "total_attempts": 2,
  "candidate_chain": [
    "wan2_1_t2v_1_3b",
    "cpu_procedural_engine"
  ],
  "attempts": [
    {
      "model_id": "wan2_1_t2v_1_3b",
      "attempt_number": 1,
      "success": false,
      "error_message": "ProviderUnavailableError: Host GPU required",
      "is_fallback": false
    },
    {
      "model_id": "cpu_procedural_engine",
      "attempt_number": 1,
      "success": true,
      "is_fallback": true
    }
  ]
}
```

---

## 7. Verification & Test Coverage

The reliability subsystem is verified by 11 unit tests in `tests/unit/test_reliability.py` as part of the 114-test regression suite:

1. `test_route_decision_fallback_chain_construction`: Verifies chain ordering and CPU inclusion.
2. `test_route_with_scene_aware_duration`: Verifies candidate disqualification when scene durations exceed model limits.
3. `test_retry_policy_classification`: Verifies classification of transient vs permanent errors.
4. `test_reliable_generator_direct_success`: Confirms clean pass-through without fallbacks.
5. `test_reliable_generator_transient_retry_success`: Verifies attempt 1 failure and attempt 2 recovery.
6. `test_reliable_generator_fallback_to_secondary`: Verifies transition from primary to secondary model.
7. `test_reliable_generator_non_retryable_skips_retries`: Confirms immediate fallback on permanent errors.
8. `test_reliable_generator_complete_exhaustion_raises`: Confirms structured `GenerationReliabilityError`.
9. `test_reliable_generator_fallback_disabled`: Verifies behavior when `enable_fallback_chain=False`.
10. `test_route_decision_serialization_with_phase5_fields`: Verifies schema round-trip serialization.
11. `test_cli_route_displays_fallback_chain`: Validates CLI terminal presentation.
