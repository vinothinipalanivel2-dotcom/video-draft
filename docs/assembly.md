# Video Clip Synthesis & FFmpeg Assembly

**Project**: `video-draft` (IncuBrix Track 03: Open-Source Draft Video Generation and Model Routing)  
**Modules**: 
- `video_draft.adapters` (`base.py`, `procedural_generator.py`, `mock_generator.py`, `validator.py`, `factory.py`)
- `video_draft.audio` (`generator.py`)
- `video_draft.assembly` (`ffmpeg_assembler.py`, `timeline_builder.py`, `ffmpeg_tools.py`)
**Schemas**: `video_draft.schema.scene_plan`, `video_draft.schema.timeline`

---

## 1. Architectural Pipeline Overview

Phase 4 implements intermediate video clip synthesis, strict clip validation, audio narration preparation, and FFmpeg filtergraph timeline assembly.

The execution flow adheres strictly to the architectural boundary:

$$\text{CreativeBrief} \longrightarrow \text{ScenePlanner} \longrightarrow \text{ScenePlan} \longrightarrow \text{Capability Router} \longrightarrow \text{Clip Generation} \longrightarrow \text{Clip Validation} \longrightarrow \text{Assembly} \longrightarrow \text{Final Video}$$

```
+---------------------------------------------------------------------------------------------------------+
|                                           CREATIVE BRIEF                                                |
|                                (Genre, Target Duration, 16:9 / 9:16)                                    |
+---------------------------------------------------------------------------------------------------------+
                                                     |
                                                     v
+---------------------------------------------------------------------------------------------------------+
|                                            SCENE PLANNER                                                |
|                              (Deterministic multi-beat scene breakdown)                                 |
+---------------------------------------------------------------------------------------------------------+
                                                     |
                                                     v
+---------------------------------------------------------------------------------------------------------+
|                                          CAPABILITY ROUTER                                              |
|                      (Evaluates open-weight models; routes to CPU engine or GPU)                        |
+---------------------------------------------------------------------------------------------------------+
                                                     |
                     +-------------------------------+-------------------------------+
                     |                                                               |
                     v                                                               v
+-----------------------------------------+                     +-----------------------------------------+
|          AUDIO NARRATION PATH           |                     |          VIDEO CLIP GENERATOR           |
|      (DeterministicAudioGenerator)      |                     |    (ProceduralClipGenerator / Mock)     |
|  - Generates 44.1kHz 16-bit PCM WAV     |                     |  - Renders exact planned duration       |
|  - Aligns scene narration chunks        |                     |  - Applies archetype color palettes     |
|  - Stitches master narration track      |                     |  - Draws burned titles & overlay badges |
+-----------------------------------------+                     +-----------------------------------------+
                     |                                                               |
                     |                                                               v
                     |                                  +-----------------------------------------+
                     |                                  |             CLIP VALIDATOR              |
                     |                                  |  - Probes file existence & stream bytes |
                     |                                  |  - Verifies duration drift <= 0.35s     |
                     |                                  |  - Validates 16:9 or 9:16 aspect ratio  |
                     |                                  |  - Verifies monotonic sequence ordering |
                     |                                  +-----------------------------------------+
                     |                                                               |
                     +-------------------------------+-------------------------------+
                                                     |
                                                     v
+---------------------------------------------------------------------------------------------------------+
|                                            TIMELINE BUILDER                                             |
|                              (Constructs & serializes editable timeline.json)                           |
+---------------------------------------------------------------------------------------------------------+
                                                     |
                                                     v
+---------------------------------------------------------------------------------------------------------+
|                                            FFMPEG ASSEMBLER                                             |
|  - Discovers FFmpeg binary (PATH, FFMPEG_PATH, or bundled imageio-ffmpeg)                               |
|  - Normalizes clips: scale preserving aspect ratio, pad to target resolution, setsar=1, format=yuv420p  |
|  - Interprets transitions: fade, dissolve, cut, wipe                                                    |
|  - Muxes master narration audio track: -c:v libx264 -c:a aac -b:a 192k -movflags +faststart             |
+---------------------------------------------------------------------------------------------------------+
                                                     |
                                                     v
                                       [final_draft.mp4 Verified]
```

