---
name: check
trigger: "Before running a notebook on Google Colab"
lifecycle_stage: preflight
description: "Pre-run validation gate — catches environment mismatches before they burn Colab compute units"
platform: colab
---

# Check Skill — Colab Preflight Validation

Run this COMPLETE checklist before running ANY notebook on Colab. Every check traces to a governance section or post-incident review.

## Automated Validation

Run the preflight script against the notebook (platform defaults to colab):

```bash
python scripts/preflight_check.py notebook.ipynb --strict
```

Run environment parity check:

```bash
python scripts/env_parity.py notebook.ipynb
```

## 1. Syntax Validation (S9.3)

- `ast.parse()` every code cell — catches syntax errors before execution
- `json.load()` every JSON artifact (adapter configs, metadata, datasets) (S16.1.4)

## 2. Construction Checklist Gate (S4)

Verify ALL items from the build skill are present:

- [ ] Deterministic seeds set (torch, numpy, random) in Cell 1
- [ ] No `input()` calls anywhere in the notebook
- [ ] Every `import X` has a corresponding `pip install X` in an earlier cell
- [ ] Install and import are in separate cells (S12.1)
- [ ] All `print()` statements include `flush=True`
- [ ] Provenance metadata emission present (S4.4)
- [ ] Evaluation heartbeat pattern present for long-running loops (S4.5)

## 3. Colab Environment Checks

### Python & CUDA Compatibility
- **Python**: Colab runs 3.12 — check for 3.12-specific issues
- **CUDA**: 12.6 with cuDNN ~9.x
- **PyTorch**: ~2.8.0+cu126

### GPU Capability Gate (S11)

The notebook MUST validate GPU capability:

```python
import torch
if torch.cuda.is_available():
    cap = torch.cuda.get_device_capability(0)
    props = torch.cuda.get_device_properties(0)
    print(f"GPU: {props.name}, Capability: {cap}, VRAM: {props.total_memory/1e9:.1f}GB", flush=True)
    if cap[0] < 7:
        import os
        os.environ["TORCH_COMPILE_DISABLE"] = "1"
        print("WARNING: GPU capability < 7.0 — disabling torch.compile", flush=True)
else:
    print("WARNING: No GPU detected. Change Runtime > Hardware accelerator.", flush=True)
```

### Colab Tier Detection

```python
import torch
if torch.cuda.is_available():
    name = torch.cuda.get_device_name(0)
    vram = torch.cuda.get_device_properties(0).total_memory / 1e9
    if 'T4' in name:
        print(f"Colab Tier: Free/Pro (T4, {vram:.0f}GB VRAM)", flush=True)
    elif 'L4' in name:
        print(f"Colab Tier: Pro (L4, {vram:.0f}GB VRAM)", flush=True)
    elif 'A100' in name:
        print(f"Colab Tier: Pro+ (A100, {vram:.0f}GB VRAM)", flush=True)
```

## 4. Google Drive Persistence Check

If the notebook produces outputs that matter:

- [ ] `drive.mount('/content/drive')` is present
- [ ] Output paths point to `/content/drive/MyDrive/...`, NOT `/content/`
- [ ] Checkpoint callbacks save to Drive, not local `/content/`

**WARNING**: Everything in `/content/` is wiped on disconnect. No Drive mount = lost outputs.

## 5. Colab Secrets Check

- [ ] If notebook references gated models (meta-llama/, google/gemma, mistralai/), verify HF_TOKEN is configured in Colab Secrets
- [ ] No hardcoded tokens in notebook cells
- [ ] Authentication uses `from google.colab import userdata` pattern

## 6. The 6-Item Colab Checklist (S16.1)

| # | Check | Fix | Ref |
|---|-------|-----|-----|
| 1 | `bitsandbytes` + Python 3.12 = `triton.ops` conflict | Skip BNB for <=7B inference-only models | S16.1.1 |
| 2 | `torch.cuda.get_device_properties(0).total_memory` not `.total_mem` | Use correct attribute name | S16.1.2 |
| 3 | Gated models need HF auth — Colab requires manual token setup each session | Use Colab Secrets or ungated mirrors | S16.1.3 |
| 4 | Validate JSON files before use | `python -c "import json; json.load(open('file.json'))"` | S16.1.4 |
| 5 | `use_fast=False` can cause TypeError with some tokenizers | Test tokenizer loading locally first | S16.1.5 |
| 6 | Quote pip versions: `"pkg==1.0.0"` not `pkg>=1.0.0` | Shell interprets `>` as redirect without quotes | S16.1.6 |

## 7. Colab-Specific Path Checks

- [ ] No hardcoded local paths (/Users/, /home/username/, C:\)
- [ ] No Kaggle paths (/kaggle/working/, /kaggle/input/)
- [ ] No SageMaker paths (/home/ec2-user/)
- [ ] Working directory references use `/content/` or `/content/drive/MyDrive/`

## 8. Colab Runtime Timeout Awareness

| Tier | Max Session | Idle Timeout | GPU Quota |
|------|-------------|--------------|-----------|
| Free | 12 hours | ~90 minutes | Dynamic (CU-based) |
| Pro | 12 hours | ~90 minutes | 100 CU/month |
| Pro+ | 24 hours | None (while running) | 100 CU/month |

**Preflight check**: Estimate training time. If it exceeds tier timeout, warn and suggest checkpointing strategy.

## Output Format

```
PREFLIGHT REPORT: notebook.ipynb
Platform: colab
===================================
BLOCKERS (N):
  [B1] description (S-ref)
WARNINGS (N):
  [W1] description (S-ref)
INFO (N):
  [I1] description
VERDICT: PASS / FAIL (N blockers)
```

## References

- Scripts: `scripts/preflight_check.py`, `scripts/env_parity.py`
- Cheatsheet: `references/cheatsheet.md`
- Case studies: CS-06 (GPU Triton), CS-09 (Five-Failure Gauntlet)
