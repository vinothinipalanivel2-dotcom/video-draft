# Assessment Disclosure & Attribution
## IncuBrix Track 03: Open-Source Draft Video Generation and Model Routing

In compliance with the IncuBrix Candidate Assessment guidelines, this document provides a complete and factual disclosure of all tools, compute resources, third-party assets, AI assistance, and models utilized in this project.

---

### 1. AI Assistance
- **Tool / Environment**: Antigravity Agentic Coding Assistant (Google DeepMind).
- **Scope of AI Assistance**:
  - Architecture drafting, modular package design, and data schema definition.
  - Implementation of scene planner, archetype strategies, capability router, clip generation adapters, audio synthesizer, and FFmpeg assembler.
  - Authoring of automated unit, integration, and benchmark tests (	ests/).
  - Codebase refactoring, bug fixes (e.g. UTF-8 BOM decoding, test isolation), and validation script creation.
  - Documentation generation and requirements traceability mapping.
- **Human Guidance & Review**: Problem statement specification, milestone boundaries, test inspection, and independent validation verification.

---

### 2. External Tools & Libraries
- **Language Runtime**: Python 3.14.6 (64-bit).
- **Media Engine**: FFmpeg version 7.1 (bundled via imageio-ffmpeg 0.6.0).
- **CLI Framework**: click (>= 8.1.0).
- **Validation & Schemas**: pydantic (>= 2.5.0).
- **Configuration & Serialization**: pyyaml (>= 6.0).
- **Media & Audio Processing**: soundfile (>= 0.12.0), 
umpy (>= 1.24.0), pillow (>= 10.0.0).
- **Test Framework**: pytest (>= 7.4.0), pluggy (>= 1.6.0), nyio (>= 4.14.0).
- **Zero Paid Tools**: Absolutely no commercial software, proprietary SaaS tools, or paid subscriptions.

---

### 3. Compute Resources
- **Local Host**: Intel(R) Core(TM) / AMD64 architecture running Windows 11 Home / Professional.
- **Hardware Acceleration**: None (has_cuda: false). 100% of pipeline orchestration, planning, routing, procedural clip generation, audio synthesis, FFmpeg assembly, validation, and quality gate evaluation runs on standard host CPU.
- **Target Free Compute Tiers**: The system architecture provides modular ingestion adapters compatible with free accelerator tiers (Google Colab T4, Kaggle GPU P100, Hugging Face ZeroGPU). A verified Colab notebook is provided at 
otebooks/video_draft_colab.ipynb.

---

### 4. Third-Party Assets
- **Visual Assets**: Procedurally generated frames using Python Pillow drawing primitives, geometric shapes, and built-in bitmap fonts. Zero copyrighted images or proprietary stock footage.
- **Audio Assets**: Procedurally generated multi-tone sinusoidal waveforms with envelope modulation synthesized via NumPy and written via SoundFile. Zero copyrighted music or voice samples.
- **Creative Briefs**: Original scientific, technology explainer, and product demonstration scenarios authored specifically for this project.

---

### 5. Manual Editing
- All code and documentation were generated, tested, and validated through the documented agentic workflow. No closed-source manual alterations or external binary patches were applied.

---

### 6. Model Usage & Open Weights
- **Evaluated Models**: Five open-weight generative video models cataloged with verified Hugging Face checkpoints, Apache-2.0 or OpenRAIL licenses, and parameter counts:
  1. Wan2.1-T2V-1.3B (Wan-AI/Wan2.1-T2V-1.3B-Diffusers, Apache-2.0)
  2. CogVideoX-2B (THUDM/CogVideoX-2b, Apache-2.0)
  3. LTX-Video-0.9.1 (Lightricks/LTX-Video, OpenRAIL)
  4. HunyuanVideo (	encent/HunyuanVideo, Apache-2.0)
  5. AnimateDiff-v3 (guoyww/animatediff-motion-adapter-v1-5-3, Apache-2.0)
- **Local Runtime Engine**: cpu_procedural_engine (local kinetic typography and pan/zoom procedural motion generator) executed locally on host CPU without GPU requirements.
- **Zero Commercial Model APIs**: No OpenAI (Sora), Runway Gen-2/3, Pika, Kling, or ElevenLabs APIs.

---

### 7. Hardware Accelerators
- **Status**: No hardware accelerators (CUDA, MPS, ROCm) were utilized during local execution. The entire pipeline operates autonomously in local CPU mode.
