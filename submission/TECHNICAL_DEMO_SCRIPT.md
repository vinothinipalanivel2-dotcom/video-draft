# IncuBrix Track 03: Technical Demonstration Video Recording Script
## PS03 — Open-Source Draft Video Generation and Model Routing
### Project: `video-draft` | Target Duration: 7m 30s (Max 8m 00s)

---

## Pre-Recording Setup & Teleprompter Guide

### 1. Screen & Window Configuration
- **Screen Resolution**: 1920x1080 (1080p, 16:9). Recommended recording software: OBS Studio or Windows Game Bar (Win+Alt+R).
- **Audio Setup**: Clean microphone input with noise suppression enabled; no background music or audio alerts.
- **Split-Screen / Tab Layout**:
  - **Left 60%**: VS Code open to `C:\Users\Vino\.gemini\antigravity\scratch\draft-video-routing`.
  - **Right 40%**: Integrated Terminal (PowerShell) with clean virtualenv prompt.
  - **Secondary Window**: Media player (VLC or Windows Media Player) pre-loaded with `submission/artifacts/final_draft.mp4`.
  - **Browser Window**: Tab 1 with local GitHub repository (`https://github.com/vinothinipalanivel2-dotcom/video-draft`), Tab 2 with Google Colab notebook (`notebooks/video_draft_colab.ipynb`).

### 2. Pre-Opened Files in VS Code
1. `README.md` (Root project overview)
2. `submission/architecture.md` (Pipeline flow diagram)
3. `configs/models/registry.yaml` (Capability registry & open models)
4. `submission/artifacts/final_draft.mp4` (Final demonstrated video)
5. `submission/artifacts/timeline.json` (Multi-track timeline)
6. `submission/artifacts/captions.srt` (Synchronized subtitles)
7. `submission/artifacts/manifest.json` (SHA-256 cryptographic provenance)
8. `submission/artifacts/evaluation_report.json` (Quality Gate 1.0000 report)
9. `submission/benchmark_summary.md` (Empirical latency & memory metrics)
10. `submission/DISCLOSURE.md` (Attribution & payment disclosure)
11. `submission/IncuBrix_PS03_Submission_Evaluation_Batch_Moderation_Workbook_COMPLETED.xlsx` (Completed official workbook)

---

## Video Timeline & Spoken Cue Script

```
+-------------------+---------------------------------------------------------+
| Timestamp Range   | Section Title & Primary Screen Focus                    |
+-------------------+---------------------------------------------------------+
| 0:00 - 0:40 (40s) | Introduction: Project Scope, Assessment & Pipeline Flow |
| 0:40 - 1:30 (50s) | Modular Architecture & Package Structure                |
| 1:30 - 2:30 (60s) | Open Model Registry, Capabilities & Fallback Strategy   |
| 2:30 - 3:30 (60s) | Live Pipeline Execution: CLI to Evaluated Draft         |
| 3:30 - 4:30 (60s) | Demonstrated Video Output & Three Use-Case Archetypes   |
| 4:30 - 5:30 (60s) | Artifact Verification: Timeline, Captions & Quality Gate|
| 5:30 - 6:30 (60s) | Automated Testing & Empirical Latency/Memory Benchmark  |
| 6:30 - 7:15 (45s) | Resilience, Reliability & Controlled Failure Recovery   |
| 7:15 - 7:45 (30s) | Assessment Integrity, Free Compute Disclosure & Handoff |
+-------------------+---------------------------------------------------------+
| Total: 7m 45s (Well within the 8-minute maximum hard cutoff)                |
+-------------------+---------------------------------------------------------+
```

---

### Segment 1: Introduction (0:00 – 0:40)
- **Time Allocation**: 40 seconds (Target word count: ~85 words)
- **On-Screen Display**:
  - Show VS Code editor viewing `README.md` and repository tree in the explorer sidebar.
  - Highlight project header: `video-draft` — IncuBrix Track 03 (PS03).
- **Spoken Narration**:
  > "Hello evaluators. Welcome to the technical demonstration of `video-draft`, our implementation for IncuBrix Track 03: Open-Source Draft Video Generation and Model Routing.
  >
  > This project implements a fully reproducible, deterministic pipeline that transforms a structured creative brief into a broadcast-ready draft video with synchronized narration, captions, and transparent provenance.
  >
  > The core pipeline operates as a strict contract-driven cascade:
  > `CreativeBrief` triggers multi-factor `RouteDecision`, generates an archetype-aware `ScenePlan`, synthesizes intermediate `Clips`, builds an editable `Timeline`, mixes master `Audio`, and renders a decodable `Final MP4 Video`."

