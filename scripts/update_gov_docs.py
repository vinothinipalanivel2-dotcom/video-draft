from pathlib import Path

gov_content = """# Open-Source Model Governance & Attribution
## IncuBrix Track 03: Open-Source Draft Video Generation and Model Routing

## 1. Compliance Statement

All generative video models cataloged in `configs/models/registry.yaml` adhere strictly to IncuBrix Track 03 requirements:
- **100% Open Weights**: Publicly accessible checkpoints hosted on Hugging Face / GitHub.
- **Disclosed Open Licenses**: Permissive or research-open licenses (Apache-2.0, OpenRAIL).
- **Zero Commercial API Spend**: No proprietary APIs, no OpenAI/Runway keys, no credit card requirements.

---

## 2. Model Capability Registry & Attribution

The capability registry catalogs 5 open generative models plus 1 zero-GPU CPU fallback engine:

| Model ID | Display Name | Organization / Checkpoint | License | Commercial Use | Min VRAM | Est. Latency | Status / Role |
| :--- | :--- | :--- | :--- | :---: | :---: | :---: | :--- |
| `wan2_1_t2v_1_3b` | Wan2.1-T2V-1.3B | `Wan-AI/Wan2.1-T2V-1.3B` | Apache-2.0 | Yes | 8.0 GB | 65.0s | Active candidate |
| `cogvideox_2b` | CogVideoX-2B | `THUDM/CogVideoX-2b` | Apache-2.0 | Yes | 10.0 GB | 55.0s | Active candidate |
| `ltx_video` | LTX-Video-0.9.1 | `Lightricks/LTX-Video` | OpenRAIL | Yes | 12.0 GB | 35.0s | Fast sampling candidate |
| `hunyuan_video` | HunyuanVideo | `tencent/HunyuanVideo` | Apache-2.0 | Yes | 24.0 GB | 150.0s | Filtered out (high VRAM/latency) |
| `animatediff_v3` | AnimateDiff-v3 | `guoyww/animatediff-motion-adapter-v1-5-3` | Apache-2.0 | Yes | 6.0 GB | 20.0s | Active candidate |
| `cpu_procedural_engine` | CPU-Procedural-Fallback-Engine | `local:procedural-v1` | Apache-2.0 | Yes | 0.0 GB | 2.5s | Guaranteed CPU fallback |

---

## 3. Fallback Hierarchy & Resolution Rules

When generative models exceed local hardware constraints (e.g. non-GPU host, constrained VRAM, or brief duration boundaries) or encounter runtime generation errors, the Capability Router automatically cascades down the deterministic fallback chain:

$$\\text{Preferred Model} \\longrightarrow \\text{Ranked Open Alternatives} \\longrightarrow \\text{CPU Procedural Fallback Engine}$$

- **Transient Errors**: Network timeouts or temporary file locks trigger controlled retry (up to 2 attempts).
- **Permanent Errors**: CUDA OOM, unsupported codec, or hardware unavailability immediately triggers cascade to the next candidate.
- **Guaranteed Output**: The `cpu_procedural_engine` operates with 0 GB VRAM requirement, guaranteeing that a valid, decodable draft MP4 is always assembled.
"""

Path("submission/model_governance.md").write_text(gov_content.strip() + "\n", encoding="utf-8")
Path("docs/model_governance.md").write_text(gov_content.strip() + "\n", encoding="utf-8")
print("Updated model governance docs to match registry.yaml.")
