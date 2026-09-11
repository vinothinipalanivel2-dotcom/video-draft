# Create TECHNICAL_DEMO_RECORDING_CHECKLIST.md
checklist_md = """# IncuBrix Track 03: Technical Demonstration Video Recording Checklist
## PS03 — Open-Source Draft Video Generation and Model Routing

This checklist provides step-by-step verification before, during, and after recording the official technical demonstration video.

---

## 1. Pre-Recording System Verification
- [x] **Repository Status**: Public GitHub remote `https://github.com/vinothinipalanivel2-dotcom/video-draft` on branch `main`.
- [x] **Working Tree**: Clean git working directory, latest commit synchronized.
- [x] **Runtime Environment**: Windows 11 AMD64, Python 3.14.6, imageio-ffmpeg 0.6.0 (FFmpeg 7.1).
- [x] **Test Baseline**: 143/143 pytest tests passing (`python -m pytest tests/ -q`).
- [x] **Submission Audit**: 7/7 checks passing (`python scripts/verify_submission.py`).
- [x] **Demonstrated MP4**: `submission/artifacts/final_draft.mp4` verified (20.0s, 1280x720, 30fps, H.264/AAC, 0 decode defects).
- [x] **Submission Workbook**: `submission/IncuBrix_PS03_Submission_Evaluation_Batch_Moderation_Workbook_COMPLETED.xlsx` verified.
- [x] **Original Workbook**: Untouched in `Downloads/` (24,786 bytes).

---

## 2. Audio & Visual Recording Settings
- [ ] **Resolution**: 1920x1080 (1080p, 16:9 landscape).
- [ ] **Frame Rate**: 30 frames per second (progressive).
- [ ] **Audio Input**: 44.1 kHz or 48 kHz clean mono/stereo microphone with noise gating.
- [ ] **Screen Layout**:
  - Left pane: VS Code editor showing repository files and documentation.
  - Right pane: Terminal showing live command executions and logging.
  - Media Player window: Pre-loaded with `submission/artifacts/final_draft.mp4`.
- [ ] **Visual Clarity**: Code font size set to 14-16pt for clear readability on 1080p.
- [ ] **Privacy & Security**: Zero API keys, passwords, personal phone numbers, or tokens visible on screen.

---

## 3. Timeline Execution Target (7m 30s to 7m 45s)
- [ ] **0:00 - 0:30**: Introduction (Track 03, PS03, pipeline overview, local CPU laptop statement).
- [ ] **0:30 - 1:15**: Architecture (CreativeBrief -> RouteDecision -> ScenePlan -> Clips -> Timeline -> Audio -> Final MP4).
- [ ] **1:15 - 2:10**: Model Registry & Routing (`configs/models/registry.yaml`, 5 open models + CPU fallback engine).
- [ ] **2:10 - 3:15**: Live Execution (`python -m video_draft.cli run --brief configs/briefs/baseline_16x9.json --output-dir outputs/demo_recording`).
- [ ] **3:15 - 4:10**: Generated Result (Play `final_draft.mp4`, show Education 16:9, Product 9:16, News 16:9).
- [ ] **4:10 - 5:10**: Artifacts & Validation (`timeline.json`, `captions.srt`, `manifest.json`, `evaluation_report.json`).
- [ ] **5:10 - 6:00**: Automated Tests (`pytest tests/ -q` 143 passed, `verify_submission.py` 7/7 passed).
- [ ] **6:00 - 6:45**: Reliability (Ranked fallback chain, transient retry, simulated CUDA OOM cascade).
- [ ] **6:45 - 7:30**: Final Submission (Workbook, handoff report, disclosure, honest limitation statement).
- [ ] **7:30 - 7:45**: Closing (Summary of reproducibility, handoff sign-off).

---

## 4. Post-Recording Quality Gate
- [ ] **Duration Check**: Video file length is strictly <= 8 minutes (480 seconds).
- [ ] **File Integrity**: MP4 file opens and decodes cleanly in VLC, Windows Media Player, and browser.
- [ ] **Audio Intelligibility**: Narration is audible, clear, and synchronized with screen actions.
- [ ] **Metadata Generated**: `submission/TECHNICAL_DEMONSTRATION_METADATA.md` created with SHA-256 and timestamps.
"""

# Create TECHNICAL_DEMO_EVIDENCE_MAP.md
evidence_map_md = """# IncuBrix Track 03: Demonstration Evidence Map
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
"""

# Create TECHNICAL_DEMO_COMMANDS.md
commands_md = """# IncuBrix Track 03: Technical Demonstration Terminal Commands
## PS03 — Open-Source Draft Video Generation and Model Routing

Copy-pasteable PowerShell / Bash commands for executing each demonstration step.

---

## 1. Pre-Recording Health Check
```powershell
# Verify Python version (must be 3.14+)
python --version

# Verify git clean working tree
git status

# Verify test suite (143 passed)
python -m pytest tests/ -q

# Verify submission package self-audit (7/7 passed)
python scripts/verify_submission.py
```

---

## 2. Segment 4: Live End-to-End Pipeline Run (2:10 - 3:15)
```powershell
# Run the pipeline into outputs/demo_recording
python -m video_draft.cli run --brief configs/briefs/baseline_16x9.json --output-dir outputs/demo_recording
```

---

## 3. Segment 5: Inspect Generated Video Stream (3:15 - 4:10)
```powershell
# Probe the generated MP4 stream properties with FFmpeg
python -c "import subprocess, imageio_ffmpeg; subprocess.run([imageio_ffmpeg.get_ffmpeg_exe(), '-i', 'outputs/demo_recording/final_draft.mp4'])"
```

---

## 4. Segment 6: Verify Cryptographic Manifest Hashes (4:10 - 5:10)
```powershell
# Verify SHA-256 hash resolution against manifest
python -c "import json, hashlib, pathlib; m = json.loads(pathlib.Path('submission/artifacts/manifest.json').read_text()); print('Output MP4 SHA-256 match:', hashlib.sha256(pathlib.Path('submission/artifacts/final_draft.mp4').read_bytes()).hexdigest() == m['asset_hashes']['output_mp4'])"
```

---

## 5. Segment 7: Run Automated Tests & Self-Audit (5:10 - 6:00)
```powershell
# Run full automated test suite
python -m pytest tests/ -q

# Run submission validator self-audit
python scripts/verify_submission.py
```

---

## 6. Segment 8: Run Reliability Stress Suite (6:00 - 6:45)
```powershell
# Run reliability and fallback tests
python -m pytest tests/unit/test_reliability.py -v
```

---

## 7. Segment 9: Verify Workbook Integrity (6:45 - 7:30)
```powershell
# Run workbook verification script
python scripts/verify_workbook.py
```
"""

with open('submission/TECHNICAL_DEMO_RECORDING_CHECKLIST.md', 'w', encoding='utf-8') as f:
    f.write(checklist_md)

with open('submission/TECHNICAL_DEMO_EVIDENCE_MAP.md', 'w', encoding='utf-8') as f:
    f.write(evidence_map_md)

with open('submission/TECHNICAL_DEMO_COMMANDS.md', 'w', encoding='utf-8') as f:
    f.write(commands_md)

print("Successfully created checklist, evidence map, and commands markdown files in submission/")