---

### Segment 2: Modular Architecture & Contracts (0:40 – 1:30)
- **Time Allocation**: 50 seconds (Target word count: ~110 words)
- **On-Screen Display**:
  - Open `submission/architecture.md`.
  - Scroll through the ASCII architectural diagram and package layout under `src/video_draft/`.
  - Briefly expand `src/video_draft/` in the sidebar (`planner/`, `router/`, `adapters/`, `audio/`, `assembly/`, `evaluation/`).
- **Spoken Narration**:
  > "Let's inspect the system architecture. The platform is organized into clean, decoupled modules under `src/video_draft`.
  >
  > First, the **Planner** parses input briefs and applies domain-specific archetype strategies for Educational explainers, News commentary, or Product socials.
  >
  > Next, the **Router** evaluates model capabilities against hardware constraints, scoring candidate architectures deterministically.
  >
  > The **Adapters** layer provides modular ingestion with retry logic and fallback chaining.
  >
  > The **Audio** synthesizer creates synchronized waveforms, while the **Assembly** engine leverages native FFmpeg filtergraphs for cross-fades, letterboxing, and subtitle burn-in.
  >
  > Finally, the **Evaluation** package enforces rigorous Quality Gates and computes SHA-256 cryptographic manifests, ensuring complete reproducibility."

---

### Segment 3: Open Model Registry & Capability Routing (1:30 – 2:30)
- **Time Allocation**: 60 seconds (Target word count: ~135 words)
- **On-Screen Display**:
  - Open `configs/models/registry.yaml`.
  - Scroll to show the cataloged models: `wan2_1_t2v_1_3b`, `cogvideox_2b`, `ltx_video`, `hunyuan_video`, `animatediff_v3`, and `cpu_procedural_engine`.
  - Highlight metadata: licenses (`Apache-2.0`, `OpenRAIL`), parameter counts, and VRAM requirements.
- **Spoken Narration**:
  > "Now, let's examine the Capability Registry in `configs/models/registry.yaml`.
  >
  > The system catalogs five premier open-weight generative video models:
  > 1. Wan2.1-T2V-1.3B under Apache-2.0 for cinematic motion dynamics.
  > 2. CogVideoX-2B under Apache-2.0 featuring a 3D causal VAE.
  > 3. LTX-Video-0.9.1 under OpenRAIL for ultra-fast DiT sampling.
  > 4. HunyuanVideo from Tencent, requiring 24 GB of VRAM.
  > 5. AnimateDiff-v3 for lightweight 6 GB consumer GPU rendering.
  >
  > Crucially, for honest engineering disclosure: these neural diffusion models are cataloged with verified Hugging Face checkpoints and tested via simulated adapters and routing algorithms.
  >
  > In our active local environment, the system executes the zero-GPU `cpu_procedural_engine`. When running without accelerator hardware, the router automatically cascades to this CPU engine, guaranteeing that high-definition draft videos render reliably without GPU dependencies or cloud API costs."

---

### Segment 4: Live Pipeline Execution (2:30 – 3:30)
- **Time Allocation**: 60 seconds (Target word count: ~120 words)
- **On-Screen Display**:
  - Focus the terminal window.
  - Run the baseline pipeline command into a demonstration output directory:
    ```powershell
    python -m video_draft.cli run --brief configs/briefs/baseline_16x9.json --output-dir outputs/demo_run
    ```
  - Highlight the live terminal logs: `[1/6] ROUTE`, `[2/6] PLAN`, `[3/6] AUDIO`, `[4/6] GENERATE`, `[5/6] VALIDATE`, `[6/6] ASSEMBLE`, `[7/7] QUALITY`.
- **Spoken Narration**:
  > "Let's demonstrate a live end-to-end run on our local CPU host using the command-line interface.
  >
  > We execute `python -m video_draft.cli run` targeting our baseline educational brief, writing to `outputs/demo_run` so existing submission artifacts remain pristine.
  >
  > Watch the sequential stage progression in the terminal:
  > Step 1 routes to our CPU Procedural Fallback Engine based on local hardware constraints.
  > Step 2 plans 4 educational beats totaling 20.0 seconds.
  > Step 3 synthesizes narration audio and formats synchronized SRT and VTT subtitles.
  > Step 4 procedurally generates 4 intermediate scene clips with kinetic typography.
  > Step 5 validates stream geometry via ffprobe.
  > Step 6 executes FFmpeg assembly with smooth cross-dissolves.
  > And Step 7 executes our Quality Gate, passing 10 out of 10 checks with a perfect 1.0000 score."

