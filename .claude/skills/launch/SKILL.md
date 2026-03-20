---
name: launch
trigger: "Deploying a notebook to Google Colab via Drive mount, GitHub, or upload"
lifecycle_stage: launch
description: "Safe Colab deployment with Drive mounting, runtime selection, and data access patterns"
platform: colab
---

# Launch Skill — Colab Deployment

Google Colab has NO `push` equivalent like Kaggle. Deployment is manual or Drive-based. This skill covers the safe deployment workflow.

## 1. Pre-Run Validation (S8, S16.3)

Before executing ANY Colab notebook:

### Drive Mount Verification
```python
from google.colab import drive
drive.mount('/content/drive')

# Verify mount succeeded
import os
assert os.path.exists('/content/drive/MyDrive'), "Drive mount failed!"
print("Drive mounted successfully", flush=True)
```

### Data Access Verification
```python
# Verify all data files exist
import os
data_files = [
    '/content/drive/MyDrive/datasets/train.csv',
    '/content/drive/MyDrive/models/my-model/',
]
for f in data_files:
    exists = os.path.exists(f)
    status = "OK" if exists else "MISSING"
    print(f"[{status}] {f}", flush=True)
```

### Colab Secrets Verification
```python
from google.colab import userdata
try:
    hf_token = userdata.get('HF_TOKEN')
    print("HF_TOKEN: configured", flush=True)
except Exception:
    print("WARNING: HF_TOKEN not set in Colab Secrets", flush=True)
```

## 2. Colab Deployment Methods

### Method 1: Google Drive Upload (Recommended)
1. Upload `.ipynb` to Google Drive
2. Right-click > Open with > Google Colab
3. Change Runtime > Select GPU type
4. Run All

### Method 2: GitHub Integration
```
https://colab.research.google.com/github/{user}/{repo}/blob/{branch}/{path}.ipynb
```
- Open any GitHub notebook directly in Colab
- Changes are not saved back to GitHub (save to Drive first)

### Method 3: gdown for Data
```python
# Download files from Google Drive by share link
!pip install -q gdown
!gdown https://drive.google.com/uc?id=FILE_ID -O /content/data.zip
!unzip -q /content/data.zip -d /content/data/
```

### Method 4: Direct Upload
```python
from google.colab import files
uploaded = files.upload()  # Opens file picker dialog
```

## 3. Runtime Selection Guide

Before running, select the right hardware:

| Model Size | Minimum GPU | Colab Tier Required |
|-----------|-------------|---------------------|
| <=3B params (FP16) | T4 (15GB) | Free |
| <=7B params (FP16) | T4 (15GB, tight) | Free (with optimization) |
| <=7B params (comfortable) | L4 (24GB) | Pro |
| <=13B params (FP16) | A100 (40GB) | Pro+ |
| <=13B params (INT4) | L4 (24GB) | Pro |
| <=70B params (INT4) | A100 (80GB) | Pro+ |

**How to change runtime:**
Runtime > Change runtime type > Hardware accelerator > Select GPU

## 4. Dry-Run Validation Cell (S16.3)

Inject this validation cell to catch issues without running full training:

```python
# Dry-run validation cell — runs in <30 seconds
import importlib
import json

# 1. Verify all imports
for mod in ["torch", "transformers", "peft"]:
    try:
        importlib.import_module(mod)
        print(f"OK: {mod}", flush=True)
    except ImportError:
        print(f"MISSING: {mod} — add to install cell", flush=True)

# 2. Verify GPU access
import torch
if torch.cuda.is_available():
    print(f"GPU: {torch.cuda.get_device_name(0)}", flush=True)
    print(f"VRAM: {torch.cuda.get_device_properties(0).total_memory/1e9:.1f}GB", flush=True)
else:
    print("NO GPU — change runtime type!", flush=True)

# 3. Verify Drive mount
import os
if os.path.exists('/content/drive/MyDrive'):
    print("Drive: mounted", flush=True)
else:
    print("Drive: NOT mounted — run drive.mount() first", flush=True)

# 4. Verify model access (download only, no inference)
from transformers import AutoConfig
try:
    config = AutoConfig.from_pretrained("{model_repo}")
    print(f"Model config loaded: {config.model_type}", flush=True)
except Exception as e:
    print(f"Model access failed: {e}", flush=True)

print("DRY-RUN COMPLETE", flush=True)
```

## 5. Colab Session Persistence

### Keep Alive (Free Tier)
Free tier disconnects after ~90 minutes of idle. To keep alive during long downloads or processing:

```javascript
// Run in browser console (Ctrl+Shift+J / Cmd+Option+J)
function keepAlive() { 
    document.querySelector("colab-connect-button").click(); 
}
setInterval(keepAlive, 60000);
```

**Better approach:** Use checkpointing to survive disconnects:
```python
import os
CHECKPOINT_DIR = '/content/drive/MyDrive/checkpoints/my-run/'
os.makedirs(CHECKPOINT_DIR, exist_ok=True)

# In training callback:
if step % 500 == 0:
    model.save_pretrained(os.path.join(CHECKPOINT_DIR, f'step-{step}'))
    print(f"[CHECKPOINT] Saved at step {step}", flush=True)
```

## 6. Post-Launch Confirmation

After starting execution:
1. Verify first cells complete without errors
2. Check GPU is actually allocated (not CPU fallback)
3. Verify Drive mount persists
4. If immediate error: run blackbox skill for triage
5. If running: hand off to monitor skill

## References

- Case studies: CS-03 (Phantom Datasets), CS-09 (Five-Failure Gauntlet)
- Monitor skill: `.claude/skills/monitor/SKILL.md`
