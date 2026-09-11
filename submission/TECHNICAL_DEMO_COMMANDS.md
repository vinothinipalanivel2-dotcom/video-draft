# IncuBrix Track 03: Technical Demonstration Terminal Commands
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
