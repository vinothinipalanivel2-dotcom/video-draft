# Phase 6: End-to-End Quality, Evaluation & Production Hardening

## 1. Overview & Architectural Goals

The **End-to-End Quality & Evaluation Framework** provides comprehensive verification, provenance tracking, and release gating for the entire draft video pipeline:

CreativeBrief -> RouteDecision -> ScenePlan -> Clips -> Timeline -> Audio -> Final MP4 Video

The framework guarantees:
1. **Strict Final Media Validation**: Bitstream integrity, codec compliance, container decodability, duration tolerance, and resolution/aspect ratio conformance via FFmpeg stream probing and null muxing.
2. **Cross-Artifact Consistency**: Automated enforcement of 7 relational contracts ensuring downstream assets faithfully preserve upstream requirements.
3. **Cryptographic Manifest & Provenance**: Cryptographic SHA-256 hashing across all inputs, intermediates, and final outputs stored in a standardized AssetManifest.
4. **Multi-Format Subtitle Generation**: SubRip (.srt) and WebVTT (.vtt) caption generation directly synchronized with the deterministic scene plan.
5. **Objective 10-Dimension Quality Gate**: Automated evaluation scoring from 0.0 to 1.0 with explicit pass/fail gating.
6. **Pipeline Idempotency**: Safe, reproducible reruns with stale intermediate cleanup.

---

## 2. Final Media Validation (FinalMediaValidator)

The FinalMediaValidator (\src/video_draft/evaluation/media_validator.py\) inspects the assembled video artifact using FFmpeg tools:

| Validation Check | Method / Rule | Pass Criterion |
| :--- | :--- | :--- |
| **Existence & Size** | File system probe (\Path.stat\) | File exists and size >= 1024 bytes |
| **Stream Probing** | FFmpeg stream header inspection (\probe_media\) | Audio and video streams detected |
| **Bitstream Decodability**| Full stream decode via FFmpeg null muxer (\fmpeg -v error -i <path> -f null -\) | Exit code 0 without bitstream corruption errors |
| **Duration Precision** | Duration drift |t_actual - t_planned| <= delta | Drift within tolerance (delta = 0.5s default) |
| **Resolution & Aspect** | Probe dimensions: 1280x720 (16:9) or 720x1280 (9:16) | Dimensions and aspect ratio match exactly |
| **Frame Rate** | Probed fps vs minimum threshold | >= 20.0 fps (default 24/30 fps) |
| **Codec Compliance** | Video stream format string | Modern baseline codec (h264, hevc, vp9, av1) |
| **Audio Multiplexing** | Audio stream presence and sample rate | Audio stream present if required |

---

## 3. Cross-Artifact Consistency Checks (CrossArtifactConsistencyChecker)

The CrossArtifactConsistencyChecker (\src/video_draft/evaluation/consistency.py\) verifies consistency across stages:

- **Scene Count Match**: len(plan.scenes) == len(clips) == len(timeline.video_tracks)
- **Scene IDs & Ordering**: Scene IDs and indices match across Plan, Clip Artifacts, and Timeline tracks (1..N).
- **Duration Alignment**:
  - Total clip duration approx planned duration (<= 0.5s drift)
  - Timeline duration approx planned duration (<= 0.5s drift)
  - Final MP4 duration approx planned duration (<= 0.5s drift)
- **Timeline Continuity**: No temporal gaps or overlaps between adjacent clips (start_{i+1} == end_i).
- **Resolution & Aspect Ratio Alignment**: Brief aspect ratio matches Plan, Clips, and Timeline track resolutions.
- **Audio Alignment**: Audio track duration matches video duration within tolerance (<= 0.5s).
- **Provenance & Route Consistency**: Clip generator models match the routed primary or fallback model.

---

## 4. Manifest Builder & Cryptographic Provenance (ManifestBuilder)

The ManifestBuilder (\src/video_draft/evaluation/manifest_builder.py\) builds the standard AssetManifest (\src/video_draft/schema/manifest.py\):

- **SHA-256 Digest Computation**: Computes byte-level SHA-256 hashes for all pipeline artifacts (final_draft.mp4, scene_plan.json, timeline.json, route_decision.json, captions.srt, master_narration.wav, and all scene clips).
- **Execution Metadata**: Records unique execution ID, brief ID, ISO-8601 UTC timestamp, and reproducibility seed.
- **Model Provenance**: Captures all model capabilities utilized (checkpoints, license, revision, hardware).

---

## 5. Subtitle & Caption Generation

The subtitle module (\src/video_draft/audio/subtitles.py\) generates industry-standard timed captions from the deterministic scene plan:

- **SubRip (.srt)**: Formatted as sequential cues with comma millisecond timestamps (00:00:00,000 --> 00:00:05,000).
- **WebVTT (.vtt)**: Formatted with standard WEBVTT header and dot millisecond timestamps (00:00:00.000 --> 00:00:05.000).
- **Fallback Extraction**: Prioritizes scene.narration_text -> scene.overlay_text -> scene.title.

---

## 6. Objective Quality Gate (QualityGate)

The QualityGate (\src/video_draft/evaluation/quality_gate.py\) evaluates 10 dimensions:

| Dimension | Weight | Criteria |
| :--- | :---: | :--- |
| planning_validity | 0.10 | Plan has >= 1 scenes, valid strategy, positive duration |
| routing_validity | 0.10 | Route decision selected valid model, target hardware specified |
| generation_success | 0.15 | All planned beats have corresponding valid clip artifacts |
| clip_validity | 0.10 | All intermediate clips meet resolution, aspect ratio, fps thresholds |
| final_media_validity | 0.15 | Final MP4 probed, decodable, correct dimensions and codec |
| timing_accuracy | 0.10 | Duration drift |t_video - t_plan| <= 0.5s |
| audio_alignment | 0.10 | Audio track present, multiplexed, synchronized |
| assembly_validity | 0.10 | Timeline tracks match clip count and output video exists |
| cross_consistency | 0.10 | All 7 relational contracts satisfied |
| fallback_usage | Info | Telemetry on primary vs CPU fallback execution |

---

## 7. CLI Commands

### Evaluate Existing Manifest
\\ash
video-draft evaluate --manifest outputs/manifest.json
\
### Full Pipeline with Built-in Quality Gate
\\ash
video-draft run --brief configs/briefs/baseline_16x9.json --output-dir outputs/run1
\