---

### Segment 5: Final Demonstrated Video & 3 Archetypes (3:30 – 4:30)
- **Time Allocation**: 60 seconds (Target word count: ~130 words)
- **On-Screen Display**:
  - Switch to the media player and play `submission/artifacts/final_draft.mp4` with audio enabled for 15–20 seconds.
  - Show the video: 1280x720 16:9, kinetic typography cards, transition dissolves, and synchronized narration.
  - In VS Code, open `submission/FINAL_HANDOFF_REPORT.md` Section 6 and show the 3 verified archetype outputs:
    - Education: `outputs/verify_16x9/final_draft.mp4` (16:9, 20.0s, 4 beats)
    - Product: `outputs/verify_9x16/final_draft.mp4` (9:16 portrait, 15.0s, 4 beats)
    - News: `outputs/verify_news/final_draft.mp4` (16:9, 18.0s, 5 beats)
- **Spoken Narration**:
  > "Here is the resulting output: `submission/artifacts/final_draft.mp4`.
  >
  > Notice the clean 16:9 1280x720 resolution, smooth 30 fps playback, synchronized multi-tone narration, and legible kinetic typography.
  >
  > The system supports three distinct creative archetypes with materially different pacing and visual layouts:
  > First, **Education** in 16:9 landscape, featuring 4 pedagogical beats: Hook, Core Concept, Demonstration, and Summary.
  > Second, **Product / Social Reels** in native 9:16 vertical portrait (720x1280), featuring rapid 3-second cuts, centered framing, and a prominent Call to Action.
  > Third, **News Commentary** in 16:9, featuring 5 high-tempo beats with lower-third visual anchors.
  >
  > Each archetype changes the underlying scene structure, pacing, and visual framing, rather than merely altering a text prompt."

---

### Segment 6: Artifact Verification, Timeline & Captions (4:30 – 5:30)
- **Time Allocation**: 60 seconds (Target word count: ~135 words)
- **On-Screen Display**:
  - Open `submission/artifacts/timeline.json`: show resolution (1280x720), duration (20.0s), 4 video tracks, cut points, and transition effects.
  - Open `submission/artifacts/captions.srt` & `captions.vtt`: show sequential timecodes matching scene boundaries.
  - Open `submission/artifacts/manifest.json`: show the SHA-256 digests for all 10 assets.
  - Open `submission/artifacts/evaluation_report.json`: show the 10 quality checks (`planning_validity`, `routing_validity`, `final_media_validity`, `cross_consistency`, etc.).
- **Spoken Narration**:
  > "Let's inspect the generated submission artifacts.
  >
  > In `timeline.json`, we have a non-destructive multi-track schema recording exact clip start times, durations, and dissolve transitions.
  >
  > Our subtitle generator produces both SubRip `captions.srt` and WebVTT `captions.vtt`, aligned to millisecond scene boundaries without text overlap.
  >
  > In `manifest.json`, every file—from raw clips to the master WAV and final MP4—is cryptographically hashed with SHA-256. All 10 hashes match the files on disk byte-for-byte.
  >
  > Finally, `evaluation_report.json` captures the automated Quality Gate results: 10 out of 10 checks passed, verifying zero duration drift, valid H.264 High profile streams, AAC audio presence, and complete cross-artifact consistency."

---

### Segment 7: Automated Testing & Latency Benchmark (5:30 – 6:30)
- **Time Allocation**: 60 seconds (Target word count: ~130 words)
- **On-Screen Display**:
  - In terminal, execute:
    ```powershell
    python -m pytest tests/ -q
    ```
  - Show the output: `143 passed in 140.60s`.
  - In VS Code, open `submission/benchmark_summary.md` and show the telemetry table.
  - Run the automated submission verification script:
    ```powershell
    python scripts/verify_submission.py
    ```
  - Show output: `7/7 checks passed (100% clean) — READY FOR SUBMISSION`.
