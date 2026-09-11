# IncuBrix Track 03: Technical Demonstration Video Recording Checklist
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