---

## 2. Clip Generation Abstraction

The system provides a clean, provider-agnostic interface allowing local procedural rendering, deterministic testing, or remote open-weight inference adapters without modifying assembly business logic.

### Base Interface & Artifact Schema

- **`ClipArtifact`**:
  - `scene_id` (str): Identifier matching `SceneBeat.scene_id`
  - `scene_index` (int): 1-based sequential scene index
  - `asset_path` (str): Filesystem path to rendered MP4
  - `asset_hash` (str): SHA-256 cryptographic digest of media file
  - `duration_sec` (float): Exact clip duration
  - `width` (int) & `height` (int): Pixel dimensions
  - `fps` (int): Frame rate (default: 30)
  - `generator_model` (str): Engine ID used for rendering
  - `transition_in` & `transition_out`: In/out effects

- **`BaseClipGenerator` (ABC)**:
  ```python
  @abstractmethod
  def generate_clip(
      self,
      beat: SceneBeat,
      model_id: str,
      aspect_ratio: str,
      output_dir: Path,
  ) -> ClipArtifact: ...
  ```

### Implemented Generators

1. **`ProceduralClipGenerator`**:
   - Primary CPU fallback engine (`cpu_procedural_engine`).
   - Generates high-quality, standardized MP4 clips using FFmpeg procedural filters (`lavfi` color, test patterns, text rendering) locally on non-GPU laptops.
   - Tailors color schemes by archetype:
     - **Education**: Dark slate blue / scholastic navy (`#1e293b`, `#0f172a`, `#1e3a5f`)
     - **News**: Deep crimson / broadcast indigo (`#3b0764`, `#450a0a`, `#172554`)
     - **Product**: Sleek titanium / matte obsidian (`#18181b`, `#27272a`, `#09090b`)
   - Burns scene title and subtitle/overlay tags directly into the video stream.

2. **`MockClipGenerator`**:
   - Ultra-fast deterministic generator for unit testing and offline development.
   - Computes deterministic SHA-256 hashes, exact durations, and supports simulated failure injection (`fail_on_scene_id`).

3. **`get_clip_generator(model_id, mock, allow_cpu_fallback)` Factory**:
   - Dynamically selects generator based on routing decision.
   - For open-weight GPU models (`zeroscope_v2_576w`, `cogvideox_2b`, etc.), seamlessly utilizes CPU procedural fallback when running on non-accelerator laptops.

---

## 3. Strict Clip Validation Layer

Every intermediate clip is rigorously validated before assembly. Invalid clips immediately halt processing with actionable errors:

### Validation Rules

| Dimension | Constraint | Failure Exception |
| :--- | :--- | :--- |
| **File Existence** | File must exist on disk and be accessible | `ClipValidationError(field="file_existence")` |
| **Integrity & Size** | File size must exceed 128 bytes (guards against truncated files) | `ClipValidationError(field="file_size")` |
| **Scene Alignment** | `clip.scene_id` and `clip.scene_index` must match planned beat | `ClipValidationError(field="scene_id" / "scene_index")` |
| **Duration Precision** | $| \text{clip.duration\_sec} - \text{beat.duration\_sec} | \le 0.35\text{s}$ | `ClipValidationError(field="duration")` |
| **Aspect Ratio (16:9)** | Frame width must exceed frame height ($1280 \times 720$) | `ClipValidationError(field="aspect_ratio")` |
| **Aspect Ratio (9:16)** | Frame height must exceed frame width ($720 \times 1280$) | `ClipValidationError(field="aspect_ratio")` |
| **Frame Rate** | FPS must be $\ge 10$ fps | `ClipValidationError(field="fps")` |
| **Stream Decoding** | FFmpeg stderr probing decodes video stream headers without corruption | `ClipValidationError(field="media_stream_decode")` |
| **Sequence Continuity** | Clip count, ordering ($1 \dots N$), and cumulative duration match `ScenePlan` | `ClipValidationError(field="sequence_order" / "clip_count")` |

---

## 4. Audio Narration Path

Audio generation is decoupled from video synthesis and assembly:

