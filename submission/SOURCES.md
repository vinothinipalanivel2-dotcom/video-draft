# SOURCES & ATTRIBUTION MANIFEST
## IncuBrix Track 03: Open-Source Draft Video Generation and Model Routing
### Project: video-draft | Candidate: Vinothini Palanivel

This document provides a comprehensive and transparent manifest of all third-party open-source libraries, open-weight generative AI models, procedural media assets, and execution environments utilized in the ideo-draft project.

---

## 1. Third-Party Software Libraries & Media Engines

All libraries used in this project are permissively licensed open-source software installed via Python package indices (pip):

| Component | Version | Role in Pipeline | Source URL | License | Commercial Use |
| :--- | :--- | :--- | :--- | :--- | :---: |
| **FFmpeg** (via imageio-ffmpeg) | 7.1 (0.6.0) | Video stream filtering, scaling, cross-fades, audio muxing, decode validation | [ffmpeg.org](https://ffmpeg.org) | LGPL-2.1 / GPL | Yes |
| **Pillow** | >= 10.4.0 | Procedural frame rasterization, kinetic typography, geometry drawing | [python-pillow.org](https://python-pillow.org) | HPND | Yes |
| **NumPy** | >= 1.24.0 | Audio waveform synthesis, envelope modulation, multi-tone mathematical generation | [numpy.org](https://numpy.org) | BSD-3-Clause | Yes |
| **SoundFile** | >= 0.12.1 | Master audio narration WAV encoding and serialization (via libsndfile) | [github.com/bastibe/python-soundfile](https://github.com/bastibe/python-soundfile) | BSD-3-Clause / LGPL | Yes |
| **Pydantic** | >= 2.9.2 | Strict schema validation for CreativeBrief, ScenePlan, Timeline, and RouteDecision | [docs.pydantic.dev](https://docs.pydantic.dev) | MIT | Yes |
| **PyYAML** | >= 6.0.2 | Serialization and deserialization of model capability registry and sample briefs | [pyyaml.org](https://pyyaml.org) | MIT | Yes |
| **Click** | >= 8.1.7 | Command-line interface orchestration (ideo-draft run, plan, 
oute, ssemble, enchmark) | [palletsprojects.com/p/click/](https://palletsprojects.com/p/click/) | BSD-3-Clause | Yes |
| **Pytest** | >= 8.3.3 | Automated regression test harness, integration tests, benchmark validation | [pytest.org](https://pytest.org) | MIT | Yes |

---

## 2. Open-Weight Generative Video Models (Capability Registry)

The system catalogs 5 leading open-weight video diffusion architectures in configs/models/registry.yaml. These models are evaluated during capability routing based on official documentation, published checkpoints, and measured hardware requirements:

| Model Identifier | Architecture / Checkpoint | Primary Source Repository | License | Min VRAM | Est. Latency | Status in Local Run |
| :--- | :--- | :--- | :--- | :---: | :---: | :--- |
| wan2_1_t2v_1_3b | Wan2.1-T2V-1.3B-Diffusers | [Wan-AI/Wan2.1-T2V-1.3B](https://huggingface.co/Wan-AI/Wan2.1-T2V-1.3B) | Apache-2.0 | 8.0 GB | 65.0s | Cataloged / Evaluated in Router |
| cogvideox_2b | CogVideoX-2B | [THUDM/CogVideoX-2b](https://huggingface.co/THUDM/CogVideoX-2b) | Apache-2.0 | 10.0 GB | 55.0s | Cataloged / Evaluated in Router |
| ltx_video | LTX-Video-0.9.1 | [Lightricks/LTX-Video](https://huggingface.co/Lightricks/LTX-Video) | OpenRAIL | 12.0 GB | 35.0s | Cataloged / Evaluated in Router |
| hunyuan_video | HunyuanVideo | [tencent/HunyuanVideo](https://huggingface.co/tencent/HunyuanVideo) | Apache-2.0 | 24.0 GB | 150.0s | Cataloged / Filtered (VRAM > 16GB) |
| nimatediff_v3 | AnimateDiff-v3 | [guoyww/animatediff-motion-adapter-v1-5-3](https://huggingface.co/guoyww/animatediff-motion-adapter-v1-5-3) | Apache-2.0 | 6.0 GB | 20.0s | Cataloged / Evaluated in Router |
| cpu_procedural_engine | CPU-Procedural-Fallback-Engine | Internal (ideo-draft) | MIT | 0.0 GB | 2.5s | **Actively Executed on Host CPU** |

*Note on Execution Honesty*: Neural diffusion checkpoints for the 5 open models require 6-24 GB VRAM. To ensure 100% reliable, zero-cost, non-GPU execution on the host Windows laptop, the active end-to-end pipeline executes via the cpu_procedural_engine, which generates high-definition motion graphics, kinetic typography, and multi-scene drafts without GPU hardware. Free cloud accelerator execution is supported via 
otebooks/video_draft_colab.ipynb.

---

## 3. Media, Data & Audio Provenance

- **Video & Graphic Assets**: All visual elements are generated algorithmically using Pillow rasterization primitives, dynamic color themes, and geometric cards. No third-party stock footage, copyrighted photographs, or unconsented likenesses were used.
- **Narration & Audio**: Audio tracks are synthesized algorithmically using pure sinusoidal waves and envelope modulation generated with NumPy and written via SoundFile. No copyrighted music or synthetic voice clones were used.
- **Creative Briefs**: Original sample briefs (education_sample.yaml, 
ews_sample.yaml, product_sample.yaml) authored specifically for this assessment.

---

## 4. Payment & Commercial API Disclosure

- **Paid APIs**: Absolutely zero paid APIs or commercial services (e.g., OpenAI Sora, Runway Gen-2/3, Pika Labs, ElevenLabs) were used.
- **Payment / Credit Cards**: Zero monetary expenditure, subscriptions, or credit card registrations were made for this assessment.
- **Hosted Endpoints**: No undisclosed commercial cloud endpoints were queried.