- **Spoken Narration**:
  > "Engineering quality is backed by comprehensive automated testing.
  >
  > Running `python -m pytest tests/`, our test suite executes 143 automated tests across unit, integration, and end-to-end reliability harnesses. Every single test passes with zero failures, zero errors, and zero skipped tests.
  >
  > In `submission/benchmark_summary.md`, our millisecond telemetry reveals an average total wall-clock pipeline latency of 9.89 seconds on standard laptop CPU. Planning takes under 10 milliseconds, capability routing takes 40 milliseconds, clip synthesis takes 1.74 seconds, and FFmpeg filtergraph assembly completes in 6.54 seconds with a peak RAM footprint of just 188.5 MB.
  >
  > Our automated validator verifies that all 7 submission criteria, documentation files, and cryptographic hashes are 100% compliant."

---

### Segment 8: Resilience, Reliability & Failure Fallbacks (6:30 – 7:15)
- **Time Allocation**: 45 seconds (Target word count: ~105 words)
- **On-Screen Display**:
  - Open `src/video_draft/adapters/reliable_generator.py` or `tests/unit/test_reliability.py`.
  - Show the fallback hierarchy and retry decorators.
  - Highlight negative test coverage: invalid brief schema rejection, model timeout retry, corrupt clip detection, and simulated CUDA OOM cascade.
- **Spoken Narration**:
  > "Robustness is essential for production video pipelines.
  >
  > In `test_reliability.py`, we verify automated recovery across four failure classes:
  > First, malformed briefs are cleanly rejected at the entry gate via Pydantic schema validation without crashing the runtime.
  > Second, transient network or lock errors trigger controlled scene-level retries up to 2 attempts.
  > Third, corrupt or truncated clips are detected during generation using ffprobe bitstream probing, triggering immediate regeneration.
  > And fourth, permanent failures—such as simulated CUDA Out-Of-Memory errors—immediately trigger our ranked fallback chain, gracefully cascading down to the CPU procedural engine to ensure a valid draft is always delivered."

---

### Segment 9: Free Compute Disclosure, Workbook & Sign-Off (7:15 – 7:45)
- **Time Allocation**: 30 seconds (Target word count: ~75 words)
- **On-Screen Display**:
  - Show `notebooks/video_draft_colab.ipynb` in VS Code or browser tab.
  - Show `submission/DISCLOSURE.md` and the official completed workbook: `submission/IncuBrix_PS03_Submission_Evaluation_Batch_Moderation_Workbook_COMPLETED.xlsx`.
  - Highlight the GitHub repository: `https://github.com/vinothinipalanivel2-dotcom/video-draft`.
- **Spoken Narration**:
  > "To conclude our assessment disclosure: this project uses zero paid APIs, zero proprietary services, and zero credit card subscriptions.
  >
  > For evaluators testing cloud accelerators, we have provided an executable Google Colab notebook supporting free-tier T4 GPUs.
  >
  > The official IncuBrix Submission Workbook is fully completed, cross-referenced with all empirical evidence, and synchronized with our public GitHub repository.
  >
  > Thank you for your review. `video-draft` is verified and ready for IncuBrix Track 03 evaluation."

---

## Quick-Reference Command Cheat-Sheet (For Recording)

Copy and paste these exact commands into your terminal during recording:

```powershell
# 1. Inspect repository status
git status

# 2. Run the end-to-end pipeline (Segment 4)
python -m video_draft.cli run --brief configs/briefs/baseline_16x9.json --output-dir outputs/demo_run

# 3. Clean up the temporary demo run folder after demonstration
Remove-Item -Recurse -Force outputs/demo_run

# 4. Run automated test suite (Segment 7)
python -m pytest tests/ -q

# 5. Run submission self-audit validator (Segment 7)
python scripts/verify_submission.py
```

---

## Post-Recording Video Checklist

Before uploading the final MP4 to your submission portal:
- [ ] **Total Runtime**: Under 8 minutes (Target: between 7m 15s and 7m 45s).
- [ ] **Resolution**: 1080p (1920x1080) or 720p (1280x720) in 16:9 landscape.
- [ ] **Audio Clarity**: Narration is audible, clear, and synchronized with screen actions.
- [ ] **Honesty Compliance**: All open models clearly identified as cataloged/routed, with active local execution accurately attributed to the CPU procedural engine.
- [ ] **Zero Secrets**: No API keys, credentials, personal tokens, or passwords visible on screen.
- [ ] **Unedited Flow**: The screen capture is a single unedited continuous demonstration as required by IncuBrix guidelines.