1. **`DeterministicAudioGenerator`**:
   - Uses Python standard library (`wave`, `struct`, `math`) without requiring external TTS API keys, credit cards, or GPU compute.
   - Generates 44.1 kHz 16-bit PCM mono WAV audio with exact sample counts:
     $$\text{samples} = \lfloor \text{duration\_sec} \times \text{sample\_rate} \rfloor$$
   - Features gentle acoustic wave envelopes with smooth 50ms fade-in/fade-out to prevent audio clicking.

2. **Master Timeline Narration Stitching**:
   - `build_narration_track(beats, output_path)` stitches individual narration chunks into a master audio track aligned with `beat.start_sec`.
   - The master track duration matches the video timeline duration.

---

## 5. FFmpeg Assembly & Transition Filtergraphs

The assembly engine (`FFmpegAssembler`) normalizes video geometry, applies transitions, and muxes audio into standard MP4 format:

### Geometry Normalization Filtergraph
Each input video stream $i$ is scaled and padded to ensure consistent resolution and pixel format regardless of source model variations:
```
[i:v]scale=W:H:force_original_aspect_ratio=decrease,pad=W:H:(ow-iw)/2:(oh-ih)/2,setsar=1,format=yuv420p[vi]
```

### Transition Interpretation
- **`fade` / `dissolve`**: Smooth crossfade / fade-to-black transition:
  - In: `fade=t=in:st=0:d=0.35`
  - Out: `fade=t=out:st=(duration - 0.35):d=0.35`
- **`cut` / `none`**: Direct hard cut concatenation.
- **`wipe`**: Directional wipe transition.
- Concatenation:
  ```
  [v0][v1]...[vN-1]concat=n=N:v=1:a=0[v_out]
  ```

### Audio Muxing & Encoding
- Video codec: `libx264`, preset `fast`, pixel format `yuv420p`.
- Audio codec: `aac` at 192 kbps.
- Container: MP4 with `+faststart` (web-optimized moov atom placement).

### Environment Discovery
FFmpeg is discovered automatically using the following hierarchy:
1. `FFMPEG_PATH` environment variable override
2. System `PATH` (`shutil.which("ffmpeg")`)
3. Bundled static binary via `imageio-ffmpeg` (`imageio_ffmpeg.get_ffmpeg_exe()`)
If no binary is found, a clear `FFmpegNotFoundError` is raised with installation instructions.

---

## 6. CLI Commands & Usage

### 1. Clip Generation
```bash
video-draft generate --scene-plan outputs/scene_plan.json --output-dir outputs/clips
```
*Optional flag: `--mock` for fast dry-run testing.*

### 2. Timeline Assembly
```bash
video-draft assemble --timeline outputs/timeline.json --output outputs/final_draft.mp4
```

### 3. Full End-to-End Pipeline
```bash
video-draft run --brief configs/briefs/baseline_16x9.json --output-dir outputs/e2e_run --force-cpu
```
Supports both 16:9 widescreen briefs and 9:16 vertical briefs (`configs/briefs/baseline_9x16.json`).

---

## 7. Verification & Test Strategy

All media operations are verified by an automated test suite that requires no external network or GPU:

| Test Module | Coverage | Status |
| :--- | :--- | :--- |
| `tests/unit/test_adapters.py` | Generator abstraction, mock generator, procedural generation, factory routing, failure simulation | **5 / 5 PASS** |
| `tests/unit/test_validator.py` | Valid clips, missing files, corrupt files, duration drift, aspect ratio, frame rate, sequence continuity | **9 / 9 PASS** |
| `tests/unit/test_audio.py` | WAV PCM synthesis, sample counts, timing alignment, master track stitching, empty list rejection | **3 / 3 PASS** |
| `tests/unit/test_assembly.py` | FFmpeg discovery, transition filter syntax, TimelineBuilder serialization, end-to-end assembly, audio mux | **4 / 4 PASS** |
| `tests/unit/test_cli.py` | Stubs compatibility, real plan generation, timeline assembly, full pipeline run | **15 / 15 PASS** |
| **All Existing Tests** | Phase 1, Phase 2, Phase 3 tests (registry, router, planner, logger, config, imports) | **80 / 80 PASS** |
| **Total Test Suite** | Full regression and new Phase 4 test suite | **103 / 103 PASS** |
